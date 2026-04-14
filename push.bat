@echo off
echo [A-SmartERP] Starting Automation Push...
git add .
set /p msg="Enter Commit Message: "
git commit -m "%msg%"
git push origin main
echo [A-SmartERP] Push Successful! Deploying on Vercel...
pause