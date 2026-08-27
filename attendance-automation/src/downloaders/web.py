"""웹 ERP 자동화 엔진 (playwright). ERP가 브라우저 방식일 때 사용.

지원 액션:
  goto                          url 로 이동
  fill      selector, value     입력란에 값 입력
  click     selector            클릭
  select    selector, value     드롭다운 선택
  wait      seconds             대기
  wait_for  selector            해당 요소가 나타날 때까지 대기
  download  selector            클릭 → 다운로드 파일을 download_dir 에 저장
"""
from pathlib import Path

from ..config import substitute
from ..logger import get_logger

log = get_logger()


class WebDownloader:
    def __init__(self, source: dict, general: dict, variables: dict):
        self.src = source
        self.general = general
        self.vars = variables

    def _sub(self, value):
        return substitute(value, self.vars) if isinstance(value, str) else value

    def run(self):
        from playwright.sync_api import sync_playwright

        log.info("=== [%s] 웹 다운로드 시작 ===", self.src["name"])
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.src.get("headless", False))
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            try:
                for i, step in enumerate(self.src["steps"], 1):
                    action = step["action"]
                    log.info("[%s] 단계 %d: %s", self.src["name"], i, action)
                    if action == "goto":
                        page.goto(self._sub(self.src["url"]))
                    elif action == "fill":
                        page.fill(step["selector"], self._sub(step["value"]))
                    elif action == "click":
                        page.click(step["selector"])
                    elif action == "select":
                        page.select_option(step["selector"], self._sub(step["value"]))
                    elif action == "wait":
                        page.wait_for_timeout(step["seconds"] * 1000)
                    elif action == "wait_for":
                        page.wait_for_selector(step["selector"], timeout=step.get("timeout", 30) * 1000)
                    elif action == "download":
                        with page.expect_download(timeout=step.get("timeout", 120) * 1000) as dl:
                            page.click(step["selector"])
                        download = dl.value
                        dest = Path(self.general["download_dir"]) / download.suggested_filename
                        download.save_as(dest)
                        log.info("다운로드 완료: %s", dest)
                    else:
                        raise ValueError(f"알 수 없는 액션: {action}")
            except Exception:
                shot = Path(__file__).resolve().parents[2] / "logs" / f"error_{self.src['name']}.png"
                shot.parent.mkdir(exist_ok=True)
                page.screenshot(path=str(shot))
                log.error("오류 시점 화면 캡처 저장: %s", shot)
                raise
            finally:
                browser.close()
        log.info("=== [%s] 웹 다운로드 완료 ===", self.src["name"])
