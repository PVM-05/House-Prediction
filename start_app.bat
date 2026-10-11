@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo ======================================================================
echo   KHOI CHAY GIAO DIEN WEB STREAMLIT - DU DOAN GIA NHA VIET NAM
echo   Dia chi truy cap: http://localhost:8501
echo   (Nhan Ctrl+C de dung may chu)
echo ======================================================================
echo.

python -m streamlit run src/serving/app.py
pause
