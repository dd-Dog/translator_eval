#!/bin/bash

# ============================================
# Translation Evaluator Background Stop Script
# ============================================

PROJECT_DIR="/root/bianjb/translation_evaluator"

cd "$PROJECT_DIR" || {
    echo "❌ 无法进入项目目录: $PROJECT_DIR"
    exit 1
}

echo "=========================================="
echo "停止翻译评估服务..."
echo "=========================================="

# 方法1: 使用PID文件
if [ -f logs/gunicorn.pid ]; then
    PID=$(cat logs/gunicorn.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "找到进程 (PID: $PID)，正在停止..."
        kill $PID
        
        # 等待进程结束
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                echo "✅ 服务已停止"
                rm -f logs/gunicorn.pid
                exit 0
            fi
            sleep 1
        done
        
        # 如果还在运行，强制杀死
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  进程未响应，强制停止..."
            kill -9 $PID
            rm -f logs/gunicorn.pid
            echo "✅ 服务已强制停止"
        fi
    else
        echo "⚠️  PID文件中的进程不存在，清理PID文件"
        rm -f logs/gunicorn.pid
    fi
fi

# 方法2: 查找所有相关进程
REMAINING=$(pgrep -f "gunicorn.*eval_server")
if [ -n "$REMAINING" ]; then
    echo "发现其他相关进程，正在停止..."
    pkill -f "gunicorn.*eval_server"
    sleep 2
    
    # 检查是否还有进程
    REMAINING=$(pgrep -f "gunicorn.*eval_server")
    if [ -n "$REMAINING" ]; then
        echo "⚠️  仍有进程运行，强制停止..."
        pkill -9 -f "gunicorn.*eval_server"
    fi
    echo "✅ 所有相关进程已停止"
else
    echo "✅ 没有运行中的服务"
fi
