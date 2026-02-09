#!/bin/bash

# ============================================
# Debug Systemd Service Script
# ============================================

echo "=========================================="
echo "检查服务状态"
echo "=========================================="
sudo systemctl status translation-evaluator --no-pager -l

echo ""
echo "=========================================="
echo "查看最近50行日志"
echo "=========================================="
sudo journalctl -u translation-evaluator -n 50 --no-pager

echo ""
echo "=========================================="
echo "查看完整错误日志"
echo "=========================================="
sudo journalctl -u translation-evaluator --no-pager | tail -100

echo ""
echo "=========================================="
echo "手动测试gunicorn启动"
echo "=========================================="
echo "请手动运行以下命令测试："
echo ""
echo "cd /root/bianjb/translation_evaluator"
echo "export USE_REQUEST_QUEUE=true"
echo "export USE_BLEURT=true"
echo "export BLEURT_USE_SUBPROCESS=true"
echo "export BLEURT_PYTHON_ENV=/root/miniconda3/envs/translator_eval_bleurt/bin/python"
echo "export BLEURT_WORKER_SCRIPT=/root/bianjb/translation_evaluator/bleurt_worker.py"
echo "export BLEURT_CHECKPOINT=/root/bianjb/translation_evaluator/BLEURT-20"
echo "export COMET_MODEL_PATH=/root/bianjb/wmt22-comet-da"
echo "export HF_HOME=/root/bianjb/huggingface"
echo "/root/miniconda3/envs/tranlator_eval/bin/gunicorn -w 1 --preload -b 0.0.0.0:5001 --timeout 600 eval_server:app"
echo ""
