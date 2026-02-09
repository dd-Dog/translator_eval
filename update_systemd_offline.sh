#!/bin/bash

# ============================================
# Update Systemd Service to Enable Offline Mode
# ===========================================

echo "=========================================="
echo "更新systemd服务配置（启用离线模式）"
echo "=========================================="

# 检查服务文件是否存在
if [ ! -f "/etc/systemd/system/translation-evaluator.service" ]; then
    echo "❌ 服务文件不存在，请先运行: sudo ./setup_systemd_service.sh"
    exit 1
fi

echo "备份当前服务文件..."
sudo cp /etc/systemd/system/translation-evaluator.service /etc/systemd/system/translation-evaluator.service.bak

echo "更新服务文件，添加离线模式环境变量..."

# 检查是否已包含离线模式环境变量
if grep -q "HF_HUB_OFFLINE" /etc/systemd/system/translation-evaluator.service; then
    echo "✅ 离线模式环境变量已存在"
else
    # 在HF_HOME环境变量后添加离线模式环境变量
    sudo sed -i '/Environment="HF_HOME=/a Environment="HF_HUB_OFFLINE=1"\nEnvironment="TRANSFORMERS_OFFLINE=1"' /etc/systemd/system/translation-evaluator.service
    echo "✅ 已添加离线模式环境变量"
fi

echo ""
echo "重新加载systemd配置..."
sudo systemctl daemon-reload

echo ""
echo "重启服务以应用新配置..."
sudo systemctl restart translation-evaluator

sleep 3

echo ""
echo "检查服务状态..."
sudo systemctl status translation-evaluator --no-pager -l | head -20

echo ""
echo "=========================================="
echo "更新完成"
echo "=========================================="
echo "服务已重启，离线模式环境变量已添加"
echo ""
echo "查看日志确认:"
echo "  sudo journalctl -u translation-evaluator -f"
