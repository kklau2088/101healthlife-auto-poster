@echo off
chcp 65001 >nul
echo 正在發布今天的 SEO 文章...
cd /d "%~dp0"
python main.py
echo 完成！
