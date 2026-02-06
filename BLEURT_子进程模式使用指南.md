# BLEURT子进程模式使用指南

## 问题说明

BLEURT和COMET环境有冲突（例如TensorFlow版本不兼容），因此需要将BLEURT运行在独立的Python环境中。

## 解决方案

使用子进程模式，将BLEURT评分程序分离到独立的Python环境中运行。

## 配置步骤

### 1. 创建BLEURT专用Python环境

```bash
# 创建conda环境（推荐）
conda create -n bleurt_env python=3.9 -y
conda activate bleurt_env

# 安装BLEURT依赖
pip install tensorflow
pip install bleurt

# 或者使用CPU版本
pip install tensorflow-cpu
pip install bleurt
```

### 2. 准备BLEURT模型

下载BLEURT模型到指定位置：

```bash
# 下载BLEURT-20模型
wget https://storage.googleapis.com/bleurt-oss-21/BLEURT-20.zip
unzip BLEURT-20.zip

# 或使用Python下载
python -c "from urllib.request import urlretrieve; urlretrieve('https://storage.googleapis.com/bleurt-oss-21/BLEURT-20.zip', 'BLEURT-20.zip')"
unzip BLEURT-20.zip
```

### 2.1. 确认BLEURT_CHECKPOINT路径

下载并解压后，需要找到BLEURT模型目录的完整路径：

#### 方法1: 查找BLEURT-20目录

```bash
# 查找BLEURT-20目录
find /root -name "BLEURT-20" -type d 2>/dev/null

# 或如果知道大概位置
ls -la /root/bianjb/BLEURT-20
# 或
ls -la ~/BLEURT-20
```

#### 方法2: 检查当前目录

如果模型下载在当前目录：

```bash
# 查看当前目录
pwd

# 查看BLEURT-20目录内容
ls -la BLEURT-20/

# 应该能看到类似这样的文件：
# bert_config.json
# bleurt_config.json
# saved_model.pb
# sent_piece.model
# sent_piece.vocab
# variables/
```

#### 方法3: 使用绝对路径

BLEURT_CHECKPOINT应该是包含以下文件的目录路径：

```
BLEURT-20/
├── bert_config.json
├── bleurt_config.json
├── saved_model.pb
├── sent_piece.model
├── sent_piece.vocab
└── variables/
    ├── variables.data-00000-of-00001
    └── variables.index
```

**常见路径示例：**

```bash
# 如果模型在项目目录
/root/bianjb/translation_evaluator/BLEURT-20

# 如果模型在用户目录
/root/BLEURT-20
# 或
~/BLEURT-20

# 如果模型在其他位置
/path/to/your/BLEURT-20
```

**验证路径是否正确：**

```bash
# 检查目录是否存在
ls -la /path/to/BLEURT-20

# 检查关键文件是否存在
ls -la /path/to/BLEURT-20/saved_model.pb
ls -la /path/to/BLEURT-20/variables/

# 如果文件都存在，路径正确
```

### 3. 确认bleurt_worker.py路径

确保`bleurt_worker.py`文件在项目根目录，或指定完整路径：

```bash
# 查找bleurt_worker.py
find /root/bianjb -name "bleurt_worker.py" 2>/dev/null

# 或如果知道项目目录
ls -la /root/bianjb/translation_evaluator/bleurt_worker.py

# 常见路径：
# /root/bianjb/translation_evaluator/bleurt_worker.py
```

### 4. 配置环境变量

#### 方法1: 使用环境变量（推荐）

**首先确认所有路径：**

```bash
# 1. 确认conda环境Python路径
conda activate translator_eval_bleurt
which python
# 输出示例: /root/miniconda3/envs/translator_eval_bleurt/bin/python

# 2. 确认BLEURT模型路径
ls -la /root/bianjb/BLEURT-20
# 应该能看到saved_model.pb等文件

# 3. 确认worker脚本路径
ls -la /root/bianjb/translation_evaluator/bleurt_worker.py
```

**然后设置环境变量并启动服务：**

```bash
# 方法1: 使用环境变量 + gunicorn（推荐）
export USE_BLEURT=true  # ⚠️ 必须设置此环境变量启用BLEURT
export BLEURT_USE_SUBPROCESS=true
export BLEURT_PYTHON_ENV=/root/miniconda3/envs/translator_eval_bleurt/bin/python
export BLEURT_WORKER_SCRIPT=/root/bianjb/translation_evaluator/bleurt_worker.py
export BLEURT_CHECKPOINT=/root/bianjb/BLEURT-20

# 启动服务（gunicorn不支持传递应用参数，必须使用环境变量）
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app

# 方法2: 使用命令行参数（更简单）
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app \
    --use-bleurt \
    --bleurt-subprocess \
    --bleurt-python-env /root/miniconda3/envs/translator_eval_bleurt/bin/python \
    --bleurt-worker-script /root/bianjb/translation_evaluator/bleurt_worker.py \
    --bleurt-checkpoint /root/bianjb/BLEURT-20
```

