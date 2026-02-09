# Systemd服务故障排查指南

## 🔍 问题诊断步骤

### 1. 查看详细错误日志

```bash
# 查看服务状态
sudo systemctl status translation-evaluator -l --no-pager

# 查看最近100行日志
sudo journalctl -u translation-evaluator -n 100 --no-pager

# 实时查看日志
sudo journalctl -u translation-evaluator -f

# 查看所有日志（从启动开始）
sudo journalctl -u translation-evaluator --no-pager
```

### 2. 检查服务文件配置

```bash
# 查看服务文件
cat /etc/systemd/system/translation-evaluator.service

# 检查语法
sudo systemctl daemon-reload
sudo systemctl status translation-evaluator
```

### 3. 手动测试启动

```bash
# 进入项目目录
cd /root/bianjb/translation_evaluator

# 设置环境变量（与服务文件中的一致）
export USE_REQUEST_QUEUE=true
export MAX_QUEUE_SIZE=50
export REQUEST_TIMEOUT=600
export USE_BLEURT=true
export BLEURT_USE_SUBPROCESS=true
export BLEURT_PYTHON_ENV=/root/miniconda3/envs/translator_eval_bleurt/bin/python
export BLEURT_WORKER_SCRIPT=/root/bianjb/translation_evaluator/bleurt_worker.py
export BLEURT_CHECKPOINT=/root/bianjb/translation_evaluator/BLEURT-20
export COMET_MODEL_PATH=/root/bianjb/wmt22-comet-da
export HF_HOME=/root/.cache/huggingface

# 测试Python导入
/root/miniconda3/envs/tranlator_eval/bin/python -c "
import sys
sys.path.insert(0, '/root/bianjb/translation_evaluator')
from translation_evaluator import UnifiedEvaluator
from translation_evaluator.request_queue import RequestQueue
import eval_server
print('✅ 所有模块导入成功')
"

# 测试gunicorn启动（会立即退出，但可以看到错误）
/root/miniconda3/envs/tranlator_eval/bin/gunicorn \
    -w 1 \
    -b 0.0.0.0:5001 \
    --timeout 600 \
    eval_server:app
```

### 4. 使用测试脚本

```bash
# 运行测试脚本
chmod +x test_gunicorn_start.sh
./test_gunicorn_start.sh
```

## 🐛 常见问题及解决方案

### 问题1: 模块导入失败

**错误信息**:
```
ModuleNotFoundError: No module named 'translation_evaluator'
```

**解决方案**:
```bash
# 检查项目是否已安装
cd /root/bianjb/translation_evaluator
/root/miniconda3/envs/tranlator_eval/bin/pip install -e .

# 检查PYTHONPATH
echo $PYTHONPATH
```

### 问题2: 请求队列初始化失败

**错误信息**:
```
⚠️  请求队列初始化失败: ...
```

**解决方案**:
- 检查`translation_evaluator/request_queue.py`是否存在
- 检查文件权限
- 临时禁用队列测试：
  ```bash
  # 修改服务文件，添加环境变量
  Environment="USE_REQUEST_QUEUE=false"
  sudo systemctl daemon-reload
  sudo systemctl restart translation-evaluator
  ```

### 问题3: 路径错误

**错误信息**:
```
FileNotFoundError: [Errno 2] No such file or directory
```

**解决方案**:
```bash
# 检查所有路径是否存在
ls -la /root/bianjb/translation_evaluator
ls -la /root/miniconda3/envs/tranlator_eval/bin/gunicorn
ls -la /root/bianjb/translation_evaluator/bleurt_worker.py
ls -la /root/bianjb/translation_evaluator/BLEURT-20
ls -la /root/bianjb/wmt22-comet-da

# 修改服务文件中的路径
sudo nano /etc/systemd/system/translation-evaluator.service
```

### 问题4: 权限问题

**错误信息**:
```
Permission denied
```

**解决方案**:
```bash
# 检查文件权限
ls -la /root/bianjb/translation_evaluator
ls -la /root/bianjb/translation_evaluator/logs

# 确保日志目录可写
chmod 755 /root/bianjb/translation_evaluator/logs
chown -R root:root /root/bianjb/translation_evaluator
```

### 问题5: 端口被占用

**错误信息**:
```
Address already in use
```

**解决方案**:
```bash
# 检查端口占用
netstat -tlnp | grep 5001
# 或
ss -tlnp | grep 5001

# 停止占用端口的进程
sudo kill <PID>

# 或修改服务端口
# 在服务文件中修改 SERVICE_PORT
```

### 问题6: 环境变量未生效

**解决方案**:
```bash
# 检查服务文件中的环境变量
sudo systemctl show translation-evaluator | grep Environment

# 确保环境变量格式正确（每行一个Environment=）
# 错误示例：
# Environment="VAR1=value1 VAR2=value2"  # 错误
# 正确示例：
# Environment="VAR1=value1"
# Environment="VAR2=value2"
```

### 问题7: --preload选项导致问题

**解决方案**:
- 移除`--preload`选项（已在最新版本中移除）
- 或者确保所有模块导入都没有问题

## 🔧 修复步骤

### 步骤1: 停止服务

```bash
sudo systemctl stop translation-evaluator
```

### 步骤2: 检查并修复配置

```bash
# 运行调试脚本
chmod +x debug_systemd_service.sh
./debug_systemd_service.sh

# 或手动检查
sudo nano /etc/systemd/system/translation-evaluator.service
```

### 步骤3: 重新加载并启动

```bash
sudo systemctl daemon-reload
sudo systemctl start translation-evaluator
sudo systemctl status translation-evaluator
```

### 步骤4: 查看日志

```bash
sudo journalctl -u translation-evaluator -f
```

## 📝 临时解决方案

如果问题持续，可以临时使用nohup方式：

```bash
# 停止systemd服务
sudo systemctl stop translation-evaluator
sudo systemctl disable translation-evaluator

# 使用nohup启动
cd /root/bianjb/translation_evaluator
chmod +x start_background.sh
./start_background.sh
```

## 🆘 获取帮助

如果以上方法都无法解决问题，请提供：

1. **完整错误日志**:
   ```bash
   sudo journalctl -u translation-evaluator --no-pager > error_log.txt
   ```

2. **服务文件内容**:
   ```bash
   cat /etc/systemd/system/translation-evaluator.service
   ```

3. **手动测试结果**:
   ```bash
   ./test_gunicorn_start.sh > test_output.txt 2>&1
   ```

4. **环境信息**:
   ```bash
   /root/miniconda3/envs/tranlator_eval/bin/python --version
   /root/miniconda3/envs/tranlator_eval/bin/pip list | grep -E "(flask|gunicorn|translation)"
   ```
