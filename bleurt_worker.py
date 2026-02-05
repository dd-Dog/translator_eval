#!/usr/bin/env python
"""
BLEURT评分工作进程
在独立的Python环境中运行，避免与COMET环境冲突
通过stdin接收JSON数据，通过stdout返回JSON结果
"""

import sys
import json
import os
import warnings
warnings.filterwarnings('ignore')

def load_bleurt_model(checkpoint_path):
    """加载BLEURT模型"""
    try:
        from bleurt import score as bleurt_score
        print(f"[BLEURT Worker] 正在加载模型: {checkpoint_path}", file=sys.stderr)
        scorer = bleurt_score.BleurtScorer(checkpoint_path)
        print(f"[BLEURT Worker] 模型加载成功", file=sys.stderr)
        return scorer
    except Exception as e:
        print(f"[BLEURT Worker] 模型加载失败: {e}", file=sys.stderr)
        return None

def score_texts(scorer, translations, references):
    """计算BLEURT分数"""
    try:
        scores = scorer.score(
            references=references,
            candidates=translations
        )
        return scores
    except Exception as e:
        print(f"[BLEURT Worker] 计算失败: {e}", file=sys.stderr)
        return None

def main():
    """主函数：从stdin读取JSON，计算结果，输出到stdout"""
    # 初始化模型（从环境变量或命令行参数获取checkpoint路径）
    checkpoint = os.environ.get("BLEURT_CHECKPOINT", "BLEURT-20")
    
    # 如果命令行提供了checkpoint路径，使用它
    if len(sys.argv) > 1:
        checkpoint = sys.argv[1]
    
    # 检查checkpoint路径是否存在
    if not os.path.exists(checkpoint):
        error_msg = f"BLEURT checkpoint not found: {checkpoint}"
        print(json.dumps({"error": error_msg}), file=sys.stderr)
        result = {"error": error_msg, "scores": []}
        print(json.dumps(result))
        sys.exit(1)
    
    # 加载模型
    scorer = load_bleurt_model(checkpoint)
    if scorer is None:
        error_msg = "Failed to load BLEURT model"
        result = {"error": error_msg, "scores": []}
        print(json.dumps(result))
        sys.exit(1)
    
    # 从stdin读取JSON数据
    try:
        input_data = json.loads(sys.stdin.read())
    except Exception as e:
        error_msg = f"Failed to parse input JSON: {e}"
        result = {"error": error_msg, "scores": []}
        print(json.dumps(result))
        sys.exit(1)
    
    translations = input_data.get("translations", [])
    references = input_data.get("references", [])
    
    if not translations or not references:
        error_msg = "translations and references are required"
        result = {"error": error_msg, "scores": []}
        print(json.dumps(result))
        sys.exit(1)
    
    if len(translations) != len(references):
        error_msg = f"translations and references length mismatch: {len(translations)} vs {len(references)}"
        result = {"error": error_msg, "scores": []}
        print(json.dumps(result))
        sys.exit(1)
    
    # 计算分数
    scores = score_texts(scorer, translations, references)
    
    if scores is None:
        error_msg = "Failed to calculate scores"
        result = {"error": error_msg, "scores": []}
    else:
        # 转换为列表（如果是tensor）
        if hasattr(scores, 'tolist'):
            scores = scores.tolist()
        elif not isinstance(scores, list):
            scores = list(scores)
        
        result = {
            "scores": scores,
            "mean_score": sum(scores) / len(scores) if scores else 0.0,
            "model": checkpoint
        }
    
    # 输出结果到stdout
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)

if __name__ == "__main__":
    main()
