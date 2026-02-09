#!/bin/bash

# ============================================
# Check Port 5001 Usage
# ============================================

PORT=5001

echo "=========================================="
echo "检查端口 $PORT 占用情况"
echo "=========================================="

# 方法1: 使用netstat
echo "使用netstat检查:"
if command -v netstat > /dev/null; then
    netstat -tlnp | grep ":$PORT " || echo "未找到占用端口的进程"
else
    echo "netstat未安装，跳过"
fi

echo ""

# 方法2: 使用ss
echo "使用ss检查:"
if command -v ss > /dev/null; then
    ss -tlnp | grep ":$PORT " || echo "未找到占用端口的进程"
else
    echo "ss未安装，跳过"
fi

echo ""

# 方法3: 使用lsof
echo "使用lsof检查:"
if command -v lsof > /dev/null; then
    lsof -i :$PORT || echo "未找到占用端口的进程"
else
    echo "lsof未安装，跳过"
fi

echo ""

# 方法4: 检查systemd服务
echo "检查systemd服务状态:"
if systemctl is-active --quiet translation-evaluator 2>/dev/null; then
    echo "✅ translation-evaluator服务正在运行"
    systemctl status translation-evaluator --no-pager -l | head -20
else
    echo "⚠️  translation-evaluator服务未运行"
fi

echo ""

# 方法5: 检查gunicorn进程
echo "检查gunicorn进程:"
ps aux | grep "gunicorn.*eval_server" | grep -v grep || echo "未找到gunicorn进程"

echo ""
echo "=========================================="
echo "建议操作:"
echo "=========================================="
echo "1. 如果systemd服务在运行:"
echo "   sudo systemctl stop translation-evaluator"
echo ""
echo "2. 如果找到gunicorn进程，停止它:"
echo "   pkill -f 'gunicorn.*eval_server'"
echo ""
echo "3. 或者使用其他端口测试:"
echo "   修改服务文件中的端口号"
