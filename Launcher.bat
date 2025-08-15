@echo off
setlocal enabledelayedexpansion

REM =====================================================================
REM Image Tea Mini Launcher Script
REM Author: Mudrikul Hikam
REM Last Updated: May 13, 2025
REM 
REM This script performs the following tasks:
REM 1. If Python folder exists, directly runs main.py
REM 2. If Python folder doesn't exist:
REM    - Downloads Python 3.12.10 embedded distribution
REM    - Sets up pip in the embedded distribution
REM    - Updates application files from GitHub repository
REM    - Installs required packages from requirements.txt
REM    - Runs main.py
REM =====================================================================

set "BASE_DIR=%~dp0"
set "BASE_DIR=%BASE_DIR:~0,-1%"
set "PYTHON_DIR=%BASE_DIR%\python\Windows"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"
set "MAIN_PY=%BASE_DIR%\main.py"
set "REQUIREMENTS_FILE=%BASE_DIR%\requirements.txt"

REM =====================================================================
REM Check if Python directory exists
REM If it exists, we can directly run the main.py file without setup
REM If not, we need to set up the environment first
REM =====================================================================
if exist "%PYTHON_DIR%" (
    echo Python installation found. Checking requirements...
    
    REM Check for requirements.txt and install if it exists
    if exist "%BASE_DIR%\requirements.txt" (
        echo Installing requirements from requirements.txt...
        "%PYTHON_EXE%" -m pip install -r "%BASE_DIR%\requirements.txt" --no-warn-script-location
    ) else (
        echo Warning: requirements.txt not found. Skipping package installation.
    )
    goto :VERIFY
)

REM User Consent Section with Green Color
powershell -Command "Write-Host '=====================================================================' -ForegroundColor Green"
powershell -Command "Write-Host 'Image Tea - User Consent Required' -ForegroundColor Green"
powershell -Command "Write-Host '=====================================================================' -ForegroundColor Green"
powershell -Command "Write-Host 'Image Tea berkomitmen menjadi aplikasi yang jujur dan transparan.' -ForegroundColor Green"
powershell -Command "Write-Host 'Untuk dapat berjalan, aplikasi ini membutuhkan Python 3.12.10 embedded, pip, dan seluruh library Python yang tercantum di requirements.txt.' -ForegroundColor Green"
powershell -Command "Write-Host 'Python dan seluruh library akan di-instal secara otomatis ke direktori berikut:' -ForegroundColor Green"
powershell -Command "Write-Host '    %PYTHON_DIR%' -ForegroundColor Green"
powershell -Command "Write-Host 'Semua file Python, pip, dan library hanya akan ditempatkan di folder tersebut, tidak akan mengubah sistem Anda.' -ForegroundColor Green"
powershell -Command "Write-Host 'Tidak ada perubahan pada PATH atau instalasi global.' -ForegroundColor Green"
powershell -Command "Write-Host ''"
powershell -Command "Write-Host 'Perkiraan total ukuran download dan instalasi:' -ForegroundColor Green"
powershell -Command "Write-Host '  - Python embedded: ~8 MB' -ForegroundColor Green"
powershell -Command "Write-Host '  - pip dan library (requirements.txt): bervariasi, rata-rata 30-100 MB tergantung kebutuhan' -ForegroundColor Green"
powershell -Command "Write-Host '  - Total estimasi: sekitar 300-500 MB (tergantung jumlah dan ukuran library)' -ForegroundColor Green"
powershell -Command "Write-Host ''"
if exist "%REQUIREMENTS_FILE%" (
    powershell -Command "Write-Host 'Daftar library yang akan diinstal:' -ForegroundColor Green"
    for /f "usebackq tokens=*" %%l in ("%REQUIREMENTS_FILE%") do (
        set "LIB=%%l"
        if not "!LIB!"=="" if "!LIB:~0,1!" NEQ "#" (
            powershell -Command "Write-Host '  - !LIB!' -ForegroundColor Green"
        )
    )
) else (
    powershell -Command "Write-Host 'Tidak ditemukan requirements.txt, tidak ada library tambahan yang akan diinstal.' -ForegroundColor Green"
)
powershell -Command "Write-Host ''"
powershell -Command "Write-Host 'Kami memahami kebutuhan privasi Anda. Aplikasi ini berjalan sepenuhnya secara lokal di komputer Anda.' -ForegroundColor Green"
powershell -Command "Write-Host 'Developer (Studio Desainia) TIDAK mengumpulkan data apapun dari pengguna.' -ForegroundColor Green"
powershell -Command "Write-Host 'Library yang diinstal diperlukan untuk komunikasi dengan platform ai dan dokumentasi lengkap dapat di lihat di internet.' -ForegroundColor Green"
powershell -Command "Write-Host ''"
powershell -Command "Write-Host 'Jika nantinya aplikasi Image Tea sudah tidak dibutuhkan, Anda dapat menghapus seluruh folder Image Tea ini dan tidak akan mempengaruhi sistem Anda.' -ForegroundColor Green"
powershell -Command "Write-Host ''"
powershell -Command "Write-Host 'Dengan melanjutkan, Anda menyetujui instalasi Python embedded, pip, dan seluruh library Python di lokasi di atas.' -ForegroundColor Green"
powershell -Command "Write-Host ''"

