@echo off
REM Sentinel Performance Testing Automation Script (Windows)
REM Applies optimizations and runs comprehensive load tests

echo ==========================================
echo Sentinel Performance Testing Suite
echo ==========================================
echo.

REM Step 1: Check prerequisites
echo Step 1: Checking prerequisites...

where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker not found. Please install Docker Desktop.
    pause
    exit /b 1
)

where locust >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Locust not found. Installing...
    pip install locust
)

echo [OK] Prerequisites OK
echo.

REM Step 2: Start infrastructure services
echo Step 2: Starting infrastructure services...
cd /d "%~dp0\.."

docker-compose up -d postgres redis redpanda
timeout /t 10 /nobreak >nul

echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo [OK] Infrastructure services started
echo.

REM Step 3: Apply database optimizations
echo Step 3: Applying database indexes...

if exist "alembic\versions\performance_indexes.sql" (
    docker exec -i sentinel-postgres psql -U sentinel -d sentinel < alembic\versions\performance_indexes.sql
    echo [OK] Database indexes applied
) else (
    echo WARNING: performance_indexes.sql not found
)

echo.

REM Step 4: Apply code optimizations
echo Step 4: Apply code optimizations?
echo This will replace api\dependencies.py with optimized version.
set /p CONTINUE="Continue? (y/n): "

if /i "%CONTINUE%"=="y" (
    if exist "api\dependencies_optimized.py" (
        copy /y api\dependencies.py api\dependencies.backup.py
        copy /y api\dependencies_optimized.py api\dependencies.py
        echo [OK] Code optimizations applied (backup saved)
    ) else (
        echo ERROR: dependencies_optimized.py not found
    )
) else (
    echo Skipping code optimizations
)

echo.

REM Step 5: Check API server
echo Step 5: Checking API server...

curl -s http://localhost:8000/health/live >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] API server already running
) else (
    echo.
    echo Please start the API server in another terminal:
    echo   cd "%~dp0\.."
    echo   .venv\Scripts\activate
    echo   uvicorn api.main:app --host 127.0.0.1 --port 8000
    echo.
    pause
)

REM Verify API is responding
curl -s http://localhost:8000/health/live >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: API server not responding at http://localhost:8000
    pause
    exit /b 1
)

echo [OK] API server responding
echo.

REM Step 6: Run load tests
echo Step 6: Running load tests...
echo.

REM Create results directory
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set TIMESTAMP=%mydate%-%mytime%
set RESULTS_DIR=benchmarks\results-%TIMESTAMP%
mkdir "%RESULTS_DIR%" 2>nul

REM Baseline test
echo Running BASELINE test (50 users, 5 min)...
locust -f tests\load\locustfile_enhanced.py ^
    --host http://localhost:8000 ^
    --users 50 ^
    --spawn-rate 5 ^
    --run-time 300s ^
    --headless ^
    --html "%RESULTS_DIR%\baseline-report.html" ^
    --csv "%RESULTS_DIR%\baseline"

echo [OK] Baseline test complete
echo.
timeout /t 10 /nobreak >nul

REM Stress test
echo Running STRESS test (200 users, 10 min)...
locust -f tests\load\locustfile_enhanced.py ^
    --host http://localhost:8000 ^
    --users 200 ^
    --spawn-rate 10 ^
    --run-time 600s ^
    --headless ^
    --html "%RESULTS_DIR%\stress-report.html" ^
    --csv "%RESULTS_DIR%\stress"

echo [OK] Stress test complete
echo.
timeout /t 10 /nobreak >nul

REM Spike test
echo Running SPIKE test (500 users, 5 min)...
locust -f tests\load\locustfile_enhanced.py ^
    --host http://localhost:8000 ^
    --users 500 ^
    --spawn-rate 50 ^
    --run-time 300s ^
    --headless ^
    --html "%RESULTS_DIR%\spike-report.html" ^
    --csv "%RESULTS_DIR%\spike"

echo [OK] Spike test complete
echo.

REM Step 7: Generate summary
echo Step 7: Generating summary report...

echo # Sentinel Performance Test Results > "%RESULTS_DIR%\SUMMARY.md"
echo **Date**: %date% %time% >> "%RESULTS_DIR%\SUMMARY.md"
echo **Test ID**: %TIMESTAMP% >> "%RESULTS_DIR%\SUMMARY.md"
echo. >> "%RESULTS_DIR%\SUMMARY.md"
echo ## Test Results >> "%RESULTS_DIR%\SUMMARY.md"
echo. >> "%RESULTS_DIR%\SUMMARY.md"
echo ### Baseline Test (50 users, 5 min) >> "%RESULTS_DIR%\SUMMARY.md"
echo See: baseline-report.html >> "%RESULTS_DIR%\SUMMARY.md"
echo. >> "%RESULTS_DIR%\SUMMARY.md"
echo ### Stress Test (200 users, 10 min) >> "%RESULTS_DIR%\SUMMARY.md"
echo See: stress-report.html >> "%RESULTS_DIR%\SUMMARY.md"
echo. >> "%RESULTS_DIR%\SUMMARY.md"
echo ### Spike Test (500 users, 5 min) >> "%RESULTS_DIR%\SUMMARY.md"
echo See: spike-report.html >> "%RESULTS_DIR%\SUMMARY.md"

echo [OK] Summary report generated
echo.

REM Step 8: Display results
echo ==========================================
echo Performance Testing Complete!
echo ==========================================
echo.
echo Results saved to: %RESULTS_DIR%
echo.
echo View reports:
echo   - Summary: %RESULTS_DIR%\SUMMARY.md
echo   - Baseline: %RESULTS_DIR%\baseline-report.html
echo   - Stress: %RESULTS_DIR%\stress-report.html
echo   - Spike: %RESULTS_DIR%\spike-report.html
echo.
echo Done!
pause
