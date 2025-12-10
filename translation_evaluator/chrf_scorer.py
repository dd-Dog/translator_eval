"""
ChrF (Character n-gram F-score)
基于字符n-gram的F分数评估
对形态变化丰富的语言（如中文）更友好
"""

from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class ChrFScorer:
    """ChrF质量评估模型"""
    
    def __init__(self, n: int = 2, beta: float = 2.0):
        """
        初始化ChrF评估器
        
        Args:
            n: n-gram的最大长度（默认2，即ChrF2）
            beta: F-score的beta参数（默认2.0，更重视精确率）
        """
        self.n = n
        self.beta = beta
        self._initialized = False
    
    def initialize(self):
        """检查依赖"""
        if self._initialized:
            return True
        
        try:
            import sacrebleu
            self._initialized = True
            print(f"✓ ChrF评估器已就绪 (ChrF{self.n})")
            return True
        except ImportError:
            print("❌ 请安装sacrebleu: pip install sacrebleu")
            return False
    
    def score(
        self,
        translations: List[str],
        references: List[str]
    ) -> Dict:
        """
        计算ChrF分数
        
        Args:
            translations: 翻译文本列表
            references: 参考翻译列表
            
        Returns:
            Dict: 包含scores和mean_score的字典
        """
        if not self._initialized:
            if not self.initialize():
                return {"scores": [], "mean_score": 0.0, "error": "Not initialized"}
        
        try:
            from sacrebleu.metrics import CHRF
            
            chrf = CHRF(word_order=self.n, beta=self.beta)
            
            # sacrebleu需要列表的列表（支持多个参考翻译）
            refs = [[ref] for ref in references]
            
            # 计算分数
            result = chrf.corpus_score(translations, refs)
            
            # 转换为0-1范围（sacrebleu返回0-100）
            scores = [result.score / 100.0] * len(translations)  # 简化：所有样本使用相同分数
            
            # 如果需要每个样本的分数，需要逐个计算
            individual_scores = []
            for trans, ref in zip(translations, references):
                individual_result = chrf.sentence_score(trans, [ref])
                individual_scores.append(individual_result.score / 100.0)
            
            return {
                "scores": individual_scores,
                "mean_score": sum(individual_scores) / len(individual_scores) if individual_scores else 0.0,
                "corpus_score": result.score / 100.0,
                "n": self.n,
                "beta": self.beta
            }
            
        except Exception as e:
            return {"scores": [], "mean_score": 0.0, "error": str(e)}
    
    def score_single(self, translation: str, reference: str) -> float:
        """
        计算单个样本的ChrF分数
        
        Returns:
            float: ChrF分数 (0-1)
        """
        result = self.score([translation], [reference])
        
        if result.get("error"):
            return 0.0
        
        scores = result.get("scores", [])
        return scores[0] if scores else 0.0


class ChrF1Scorer(ChrFScorer):
    """ChrF1评估器（1-gram）"""
    def __init__(self):
        super().__init__(n=1, beta=2.0)


class ChrF2Scorer(ChrFScorer):
    """ChrF2评估器（2-gram，论文常用）"""
    def __init__(self):
        super().__init__(n=2, beta=2.0)


class ChrF3Scorer(ChrFScorer):
    """ChrF3评估器（3-gram）"""
    def __init__(self):
        super().__init__(n=3, beta=2.0)

