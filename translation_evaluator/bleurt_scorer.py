"""
BLEURT (Bilingual Evaluation Understudy with Representations from Transformers)
基于BERT的翻译质量评估模型
"""

from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class BLEURTScorer:
    """BLEURT质量评估模型"""
    
    def __init__(self, checkpoint: str = "BLEURT-20"):
        """
        初始化BLEURT模型
        
        Args:
            checkpoint: BLEURT检查点
                - "BLEURT-20" (推荐)
                - "BLEURT-20-D12"
        """
        self.checkpoint = checkpoint
        self.scorer = None
        self._initialized = False
    
    def initialize(self):
        """延迟初始化模型"""
        if self._initialized:
            return True
        
        try:
            from bleurt import score as bleurt_score
            
            print(f"正在加载BLEURT模型: {self.checkpoint}...")
            self.scorer = bleurt_score.BleurtScorer(self.checkpoint)
            
            self._initialized = True
            print(f"✓ BLEURT模型加载成功")
            return True
            
        except ImportError:
            print("❌ 请安装BLEURT: pip install bleurt")
            print("   或参考: https://github.com/google-research/bleurt")
            return False
        except Exception as e:
            print(f"❌ BLEURT模型加载失败: {e}")
            return False
    
    def score(
        self,
        translations: List[str],
        references: List[str]
    ) -> Dict:
        """
        计算BLEURT分数
        
        Args:
            translations: 翻译文本列表
            references: 参考翻译列表
            
        Returns:
            Dict: 包含scores的字典
        """
        if not self._initialized:
            if not self.initialize():
                return {"scores": [], "error": "Model not initialized"}
        
        try:
            scores = self.scorer.score(
                references=references,
                candidates=translations
            )
            
            return {
                "scores": scores,
                "mean_score": sum(scores) / len(scores) if scores else 0.0,
                "model": self.checkpoint
            }
            
        except Exception as e:
            return {"scores": [], "error": str(e)}
    
    def score_single(self, translation: str, reference: str) -> float:
        """
        计算单个样本的BLEURT分数
        
        Returns:
            float: BLEURT分数
        """
        result = self.score([translation], [reference])
        
        if result.get("error"):
            return 0.0
        
        scores = result.get("scores", [])
        return scores[0] if scores else 0.0

