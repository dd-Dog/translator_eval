# Ubuntu云服务器部署方案评估

## 📋 部署概述

本文档评估将翻译评估器部署到Ubuntu云服务器的完整方案，包括环境配置、依赖安装、服务部署、监控和维护等方面。

---

## 🎯 部署目标

1. **服务稳定性**: 7x24小时稳定运行
2. **性能优化**: 快速响应评估请求
3. **易于维护**: 便于更新和监控
4. **安全性**: 保护服务安全
5. **可扩展性**: 支持未来扩展

---

## 🖥️ 服务器要求

### 最低配置（测试/小规模使用）

| 资源 | 要求 | 说明 |
|------|------|------|
| **CPU** | 2核心 | 支持基本评估 |
| **内存** | 8GB | 模型加载需要 |
| **存储** | 50GB | 系统+模型+日志 |
| **网络** | 10Mbps | 模型下载需要 |

### 推荐配置（生产环境）

| 资源 | 要求 | 说明 |
|------|------|------|
| **CPU** | 4核心+ | 支持并发评估 |
| **内存** | 16GB+ | 多个模型同时加载 |
| **存储** | 100GB+ | 系统+模型+日志+备份 |
| **网络** | 50Mbps+ | 快速响应 |
| **GPU** | 可选 | 加速神经网络模型（COMET/BLEURT） |

### 存储空间估算

```
系统文件:          ~10GB
Python环境:        ~5GB
模型文件:
  - COMET:         ~500MB (首次下载)
  - BLEURT-20:     ~500MB (已包含)
  - BERTScore:     ~400MB (首次下载)
  - PyTorch:       ~2GB
  - TensorFlow:    ~1GB
日志文件:          ~5GB (按需清理)
预留空间:          ~20GB
─────────────────────────
总计:              ~44GB (推荐100GB)
```

---

## 📦 依赖分析

### 系统依赖

```bash
# Ubuntu系统包
sudo apt-get update
sudo apt-get install -y \
    python3.8+ \
    python3-pip \
    python3-venv \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev
```

### Python依赖

#### 基础依赖（必需）
```python
numpy>=1.20.0
flask>=2.0.0
flask-cors>=3.0.0
requests>=2.25.0
```

#### 评估器依赖（可选）
```python
# BERTScore
bert-score>=0.3.13

# COMET
unbabel-comet>=2.0.0
pytorch  # 需要单独安装

# BLEURT
bleurt>=0.0.1
tensorflow  # 需要单独安装

# ChrF
sacrebleu>=2.0.0
```

### 特殊依赖说明

1. **NumPy版本冲突**: COMET和BLEURT可能有numpy版本冲突，建议固定版本
2. **PyTorch**: 建议使用conda安装，支持CUDA加速
3. **TensorFlow**: BLEURT需要，注意版本兼容性

---

## 🚀 部署方案

### 方案一：Conda环境 + Gunicorn（推荐）

#### 优点
- ✅ 依赖隔离好
- ✅ 易于管理
- ✅ 支持生产级WSGI服务器
- ✅ 便于多版本Python管理

#### 部署步骤

```bash
# 1. 安装Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
source ~/.bashrc

# 2. 创建conda环境
conda create -n translator_eval python=3.9 -y
conda activate translator_eval

# 3. 安装指定版本的numpy（避免冲突）
conda install numpy=1.23.5 -y

# 4. 安装PyTorch（COMET依赖）
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y

# 5. 安装COMET
pip install unbabel-comet

# 6. 安装BLEURT（从GitHub）
git clone https://github.com/google-research/bleurt.git
cd bleurt
pip install . --no-deps
cd ..

# 7. 安装TensorFlow（BLEURT依赖）
pip install tensorflow

# 8. 安装其他依赖
pip install bert-score sacrebleu

# 9. 安装项目
cd /path/to/translation_evaluator
pip install -e .

# 10. 安装Gunicorn
pip install gunicorn

# 11. 启动服务
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app
```

#### Systemd服务配置

创建 `/etc/systemd/system/translation-evaluator.service`:

```ini
[Unit]
Description=Translation Evaluator API Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/translation_evaluator
Environment="PATH=/home/your_user/miniconda3/envs/translator_eval/bin"
ExecStart=/home/your_user/miniconda3/envs/translator_eval/bin/gunicorn \
    -w 4 \
    -b 0.0.0.0:5001 \
    --timeout 300 \
    --access-logfile /path/to/translation_evaluator/logs/access.log \
    --error-logfile /path/to/translation_evaluator/logs/error.log \
    eval_server:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable translation-evaluator
sudo systemctl start translation-evaluator
sudo systemctl status translation-evaluator
```

