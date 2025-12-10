"""
翻译评估API客户端
用于调用评估API服务的示例代码
"""

import requests
from typing import Dict, List, Optional, Union


class EvaluationClient:
    """评估API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        """
        初始化客户端
        
        Args:
            base_url: API服务器地址
        """
        self.base_url = base_url.rstrip('/')
        self.eval_url = f"{self.base_url}/eval"
        self.batch_url = f"{self.base_url}/eval/batch"
    
    def health_check(self) -> Dict:
        """健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def evaluate(
        self,
        translation: str,
        reference: str,
        source: Optional[str] = None,
        mqm_score: Optional[Dict] = None
    ) -> Dict:
        """
        评估单个翻译样本
        
        Args:
            translation: 翻译文本
            reference: 参考翻译
            source: 源文本（可选）
            mqm_score: MQM评分（可选）
            
        Returns:
            评估结果字典
        """
        data = {
            "translation": translation,
            "reference": reference
        }
        
        if source:
            data["source"] = source
        
        if mqm_score:
            data["mqm_score"] = mqm_score
        
        try:
            response = requests.post(self.eval_url, json=data, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"请求失败: {str(e)}"
            }
    
    def evaluate_batch(
        self,
        translations: List[str],
        references: List[str],
        sources: Optional[List[str]] = None,
        mqm_scores: Optional[List[Dict]] = None
    ) -> Dict:
        """
        批量评估
        
        Args:
            translations: 翻译文本列表
            references: 参考翻译列表
            sources: 源文本列表（可选）
            mqm_scores: MQM评分列表（可选）
            
        Returns:
            批量评估结果字典
        """
        data = {
            "translations": translations,
            "references": references
        }
        
        if sources:
            data["sources"] = sources
        
        if mqm_scores:
            data["mqm_scores"] = mqm_scores
        
        try:
            response = requests.post(self.batch_url, json=data, timeout=300)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"请求失败: {str(e)}"
            }


def evaluate_translation(
    translation: str,
    reference: str,
    source: str = "",
    api_url: str = "http://localhost:5001"
) -> Dict:
    """
    简单的评估函数（向后兼容）
    
    Args:
        translation: 翻译文本
        reference: 参考翻译
        source: 源文本（可选）
        api_url: API服务器地址
        
    Returns:
        评估结果
    """
    client = EvaluationClient(base_url=api_url)
    return client.evaluate(translation, reference, source)


if __name__ == "__main__":
    # 示例使用
    print("=" * 80)
    print("翻译评估API客户端示例")
    print("=" * 80)
    
    # 创建客户端
    client = EvaluationClient()
    
    # 健康检查
    print("\n1. 健康检查...")
    health = client.health_check()
    print(f"   状态: {health}")
    
    if health.get("status") != "healthy":
        print("\n❌ API服务器未运行或不可访问")
        print("   请先启动服务器: python eval_server.py")
        exit(1)
    
    # 单个样本评估
    print("\n2. 单个样本评估...")
    result = client.evaluate(
        translation="机器学习是人工智能的一个子集。",
        reference="机器学习是人工智能的一个子集。",
        source="Machine learning is a subset of artificial intelligence."
    )
    
    if result.get("success"):
        score = result.get("score", {})
        print(f"   ✅ 评估成功")
        print(f"   BLEU: {score.get('bleu', 0):.4f}")
        print(f"   COMET: {score.get('comet', 0):.4f}")
        bleurt_score = score.get('bleurt', 0)
        if bleurt_score > 0:
            print(f"   BLEURT: {bleurt_score:.4f}")
        else:
            print(f"   BLEURT: {bleurt_score:.4f} (未计算或为0)")
        print(f"   BERTScore: {score.get('bertscore_f1', 0):.4f}")
        print(f"   ChrF: {score.get('chrf', 0):.4f}")
        print(f"   综合评分: {score.get('final_score', 0):.4f}")
    else:
        print(f"   ❌ 评估失败: {result.get('error')}")
    
    # 批量评估
    print("\n3. 批量评估...")
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
            print(f"   样本 {i}: 综合评分 = {score.get('final_score', 0):.4f}")
    else:
        print(f"   ❌ 批量评估失败: {batch_result.get('error')}")
    
    print("\n" + "=" * 80)
    print("示例完成")
    print("=" * 80)

