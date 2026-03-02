@echo off
echo Deploying to Streamlit Cloud...
git add -A
git commit -m "Update app"
git push origin main
echo.
echo Done! Changes will be live in 1-2 minutes.
pause
