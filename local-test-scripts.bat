@echo off
REM LOCAL E2E TEST SCRIPTS - NOT FOR PRODUCTION
REM These scripts run tests in isolation using port 8080 mock backend
setlocal enabledelayedexpansion

REM Safety check to prevent running in CI/production
if "%CI%"=="true" (
    echo [ERROR] LOCAL TEST SCRIPTS BLOCKED IN PRODUCTION ENVIRONMENT
    echo This is a safety measure to prevent conflicts with production systems.
    exit /b 1
)
if "%NODE_ENV%"=="production" (
    echo [ERROR] LOCAL TEST SCRIPTS BLOCKED IN PRODUCTION ENVIRONMENT
    exit /b 1
)

echo ========================================
echo Facebook-Automation Local E2E Test Runner
echo WARNING: FOR LOCAL TESTING ONLY
echo ========================================
echo.

set COMMAND=%~1
if "%COMMAND%"=="" set COMMAND=full

if /i "%COMMAND%"=="setup" goto :cmd_setup
if /i "%COMMAND%"=="test" goto :cmd_test
if /i "%COMMAND%"=="full" goto :cmd_full
if /i "%COMMAND%"=="cleanup" goto :cmd_cleanup
if /i "%COMMAND%"=="logs" goto :cmd_logs
if /i "%COMMAND%"=="help" goto :show_usage
if /i "%COMMAND%"=="--help" goto :show_usage
if /i "%COMMAND%"=="-h" goto :show_usage

echo [ERROR] Unknown command: %COMMAND%
echo.
goto :show_usage

REM ====== COMMANDS ======

:cmd_setup
    call :start_mock_backend
    if errorlevel 1 exit /b 1
    call :start_frontend
    if errorlevel 1 exit /b 1
    echo.
    echo [OK] Local test environment ready!
    echo   Mock Backend: http://localhost:8080
    echo   Frontend:     http://localhost:5173
    goto :end

:cmd_test
    call :run_tests
    goto :end

:cmd_full
    echo [Starting complete local test run...]
    call :cleanup
    call :start_mock_backend
    if errorlevel 1 exit /b 1
    call :start_frontend
    if errorlevel 1 exit /b 1
    timeout /t 3 /nobreak >nul
    call :run_tests
    set TEST_RESULT=!errorlevel!
    call :cleanup
    echo.
    if !TEST_RESULT!==0 (
        echo [OK] Local E2E tests completed successfully!
    ) else (
        echo [FAIL] Local E2E tests failed
        exit /b 1
    )
    goto :end

:cmd_cleanup
    call :cleanup
    goto :end

:cmd_logs
    echo ========================================
    echo Service Logs
    echo ========================================
    echo.
    echo === Mock Backend ===
    if exist "local-mock.log" (
        type local-mock.log
    ) else (
        echo No mock backend log found
    )
    echo.
    echo === Frontend ===
    if exist "local-frontend.log" (
        type local-frontend.log
    ) else (
        echo No frontend log found
    )
    goto :end

REM ====== FUNCTIONS ======

:start_mock_backend
    echo [Starting mock backend on port 8080...]

    REM Check if port 8080 is already in use
    netstat -ano 2>nul | findstr ":8080.*LISTENING" >nul 2>&1
    if !errorlevel!==0 (
        echo [WARN] Port 8080 already in use. Stopping existing process...
        for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8080.*LISTENING"') do (
            taskkill /PID %%a /F >nul 2>&1
        )
        timeout /t 2 /nobreak >nul
    )

    REM Start mock server in background
    start /B "" node local-mock-server.js > local-mock.log 2>&1

    REM Wait for server to start (max 30 seconds)
    set /a attempts=0
    :wait_mock
    curl -s http://localhost:8080/health >nul 2>&1
    if !errorlevel!==0 (
        echo [OK] Mock server ready!
        exit /b 0
    )
    set /a attempts+=1
    if !attempts! GEQ 30 (
        echo [ERROR] Failed to start mock server
        exit /b 1
    )
    timeout /t 1 /nobreak >nul
    goto :wait_mock

:start_frontend
    echo [Starting frontend with local configuration...]

    if not exist "frontend\.env.local" (
        echo [ERROR] frontend\.env.local not found.
        echo Please copy the template first:
        echo   copy frontend\.env.local.example frontend\.env.local
        exit /b 1
    )

    REM Start frontend in background
    pushd frontend
    start /B "" npm run dev > ..\local-frontend.log 2>&1
    popd

    REM Wait for frontend to start (max 60 seconds)
    set /a attempts=0
    :wait_frontend
    curl -s http://localhost:5173 >nul 2>&1
    if !errorlevel!==0 (
        echo [OK] Frontend ready!
        exit /b 0
    )
    set /a attempts+=1
    if !attempts! GEQ 60 (
        echo [ERROR] Failed to start frontend
        exit /b 1
    )
    timeout /t 1 /nobreak >nul
    goto :wait_frontend

:run_tests
    echo [Running E2E tests...]
    set TEST_FAILED=0

    pushd frontend

    echo Running core tests...
    call npm run test:core
    if errorlevel 1 set TEST_FAILED=1

    if !TEST_FAILED!==0 (
        echo Running tenant tests...
        call npm run test:tenant
        if errorlevel 1 set TEST_FAILED=1
    )

    popd

    if !TEST_FAILED!==1 (
        echo [FAIL] Some tests failed
        exit /b 1
    )
    echo [OK] All tests passed!
    exit /b 0

:cleanup
    echo [Cleaning up local test processes...]

    REM Kill any node processes on port 8080
    for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8080.*LISTENING"') do (
        echo Stopping mock backend (PID: %%a)
        taskkill /PID %%a /F >nul 2>&1
    )

    REM Kill any node processes on port 5173
    for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5173.*LISTENING"') do (
        echo Stopping frontend (PID: %%a)
        taskkill /PID %%a /F >nul 2>&1
    )

    REM Clean up runtime files
    del /Q local-mock.log local-frontend.log local-mock.pid local-frontend.pid >nul 2>&1

    echo [OK] Cleanup complete
    exit /b 0

:show_usage
    echo Usage: %~nx0 [COMMAND]
    echo.
    echo Commands:
    echo   setup     Start mock backend and frontend
    echo   test      Run E2E tests (assumes services running)
    echo   full      Complete test run: setup + test + cleanup
    echo   cleanup   Stop all processes and clean up
    echo   logs      Show service logs
    echo.
    echo Examples:
    echo   %~nx0 full              Run complete test suite
    echo   %~nx0 setup             Start services only
    echo   %~nx0 test              Run tests only
    goto :end

:end
    endlocal
    exit /b %errorlevel%
