@echo off
if exist "C:\Program Files\Java\jdk-17" (
    set "JAVA_HOME=C:\Program Files\Java\jdk-17"
    set "PATH=C:\Program Files\Java\jdk-17\bin;%PATH%"
)
cd /d "%~dp0"

if /i "%~1"=="test" (
    python -m pytest tests/test_pipelines.py -v
    exit /b %errorlevel%
)
if /i "%~1"=="charts" (
    python -m src.analytics.generate_eda_charts
    exit /b %errorlevel%
)
if not "%~1"=="" (
    python run_pipeline.py %*
    exit /b %errorlevel%
)

:MENU
cls
echo ===============================================================================
echo   HE THONG TICH HOP ^& PHAN TICH DU LIEU LON BAT DONG SAN VIET NAM
echo   Medallion Lakehouse (PySpark) + Machine Learning + Streamlit Dashboard
echo ===============================================================================
echo.
echo   Chon chuc nang can thuc thi:
echo.
echo   [1] Khoi chay Giao dien Web Streamlit (4 Phan He Dashboard Hoc Thuat)
echo   [2] Chay Toan bo Pipeline 6 Tang (Ingest -^> Silver -^> Gold -^> DB -^> ML -^> Eval)
echo   [3] Chay Buoc PySpark ETL (Lam sach Silver ^& Trich xuat dac trung Gold)
echo   [4] Chay Buoc Nap Co So Du Lieu Serving (PostgreSQL / SQLite Fallback)
echo   [5] Chay Huan Luyen Mo Hinh Machine Learning (Ridge Baseline ^& LightGBM)
echo   [6] Chay Bo Kiem Thu Tu Dong Toan Dien (Pytest 10/10 Test Cases)
echo   [7] Tao Bo So Lieu Tom Tat ^& 7 Bieu Do Phan Tich Chuan Hoc Thuat
echo   [8] Xuat 10,000 Dong Du Lieu Mau Ra File Excel (.xlsx) va CSV (.csv)
echo   [0] Thoat
echo.
echo ===============================================================================
set choice=
set /p choice="Nhap lua chon cua ban (0-8): "

if "%choice%"=="1" goto RUN_APP
if "%choice%"=="2" goto RUN_ALL
if "%choice%"=="3" goto RUN_ETL
if "%choice%"=="4" goto RUN_LOAD
if "%choice%"=="5" goto RUN_TRAIN
if "%choice%"=="6" goto RUN_TEST
if "%choice%"=="7" goto RUN_CHARTS
if "%choice%"=="8" goto RUN_EXCEL
if "%choice%"=="0" goto EXIT_SCRIPT

echo.
echo [!] Lua chon khong hop le. Vui long nhap tu 0 den 8.
echo.
pause
goto MENU

:RUN_APP
echo.
echo [*] Dang khoi chay ung dung Streamlit tai: http://localhost:8501 ...
echo [*] Nhan Ctrl+C trong cua so nay neu muon dung ung dung.
echo.
python -m streamlit run src/serving/app.py --server.port 8501
pause
goto MENU

:RUN_ALL
echo.
echo [*] Dang thuc thi toan bo 6 tang pipeline du lieu lon...
python run_pipeline.py all
echo.
pause
goto MENU

:RUN_ETL
echo.
echo [*] Dang chay PySpark ETL (Silver Clean ^& Gold Features)...
python run_pipeline.py etl
echo.
pause
goto MENU

:RUN_LOAD
echo.
echo [*] Dang nap du lieu Tang Vang vao Co so du lieu Serving...
python run_pipeline.py load
echo.
pause
goto MENU

:RUN_TRAIN
echo.
echo [*] Dang huan luyen va danh gia mo hinh Machine Learning...
python run_pipeline.py train
python run_pipeline.py evaluate
echo.
pause
goto MENU

:RUN_TEST
echo.
echo [*] Dang chay bo kiem thu tu dong 10 bai kiem thu (Pytest)...
python -m pytest tests/test_pipelines.py -v
echo.
pause
goto MENU

:RUN_CHARTS
echo.
echo [*] Dang tao bo so lieu tom tat va 7 bieu do phan tich chuan hoc thuat...
python -m src.analytics.generate_eda_charts
echo.
pause
goto MENU

:RUN_EXCEL
echo.
echo [*] Dang xuat 10,000 dong du lieu mau sang Excel va CSV...
python -c "import pandas as pd; df = pd.read_parquet('data/gold/vietnam_real_estates_gold.parquet'); df.head(10000).to_excel('data/vietnam_real_estates_sample.xlsx', index=False); df.head(10000).to_csv('data/vietnam_real_estates_sample.csv', index=False, encoding='utf-8-sig'); print('[OK] Da xuat thanh cong: data/vietnam_real_estates_sample.xlsx va .csv')"
echo.
pause
goto MENU

:EXIT_SCRIPT
echo.
echo Thoat chuong trinh. Tam biet!
exit /b 0
