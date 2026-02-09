#!/bin/bash

# ============================================
# Test Gunicorn Start Script
# ============================================

PROJECT_DIR="/root/bianjb/translation_evaluator"
CONDA_ENV="/root/miniconda3/envs/tranlator_eval"

cd "$PROJECT_DIR" || exit 1

echo "=========================================="
echo "测试gunicorn启动"
echo "=========================================="

# 设置环境变量
export USE_REQUEST_QUEUE=true
export MAX_QUEUE_SIZE=50
export REQUEST_TIMEOUT=600
export USE_BLEURT=true
export BLEURT_USE_SUBPROCESS=true
export BLEURT_PYTHON_ENV=/root/miniconda3/envs/translator_eval_bleurt/bin/python
export BLEURT_WORKER_SCRIPT="$PROJECT_DIR/bleurt_worker.py"
export BLEURT_CHECKPOINT="$PROJECT_DIR/BLEURT-20"
export COMET_MODEL_PATH=/root/bianjb/wmt22-comet-da
export HF_HOME=/root/.cache/huggingface

echo "环境变量:"
echo "  USE_REQUEST_QUEUE=$USE_REQUEST_QUEUE"
echo "  USE_BLEURT=$USE_BLEURT"
echo "  COMET_MODEL_PATH=$COMET_MODEL_PATH"
echo ""

echo "测试Python导入..."
"$CONDA_ENV/bin/python" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from translation_evaluator import UnifiedEvaluator
    print('✅ UnifiedEvaluator导入成功')
except Exception as e:
    print(f'❌ UnifiedEvaluator导入失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from translation_evaluator.request_queue import RequestQueue
    print('✅ RequestQueue导入成功')
except Exception as e:
    print(f'❌ RequestQueue导入失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    import eval_server
    print('✅ eval_server模块导入成功')
except Exception as e:
    print(f'❌ eval_server模块导入失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 模块导入测试失败，请检查错误信息"
    exit 1
fi

echo ""
echo "=========================================="
echo "检查端口5001占用"
echo "=========================================="

# 检查端口占用
if command -v ss > /dev/null; then
    PORT_USAGE=$(ss -tlnp | grep ":5001 ")
    if [ -n "$PORT_USAGE" ]; then
        echo "⚠️  端口5001已被占用:"
        echo "$PORT_USAGE"
        echo ""
        echo "请先停止占用端口的服务:"
        echo "  sudo systemctl stop translation-evaluator"
        echo "  或"
        echo "  ./stop_all_services.sh"
        exit 1
    else
        echo "✅ 端口5001可用"
    fi
else
    echo "⚠️  无法检查端口（ss未安装），继续测试..."
fi

echo ""
echo "=========================================="
echo "测试gunicorn启动（5秒后自动停止）"
echo "=========================================="

# 启动gunicorn，5秒后自动停止
timeout 5 "$CONDA_ENV/bin/gunicorn" \
    -w 1 \
    -b 0.0.0.0:5001 \
    --timeout 600 \
    eval_server:app 2>&1 || {
    EXIT_CODE=$?
    echo ""
    echo "=========================================="
    echo "gunicorn启动测试完成"
    echo "=========================================="
    if [ $EXIT_CODE -eq 124 ]; then
        echo "✅ 启动成功（5秒后自动停止）"
    elif [ $EXIT_CODE -eq 98 ] || echo "$?" | grep -q "Address already in use"; then
        echo "❌ 端口被占用，请先停止其他服务"
        echo "   运行: ./stop_all_services.sh"
    else
        echo "⚠️  启动失败，请检查上面的错误信息"
    fi
}
