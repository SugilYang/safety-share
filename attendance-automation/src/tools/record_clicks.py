"""좌표 기록 도구 (폴백용).

inspect_windows.py 로 컨트롤이 인식되지 않는 프로그램(그림으로만 그려진 화면 등)은
화면 좌표 클릭(click_xy)으로 자동화해야 합니다. 이 도구를 실행한 뒤
자동화할 버튼 위에 마우스를 올리고 F8 을 누르면 좌표가 기록됩니다.
ESC 로 종료하면 기록된 좌표가 config.yaml 에 붙여넣을 수 있는 형태로 출력됩니다.

  python -m src.tools.record_clicks
"""
import pyautogui

try:
    import keyboard  # pip install keyboard
except ImportError:
    print("먼저 설치하세요: pip install keyboard")
    raise SystemExit(1)

print("버튼 위에 마우스를 올리고 F8 → 좌표 기록, ESC → 종료")
recorded = []

while True:
    event = keyboard.read_event()
    if event.event_type != "down":
        continue
    if event.name == "esc":
        break
    if event.name == "f8":
        x, y = pyautogui.position()
        label = input(f"  ({x}, {y}) 이 버튼의 이름(메모): ")
        recorded.append((label, x, y))
        print(f"  기록됨: {label} → ({x}, {y})")

print("\n=== config.yaml steps 에 붙여넣을 내용 ===")
for label, x, y in recorded:
    print(f"      - {{action: click_xy, x: {x}, y: {y}}}   # {label}")