**⚠️ 重要提示：**
- **使用gunicorn时**：必须设置环境变量 `USE_BLEURT=true`，因为gunicorn不支持传递应用参数
- **使用python直接启动时**：可以传递 `--use-bleurt` 参数或设置 `USE_BLEURT=true` 环境变量
- 如果使用子进程模式，还需要传递 `--bleurt-subprocess` 或设置 `BLEURT_USE_SUBPROCESS=true`

#### 方法2: 使用命令行参数（推荐）

**⚠️ 重要：必须传递 `--use-bleurt` 参数！**

```bash
# 使用gunicorn启动（生产环境）
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app \
    --use-bleurt \
    --bleurt-subprocess \
    --bleurt-python-env /root/miniconda3/envs/translator_eval_bleurt/bin/python \
    --bleurt-worker-script /root/bianjb/translation_evaluator/bleurt_worker.py \
    --bleurt-checkpoint /root/bianjb/BLEURT-20

# 或使用python直接启动（开发环境）
python eval_server.py \
    --use-bleurt \
    --bleurt-subprocess \
    --bleurt-python-env /root/miniconda3/envs/translator_eval_bleurt/bin/python \
    --bleurt-worker-script /root/bianjb/translation_evaluator/bleurt_worker.py \
    --bleurt-checkpoint /root/bianjb/BLEURT-20
```

**注意：使用gunicorn时，参数需要放在 `eval_server:app` 之后！**

### 5. 验证配置

启动服务后，查看日志应该看到：

```
🔧 启用BLEURT子进程模式
   Python环境: /path/to/bleurt_env/bin/python
   工作脚本: /path/to/bleurt_worker.py
   检查点: /path/to/BLEURT-20
🔧 BLEURT使用子进程模式
✅ BLEURT子进程模式已就绪
```

## 环境变量说明

| 环境变量 | 说明 | 必需 |
|---------|------|------|
| `BLEURT_USE_SUBPROCESS` | 设置为`true`启用子进程模式 | 是 |
| `BLEURT_PYTHON_ENV` | BLEURT的Python环境路径 | 是 |
| `BLEURT_WORKER_SCRIPT` | BLEURT工作脚本路径 | 否（默认：`./bleurt_worker.py`） |
| `BLEURT_CHECKPOINT` | BLEURT检查点路径 | 否（默认：`BLEURT-20`） |

## 工作原理

1. 主进程（COMET环境）调用BLEURT评分时
2. 通过subprocess启动独立的Python进程（BLEURT环境）
3. 将翻译文本和参考文本通过stdin传递给worker脚本
4. Worker脚本在BLEURT环境中计算分数
5. 通过stdout返回JSON格式的结果
6. 主进程解析结果并返回

## 常见问题

### Q1: Worker脚本找不到

**A**: 确保`bleurt_worker.py`在正确的位置，或使用绝对路径设置`BLEURT_WORKER_SCRIPT`。

### Q2: Python环境路径错误

**A**: 使用完整路径，例如：
```bash
export BLEURT_PYTHON_ENV=/root/miniconda3/envs/bleurt_env/bin/python
```

### Q3: 模型路径错误

**A**: 使用绝对路径设置检查点：
```bash
export BLEURT_CHECKPOINT=/root/bianjb/BLEURT-20
```

### Q4: 子进程超时

**A**: 默认超时300秒，如果模型很大可能需要更长时间。可以修改`bleurt_scorer.py`中的`timeout=300`。

### Q5: BLEURT未启用（use_bleurt=False）

**A**: 必须传递 `--use-bleurt` 参数！即使设置了所有环境变量，如果没有传递 `--use-bleurt`，BLEURT也不会被启用。

```bash
# ❌ 错误：缺少 --use-bleurt
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app

# ✅ 正确：包含 --use-bleurt
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app --use-bleurt --bleurt-subprocess ...
```

### Q6: 性能问题

**A**: 子进程模式会有一定的性能开销（进程启动和通信），但可以避免环境冲突。如果需要高性能，考虑使用进程池复用worker进程。

## 性能优化建议

1. **批量处理**：尽量使用批量评估接口，减少子进程启动次数
2. **进程池**：未来可以考虑实现进程池，复用worker进程
3. **缓存**：对于相同的文本对，可以添加缓存机制

## 完整示例

```bash
# 1. 创建BLEURT环境
conda create -n bleurt_env python=3.9 -y
conda activate bleurt_env
pip install tensorflow-cpu bleurt

# 2. 下载模型
cd /root/bianjb
wget https://storage.googleapis.com/bleurt-oss-21/BLEURT-20.zip
unzip BLEURT-20.zip

# 3. 设置环境变量
export BLEURT_USE_SUBPROCESS=true
export BLEURT_PYTHON_ENV=/root/miniconda3/envs/bleurt_env/bin/python
export BLEURT_WORKER_SCRIPT=/root/bianjb/translation_evaluator/bleurt_worker.py
export BLEURT_CHECKPOINT=/root/bianjb/BLEURT-20

# 4. 启动服务
cd /root/bianjb/translation_evaluator
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app --use-bleurt
```
