@echo off
rem =========================================
rem 근태자동화 전체 실행 (더블클릭 or 작업 스케줄러용)
rem =========================================
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [설치] 가상환경 생성 및 패키지 설치 중... 최초 1회만 수행됩니다.
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

".venv\Scripts\python.exe" -m src.main
set EXITCODE=%ERRORLEVEL%

if %EXITCODE% NEQ 0 (
    echo.
    echo [실패] 오류가 발생했습니다. logs 폴더의 오늘 날짜 로그와 error_*.png 를 확인하세요.
    pause
)
exit /b %EXITCODE%
