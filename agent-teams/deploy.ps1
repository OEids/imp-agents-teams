# deploy.ps1 - Quick deploy script for Streamlit Cloud
# Usage: .\deploy.ps1 "Your commit message"

param(
    [Parameter(Mandatory=$false)]
    [string]$Message = "Update app"
)

Write-Host "`n=== Streamlit Deploy Script ===" -ForegroundColor Cyan

# Step 1: Check for uncommitted changes
$status = git status --porcelain
if (-not $status) {
    Write-Host "No changes to deploy." -ForegroundColor Yellow
    exit 0
}

Write-Host "`nChanges to deploy:" -ForegroundColor Green
git status --short

# Step 2: Pull latest to avoid conflicts
Write-Host "`nPulling latest changes..." -ForegroundColor Cyan
git pull --rebase
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Pull failed. Resolve conflicts first." -ForegroundColor Red
    exit 1
}

# Step 3: Stage all changes
Write-Host "`nStaging changes..." -ForegroundColor Cyan
git add -A

# Step 4: Commit
Write-Host "`nCommitting: $Message" -ForegroundColor Cyan
git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Commit failed." -ForegroundColor Red
    exit 1
}

# Step 5: Push
Write-Host "`nPushing to remote..." -ForegroundColor Cyan
git push
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Push failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Deployed Successfully! ===" -ForegroundColor Green
Write-Host "Streamlit Cloud will auto-update in ~30 seconds." -ForegroundColor Gray
Write-Host "Or manually reboot at: https://share.streamlit.io" -ForegroundColor Gray
