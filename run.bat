@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

REM Neu co tham so truyen vao tu dong lenh (vd: run.bat all, run.bat app, run.bat test)
if not "%~1"=="" (
    if /i "%~1"=="test" (
        python -m pytest tests/test_pipelines.py -v
        goto :eof
    )
    python run_pipeline.py %*
    goto :eof
)

:MENU
cls
echo ======================================================================
echo   HE THONG DU DOAN GIA NHA VIET NAM - BIG DATA ^& MACHINE LEARNING
echo ======================================================================
echo.
echo   Chon chuc nang can thuc thi:
echo.
echo   [1] Khoi chay Giao dien Web Streamlit (Demo Dinh gia ^& Dashboard)
echo   [2] Chay Toan bo Pipeline 6 Tang (Ingest -^> ETL -^> DB -^> ML -^> Eval)
echo   [3] Chay Buoc ETL PySpark (Lam sach Silver ^& Tao dac trung Gold)
echo   [4] Chay Huan luyen Mo hinh (Ridge Baseline ^& LightGBM Regressor)
echo   [5] Chay Bo Kiem thu Tu dong (Pytest 7 Test Cases)
echo   [6] Xuat Du lieu Mau ra File Excel (.xlsx va .csv)
echo   [0] Thoat
echo.
echo ======================================================================
set /p choice="Nhap lua chon cua ban (0-6): "

if "%choice%"=="1" goto RUN_APP
if "%choice%"=="2" goto RUN_ALL
if "%choice%"=="3" goto RUN_ETL
if "%choice%"=="4" goto RUN_TRAIN
if "%choice%"=="5" goto RUN_TEST
if "%choice%"=="6" goto RUN_EXCEL
if "%choice%"=="0" goto EXIT_SCRIPT

echo Lua chon khong hop le. Vui long thu lai.
pause
goto MENU

:RUN_APP
echo.
echo [*] Dang khoi chay ung dung Streamlit tai http://localhost:8501 ...
echo [*] Nhan Ctrl+C trong cua so nay de dung ung dung.
echo.
python -m streamlit run src/serving/app.py
pause
goto MENU

:RUN_ALL
echo.
echo [*] Dang chay toan bo 6 tang pipeline...
python run_pipeline.py all
echo.
pause
goto MENU

:RUN_ETL
echo.
echo [*] Dang chay PySpark ETL (Clean Silver ^& Features Gold)...
python run_pipeline.py etl
echo.
pause
goto MENU

:RUN_TRAIN
echo.
echo [*] Dang chay huan luyen va danh gia mo hinh Machine Learning...
python run_pipeline.py train
python run_pipeline.py evaluate
echo.
pause
goto MENU

:RUN_TEST
echo.
echo [*] Dang chay bo kiem thu tu dong Pytest...
python -m pytest tests/test_pipelines.py -v
echo.
pause
goto MENU

:RUN_EXCEL
echo.
echo [*] Dang xuat 10,000 dong du lieu mau sang Excel va CSV...
python -c "import pandas as pd; df = pd.read_parquet('data/gold/vietnam_real_estates_gold.parquet'); df.head(10000).to_excel('data/vietnam_real_estates_sample.xlsx', index=False); df.head(10000).to_csv('data/vietnam_real_estates_sample.csv', index=False, encoding='utf-8-sig'); print('[+] Da xuat thanh cong: data/vietnam_real_estates_sample.xlsx va .csv')"
echo.
pause
goto MENU

:EXIT_SCRIPT
echo Thoat chuong trinh.
exit /b 0
