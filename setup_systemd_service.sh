#!/bin/bash

# ============================================
# Translation Evaluator Systemd Service Setup
# ============================================

# 配置变量（请根据实际情况修改）
PROJECT_DIR="/root/bianjb/translation_evaluator"
CONDA_ENV="/root/miniconda3/envs/tranlator_eval"
SERVICE_PORT="5001"
SERVICE_USER="root"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用sudo运行此脚本"
    exit 1
fi

# 检查项目目录是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    echo "请修改脚本中的 PROJECT_DIR 变量"
    exit 1
fi

# 检查conda环境是否存在
if [ ! -d "$CONDA_ENV" ]; then
    echo "❌ Conda环境不存在: $CONDA_ENV"
    echo "请修改脚本中的 CONDA_ENV 变量"
    exit 1
fi

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"
chmod 755 "$PROJECT_DIR/logs"

echo "=========================================="
echo "创建systemd服务文件..."
echo "=========================================="

# 创建服务文件
cat > /etc/systemd/system/translation-evaluator.service <<EOF
[Unit]
Description=Translation Evaluator API Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$CONDA_ENV/bin"
Environment="USE_REQUEST_QUEUE=true"
Environment="MAX_QUEUE_SIZE=50"
Environment="REQUEST_TIMEOUT=600"
Environment="USE_BLEURT=true"
Environment="BLEURT_USE_SUBPROCESS=true"
Environment="BLEURT_PYTHON_ENV=/root/miniconda3/envs/translator_eval_bleurt/bin/python"
Environment="BLEURT_WORKER_SCRIPT=$PROJECT_DIR/bleurt_worker.py"
Environment="BLEURT_CHECKPOINT=$PROJECT_DIR/BLEURT-20"
Environment="COMET_MODEL_PATH=/root/bianjb/wmt22-comet-da"
Environment="HF_HOME=/root/.cache/huggingface"
Environment="HF_HUB_OFFLINE=1"
Environment="TRANSFORMERS_OFFLINE=1"
ExecStart=$CONDA_ENV/bin/gunicorn \
    -w 1 \
    -b 0.0.0.0:$SERVICE_PORT \
    --timeout 600 \
    --access-logfile $PROJECT_DIR/logs/access.log \
    --error-logfile $PROJECT_DIR/logs/error.log \
    --capture-output \
    --log-level info \
    eval_server:app
Restart=always
RestartSec=10
MemoryMax=8G
CPUQuota=200%
StandardOutput=journal
StandardError=journal
SyslogIdentifier=translation-evaluator

[Install]
WantedBy=multi-user.target
EOF

echo "✅ 服务文件已创建: /etc/systemd/system/translation-evaluator.service"

# 重新加载systemd
echo ""
echo "=========================================="
echo "重新加载systemd配置..."
echo "=========================================="
systemctl daemon-reload

# 启用服务（开机自启）
echo ""
echo "=========================================="
echo "启用服务（开机自启）..."
echo "=========================================="
systemctl enable translation-evaluator

# 检查服务是否已在运行
if systemctl is-active --quiet translation-evaluator; then
    echo ""
    echo "⚠️  服务已在运行，正在重启..."
    systemctl restart translation-evaluator
else
    echo ""
    echo "=========================================="
    echo "启动服务..."
    echo "=========================================="
    systemctl start translation-evaluator
fi

# 等待服务启动
echo ""
echo "等待服务启动（3秒）..."
sleep 3

# 显示状态
echo ""
echo "=========================================="
echo "服务状态:"
echo "=========================================="
systemctl status translation-evaluator --no-pager -l

# 测试健康检查
echo ""
echo "=========================================="
echo "健康检查:"
echo "=========================================="
sleep 2
if curl -s http://localhost:$SERVICE_PORT/health > /dev/null; then
    echo "✅ 服务运行正常"
    curl -s http://localhost:$SERVICE_PORT/health | python3 -m json.tool 2>/dev/null || echo "（JSON解析失败，但服务已响应）"
else
    echo "⚠️  服务可能还在启动中，请稍后检查"
fi

echo ""
echo "=========================================="
echo "常用命令:"
echo "=========================================="
echo "启动服务: sudo systemctl start translation-evaluator"
echo "停止服务: sudo systemctl stop translation-evaluator"
echo "重启服务: sudo systemctl restart translation-evaluator"
echo "查看状态: sudo systemctl status translation-evaluator"
echo "查看日志: sudo journalctl -u translation-evaluator -f"
echo "查看最近日志: sudo journalctl -u translation-evaluator -n 100"
echo "禁用服务: sudo systemctl disable translation-evaluator"
echo ""
echo "=========================================="
echo "服务配置:"
echo "=========================================="
echo "项目目录: $PROJECT_DIR"
echo "服务端口: $SERVICE_PORT"
echo "Conda环境: $CONDA_ENV"
echo "日志目录: $PROJECT_DIR/logs"
echo ""
echo "✅ 配置完成！"
