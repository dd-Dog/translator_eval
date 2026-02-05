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

### 3. 确保bleurt_worker.py在项目目录

确保`bleurt_worker.py`文件在项目根目录，或指定完整路径。

### 4. 配置环境变量

#### 方法1: 使用环境变量（推荐）

```bash
export BLEURT_USE_SUBPROCESS=true
export BLEURT_PYTHON_ENV=/path/to/bleurt_env/bin/python
export BLEURT_WORKER_SCRIPT=/path/to/translation_evaluator/bleurt_worker.py
export BLEURT_CHECKPOINT=/path/to/BLEURT-20

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app --use-bleurt
```

#### 方法2: 使用命令行参数

```bash
python eval_server.py \
    --use-bleurt \
    --bleurt-subprocess \
    --bleurt-python-env /path/to/bleurt_env/bin/python \
    --bleurt-worker-script /path/to/bleurt_worker.py \
    --bleurt-checkpoint /path/to/BLEURT-20
```

#### 方法3: 使用gunicorn（需要设置环境变量）

```bash
export BLEURT_USE_SUBPROCESS=true
export BLEURT_PYTHON_ENV=/root/miniconda3/envs/bleurt_env/bin/python
export BLEURT_WORKER_SCRIPT=/root/bianjb/translation_evaluator/bleurt_worker.py
export BLEURT_CHECKPOINT=/root/bianjb/BLEURT-20

gunicorn -w 4 -b 0.0.0.0:5001 --timeout 300 eval_server:app
```

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

### Q5: 性能问题

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
