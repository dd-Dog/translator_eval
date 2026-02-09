#!/bin/bash

# ============================================
# Stop All Translation Evaluator Services
# ===========================================

echo "=========================================="
echo "停止所有翻译评估服务"
echo "=========================================="

# 1. 停止systemd服务
echo "1. 停止systemd服务..."
if systemctl is-active --quiet translation-evaluator 2>/dev/null; then
    echo "   正在停止systemd服务..."
    sudo systemctl stop translation-evaluator
    sleep 2
    if systemctl is-active --quiet translation-evaluator 2>/dev/null; then
        echo "   ⚠️  systemd服务仍在运行"
    else
        echo "   ✅ systemd服务已停止"
    fi
else
    echo "   ℹ️  systemd服务未运行"
fi

echo ""

# 2. 停止所有gunicorn进程
echo "2. 停止所有gunicorn进程..."
GUNICORN_PIDS=$(pgrep -f "gunicorn.*eval_server")
if [ -n "$GUNICORN_PIDS" ]; then
    echo "   找到进程: $GUNICORN_PIDS"
    echo "   进程详情:"
    ps aux | grep "gunicorn.*eval_server" | grep -v grep | while read line; do
        echo "     $line"
    done
    echo ""
    echo "   正在停止进程..."
    pkill -f "gunicorn.*eval_server"
    sleep 3
    
    # 检查是否还在运行
    REMAINING=$(pgrep -f "gunicorn.*eval_server")
    if [ -n "$REMAINING" ]; then
        echo "   ⚠️  仍有进程运行，强制停止..."
        pkill -9 -f "gunicorn.*eval_server"
        sleep 2
    fi
    
    REMAINING=$(pgrep -f "gunicorn.*eval_server")
    if [ -z "$REMAINING" ]; then
        echo "   ✅ 所有gunicorn进程已停止"
    else
        echo "   ❌ 仍有进程无法停止: $REMAINING"
        echo "   请手动停止: kill -9 $REMAINING"
    fi
else
    echo "   ℹ️  未找到gunicorn进程"
fi

echo ""

# 3. 检查端口占用
echo "3. 检查端口5001占用..."
if command -v ss > /dev/null; then
    PORT_USAGE=$(ss -tlnp | grep ":5001 ")
    if [ -n "$PORT_USAGE" ]; then
        echo "   ⚠️  端口5001仍被占用:"
        echo "   $PORT_USAGE"
        echo "   请手动检查并停止占用端口的进程"
    else
        echo "   ✅ 端口5001已释放"
    fi
else
    echo "   ℹ️  无法检查端口（ss未安装）"
fi

echo ""
echo "=========================================="
echo "操作完成"
echo "=========================================="
echo ""
echo "现在可以重新启动服务:"
echo "  sudo systemctl start translation-evaluator"
echo "  或"
echo "  ./start_background.sh"
