@echo off
echo ========================================
echo KanVer Docker Setup
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo [IMPORTANT] Please edit .env file and update:
    echo   - POSTGRES_PASSWORD
    echo   - JWT_SECRET_KEY
    echo.
    pause
)

echo Starting Docker containers...
echo.

docker-compose up -d

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [SUCCESS] All services started!
    echo ========================================
    echo.
    echo Services:
    echo   - Backend API: http://localhost:8000
    echo   - API Docs: http://localhost:8000/docs
    echo   - PostgreSQL: localhost:5432
    echo   - Redis: localhost:6379
    echo.
    echo To view logs: docker-compose logs -f
    echo To stop: docker-compose down
    echo.
) else (
    echo.
    echo [ERROR] Failed to start services!
    echo Check the error messages above.
    echo.
)

pause
