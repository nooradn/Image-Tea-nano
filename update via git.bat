@echo off
REM Cek apakah git sudah terpasang
git --version >nul 2>&1
if %errorlevel%==0 (
    REM Opsi hapus database sebelum update
    echo.
    echo ========== PERINGATAN ==========
    echo Anda akan melakukan update aplikasi.
    echo Jika skema database berubah, Anda bisa menghapus database lama agar update berjalan lancar.
    echo.
    echo PERINGATAN: Semua API key dan data yang tersimpan di aplikasi akan HILANG dan TIDAK DAPAT DIKEMBALIKAN!
    echo Jangan gunakan Image Tea sebagai aplikasi penyimpanan data, aplikasi ini hanya untuk generate metadata.
    echo.
    set /p DELDB="Apakah Anda ingin menghapus database lama sebelum update? (Y/N): "
    if /I "%DELDB%"=="Y" (
        if exist "database\database.db" (
            del /f /q "database\database.db"
            echo Database database\database.db telah dihapus.
        ) else (
            echo Database database\database.db tidak ditemukan, tidak ada yang dihapus.
        )
    ) else (
        echo Database tidak dihapus.
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