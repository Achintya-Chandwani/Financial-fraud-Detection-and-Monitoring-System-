@echo off
REM ================================================================
REM FraudShield AI — Windows Startup Script
REM Run this AFTER completing the initial setup in README.md
REM ================================================================

echo.
echo  ========================================
echo   FraudShield AI - Starting Services
echo  ========================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Copy .env.example to .env and fill in your database credentials.
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Check if model exists
if not exist "models\best_model.joblib" (
    echo [WARNING] Trained model not found.
    echo Run the Jupyter notebooks in order (01 to 05) first.
    echo The backend will start but predictions won't work until model is trained.
    echo.
)

REM Activate venv and start backend in new window
echo [1/2] Starting FastAPI backend on http://localhost:8000 ...
start "FraudShield Backend" cmd /k "venv\Scripts\activate && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

REM Brief pause to let backend start
timeout /t 3 /nobreak > nul

REM Start frontend using Python's built-in HTTP server in new window
echo [2/2] Starting frontend server on http://localhost:5500 ...
start "FraudShield Frontend" cmd /k "venv\Scripts\activate && python -m http.server 5500 --directory frontend"

timeout /t 2 /nobreak > nul

echo.
echo  ========================================
echo   Both services are starting...
echo  ========================================
echo.
echo  Dashboard  : http://localhost:5500
echo  API Docs   : http://localhost:8000/docs
echo  API Health : http://localhost:8000/api/health
echo.
echo  Close the terminal windows to stop the services.
echo.

REM Open browser
timeout /t 3 /nobreak > nul
start http://localhost:5500
