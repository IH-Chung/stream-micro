@echo off
setlocal
cd /d "%~dp0"

echo Starting stream-micro...

REM Activate the virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] .venv not found. Run: uv sync --dev
    exit /b 1
)
call ".venv\Scripts\activate.bat"

REM Ensure the frontend is built
if not exist "frontend\dist\index.html" (
    echo [INFO] Frontend not built. Building...
    pushd frontend
    if not exist "node_modules" (
        npm ci || ( echo [ERROR] npm ci failed & popd & exit /b 1 )
    )
    npm run build || ( echo [ERROR] npm run build failed & popd & exit /b 1 )
    popd
)

REM Launch the Bridge service
echo [INFO] Bridge starting on http://127.0.0.1:8765
uv run stream-micro serve

endlocal