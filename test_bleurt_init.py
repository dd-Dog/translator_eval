#!/usr/bin/env python
"""
在主环境中测试BLEURT初始化
模拟eval_server的初始化过程
"""

import os
import sys

# 设置环境变量（如果还没设置）
os.environ.setdefault("USE_BLEURT", "true")
os.environ.setdefault("BLEURT_USE_SUBPROCESS", "true")
os.environ.setdefault("BLEURT_PYTHON_ENV", "/root/miniconda3/envs/translator_eval_bleurt/bin/python")
os.environ.setdefault("BLEURT_WORKER_SCRIPT", "/root/bianjb/translation_evaluator/bleurt_worker.py")
os.environ.setdefault("BLEURT_CHECKPOINT", "/root/bianjb/translation_evaluator/BLEURT-20")

print("=" * 60)
print("在主环境中测试BLEURT初始化")
print("=" * 60)
print()

print("环境变量:")
print(f"  USE_BLEURT: {os.environ.get('USE_BLEURT')}")
print(f"  BLEURT_USE_SUBPROCESS: {os.environ.get('BLEURT_USE_SUBPROCESS')}")
print(f"  BLEURT_PYTHON_ENV: {os.environ.get('BLEURT_PYTHON_ENV')}")
print(f"  BLEURT_WORKER_SCRIPT: {os.environ.get('BLEURT_WORKER_SCRIPT')}")
print(f"  BLEURT_CHECKPOINT: {os.environ.get('BLEURT_CHECKPOINT')}")
print()

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("开始初始化BLEURT...")
print()

try:
    from translation_evaluator.bleurt_scorer import BLEURTScorer
    
    use_subprocess = os.environ.get("BLEURT_USE_SUBPROCESS", "false").lower() == "true"
    python_env = os.environ.get("BLEURT_PYTHON_ENV")
    worker_script = os.environ.get("BLEURT_WORKER_SCRIPT", "bleurt_worker.py")
    checkpoint = os.environ.get("BLEURT_CHECKPOINT", "BLEURT-20")
    
    print(f"使用子进程模式: {use_subprocess}")
    print(f"Python环境: {python_env}")
    print(f"Worker脚本: {worker_script}")
    print(f"Checkpoint: {checkpoint}")
    print()
    
    if use_subprocess:
        scorer = BLEURTScorer(
            checkpoint=checkpoint,
            use_subprocess=True,
            python_env=python_env,
            worker_script=worker_script
        )
    else:
        scorer = BLEURTScorer(checkpoint=checkpoint)
    
    print("调用initialize()...")
    result = scorer.initialize()
    print(f"initialize()返回: {result}")
    
    if result:
        print("✅ BLEURT初始化成功！")
        
        # 测试评分
        print("\n测试评分...")
        test_result = scorer.score(["Hello world"], ["Hello world"])
        if test_result.get("error"):
            print(f"❌ 评分失败: {test_result.get('error')}")
        else:
            scores = test_result.get("scores", [])
            if scores:
                print(f"✅ 评分成功，分数: {scores[0]:.4f}")
            else:
                print("⚠️  评分返回空结果")
    else:
        print("❌ BLEURT初始化失败")
        
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ 异常: {e}")
    import traceback
    traceback.print_exc()

print()