choice /c yn /n /m "Setuju? (Y/N):"
if errorlevel 2 (
    echo.
    echo Anda tidak menyetujui instalasi. Proses dibatalkan.
    endlocal
    exit /b
)

echo Terima kasih atas konfirmasi Anda.
echo Proses pengunduhan Python dan library akan segera dimulai.
echo Proses ini membutuhkan waktu dan koneksi internet yang stabil.
echo Jika terjadi kegagalan atau Anda berubah pikiran, silakan tutup jendela CMD ini dan jalankan ulang Launcher.bat.

REM =====================================================================
REM Define variables for setup process
REM =====================================================================
set "PYTHON_ZIP=%TEMP%\python-3.12.10-embed-amd64.zip"
set "PYTHON_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"
set "REQUIREMENTS_FILE=%BASE_DIR%\requirements.txt"

REM =====================================================================
REM Create Python directory
REM =====================================================================
echo Creating Python directory...
mkdir "%PYTHON_DIR%"

REM =====================================================================
REM Download and extract Python embedded distribution
REM Uses PowerShell to download the file and extract it
REM =====================================================================
echo Downloading Python embedded distribution...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_ZIP%'"

echo Extracting Python...
powershell -Command "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '%PYTHON_DIR%' -Force"

REM =====================================================================
REM Set up pip in the embedded Python distribution
REM 1. Check if requirements.txt exists, create if not
REM 2. Enable site-packages by modifying the _pth file
REM 3. Download and run get-pip.py to install pip
REM 4. Install required packages from requirements.txt
REM =====================================================================
echo Setting up pip...

REM Create requirements.txt if it doesn't exist
if not exist "%REQUIREMENTS_FILE%" (
    echo Creating empty requirements.txt file...
    echo. > "%REQUIREMENTS_FILE%"
)

REM Enable site-packages in embedded Python by modifying python*._pth file
REM This is required for pip to work in embedded distribution
for %%F in ("%PYTHON_DIR%\python*._pth") do (
    type "%%F" > "%%F.tmp"
    echo import site >> "%%F.tmp"
    move /y "%%F.tmp" "%%F"
)

REM Download get-pip.py and install pip
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%PYTHON_DIR%\get-pip.py'"
"%PYTHON_DIR%\python.exe" "%PYTHON_DIR%\get-pip.py" --no-warn-script-location

REM Upgrade pip to the latest version
echo Upgrading pip to the latest version...
"%PYTHON_DIR%\python.exe" -m pip install --upgrade pip --no-warn-script-location

REM Check if requirements.txt exists and install required packages
if exist "%REQUIREMENTS_FILE%" (
    echo Installing required packages from requirements.txt...
    "%PYTHON_DIR%\python.exe" -m pip install -r "%REQUIREMENTS_FILE%" --no-warn-script-location
) else (
    echo Warning: requirements.txt not found. Skipping package installation.
)

:VERIFY
echo.
echo ================================
echo Verifying Python and pip version:
echo ================================
"%PYTHON_EXE%" --version
"%PYTHON_EXE%" -c "import sys; print('Python executable:', sys.executable)"
"%PYTHON_EXE%" -m pip --version

echo.
echo ================================
echo Verifying installed requirements:
echo ================================
if exist "%BASE_DIR%\requirements.txt" (
    "%PYTHON_EXE%" -m pip freeze > "%TEMP%\pip_freeze.txt"
    for /f "usebackq tokens=*" %%r in ("%BASE_DIR%\requirements.txt") do (
        set "REQ=%%r"
        if not "!REQ!"=="" if "!REQ:~0,1!" NEQ "#" (
            echo Checking !REQ! ...
            findstr /I /C:"!REQ!" "%TEMP%\pip_freeze.txt" >nul
            if errorlevel 1 (
                echo   [MISSING/DIFFERENT] !REQ!
            ) else (
                echo   [OK] !REQ!
            )
        )
    )
    del "%TEMP%\pip_freeze.txt"
) else (
    echo requirements.txt not found, skipping requirements verification.
)

echo.
echo Setup complete. Running main.py...
"%PYTHON_EXE%" "%MAIN_PY%"

endlocal