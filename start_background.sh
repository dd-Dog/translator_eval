#!/bin/bash

# ============================================
# Translation Evaluator Background Start Script
# ============================================

PROJECT_DIR="/root/bianjb/translation_evaluator"
CONDA_ENV="/root/miniconda3/envs/tranlator_eval"

# 进入项目目录
cd "$PROJECT_DIR" || {
    echo "❌ 无法进入项目目录: $PROJECT_DIR"
    exit 1
}

# 检查是否已在运行
if pgrep -f "gunicorn.*eval_server" > /dev/null; then
    echo "⚠️  服务已在运行中"
    echo "进程信息:"
    ps aux | grep "gunicorn.*eval_server" | grep -v grep
    echo ""
    echo "如需重启，请先运行: ./stop_background.sh"
    exit 1
fi

# 设置环境变量
export USE_REQUEST_QUEUE=true
export MAX_QUEUE_SIZE=50
export REQUEST_TIMEOUT=600
export USE_BLEURT=true
export BLEURT_USE_SUBPROCESS=true
export BLEURT_PYTHON_ENV=/root/miniconda3/envs/translator_eval_bleurt/bin/python
export BLEURT_WORKER_SCRIPT="$PROJECT_DIR/bleurt_worker.py"
export BLEURT_CHECKPOINT="$PROJECT_DIR/BLEURT-20"
export COMET_MODEL_PATH=/root/bianjb/wmt22-comet-da
export HF_HOME=/root/.cache/huggingface

# 创建日志目录
mkdir -p logs

# 激活conda环境（如果使用conda）
if [ -d "$CONDA_ENV" ]; then
    source "$(dirname "$CONDA_ENV")/../etc/profile.d/conda.sh" 2>/dev/null || true
    conda activate "$(basename "$CONDA_ENV")" 2>/dev/null || {
        echo "⚠️  无法激活conda环境，尝试直接使用Python"
        PYTHON_BIN="$CONDA_ENV/bin/gunicorn"
    }
else
    PYTHON_BIN="gunicorn"
fi

# 启动服务
echo "=========================================="
echo "启动翻译评估服务..."
echo "=========================================="
echo "项目目录: $PROJECT_DIR"
echo "日志文件: $PROJECT_DIR/logs/gunicorn.log"
echo ""

# 使用nohup后台运行
nohup "$PYTHON_BIN" -w 1 --preload -b 0.0.0.0:5001 --timeout 600 eval_server:app > logs/gunicorn.log 2>&1 &

# 保存进程ID
PID=$!
echo $PID > logs/gunicorn.pid

echo "✅ 服务已启动"
echo "进程ID: $PID"
echo ""
echo "查看日志: tail -f logs/gunicorn.log"
echo "停止服务: ./stop_background.sh"
echo "检查状态: ps aux | grep gunicorn"
echo ""

# 等待几秒后检查服务是否正常运行
sleep 3
if ps -p $PID > /dev/null 2>&1; then
    echo "✅ 服务运行正常"
    if curl -s http://localhost:5001/health > /dev/null 2>&1; then
        echo "✅ API服务响应正常"
    else
        echo "⚠️  API服务可能还在启动中，请稍后检查"
    fi
else
    echo "❌ 服务启动失败，请查看日志: tail -n 50 logs/gunicorn.log"
    exit 1
fi
