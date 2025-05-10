
@echo off
cd /d "%~dp0"
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/Ahmedhammad25/Microserial.git
git push -u origin main
pause