---

### 方案二：Python venv + Nginx反向代理

#### 优点
- ✅ 轻量级
- ✅ Nginx提供负载均衡和SSL
- ✅ 适合小规模部署

#### 部署步骤

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖（同上，但使用pip而非conda）
pip install numpy==1.23.5
pip install torch torchvision torchaudio
pip install unbabel-comet
pip install tensorflow
pip install bert-score sacrebleu
pip install -e .

# 3. 安装Gunicorn
pip install gunicorn

# 4. 启动服务（后台运行）
nohup gunicorn -w 4 -b 127.0.0.1:5001 eval_server:app > logs/gunicorn.log 2>&1 &
```

#### Nginx配置

创建 `/etc/nginx/sites-available/translation-evaluator`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到HTTPS（如果使用SSL）
    # return 301 https://$server_name$request_uri;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间（模型加载需要时间）
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 日志
    access_log /var/log/nginx/translation-evaluator-access.log;
    error_log /var/log/nginx/translation-evaluator-error.log;
}
```

启用配置:
```bash
sudo ln -s /etc/nginx/sites-available/translation-evaluator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

### 方案三：Docker容器化部署（推荐用于生产）

#### 优点
- ✅ 完全隔离
- ✅ 易于部署和扩展
- ✅ 版本控制
- ✅ 便于迁移

#### Dockerfile示例

```dockerfile
FROM continuumio/miniconda3:latest

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# 创建conda环境
RUN conda create -n translator_eval python=3.9 -y

# 激活环境并安装依赖
RUN echo "conda activate translator_eval" >> ~/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

RUN conda install -n translator_eval numpy=1.23.5 -y && \
    conda install -n translator_eval pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y

RUN /opt/conda/envs/translator_eval/bin/pip install \
    unbabel-comet \
    tensorflow \
    bert-score \
    sacrebleu \
    flask \
    flask-cors \
    requests \
    gunicorn

# 安装BLEURT
RUN git clone https://github.com/google-research/bleurt.git /tmp/bleurt && \
    /opt/conda/envs/translator_eval/bin/pip install /tmp/bleurt --no-deps && \
    rm -rf /tmp/bleurt

# 复制项目文件
COPY . /app

# 安装项目
RUN /opt/conda/envs/translator_eval/bin/pip install -e .

# 暴露端口
EXPOSE 5001

