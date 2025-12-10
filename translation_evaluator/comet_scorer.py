"""
COMET (Crosslingual Optimized Metric for Evaluation of Translation)
基于神经网络的翻译质量评估模型
"""

from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class COMETScorer:
    """COMET质量评估模型"""
    
    def __init__(self, model_name: str = "Unbabel/wmt22-comet-da"):
        """
        初始化COMET模型
        
        Args:
            model_name: COMET模型名称
                - "Unbabel/wmt22-comet-da" (推荐，有参考翻译)
                - "Unbabel/wmt22-cometkiwi-da" (无参考翻译)
                - "Unbabel/XCOMET-XL" (最新，最强)
        """
        self.model_name = model_name
        self.model = None
        self._initialized = False
    
    def initialize(self):
        """延迟初始化模型（避免启动时加载）"""
        if self._initialized:
            return True
        
        try:
            from comet import download_model, load_from_checkpoint
            
            print(f"正在下载COMET模型: {self.model_name}...")
            model_path = download_model(self.model_name)
            
            print(f"正在加载模型...")
            self.model = load_from_checkpoint(model_path)
            
            self._initialized = True
            print(f"✓ COMET模型加载成功")
            return True
            
        except ImportError:
            print("❌ 请安装COMET: pip install unbabel-comet")
            return False
        except Exception as e:
            print(f"❌ COMET模型加载失败: {e}")
            return False
    
    def score(
        self,
        sources: List[str],
        translations: List[str],
        references: Optional[List[str]] = None
    ) -> Dict:
        """
        计算COMET分数
        
        Args:
            sources: 源文本列表
            translations: 翻译文本列表
            references: 参考翻译列表（可选，但推荐提供）
            
        Returns:
            Dict: 包含scores和system_score的字典
        """
        if not self._initialized:
            if not self.initialize():
                return {"scores": [], "system_score": 0.0, "error": "Model not initialized"}
        
        try:
            # 构建数据
            data = []
            for i in range(len(sources)):
                item = {
                    "src": sources[i],
                    "mt": translations[i]
                }
                if references and i < len(references):
                    item["ref"] = references[i]
                data.append(item)
            
            # 预测
            output = self.model.predict(data, batch_size=8, gpus=0)
            
            return {
                "scores": output.scores,  # 每个样本的分数
                "system_score": output.system_score,  # 整体分数
                "model": self.model_name
            }
            
        except Exception as e:
            return {"scores": [], "system_score": 0.0, "error": str(e)}
    
    def score_single(
        self,
        source: str,
        translation: str,
        reference: Optional[str] = None
    ) -> float:
        """
        计算单个样本的COMET分数
        
        Returns:
            float: COMET分数 (0-1)
        """
        result = self.score([source], [translation], [reference] if reference else None)
        
        if result.get("error"):
            return 0.0
        
        scores = result.get("scores", [])
        return scores[0] if scores else 0.0


class COMETKiwiScorer(COMETScorer):
    """COMET-Kiwi: 无参考翻译的QE模型"""
    
    def __init__(self):
        super().__init__(model_name="Unbabel/wmt22-cometkiwi-da")
    
    def score(self, sources: List[str], translations: List[str], references: Optional[List[str]] = None):
        """无参考翻译评估"""
        # COMET-Kiwi不需要参考翻译
        return super().score(sources, translations, references=None)

