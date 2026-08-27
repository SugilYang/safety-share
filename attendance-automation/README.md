# 근태자동화 (완전 자동화)

세콤매니저(PC 프로그램)와 ERP에서 근태 엑셀을 자동으로 다운로드하고,
기존 통합 파이썬 로직까지 한 번에 실행하는 자동화입니다.
회사 PC에서 매일 정해진 시각에 자동 실행되도록 설계했습니다.

```
[매일 08:30 작업 스케줄러]
        │
        ▼
 ① 세콤매니저 실행 → 로그인 → 조회 → 엑셀 저장   (pywinauto)
 ② ERP 실행 → 로그인 → 근태 조회 → 엑셀 저장     (pywinauto / playwright)
 ③ 세 번째 자료 다운로드 (필요 시)
        │
        ▼
 ④ 통합 파이썬 실행 → C:\근태자동화\결과\통합근태_YYYYMMDD.xlsx
```

---

## 1. 최초 설치 (회사 PC에서 1회)

1. **Python 설치**: https://python.org 에서 3.11 이상 설치
   (설치 시 "Add Python to PATH" 반드시 체크)
2. 이 폴더(`attendance-automation`)를 회사 PC로 복사
   (예: `C:\근태자동화\attendance-automation`)
3. 설정 파일 준비:
   - `config/config.example.yaml` → 복사해서 `config/config.yaml` 생성
   - `.env.example` → 복사해서 `.env` 생성 후 **세콤/ERP 계정 입력**
   - 기존 통합 파이썬 코드가 있으면 `custom_integrate.example.py` 를 복사해
     `custom_integrate.py` 로 만들고 `integrate()` 함수 안에 붙여넣기
4. `run_all.bat` 더블클릭 → 최초 실행 시 필요한 패키지가 자동 설치됨

## 2. 화면 정보 수집 (캘리브레이션 — 1회)

세콤매니저와 ERP의 버튼·입력란 이름은 PC마다 다르므로, 최초 1회
진단 도구로 화면 구조를 뽑아서 `config.yaml` 의 `steps` 를 완성해야 합니다.

```bat
cd C:\근태자동화\attendance-automation
.venv\Scripts\activate

rem 세콤매니저를 실행해 로그인 화면을 띄워 놓은 상태에서:
python -m src.tools.inspect_windows            :: 떠 있는 창 목록 확인
python -m src.tools.inspect_windows "세콤"      :: 세콤 창의 전체 컨트롤 구조 덤프
```

- 결과가 `logs/inspect_결과.txt` 에 저장됩니다.
  **이 내용을 Claude에게 붙여넣으면 config.yaml 의 steps 를 만들어 드립니다.**
- 로그인 후 화면(조회/엑셀저장 화면)에서도 한 번 더 실행해서 함께 전달하세요.
- ERP도 동일하게 진행합니다.
- 컨트롤이 하나도 안 잡히는 화면(그림 기반 UI)은
  `python -m src.tools.record_clicks` 로 버튼 좌표를 기록해 `click_xy` 방식으로 대체합니다.

## 3. 단계별 테스트

```bat
python -m src.main --only secom            :: 세콤 다운로드만 테스트
python -m src.main --only erp_attendance   :: ERP 다운로드만 테스트
python -m src.main --skip-download         :: 이미 받은 파일로 통합만 테스트
python -m src.main                         :: 전체 실행
```

실패하면 `logs\YYYYMMDD.log` 와 `logs\error_*.png`(실패 시점 화면 캡처)를 확인하세요.

## 4. 매일 자동 실행 등록

`register_task.bat` 를 **우클릭 → 관리자 권한으로 실행**하면
매일 08:30에 자동 실행되도록 Windows 작업 스케줄러에 등록됩니다.
(시각 변경은 파일 안의 `ST=08:30` 수정)

> ⚠️ UI 자동화 특성상 **PC가 켜져 있고 화면이 잠기지 않은 상태**여야 합니다.
> 화면 잠금을 꺼 두거나, 자동 실행 시각에 로그인 상태를 유지하세요.

## 5. 폴더 구조

```
attendance-automation/
├── run_all.bat                  ← 더블클릭 한 번으로 전체 실행
├── register_task.bat            ← 매일 자동 실행 등록
├── config/config.example.yaml   ← 설정 (복사해서 config.yaml 로)
├── .env.example                 ← 계정 정보 (복사해서 .env 로)
├── custom_integrate.example.py  ← 기존 통합 코드 넣는 자리
└── src/
    ├── main.py                  ← 전체 흐름 (다운로드 → 통합)
    ├── downloaders/client.py    ← PC 프로그램 자동화 엔진
    ├── downloaders/web.py       ← 웹 ERP 자동화 엔진
    ├── integrate.py             ← 통합 단계
    └── tools/inspect_windows.py ← 화면 구조 진단 도구
```

## 6. 보안 주의

- `.env`(계정 정보), `config.yaml`, `custom_integrate.py` 는 git에 올라가지 않습니다.
- 결과 엑셀에는 직원 개인정보가 포함되므로 공개 저장소에 커밋하지 마세요.
