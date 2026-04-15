@echo off
cls
echo ==========================================
echo    ATHARV TECH - ERP PUSH SYSTEM
echo ==========================================
echo.

:: Adding all changes
git add .

:: Creating a commit with timestamp
set msg=Invoicing-ERP-Reset-%date%-%time%
git commit -m "%msg%"

:: Pushing to GitHub
echo Pushing code to Cloud...
git push origin main

echo.
echo ==========================================
echo    SUCCESS: Code is now LIVE on Vercel!
echo ==========================================
pause