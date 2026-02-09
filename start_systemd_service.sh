#!/bin/bash

# ============================================
# Start Systemd Service Script
# ===========================================

echo "=========================================="
echo "启动Systemd服务"
echo "=========================================="

# 1. 停止所有现有进程
echo "1. 停止所有现有gunicorn进程..."
pkill -f "gunicorn.*eval_server" 2>/dev/null
sleep 2
REMAINING=$(pgrep -f "gunicorn.*eval_server")
if [ -n "$REMAINING" ]; then
    echo "   强制停止剩余进程..."
    pkill -9 -f "gunicorn.*eval_server" 2>/dev/null
    sleep 1
fi

# 检查端口
if command -v ss > /dev/null; then
    PORT_USAGE=$(ss -tlnp | grep ":5001 ")
    if [ -n "$PORT_USAGE" ]; then
        echo "   ⚠️  端口5001仍被占用，请手动检查"
    else
        echo "   ✅ 端口5001已释放"
    fi
fi

echo ""

# 2. 检查服务文件是否存在
echo "2. 检查systemd服务文件..."
if [ ! -f "/etc/systemd/system/translation-evaluator.service" ]; then
    echo "   ❌ 服务文件不存在"
    echo "   请先运行: sudo ./setup_systemd_service.sh"
    exit 1
else
    echo "   ✅ 服务文件存在"
fi

echo ""

# 3. 重新加载systemd配置
echo "3. 重新加载systemd配置..."
sudo systemctl daemon-reload
if [ $? -eq 0 ]; then
    echo "   ✅ systemd配置已重新加载"
else
    echo "   ❌ systemd配置重新加载失败"
    exit 1
fi

echo ""

# 4. 启动服务
echo "4. 启动服务..."
sudo systemctl start translation-evaluator
sleep 3

# 5. 检查服务状态
echo ""
echo "5. 检查服务状态..."
if systemctl is-active --quiet translation-evaluator; then
    echo "   ✅ 服务运行正常"
else
    echo "   ❌ 服务启动失败"
    echo ""
    echo "   查看错误日志:"
    sudo journalctl -u translation-evaluator -n 50 --no-pager
    exit 1
fi

echo ""

# 6. 显示服务状态
echo "=========================================="
echo "服务状态详情:"
echo "=========================================="
sudo systemctl status translation-evaluator --no-pager -l | head -30

echo ""
echo "=========================================="
echo "服务信息:"
echo "=========================================="
echo "服务状态: $(systemctl is-active translation-evaluator)"
echo "是否开机自启: $(systemctl is-enabled translation-evaluator 2>/dev/null || echo '未启用')"
echo ""

# 7. 测试API
echo "=========================================="
echo "测试API连接:"
echo "=========================================="
sleep 2
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "✅ API服务响应正常"
    echo ""
    echo "健康检查结果:"
    curl -s http://localhost:5001/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5001/health
else
    echo "⚠️  API服务可能还在启动中，请稍后检查"
    echo "   运行: curl http://localhost:5001/health"
fi

echo ""
echo "=========================================="
echo "常用命令:"
echo "=========================================="
echo "查看状态: sudo systemctl status translation-evaluator"
echo "查看日志: sudo journalctl -u translation-evaluator -f"
echo "停止服务: sudo systemctl stop translation-evaluator"
echo "重启服务: sudo systemctl restart translation-evaluator"
echo "查看最近日志: sudo journalctl -u translation-evaluator -n 100"
echo ""
echo "✅ 服务启动完成！"
