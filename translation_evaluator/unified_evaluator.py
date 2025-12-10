"""
统一评估器 - 集成所有6个评估指标
BLEU, COMET, BLEURT, BERTScore, MQM, ChrF
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from .combined_scorer import ComprehensiveScore, CombinedQualityScorer
from .chrf_scorer import ChrF2Scorer


@dataclass
class PaperGradeScore(ComprehensiveScore):
    """论文级评估分数（包含ChrF）"""
    chrf: float = 0.0  # ChrF分数


class UnifiedEvaluator(CombinedQualityScorer):
    """
    统一评估器
    支持所有6个评估指标：BLEU, COMET, BLEURT, BERTScore, MQM, ChrF
    """
    
    def __init__(
        self,
        use_bleu: bool = True,
        use_comet: bool = True,
        use_bleurt: bool = False,
        use_bertscore: bool = True,
        use_mqm: bool = True,
        use_chrf: bool = True,
        comet_model: str = "Unbabel/wmt22-comet-da"
    ):
        """
        初始化统一评估器
        
        Args:
            use_bleu: 是否使用BLEU
            use_comet: 是否使用COMET
            use_bleurt: 是否使用BLEURT
            use_bertscore: 是否使用BERTScore
            use_mqm: 是否使用MQM（单模型系统通常为False）
            use_chrf: 是否使用ChrF
            comet_model: COMET模型名称
        """
        super().__init__(
            use_comet=use_comet,
            use_bleurt=use_bleurt,
            use_bertscore=use_bertscore,
            comet_model=comet_model
        )
        
        self.use_bleu = use_bleu
        self.use_mqm = use_mqm
        self.use_chrf = use_chrf
        
        # ChrF评估器
        self.chrf_scorer = None
        if self.use_chrf:
            self.chrf_scorer = ChrF2Scorer()
    
    def initialize(self):
        """初始化所有评估模型"""
        success = super().initialize()
        
        # 初始化ChrF
        if self.use_chrf and self.chrf_scorer:
            if self.chrf_scorer.initialize():
                print("✅ ChrF评估器已就绪")
            else:
                print("⚠️  ChrF不可用，将跳过")
                self.use_chrf = False
                success = False
        
        return success
    
    def score(
        self,
        source: str,
        translation: str,
        reference: Optional[str] = None,
        mqm_score: Optional[Dict] = None
    ) -> PaperGradeScore:
        """
        综合评分（包含所有6个指标）
        
        Args:
            source: 源文本
            translation: 翻译文本
            reference: 参考翻译（可选）
            mqm_score: MQM评分（可选，单模型系统通常为None）
            
        Returns:
            PaperGradeScore: 包含所有6个指标的评分
        """
        # 使用父类方法计算基础指标
        base_score = super().score(source, translation, reference, mqm_score)
        
        # 创建论文级评分对象
        result = PaperGradeScore(
            bleu=base_score.bleu if self.use_bleu else 0.0,
            comet=base_score.comet,
            bleurt=base_score.bleurt,
            bertscore_f1=base_score.bertscore_f1,
            mqm_adequacy=base_score.mqm_adequacy if self.use_mqm and mqm_score else 0.0,
            mqm_fluency=base_score.mqm_fluency if self.use_mqm and mqm_score else 0.0,
            mqm_terminology=base_score.mqm_terminology if self.use_mqm and mqm_score else 0.0,
            mqm_overall=base_score.mqm_overall if self.use_mqm and mqm_score else 0.0,
            final_score=0.0,  # 重新计算
            model_info=base_score.model_info
        )
        
        # 计算ChrF
        if self.use_chrf and self.chrf_scorer and reference:
            result.chrf = self.chrf_scorer.score_single(translation, reference)
        
        # 重新计算综合评分（包含ChrF）
        result.final_score = self._calculate_paper_grade_score(result)
        
        return result
    
    def _calculate_paper_grade_score(self, result: PaperGradeScore) -> float:
        """
        计算论文级综合评分（包含ChrF）
        
        权重分配（6个指标）：
        - COMET: 25%
        - BERTScore: 20%
        - BLEURT: 15%
        - MQM: 20%（如果可用）
        - BLEU: 10%
        - ChrF: 10%
        
        如果某些指标不可用，权重自动调整
        """
        scores = []
        weights = []
        
        # COMET
        if result.comet > 0:
            scores.append(result.comet)
            weights.append(0.25)
        
        # BERTScore
        if result.bertscore_f1 > 0:
            scores.append(result.bertscore_f1)
            weights.append(0.20)
        
        # BLEURT
        if result.bleurt > 0:
            scores.append(result.bleurt)
            weights.append(0.15)
        
        # MQM
        if result.mqm_overall > 0:
            scores.append(result.mqm_overall)
            weights.append(0.20)
        
        # BLEU
        if result.bleu > 0:
            scores.append(result.bleu)
            weights.append(0.10)
        
        # ChrF
        if result.chrf > 0:
            scores.append(result.chrf)
            weights.append(0.10)
        
        if not scores:
            return 0.0
        
        # 归一化权重
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # 加权平均
        final = sum(s * w for s, w in zip(scores, normalized_weights))
        
        return final
    
    def batch_score(
        self,
        sources: List[str],
        translations: List[str],
        references: Optional[List[str]] = None,
        mqm_scores: Optional[List[Dict]] = None
    ) -> List[PaperGradeScore]:
        """
        批量评分
        
        Returns:
            List[PaperGradeScore]: 每个样本的综合评分
        """
        results = []
        
        for i in range(len(translations)):
            source = sources[i]
            translation = translations[i]
            reference = references[i] if references and i < len(references) else None
            mqm = mqm_scores[i] if mqm_scores and i < len(mqm_scores) else None
            
            score = self.score(source, translation, reference, mqm)
            results.append(score)
        
        return results

