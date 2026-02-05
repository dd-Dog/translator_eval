# COMET和BERTScore模型离线部署指南

## 问题说明

1. **COMET模型**：虽然checkpoint文件是本地的，但它依赖的tokenizer（`xlm-roberta-large`）需要从HuggingFace下载。
2. **BERTScore模型**：需要从HuggingFace下载`bert-base-multilingual-cased`模型。

如果服务器无法访问外网，需要手动下载并配置这些模型。

## 解决方案

### 方法1: 在能访问外网的机器上下载模型（推荐）

#### 步骤1: 下载xlm-roberta-large模型

在有外网的机器上运行：

```bash
# 安装huggingface_hub
pip install huggingface_hub

# 下载模型
python download_huggingface_model.py --output-dir ./models
```

或者直接使用Python：

```python
from huggingface_hub import snapshot_download

# 下载模型
model_path = snapshot_download(
    repo_id="xlm-roberta-large",
    cache_dir="./models"
)
print(f"模型下载到: {model_path}")
```

#### 步骤2: 传输到服务器

```bash
# 将模型目录传输到服务器
scp -r ./models/xlm-roberta-large user@server:/root/.cache/huggingface/hub/
```

#### 步骤3: 在服务器上设置环境变量

```bash
# 设置HuggingFace缓存目录
export HF_HOME=/root/.cache/huggingface
export TRANSFORMERS_CACHE=/root/.cache/huggingface/hub

# 或者设置为离线模式（如果模型已完全下载）
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

#### 步骤4: 启动服务

**重要**: COMET_MODEL_PATH应该指向checkpoint文件，而不是目录：

```bash
# 方法1: 使用环境变量
export COMET_MODEL_PATH=/root/bianjb/wmt22-comet-da/checkpoints/model.ckpt
export HF_HOME=/root/.cache/huggingface
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app

# 方法2: 使用命令行参数
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app \
    --comet-model /root/bianjb/wmt22-comet-da/checkpoints/model.ckpt \
    --hf-home /root/.cache/huggingface
```

**注意**: 
- 如果checkpoint文件在 `checkpoints/model.ckpt`，代码会自动查找
- 但如果直接指定checkpoint文件路径，会更可靠

### 方法2: 使用git lfs下载（如果HuggingFace Hub不可用）

```bash
# 安装git-lfs
sudo apt-get install git-lfs
git lfs install

# 克隆模型仓库
git clone https://huggingface.co/xlm-roberta-large

# 传输到服务器
scp -r xlm-roberta-large user@server:/root/.cache/huggingface/hub/
```

### 方法3: 手动下载文件

访问 https://huggingface.co/xlm-roberta-large/tree/main 下载以下文件：

必需文件：
- `tokenizer_config.json`
- `tokenizer.json`
- `sentencepiece.bpe.model`
- `vocab.json`
- `merges.txt`

可选文件（如果需要完整模型）：
- `pytorch_model.bin` 或 `model.safetensors`
- `config.json`

将文件放到：`/root/.cache/huggingface/hub/models--xlm-roberta-large/snapshots/[hash]/`

## 验证模型是否可用

运行测试脚本：

```bash
python test_comet_path.py
```

如果看到模型加载成功，说明配置正确。

## 常见问题

### Q1: 仍然尝试连接HuggingFace

**A**: 确保设置了正确的环境变量：
```bash
export HF_HOME=/root/.cache/huggingface
export TRANSFORMERS_CACHE=/root/.cache/huggingface/hub
export HF_HUB_OFFLINE=1
```

### Q2: 找不到tokenizer文件

**A**: 检查文件路径是否正确：
```bash
ls -la /root/.cache/huggingface/hub/models--xlm-roberta-large/snapshots/*/
```

应该能看到 `tokenizer_config.json` 等文件。

### Q3: 模型路径结构

HuggingFace缓存目录结构：
```
~/.cache/huggingface/hub/
└── models--xlm-roberta-large/
    └── snapshots/
        └── [hash]/
            ├── tokenizer_config.json
            ├── tokenizer.json
            ├── sentencepiece.bpe.model
            └── ...
```

## 快速检查清单

- [ ] xlm-roberta-large模型已下载
- [ ] 模型文件已传输到服务器
- [ ] 环境变量已设置（HF_HOME或TRANSFORMERS_CACHE）
- [ ] COMET_MODEL_PATH指向正确的checkpoint文件
- [ ] 测试脚本运行成功
- [ ] 服务启动成功
