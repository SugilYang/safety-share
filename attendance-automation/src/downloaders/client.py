"""PC 설치 프로그램(세콤매니저, K-System ERP 등) 자동화 엔진.

config.yaml 의 steps 목록을 순서대로 실행한다. 지원 액션:

  start_app                        프로그램 실행 (이미 떠 있으면 그 창에 연결)
  wait_window   timeout            메인 창이 뜰 때까지 대기
  click         control            버튼/탭/메뉴 클릭
  double_click  control            더블클릭
  set_text      control, value     입력란에 값 입력
  send_keys     keys               키 입력 (예: "{ENTER}", "%{F4}")
  select_menu   path               메뉴 선택 (예: "파일->내보내기->엑셀")
  click_xy      x, y               화면 좌표 클릭 (컨트롤 인식이 안 될 때 최후 수단)
  wait          seconds            대기
  save_dialog   filename           '다른 이름으로 저장' 대화상자에 경로 입력 후 저장
  wait_file     timeout            expect_file_pattern 파일이 생길 때까지 대기
  close_app                        프로그램 종료

control 지정 방법 (inspect_windows.py 결과에서 확인):
  {auto_id: "txtUserId"}                        AutomationId 로 찾기 (가장 확실)
  {title: "로그인", control_type: "Button"}      표시 텍스트 + 종류로 찾기
  {title_re: "조회.*"}                           정규식으로 찾기
"""
import glob
import time
from pathlib import Path

from ..config import substitute
from ..logger import get_logger

log = get_logger()


class ClientDownloader:
    def __init__(self, source: dict, general: dict, variables: dict):
        self.src = source
        self.general = general
        self.vars = variables
        self.app = None
        self.win = None

    # ---------------- 내부 유틸 ----------------

    def _sub(self, value):
        return substitute(value, self.vars) if isinstance(value, str) else value

    def _find_control(self, spec: dict):
        crit = {}
        if "auto_id" in spec:
            crit["auto_id"] = spec["auto_id"]
        if "title" in spec:
            crit["title"] = self._sub(spec["title"])
        if "title_re" in spec:
            crit["title_re"] = spec["title_re"]
        if "control_type" in spec:
            crit["control_type"] = spec["control_type"]
        if "class_name" in spec:
            crit["class_name"] = spec["class_name"]
        ctrl = self.win.child_window(**crit)
        ctrl.wait("exists visible", timeout=spec.get("timeout", 20))
        return ctrl

    def _existing_files(self) -> set:
        pattern = str(Path(self.general["download_dir"]) / self.src["expect_file_pattern"])
        return set(glob.glob(pattern))

    # ---------------- 액션 구현 ----------------

    def _do_start_app(self, step):
        from pywinauto import Application

        backend = self.src.get("backend", "uia")
        exe = self.src["exe_path"]
        try:
            self.app = Application(backend=backend).connect(
                title_re=self.src["window_title_re"], timeout=3
            )
            log.info("이미 실행 중인 프로그램에 연결: %s", self.src["name"])
        except Exception:
            log.info("프로그램 실행: %s", exe)
            self.app = Application(backend=backend).start(exe)

    def _do_wait_window(self, step):
        self.win = self.app.window(title_re=self.src["window_title_re"])
        self.win.wait("exists visible", timeout=step.get("timeout", 30))
        self.win.set_focus()
        log.info("창 감지됨: %s", self.win.window_text())

    def _do_click(self, step):
        self._find_control(step["control"]).click_input()

    def _do_double_click(self, step):
        self._find_control(step["control"]).double_click_input()

    def _do_set_text(self, step):
        ctrl = self._find_control(step["control"])
        value = self._sub(step["value"])
        ctrl.click_input()
        ctrl.type_keys("^a{DELETE}", set_foreground=False)
        ctrl.type_keys(value, with_spaces=True, set_foreground=False)

    def _do_send_keys(self, step):
        from pywinauto.keyboard import send_keys
        self.win.set_focus()
        send_keys(self._sub(step["keys"]))

    def _do_select_menu(self, step):
        self.win.menu_select(self._sub(step["path"]))

    def _do_click_xy(self, step):
        import pyautogui
        pyautogui.click(step["x"], step["y"])

    def _do_wait(self, step):
        time.sleep(step["seconds"])

    def _do_save_dialog(self, step):
        """표준 '다른 이름으로 저장' 대화상자에 전체 경로를 입력하고 저장."""
        from pywinauto import Desktop
        from pywinauto.keyboard import send_keys

        filename = self._sub(step["filename"])
        full_path = str(Path(self.general["download_dir"]) / filename)

        dlg = Desktop(backend="win32").window(title_re=".*(저장|Save).*")
        dlg.wait("exists visible", timeout=step.get("timeout", 30))
        dlg.set_focus()
        time.sleep(1)
        send_keys(full_path, with_spaces=True)
        time.sleep(0.5)
        send_keys("{ENTER}")
        # '덮어쓰기' 확인창이 뜨면 예 선택
        time.sleep(1.5)
        try:
            confirm = Desktop(backend="win32").window(title_re=".*(확인|Confirm).*")
            if confirm.exists(timeout=2):
                send_keys("{ENTER}")
        except Exception:
            pass
        log.info("저장 경로 입력: %s", full_path)

    def _do_wait_file(self, step):
        timeout = step.get("timeout", 60)
        deadline = time.time() + timeout
        while time.time() < deadline:
            new = self._existing_files() - self._before_files
            # 파일 크기가 안정될 때까지(쓰기 완료) 확인
            for f in new:
                size1 = Path(f).stat().st_size
                time.sleep(2)
                if Path(f).stat().st_size == size1 and size1 > 0:
                    log.info("다운로드 완료: %s", f)
                    return
            time.sleep(2)
        raise TimeoutError(
            f"{timeout}초 내에 '{self.src['expect_file_pattern']}' 파일이 생성되지 않았습니다."
        )

    def _do_close_app(self, step):
        try:
            self.app.kill()
        except Exception:
            pass

    # ---------------- 실행 ----------------

    def run(self):
        log.info("=== [%s] 다운로드 시작 ===", self.src["name"])
        self._before_files = self._existing_files()
        try:
            for i, step in enumerate(self.src["steps"], 1):
                action = step["action"]
                log.info("[%s] 단계 %d: %s", self.src["name"], i, action)
                getattr(self, f"_do_{action}")(step)
        except Exception:
            # 실패 시 화면 캡처를 남겨 원인 파악에 사용
            self._screenshot_on_error()
            raise
        finally:
            if any(s.get("action") == "close_app" for s in self.src["steps"]) is False:
                self._do_close_app({})
        log.info("=== [%s] 다운로드 완료 ===", self.src["name"])

    def _screenshot_on_error(self):
        try:
            import pyautogui
            shot_dir = Path(__file__).resolve().parents[2] / "logs"
            shot_dir.mkdir(exist_ok=True)
            path = shot_dir / f"error_{self.src['name']}_{int(time.time())}.png"
            pyautogui.screenshot(str(path))
            log.error("오류 시점 화면 캡처 저장: %s", path)
        except Exception:
            pass
