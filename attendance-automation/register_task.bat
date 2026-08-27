@echo off
rem =========================================
rem Windows 작업 스케줄러에 매일 자동 실행 등록
rem 사용법: 이 파일을 우클릭 → "관리자 권한으로 실행"
rem 실행 시각을 바꾸려면 아래 ST 값을 수정 (24시간제)
rem =========================================
chcp 65001 >nul
set ST=08:30

schtasks /Create /F ^
  /TN "근태자동화" ^
  /TR "\"%~dp0run_all.bat\"" ^
  /SC DAILY /ST %ST% ^
  /RL HIGHEST

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [완료] 매일 %ST% 에 자동 실행되도록 등록되었습니다.
    echo 주의: UI 자동화 특성상 PC가 켜져 있고 로그인된 상태여야 합니다.
    echo       (화면 잠금 상태에서는 클릭 자동화가 실패할 수 있습니다)
) else (
    echo [실패] 관리자 권한으로 다시 실행해 보세요.
)
pause
