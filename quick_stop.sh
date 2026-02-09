#!/bin/bash

# ============================================
# Quick Stop Script
# ============================================

echo "正在停止所有gunicorn进程..."

# 停止所有gunicorn进程
pkill -f "gunicorn.*eval_server"

# 等待2秒
sleep 2

# 检查是否还有进程
REMAINING=$(pgrep -f "gunicorn.*eval_server")
if [ -n "$REMAINING" ]; then
    echo "强制停止剩余进程..."
    pkill -9 -f "gunicorn.*eval_server"
    sleep 1
fi

# 最终检查
REMAINING=$(pgrep -f "gunicorn.*eval_server")
if [ -z "$REMAINING" ]; then
    echo "✅ 所有进程已停止"
    
    # 检查端口
    if command -v ss > /dev/null; then
        PORT_USAGE=$(ss -tlnp | grep ":5001 ")
        if [ -z "$PORT_USAGE" ]; then
            echo "✅ 端口5001已释放"
        else
            echo "⚠️  端口5001仍被占用:"
            echo "$PORT_USAGE"
        fi
    fi
else
    echo "❌ 仍有进程无法停止: $REMAINING"
    echo "请手动停止: kill -9 $REMAINING"
fi
