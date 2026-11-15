@echo off
rem Mematikan SIDIK. Data tetap tersimpan; jalankan mulai.cmd lagi untuk melanjutkan.
cd /d "%~dp0"
docker compose -f juri/docker-compose.yml down
echo SIDIK dimatikan. Data tetap tersimpan.
echo.
pause
