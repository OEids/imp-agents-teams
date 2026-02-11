# IMP Agent Teams Launcher (PowerShell)

Write-Host ""
Write-Host " ====================================" -ForegroundColor Cyan
Write-Host "  IMP Planner Agent Teams" -ForegroundColor Cyan
Write-Host " ====================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# Check if streamlit is installed
$streamlit = pip show streamlit 2>$null
if (-not $streamlit) {
    Write-Host " Installing required packages..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host " Starting application..." -ForegroundColor Green
Write-Host " Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
