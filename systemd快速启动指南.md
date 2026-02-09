# Systemd快速启动指南

## 🚀 快速启动步骤

### 1. 停止所有现有进程

```bash
# 快速停止
chmod +x quick_stop.sh
./quick_stop.sh

# 或手动停止
pkill -f "gunicorn.*eval_server"
```

### 2. 配置并启动systemd服务

#### 方法A：使用自动配置脚本（推荐）

```bash
# 1. 运行配置脚本（如果还没运行过）
sudo chmod +x setup_systemd_service.sh
sudo ./setup_systemd_service.sh

# 2. 如果服务文件已存在，直接启动
chmod +x start_systemd_service.sh
./start_systemd_service.sh
```

#### 方法B：手动启动

```bash
# 1. 检查服务文件是否存在
ls -la /etc/systemd/system/translation-evaluator.service

# 2. 如果不存在，先配置
sudo ./setup_systemd_service.sh

# 3. 重新加载systemd配置
sudo systemctl daemon-reload

# 4. 启动服务
sudo systemctl start translation-evaluator

# 5. 查看状态
sudo systemctl status translation-evaluator

# 6. 启用开机自启（可选）
sudo systemctl enable translation-evaluator
```

## 📊 验证服务运行

### 1. 检查服务状态

```bash
sudo systemctl status translation-evaluator
```

**正常状态应该显示**:
- `Active: active (running)`
- 没有错误信息

### 2. 测试API

```bash
# 健康检查
curl http://localhost:5001/health

# 队列统计（如果启用队列）
curl http://localhost:5001/queue/stats
```

### 3. 查看日志

```bash
# 实时查看日志
sudo journalctl -u translation-evaluator -f

# 查看最近100行
sudo journalctl -u translation-evaluator -n 100

# 查看所有日志
sudo journalctl -u translation-evaluator --no-pager
```

## 🔧 常用操作

### 启动服务

```bash
sudo systemctl start translation-evaluator
```

### 停止服务

```bash
sudo systemctl stop translation-evaluator
```

### 重启服务

```bash
sudo systemctl restart translation-evaluator
```

### 查看状态

```bash
sudo systemctl status translation-evaluator
```

### 查看日志

```bash
# 实时日志
sudo journalctl -u translation-evaluator -f

# 最近50行
sudo journalctl -u translation-evaluator -n 50

# 从某个时间开始
sudo journalctl -u translation-evaluator --since "2026-02-09 09:00:00"
```

### 启用/禁用开机自启

```bash
# 启用开机自启
sudo systemctl enable translation-evaluator

# 禁用开机自启
sudo systemctl disable translation-evaluator
```

## 🐛 故障排查

### 问题1: 服务启动失败

```bash
# 查看详细错误
sudo journalctl -u translation-evaluator -n 100 --no-pager

# 检查服务文件
cat /etc/systemd/system/translation-evaluator.service

# 手动测试启动
cd /root/bianjb/translation_evaluator
export USE_REQUEST_QUEUE=true
export USE_BLEURT=true
# ... 其他环境变量
/root/miniconda3/envs/tranlator_eval/bin/gunicorn -w 1 -b 0.0.0.0:5001 eval_server:app
```

### 问题2: 端口被占用

```bash
# 检查端口占用
./check_port.sh

# 停止占用端口的进程
./quick_stop.sh
```

### 问题3: 服务不断重启

```bash
# 查看重启原因
sudo journalctl -u translation-evaluator --no-pager | grep -i "restart\|fail\|error"

# 检查服务文件中的Restart策略
cat /etc/systemd/system/translation-evaluator.service | grep Restart
```

## 📝 服务配置说明

服务文件位置: `/etc/systemd/system/translation-evaluator.service`

主要配置:
- **工作目录**: `/root/bianjb/translation_evaluator`
- **Python环境**: `/root/miniconda3/envs/tranlator_eval`
- **监听端口**: `5001`
- **Worker数量**: `1` (配合队列模式)
- **自动重启**: `Restart=always`
- **重启延迟**: `RestartSec=10`

## ✅ 启动成功标志

1. **服务状态**: `Active: active (running)`
2. **API响应**: `curl http://localhost:5001/health` 返回JSON
3. **日志正常**: 没有ERROR或FAILURE信息
4. **端口监听**: `ss -tlnp | grep 5001` 显示监听状态

## 🎯 完整启动流程

```bash
# 1. 停止所有现有进程
./quick_stop.sh

# 2. 配置systemd服务（如果还没配置）
sudo ./setup_systemd_service.sh

# 3. 启动服务
./start_systemd_service.sh

# 4. 验证服务
curl http://localhost:5001/health
```

## 📚 相关文档

- [后台运行指南.md](./后台运行指南.md)
- [systemd故障排查指南.md](./systemd故障排查指南.md)
- [请求队列使用指南.md](./请求队列使用指南.md)