# 启动命令
CMD ["/opt/conda/envs/translator_eval/bin/gunicorn", \
     "-w", "4", \
     "-b", "0.0.0.0:5001", \
     "--timeout", "300", \
     "eval_server:app"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  translation-evaluator:
    build: .
    ports:
      - "5001:5001"
    volumes:
      - ./logs:/app/logs
      - ./BLEURT-20:/app/BLEURT-20
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

部署:
```bash
docker-compose up -d
```

---

## 🔧 配置优化

### 1. Gunicorn配置优化

创建 `gunicorn_config.py`:

```python
import multiprocessing

bind = "0.0.0.0:5001"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 300
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
```

启动:
```bash
gunicorn -c gunicorn_config.py eval_server:app
```

### 2. 模型预加载优化

在 `eval_server.py` 中，确保模型在启动时预加载:

```python
# 在应用启动时初始化评估器
@app.before_first_request
def initialize():
    init_evaluator()
```

### 3. 日志轮转配置

创建 `/etc/logrotate.d/translation-evaluator`:

```
/path/to/translation_evaluator/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 your_user your_user
}
```

---

## 🔐 安全配置

### 1. 防火墙配置

```bash
# 只开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (如果使用Nginx)
sudo ufw allow 443/tcp   # HTTPS (如果使用SSL)
sudo ufw enable
```

### 2. API认证（可选）

如果需要API认证，可以添加:

```python
# 在eval_server.py中添加
from functools import wraps
import os

API_KEY = os.environ.get('API_KEY', '')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if API_KEY and api_key != API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route("/eval", methods=["POST"])
@require_api_key
def eval_text():
    # ...
```

### 3. SSL/TLS配置（使用Let's Encrypt）

```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 📊 监控和维护

### 1. 健康检查

```bash
# 手动检查
curl http://localhost:5001/health

# 定时检查脚本
#!/bin/bash
# health_check.sh
response=$(curl -s http://localhost:5001/health)
if [[ $response != *"healthy"* ]]; then
    echo "Service is down!" | mail -s "Alert" admin@example.com
    sudo systemctl restart translation-evaluator
fi
```

### 2. 日志监控

```bash
# 实时查看日志
tail -f logs/api_$(date +%Y%m%d).log

# 查看错误日志
grep ERROR logs/api_*.log

# 统计请求数
grep "收到单个样本评估请求" logs/api_*.log | wc -l
```

### 3. 性能监控

使用 `htop` 或 `top` 监控资源使用:

```bash
sudo apt-get install htop -y
htop
```

### 4. 磁盘空间监控

```bash
# 检查磁盘使用
df -h

# 清理旧日志
find logs/ -name "*.log" -mtime +30 -delete
```

---

## 🚨 故障排除

### 问题1: 模型加载失败

**症状**: COMET或BLEURT初始化失败

**解决方案**:
```bash
# 检查模型文件
ls -lh ~/.cache/huggingface/  # COMET模型
ls -lh BLEURT-20/             # BLEURT模型

# 重新下载模型
python -c "from translation_evaluator import COMETScorer; s = COMETScorer(); s.initialize()"
```

### 问题2: 内存不足

**症状**: OOM错误，服务崩溃

**解决方案**:
- 减少Gunicorn worker数量
- 禁用部分评估器（如BLEURT）
- 增加服务器内存

### 问题3: 请求超时

**症状**: 评估请求超时

**解决方案**:
- 增加Gunicorn timeout时间
- 检查网络连接
- 优化模型加载

### 问题4: 端口被占用

**症状**: 启动失败，端口已被占用

**解决方案**:
```bash
# 查找占用端口的进程
sudo lsof -i :5001

# 杀死进程
sudo kill -9 <PID>

# 或更改端口
python eval_server.py --port 5002
```

---

## 📈 性能优化建议

### 1. 使用GPU加速（如果可用）

```bash
# 安装CUDA版本的PyTorch和TensorFlow
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
pip install tensorflow[and-cuda]
```

### 2. 模型缓存优化

确保模型文件缓存在SSD上，提高加载速度。

### 3. 批量处理优化

对于大量评估请求，使用批量接口而不是单个接口。

### 4. 负载均衡（高并发场景）

使用Nginx或HAProxy进行负载均衡:

```nginx
upstream translation_evaluator {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    location / {
        proxy_pass http://translation_evaluator;
    }
}
```

---

## 📝 部署检查清单

### 部署前
- [ ] 服务器资源满足要求
- [ ] 系统依赖已安装
- [ ] Python环境已配置
- [ ] 项目代码已上传
- [ ] 模型文件已准备

### 部署中
- [ ] 依赖安装成功
- [ ] 模型加载测试通过
- [ ] 服务启动成功
- [ ] 健康检查通过
- [ ] API测试通过

### 部署后
- [ ] 防火墙配置正确
- [ ] 日志记录正常
- [ ] 监控脚本运行
- [ ] 备份策略已实施
- [ ] 文档已更新

---

## 🎯 推荐部署方案

### 小规模使用（<100请求/天）
- **方案**: Python venv + Gunicorn
- **配置**: 2核CPU, 8GB内存
- **成本**: 低

### 中等规模（100-1000请求/天）
- **方案**: Conda环境 + Gunicorn + Nginx
- **配置**: 4核CPU, 16GB内存
- **成本**: 中

### 大规模（>1000请求/天）
- **方案**: Docker容器化 + Kubernetes + 负载均衡
- **配置**: 多节点，每节点4核CPU, 16GB内存
- **成本**: 高

---

## 📌 总结

### 部署要点

1. **环境隔离**: 使用conda或venv隔离依赖
2. **生产级服务器**: 使用Gunicorn而非Flask开发服务器
3. **反向代理**: 使用Nginx提供SSL和负载均衡
4. **监控告警**: 设置健康检查和日志监控
5. **安全配置**: 配置防火墙和API认证
6. **备份策略**: 定期备份模型和配置

### 关键成功因素

✅ **充足的资源**: 确保有足够的内存和存储  
✅ **正确的依赖**: 注意版本兼容性  
✅ **完善的监控**: 及时发现问题  
✅ **良好的文档**: 便于维护和扩展  

通过以上方案，可以成功将翻译评估器部署到Ubuntu云服务器，并提供稳定可靠的服务。

