@echo off
chcp 65001 >nul
echo ========================================
echo    验证码系统 - 启动脚本
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/2] 检查依赖...
python -c "import fastapi, uvicorn, PIL, captcha" 2>nul
if errorlevel 1 (
    echo   依赖未完全安装，正在安装...
    pip install -r requirements.txt -q
)

echo [2/2] 启动服务器...
echo   访问地址: http://localhost:8000
echo   按 Ctrl+C 停止服务器
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
