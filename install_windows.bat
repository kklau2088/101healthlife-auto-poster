@echo off
chcp 65001 >nul
echo ============================================
echo  101healthlife.com Auto SEO Poster
echo  Windows 一鍵安裝腳本
echo ============================================
echo.

:: 檢查 Python 是否已安裝
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 找不到 Python！
    echo.
    echo 請先到以下網址下載並安裝 Python 3.11：
    echo https://www.python.org/downloads/
    echo.
    echo 安裝時請勾選 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [1/3] 已偵測到 Python：
python --version
echo.

:: 安裝依賴套件
echo [2/3] 安裝 Python 套件中（openai, requests, schedule）...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [錯誤] 套件安裝失敗，請檢查網路連線後重試。
    pause
    exit /b 1
)
echo 套件安裝完成！
echo.

:: 測試連線
echo [3/3] 測試 WordPress 連線...
echo （如果尚未填入 config.py，請先編輯後再測試）
echo.
set /p choice=是否現在測試連線？(y/n): 
if /i "%choice%"=="y" (
    python main.py --test-connection
)

echo.
echo ============================================
echo  安裝完成！
echo.
echo  下一步：
echo  1. 用記事本打開 config.py 填入您的憑證
echo  2. 執行測試：python main.py --now
echo  3. 設定每日排程（見 README.md）
echo ============================================
pause
