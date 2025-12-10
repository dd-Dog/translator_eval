"""
快速测试API服务器
"""

import time
import requests
from eval_client import EvaluationClient

def test_api():
    """测试API服务器"""
    print("=" * 80)
    print("测试翻译评估API")
    print("=" * 80)
    
    client = EvaluationClient()
    
    # 1. 健康检查
    print("\n1. 健康检查...")
    try:
        health = client.health_check()
        if health.get("status") == "healthy":
            print("   ✅ API服务器运行正常")
        else:
            print(f"   ⚠️  服务器状态: {health}")
    except Exception as e:
        print(f"   ❌ 无法连接到API服务器: {e}")
        print("   请先启动服务器: python eval_server.py")
        return False
    
    # 2. 单个样本评估
    print("\n2. 单个样本评估...")
    try:
        result = client.evaluate(
            translation="机器学习是人工智能的一个子集。",
            reference="机器学习是人工智能的一个子集。",
            source="Machine learning is a subset of artificial intelligence."
        )
        
        if result.get("success"):
            score = result.get("score", {})
            print("   ✅ 评估成功")
            print(f"      BLEU: {score.get('bleu', 0):.4f}")
            print(f"      COMET: {score.get('comet', 0):.4f}")
            print(f"      BERTScore: {score.get('bertscore_f1', 0):.4f}")
            print(f"      ChrF: {score.get('chrf', 0):.4f}")
            print(f"      综合评分: {score.get('final_score', 0):.4f}")
        else:
            print(f"   ❌ 评估失败: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ❌ 评估出错: {e}")
        return False
    
    # 3. 批量评估
    print("\n3. 批量评估...")
    try:
        batch_result = client.evaluate_batch(
            translations=[
                "机器学习是人工智能的一个子集。",
                "深度学习是机器学习的一个分支。"
            ],
            references=[
                "机器学习是人工智能的一个子集。",
                "深度学习是机器学习的一个分支。"
            ],
            sources=[
                "Machine learning is a subset of artificial intelligence.",
                "Deep learning is a branch of machine learning."
            ]
        )
        
        if batch_result.get("success"):
            print(f"   ✅ 批量评估成功，共 {batch_result.get('count', 0)} 个样本")
            for i, score in enumerate(batch_result.get("scores", []), 1):
                print(f"      样本 {i}: 综合评分 = {score.get('final_score', 0):.4f}")
        else:
            print(f"   ❌ 批量评估失败: {batch_result.get('error')}")
            return False
    except Exception as e:
        print(f"   ❌ 批量评估出错: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_api()
    exit(0 if success else 1)

