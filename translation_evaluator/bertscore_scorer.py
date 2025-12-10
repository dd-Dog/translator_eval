"""
BERTScore
基于BERT embedding的语义相似度评估
"""

from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')


class BERTScoreScorer:
    """BERTScore评估模型"""
    
    def __init__(self, lang: str = "zh", model_type: str = None):
        """
        初始化BERTScore
        
        Args:
            lang: 语言代码 (zh, en, etc.)
            model_type: BERT模型类型（可选）
                - 中文: "bert-base-chinese"
                - 多语言: "bert-base-multilingual-cased"
        """
        self.lang = lang
        self.model_type = model_type
        self._initialized = False
    
    def initialize(self):
        """检查依赖"""
        if self._initialized:
            return True
        
        try:
            import bert_score
            self._initialized = True
            print(f"✓ BERTScore已就绪")
            return True
        except ImportError:
            print("❌ 请安装BERTScore: pip install bert-score")
            return False
    
    def score(
        self,
        translations: List[str],
        references: List[str]
    ) -> Dict:
        """
        计算BERTScore
        
        Args:
            translations: 翻译文本列表
            references: 参考翻译列表
            
        Returns:
            Dict: 包含P, R, F1的字典
        """
        if not self._initialized:
            if not self.initialize():
                return {"P": [], "R": [], "F1": [], "error": "Not initialized"}
        
        try:
            from bert_score import score
            
            P, R, F1 = score(
                translations,
                references,
                lang=self.lang,
                model_type=self.model_type,
                verbose=False
            )
            
            return {
                "P": P.tolist(),  # Precision
                "R": R.tolist(),  # Recall
                "F1": F1.tolist(),  # F1 score
                "mean_F1": F1.mean().item(),
                "lang": self.lang
            }
            
        except Exception as e:
            return {"P": [], "R": [], "F1": [], "error": str(e)}
    
    def score_single(self, translation: str, reference: str) -> float:
        """
        计算单个样本的BERTScore F1
        
        Returns:
            float: F1分数
        """
        result = self.score([translation], [reference])
        
        if result.get("error"):
            return 0.0
        
        f1_scores = result.get("F1", [])
        return f1_scores[0] if f1_scores else 0.0

