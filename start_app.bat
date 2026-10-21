@echo off
if exist "C:\Program Files\Java\jdk-17" (
    set "JAVA_HOME=C:\Program Files\Java\jdk-17"
    set "PATH=C:\Program Files\Java\jdk-17\bin;%PATH%"
)
cd /d "%~dp0"

echo ===============================================================================
echo   HOUSE PREDICTION - BIG DATA LAKEHOUSE ^& MARKET ANALYTICS
echo   He Thong Tich Hop ^& Phan Tich Du Lieu Lon Bat Dong San Viet Nam
echo ===============================================================================
echo.
echo [*] Dang khoi dong may chu Streamlit...
echo [*] Dia chi truy cap ung dung: http://localhost:8501
echo [*] Nhan Ctrl+C trong cua so nay neu ban muon dung may chu.
echo.

python -m streamlit run src/serving/app.py --server.port 8501

if %errorlevel% neq 0 (
    echo.
    echo [!] Co loi xay ra khi khoi chay Streamlit (Ma loi: %errorlevel%).
    echo [!] Nhan phim bat ky de dong...
    pause >nul
)
