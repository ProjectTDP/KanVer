@echo off
echo ========================================
echo Stopping KanVer Docker Services
echo ========================================
echo.

docker-compose down

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] All services stopped!
    echo.
) else (
    echo.
    echo [ERROR] Failed to stop services!
    echo.
)

pause
