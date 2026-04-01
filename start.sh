#!/bin/bash
set -e

echo "========================================"
echo "   验证码系统 - 启动脚本"
echo "========================================"
echo

# 切换到脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/backend"

echo "[1/2] 检查依赖..."
if ! python3 -c "import fastapi, uvicorn, PIL, captcha" 2>/dev/null; then
    echo "  依赖未完全安装，正在安装..."
    pip3 install -r requirements.txt -q
fi

echo "[2/2] 启动服务器..."
echo "  访问地址: http://localhost:8000"
echo "  按 Ctrl+C 停止服务器"
echo

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
