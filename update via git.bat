@echo off
REM Dapatkan direktori script ini
set SCRIPT_DIR=%~dp0
REM Hapus trailing backslash jika ada
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM Cek apakah git sudah terpasang
git --version >nul 2>&1
if %errorlevel%==0 (
    REM Opsi hapus database sebelum update
    echo.
    powershell -Command "Write-Host '========== PERINGATAN ==========' -ForegroundColor Yellow"
    powershell -Command "Write-Host 'Anda akan melakukan update aplikasi.' -ForegroundColor Red"
    powershell -Command "Write-Host 'Update aplikasi mungkin menyebabkan perubahan struktur database (skema).' -ForegroundColor Yellow"
    powershell -Command "Write-Host 'Aplikasi ini TIDAK mendukung migrasi database otomatis.' -ForegroundColor Yellow"
    powershell -Command "Write-Host 'Jika Anda melanjutkan update tanpa menghapus database lama, aplikasi bisa error atau data tidak terbaca.' -ForegroundColor Yellow"
    powershell -Command "Write-Host ''"
    powershell -Command "Write-Host 'PERINGATAN: Semua API key dan data yang tersimpan di database.db akan HILANG dan TIDAK DAPAT DIKEMBALIKAN!' -ForegroundColor Red"
    powershell -Command "Write-Host 'Jangan gunakan Image Tea sebagai aplikasi penyimpanan data, aplikasi ini hanya untuk generate metadata.' -ForegroundColor Yellow"
    powershell -Command "Write-Host 'Meskipun Image Tea menyimpan API key untuk kemudahan, jika database dihapus (misal saat update), seluruh API key akan hilang.' -ForegroundColor Yellow"
    powershell -Command "Write-Host 'Sebaiknya simpan API key Anda di tempat lain yang aman, jangan hanya di aplikasi ini.' -ForegroundColor Yellow"
    powershell -Command "Write-Host ''"
    choice /c YN /n /m "Apakah Anda ingin menghapus database lama sebelum update? (Y/N): "
    if errorlevel 2 (
        echo Database tidak dihapus.
    ) else (
        set DB_PATH=%SCRIPT_DIR%\database\database.db
        if exist "%DB_PATH%" (
            del /f /q "%DB_PATH%"
            echo Database %DB_PATH% telah dihapus.
        ) else (
            echo Database %DB_PATH% tidak ditemukan, tidak ada yang dihapus.
        )
    )
    echo.
    REM Cek apakah sudah login git (user.name harus ada)
    git config --get user.name >nul 2>&1
    if %errorlevel%==0 (
        echo Git ditemukan dan sudah login.
        echo Username: 
        git config --get user.name
        echo Email: 
        git config --get user.email
        echo Menjalankan update...
        git pull
        pause
    ) else (
        echo Git ditemukan, tetapi Anda belum login ke git.
        set /p GITUSER=Masukkan username GitHub Anda: 
        set /p GITEMAIL=Masukkan email GitHub Anda: 
        git config --global user.name "%GITUSER%"
        git config --global user.email "%GITEMAIL%"
        echo Login git berhasil. Menjalankan update...
        git pull
        pause
    )
) else (
    echo Git tidak ditemukan di sistem Anda.
    echo Silakan install Git terlebih dahulu.
    echo Download Git dari: https://git-scm.com/download/win
    echo Setelah instalasi selesai, jalankan kembali script ini.
    pause
)