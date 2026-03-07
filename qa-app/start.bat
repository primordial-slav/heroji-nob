@echo off
cd /d "%~dp0"

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

REM Set up PDF symlink if missing
if not exist "public\pdfs" (
    echo Creating PDF symlink...
    mklink /D "public\pdfs" "..\..\website\public\pdfs" >nul 2>&1
    if errorlevel 1 (
        echo Symlink failed, copying PDFs instead...
        xcopy /E /I /Y "..\website\public\pdfs" "public\pdfs" >nul
    )
)

REM Copy PDF worker if missing
if not exist "public\pdf.worker.min.mjs" (
    copy "..\website\public\pdf.worker.min.mjs" "public\" >nul
)

echo Starting QA Review app on http://localhost:3001
echo.
start http://localhost:3001
npm run dev
