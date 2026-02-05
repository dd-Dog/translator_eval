# BERTScore离线部署指南

## 问题说明

BERTScore需要从HuggingFace下载`bert-base-multilingual-cased`模型。如果服务器无法访问外网，需要手动下载模型。

## 解决方案

### 方法1: 在能访问外网的机器上下载模型（推荐）

#### 步骤1: 下载bert-base-multilingual-cased模型

在有外网的机器上运行：

```bash
# 安装依赖
pip install huggingface_hub transformers

# 下载模型
python -c "from huggingface_hub import snapshot_download; snapshot_download('bert-base-multilingual-cased', cache_dir='./models')"
```

或者使用Python脚本：

```python
from huggingface_hub import snapshot_download

# 下载模型
model_path = snapshot_download(
    repo_id="bert-base-multilingual-cased",
    cache_dir="./models"
)
print(f"模型下载到: {model_path}")
```

#### 步骤2: 传输到服务器

```bash
# 将模型传输到服务器的HuggingFace缓存目录
scp -r ./models/models--bert-base-multilingual-cased root@server:/root/.cache/huggingface/hub/
```

或者如果使用自定义HF_HOME：

```bash
scp -r ./models/models--bert-base-multilingual-cased root@server:/root/bianjb/huggingface/hub/
```

#### 步骤3: 在服务器上设置环境变量

```bash
# 设置HuggingFace缓存目录和离线模式
export HF_HOME=/root/bianjb/huggingface  # 或 /root/.cache/huggingface
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

#### 步骤4: 验证模型

```bash
# 检查模型文件是否存在
ls -la /root/bianjb/huggingface/hub/models--bert-base-multilingual-cased/snapshots/*/
```

应该能看到以下文件：
- `config.json`
- `pytorch_model.bin` 或 `model.safetensors`
- `tokenizer_config.json`
- `vocab.txt`
- 等

### 方法2: 使用git lfs下载

```bash
# 安装git-lfs
sudo apt-get install git-lfs
git lfs install

# 克隆模型仓库
git clone https://huggingface.co/bert-base-multilingual-cased

# 传输到服务器
scp -r bert-base-multilingual-cased root@server:/root/bianjb/huggingface/hub/models--bert-base-multilingual-cased/
```

然后运行修复脚本（类似COMET）：

```bash
python fix_git_downloaded_model.py
```

但需要修改脚本中的模型路径。

### 方法3: 手动下载文件

访问 https://huggingface.co/bert-base-multilingual-cased/tree/main 下载以下文件：

必需文件：
- `config.json`
- `pytorch_model.bin` 或 `model.safetensors`
- `tokenizer_config.json`
- `vocab.txt`
- `tokenizer.json`（如果有）

将文件放到：`/root/bianjb/huggingface/hub/models--bert-base-multilingual-cased/snapshots/[hash]/`

## 启动服务

设置环境变量后启动服务：

```bash
export HF_HOME=/root/bianjb/huggingface
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export COMET_MODEL_PATH=/root/bianjb/wmt22-comet-da/checkpoints/model.ckpt

gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app
```

## 验证

重启服务后，查看日志应该看到：

```
🔧 检测到本地BERT模型，已启用离线模式
✓ BERTScore已就绪
```

如果看到错误，检查：
1. 模型文件是否完整
2. 环境变量是否正确设置
3. 模型路径是否正确

## 常见问题

### Q1: 仍然尝试连接HuggingFace

**A**: 确保设置了环境变量：
```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/root/bianjb/huggingface
```

### Q2: 找不到模型文件

**A**: 检查文件路径：
```bash
ls -la /root/bianjb/huggingface/hub/models--bert-base-multilingual-cased/snapshots/*/
```

### Q3: 模型路径结构

HuggingFace缓存目录结构：
```
~/.cache/huggingface/hub/
└── models--bert-base-multilingual-cased/
    └── snapshots/
        └── [hash]/
            ├── config.json
            ├── pytorch_model.bin
            ├── tokenizer_config.json
            └── ...
```

## 快速检查清单

- [ ] bert-base-multilingual-cased模型已下载
- [ ] 模型文件已传输到服务器
- [ ] 环境变量已设置（HF_HOME、HF_HUB_OFFLINE、TRANSFORMERS_OFFLINE）
- [ ] 服务启动时看到"检测到本地BERT模型，已启用离线模式"
- [ ] BERTScore计算成功
