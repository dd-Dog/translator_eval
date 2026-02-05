#!/bin/bash
# Ubuntu云服务器部署脚本
# Translation Evaluator 快速部署脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "Translation Evaluator Ubuntu部署脚本"
echo "=========================================="

# 配置变量
PROJECT_DIR="/opt/translation_evaluator"
SERVICE_USER="www-data"
CONDA_ENV_NAME="translator_eval"
SERVICE_PORT=5001

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用sudo运行此脚本"
    exit 1
fi

# 1. 安装系统依赖
echo ""
echo "步骤 1/8: 安装系统依赖..."
apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    nginx \
    supervisor

# 2. 安装Miniconda（如果未安装）
if ! command -v conda &> /dev/null; then
    echo ""
    echo "步骤 2/8: 安装Miniconda..."
    cd /tmp
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda3
    export PATH="/opt/miniconda3/bin:$PATH"
    echo 'export PATH="/opt/miniconda3/bin:$PATH"' >> /etc/profile
else
    echo ""
    echo "步骤 2/8: Miniconda已安装，跳过"
    export PATH="/opt/miniconda3/bin:$PATH"
fi

# 3. 创建项目目录
echo ""
echo "步骤 3/8: 创建项目目录..."
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/logs
chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR

# 4. 创建conda环境
echo ""
echo "步骤 4/8: 创建conda环境..."
source /opt/miniconda3/etc/profile.d/conda.sh
if conda env list | grep -q "^${CONDA_ENV_NAME} "; then
    echo "环境 ${CONDA_ENV_NAME} 已存在，跳过创建"
else
    conda create -n $CONDA_ENV_NAME python=3.9 -y
fi

# 5. 安装Python依赖
echo ""
echo "步骤 5/8: 安装Python依赖..."
conda activate $CONDA_ENV_NAME

# 安装指定版本的numpy
conda install -n $CONDA_ENV_NAME numpy=1.23.5 -y

# 安装PyTorch
echo "安装PyTorch（可能需要几分钟）..."
conda install -n $CONDA_ENV_NAME pytorch torchvision torchaudio cpuonly -c pytorch -y

# 安装其他依赖
/opt/miniconda3/envs/$CONDA_ENV_NAME/bin/pip install \
    unbabel-comet \
    tensorflow \
    bert-score \
    sacrebleu \
    flask \
    flask-cors \
    requests \
    gunicorn

# 安装BLEURT
echo "安装BLEURT..."
cd /tmp
if [ -d "bleurt" ]; then
    rm -rf bleurt
fi
git clone https://github.com/google-research/bleurt.git
cd bleurt
/opt/miniconda3/envs/$CONDA_ENV_NAME/bin/pip install . --no-deps
cd ..
rm -rf bleurt

# 6. 复制项目文件（假设项目文件在当前目录）
echo ""
echo "步骤 6/8: 复制项目文件..."
echo "请确保项目文件在当前目录，然后按Enter继续..."
read

# 复制文件到项目目录
cp -r translation_evaluator $PROJECT_DIR/
cp eval_server.py $PROJECT_DIR/
cp eval_client.py $PROJECT_DIR/
cp setup.py $PROJECT_DIR/
cp README.md $PROJECT_DIR/

# 如果存在BLEURT模型，也复制
if [ -d "BLEURT-20" ]; then
    cp -r BLEURT-20 $PROJECT_DIR/
fi

# 安装项目
cd $PROJECT_DIR
/opt/miniconda3/envs/$CONDA_ENV_NAME/bin/pip install -e .

# 7. 创建systemd服务
echo ""
echo "步骤 7/8: 创建systemd服务..."
cat > /etc/systemd/system/translation-evaluator.service <<EOF
[Unit]
Description=Translation Evaluator API Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=/opt/miniconda3/envs/$CONDA_ENV_NAME/bin"
ExecStart=/opt/miniconda3/envs/$CONDA_ENV_NAME/bin/gunicorn \
    -w 4 \
    -b 127.0.0.1:$SERVICE_PORT \
    --timeout 300 \
    --access-logfile $PROJECT_DIR/logs/access.log \
    --error-logfile $PROJECT_DIR/logs/error.log \
    eval_server:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 8. 配置Nginx反向代理
echo ""
echo "步骤 8/8: 配置Nginx..."
cat > /etc/nginx/sites-available/translation-evaluator <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:$SERVICE_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    access_log /var/log/nginx/translation-evaluator-access.log;
    error_log /var/log/nginx/translation-evaluator-error.log;
}
EOF

# 启用Nginx配置
ln -sf /etc/nginx/sites-available/translation-evaluator /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

# 设置权限
chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR

# 启动服务
echo ""
echo "启动服务..."
systemctl daemon-reload
systemctl enable translation-evaluator
systemctl start translation-evaluator
systemctl restart nginx

# 等待服务启动
sleep 5

# 检查服务状态
echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "服务状态:"
systemctl status translation-evaluator --no-pager -l

echo ""
echo "健康检查:"
curl -s http://localhost:$SERVICE_PORT/health | python3 -m json.tool || echo "服务可能还在启动中，请稍后重试"

echo ""
echo "服务信息:"
echo "  - 项目目录: $PROJECT_DIR"
echo "  - 服务端口: $SERVICE_PORT"
echo "  - Nginx端口: 80"
echo "  - 日志目录: $PROJECT_DIR/logs"
echo ""
echo "常用命令:"
echo "  启动服务: sudo systemctl start translation-evaluator"
echo "  停止服务: sudo systemctl stop translation-evaluator"
echo "  查看日志: sudo journalctl -u translation-evaluator -f"
echo "  查看API日志: tail -f $PROJECT_DIR/logs/api_*.log"
echo ""
echo "=========================================="

