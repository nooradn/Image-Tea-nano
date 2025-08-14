@echo off
REM Cek apakah git sudah terpasang
git --version >nul 2>&1
if %errorlevel%==0 (
	echo Git ditemukan. Menjalankan update...
	git pull
) else (
	echo Git tidak ditemukan di sistem Anda.
	echo Silakan install Git terlebih dahulu.
	echo Download Git dari: https://git-scm.com/download/win
	echo Setelah instalasi selesai, jalankan kembali script ini.
	pause
)