@echo off
REM Quick Start Script for AI Gateway (Windows)
REM This script helps you quickly test and run the AI Gateway system

setlocal EnableDelayedExpansion

REM Colors (limited in Windows CMD)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

cd /d "%PROJECT_DIR%"

echo %INFO% AI Gateway Quick Start Script
echo %INFO% Project directory: %PROJECT_DIR%
echo.

REM Check prerequisites
echo %INFO% Checking prerequisites...

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %ERROR% Python is not installed or not in PATH. Please install Python 3.11+ first.
    exit /b 1
)

for /f "tokens=*" %%a in ('python --version') do set PYTHON_VERSION=%%a
echo %SUCCESS% Found %PYTHON_VERSION%

REM Check Node.js
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %ERROR% Node.js is not installed or not in PATH. Please install Node.js 18+ first.
    exit /b 1
)

for /f "tokens=*" %%a in ('node --version') do set NODE_VERSION=%%a
echo %SUCCESS% Found Node.js %NODE_VERSION%

REM Check Docker
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %WARNING% Docker is not installed. You won't be able to run infrastructure services.
    set DOCKER_AVAILABLE=0
) else (
    echo %SUCCESS% Docker is available
    set DOCKER_AVAILABLE=1
)

echo.
echo %INFO% All basic prerequisites met!
echo.

REM Function to start infrastructure
:START_INFRASTRUCTURE
if %DOCKER_AVAILABLE% NEQ 1 (
    echo %ERROR% Docker is required for infrastructure services
    goto :EOF
)
echo %INFO% Starting infrastructure services (MongoDB, Redis, Qdrant)...
docker-compose up -d mongodb redis qdrant
echo %INFO% Waiting for services to be ready...
timeout /t 5 /nobreak >nul
echo %SUCCESS% Infrastructure services started
goto :EOF

REM Function to setup backend
:SETUP_BACKEND
echo %INFO% Setting up Python backend...
cd /d "%PROJECT_DIR%\app"

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo %INFO% Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
echo %INFO% Installing Python dependencies...
call venv\Scripts\activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo %SUCCESS% Backend dependencies installed
goto :EOF

REM Function to setup frontend
:SETUP_FRONTEND
echo %INFO% Setting up Node.js frontend...
cd /d "%PROJECT_DIR%\wei-ui"

REM Check if node_modules exists
if not exist "node_modules" (
    echo %INFO% Installing Node.js dependencies...
    call npm install
) else (
    echo %INFO% Node.js dependencies already installed
)
echo %SUCCESS% Frontend dependencies ready
goto :EOF

REM Function to run tests
:RUN_TESTS
echo %INFO% Running integration tests...
cd /d "%PROJECT_DIR%\app"
call venv\Scripts\activate
python -m pytest tests\test_integration.py -v --tb=short
goto :EOF

REM Function to start backend
:START_BACKEND
echo %INFO% Starting backend server...
echo %INFO% Backend will be available at: http://localhost:8000
echo %INFO% API Documentation: http://localhost:8000/docs

cd /d "%PROJECT_DIR%\app"
call venv\Scripts\activate

REM Start in new window
start "AI Gateway Backend" cmd /k "venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo %SUCCESS% Backend server started in new window
goto :EOF

REM Function to start frontend
:START_FRONTEND
echo %INFO% Starting frontend development server...
echo %INFO% Frontend will be available at: http://localhost:5175

cd /d "%PROJECT_DIR%\wei-ui"

REM Start in new window
start "AI Gateway Frontend" cmd /k "npm run dev"

echo %SUCCESS% Frontend server started in new window
goto :EOF

REM Main menu
:MENU
cls
echo =================================
echo     AI Gateway Quick Start
echo =================================
echo.
echo 1) Full Setup (Infrastructure + Backend + Frontend)
echo 2) Start Infrastructure Only (Docker services)
echo 3) Setup Backend Only
echo 4) Setup Frontend Only
echo 5) Run Tests
echo 6) Start Backend Server
echo 7) Start Frontend Server
echo 8) Start Both Servers
echo 9) Show Status
echo 10) Stop Infrastructure
echo 0) Exit
echo.
set /p choice="Select an option: "

if "%choice%"=="1" goto FULL_SETUP
if "%choice%"=="2" goto START_INFRASTRUCTURE
if "%choice%"=="3" goto SETUP_BACKEND
if "%choice%"=="4" goto SETUP_FRONTEND
if "%choice%"=="5" goto RUN_TESTS
if "%choice%"=="6" goto START_BACKEND
if "%choice%"=="7" goto START_FRONTEND
if "%choice%"=="8" goto START_BOTH
if "%choice%"=="9" goto SHOW_STATUS
if "%choice%"=="10" goto STOP_INFRASTRUCTURE
if "%choice%"=="0" goto EXIT

echo %ERROR% Invalid option
pause
goto :MENU

:FULL_SETUP
echo %INFO% Running full setup...
call :START_INFRASTRUCTURE
call :SETUP_BACKEND
call :SETUP_FRONTEND
call :START_BACKEND
call :START_FRONTEND
echo %SUCCESS% Full setup complete!
echo.
echo Frontend: http://localhost:5175
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
pause
goto :MENU

:START_BOTH
call :START_BACKEND
call :START_FRONTEND
pause
goto :MENU

:SHOW_STATUS
echo %INFO% Checking system status...
echo.
echo === Infrastructure Services ===
docker-compose ps mongodb redis qdrant 2>nul || echo Not running or Docker not available
echo.
echo === Backend Server ===
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo %SUCCESS% Backend is running at http://localhost:8000
    curl -s http://localhost:8000/api/v1/health
) else (
    echo %ERROR% Backend is not running
)
echo.
echo === Frontend Server ===
curl -s http://localhost:5175 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo %SUCCESS% Frontend is running at http://localhost:5175
) else (
    echo %ERROR% Frontend is not running
)
pause
goto :MENU

:STOP_INFRASTRUCTURE
if %DOCKER_AVAILABLE% EQU 1 (
    docker-compose down
    echo %SUCCESS% Infrastructure stopped
) else (
    echo %ERROR% Docker is not available
)
pause
goto :MENU

:EXIT
echo %INFO% Exiting...
exit /b 0
