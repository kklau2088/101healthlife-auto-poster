@echo off
chcp 65001 >nul
echo ============================================
echo  設定 Windows 每日自動排程
echo ============================================
echo.

:: 取得當前資料夾的完整路徑
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

echo 腳本路徑：%SCRIPT_DIR%
echo.
echo 設定每天早上 08:00 自動發文...

:: 建立 Windows 工作排程器任務
schtasks /create /tn "101HealthLife Auto Post" ^
    /tr "python \"%SCRIPT_DIR%\main.py\"" ^
    /sc daily ^
    /st 08:00 ^
    /f

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo  排程設定成功！
    echo  每天 08:00 會自動發布一篇 SEO 文章。
    echo.
    echo  查看排程：
    echo  schtasks /query /tn "101HealthLife Auto Post"
    echo.
    echo  刪除排程：
    echo  schtasks /delete /tn "101HealthLife Auto Post" /f
    echo ============================================
) else (
    echo [錯誤] 排程設定失敗，請以系統管理員身份執行此腳本。
    echo 右鍵點擊 setup_scheduler.bat，選擇「以系統管理員身份執行」
)
echo.
pause
