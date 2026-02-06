#!/bin/bash
# 启动评估API服务器（Linux/Mac）

echo "启动翻译评估API服务器..."
echo "================================"

# 检查conda环境
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "⚠️  未检测到conda环境，建议使用: conda activate translator_eval"
fi

# 启动服务器
python eval_server.py "$@"
