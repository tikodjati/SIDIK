@echo off
rem SIDIK untuk juri (Windows): satu perintah menyalakan sistem, mengisi data demo, dan
rem menyiapkan bahan uji. Aman dijalankan berulang kali. Klik dua kali berkas ini.
setlocal
cd /d "%~dp0"
set COMPOSE=docker compose -f juri/docker-compose.yml

docker --version >nul 2>&1
if errorlevel 1 (
  echo Docker belum terpasang. Pasang Docker Desktop: https://www.docker.com/products/docker-desktop/
  echo Lalu jalankan ulang berkas ini.
  goto selesai
)
docker info >nul 2>&1
if errorlevel 1 (
  echo Docker terpasang tetapi belum berjalan. Buka Docker Desktop, tunggu sampai siap,
  echo lalu jalankan ulang berkas ini.
  goto selesai
)
docker compose version >nul 2>&1
if errorlevel 1 (
  echo Perlu Docker Compose v2 ^(perintah "docker compose"^). Perbarui Docker Desktop.
  goto selesai
)

rem Port: dipakai yang diminta (SIDIK_PORT), atau port stack ini yang sudah jalan, atau yang pertama kosong.
if not "%SIDIK_PORT%"=="" goto portok
for /f "tokens=2 delims=:" %%a in ('%COMPOSE% port app 7860 2^>nul') do set SIDIK_PORT=%%a
if not "%SIDIK_PORT%"=="" goto portok
for %%p in (3000 3001 3002 3300 3301 8080) do call :cekport %%p
if "%SIDIK_PORT%"=="" set SIDIK_PORT=3000
goto portok
:cekport
if not "%SIDIK_PORT%"=="" exit /b
netstat -an | findstr /r /c:":%1 .*LISTENING" >nul
if errorlevel 1 set SIDIK_PORT=%1
exit /b
:portok

if not exist sidik-image.tar.gz goto bangun
docker image inspect sidik-juri:latest >nul 2>&1
if not errorlevel 1 goto bangun
echo Memuat image siap pakai ^(sekali saja, beberapa menit^)...
docker load -i sidik-image.tar.gz
if errorlevel 1 goto gagal

:bangun
echo Menyalakan SIDIK. Tanpa paket offline, jalan pertama membangun image dan butuh internet ^(sekitar 5-15 menit^).
%COMPOSE% up -d --wait
if errorlevel 1 goto gagal

echo Menyiapkan akun dan data demo...
%COMPOSE% exec -T -w /home/user/app/backend app python -m scripts.demo_juri
if errorlevel 1 goto gagal
if not exist bahan_uji mkdir bahan_uji
%COMPOSE% cp app:/home/user/app/data/bahan_uji/. bahan_uji/
if errorlevel 1 goto gagal

echo.
echo SIDIK siap: http://localhost:%SIDIK_PORT%
echo.
echo Akun ^(kata sandi semuanya: Juri-SIDIK-2026^):
echo   juri1         admin ^(cukup untuk mencoba hampir semuanya^)
echo   juri2         admin kedua ^(untuk persetujuan ganda^)
echo   distributor   distributor
echo   investigator  investigator
echo.
echo Langkah uji: MULAI-DI-SINI.md. Bahan uji: folder bahan_uji\
start "" http://localhost:%SIDIK_PORT%
goto selesai

:gagal
echo.
echo GAGAL. Lihat bagian Pemecahan Masalah di docs/PANDUAN_JURI.md.
echo Log aplikasi: %COMPOSE% logs app

:selesai
echo.
pause
