@echo off
echo.
echo  NEXILA HR MANAGEMENT PORTAL
echo  West Tambaram, Chennai
echo.

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause & exit /b 1
)

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt -q

if not exist ".env" (
    copy .env.example .env
    echo Created .env — edit it to configure SMTP settings.
)

if not exist "uploads\resumes" mkdir uploads\resumes
if not exist "uploads\payslips" mkdir uploads\payslips

echo.
echo Starting Nexila HR on http://localhost:8000
echo Press Ctrl+C to stop
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
