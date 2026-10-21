@echo off
if exist "C:\Program Files\Java\jdk-17" (
    set "JAVA_HOME=C:\Program Files\Java\jdk-17"
    set "PATH=C:\Program Files\Java\jdk-17\bin;%PATH%"
)
cd /d "%~dp0"

echo ===============================================================================
echo   CHAY TOAN BO PIPELINE DU LIEU LON 6 TANG (END-TO-END)
echo   Bronze -^> Silver -^> Gold -^> Lakehouse DB -^> Machine Learning -^> Analytics
echo ===============================================================================
echo.

python run_pipeline.py all

if %errorlevel% equ 0 (
    echo.
    echo ===============================================================================
    echo   [OK] PIPELINE DA HOAN THANH XUAT SAC TOAN TRINH!
    echo   Khoi chay giao dien Web Streamlit bang cach chay file: chay_app.bat
    echo ===============================================================================
) else (
    echo.
    echo [!] Pipeline dung lai do co loi (Ma loi: %errorlevel%).
)

echo.
pause
