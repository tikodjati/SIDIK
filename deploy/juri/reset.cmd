@echo off
rem Mematikan SIDIK dan MENGHAPUS semua datanya (akun, salinan, audit trail, bahan uji), supaya
rem jalan berikutnya mulai bersih. Image hasil build tidak dihapus.
cd /d "%~dp0"
set /p JAWAB=Semua data SIDIK akan dihapus. Lanjut? (ketik ya):
if /i not "%JAWAB%"=="ya" (
  echo Dibatalkan.
  goto selesai
)
docker compose -f juri/docker-compose.yml down -v
if exist bahan_uji rmdir /s /q bahan_uji
echo Data dihapus. Jalankan mulai.cmd untuk mulai bersih.
:selesai
echo.
pause
