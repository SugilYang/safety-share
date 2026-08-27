"""화면 구조 진단 도구.

세콤매니저/ERP 를 자동화하려면 버튼·입력란의 '이름표'(AutomationId, 텍스트)가
필요합니다. 이 도구를 회사 PC에서 실행하면 현재 떠 있는 프로그램의 구조를
텍스트 파일로 뽑아 줍니다. 그 결과를 Claude에게 붙여넣으면
config.yaml 의 steps 를 완성할 수 있습니다.

사용법 (프로그램을 먼저 실행해서 자동화할 화면을 띄운 상태에서):

  python -m src.tools.inspect_windows                # 떠 있는 창 목록 보기
  python -m src.tools.inspect_windows "세콤"          # 제목에 '세콤'이 들어간 창 구조 덤프
  python -m src.tools.inspect_windows "세콤" win32    # uia 로 안 잡힐 때 win32 백엔드로

결과는 logs/inspect_결과.txt 에도 저장됩니다.
"""
import sys
from pathlib import Path

from pywinauto import Desktop

OUT = Path(__file__).resolve().parents[2] / "logs" / "inspect_결과.txt"


def list_windows():
    print("=== 현재 떠 있는 창 목록 ===")
    for w in Desktop(backend="uia").windows():
        title = w.window_text().strip()
        if title:
            print(f"  제목: {title!r}   클래스: {w.class_name()}")
    print("\n다음 단계: python -m src.tools.inspect_windows \"창제목일부\"")


def dump_window(keyword: str, backend: str = "uia"):
    win = Desktop(backend=backend).window(title_re=f".*{keyword}.*")
    win.wait("exists", timeout=10)
    OUT.parent.mkdir(exist_ok=True)

    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        win.print_control_identifiers(depth=None)
    text = buf.getvalue()

    OUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"\n=== 위 내용이 {OUT} 에 저장되었습니다 ===")
    print("이 파일 내용을 Claude에게 붙여넣어 주세요.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        list_windows()
    else:
        dump_window(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "uia")
