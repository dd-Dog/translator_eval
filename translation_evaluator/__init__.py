"""
Translation Evaluator - 统一翻译质量评估库
支持BLEU, COMET, BLEURT, BERTScore, MQM, ChrF
"""

from .comet_scorer import COMETScorer, COMETKiwiScorer
from .bleurt_scorer import BLEURTScorer
from .bertscore_scorer import BERTScoreScorer
from .chrf_scorer import ChrFScorer, ChrF1Scorer, ChrF2Scorer, ChrF3Scorer
from .combined_scorer import CombinedQualityScorer, ComprehensiveScore
from .unified_evaluator import UnifiedEvaluator, PaperGradeScore

__version__ = "1.0.0"

__all__ = [
    "COMETScorer",
    "COMETKiwiScorer",
    "BLEURTScorer",
    "BERTScoreScorer",
    "ChrFScorer",
    "ChrF1Scorer",
    "ChrF2Scorer",
    "ChrF3Scorer",
    "CombinedQualityScorer",
    "ComprehensiveScore",
    "UnifiedEvaluator",
    "PaperGradeScore",
]
