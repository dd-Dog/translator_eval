"""
组合质量评估器
整合多种专业评估模型和自定义MQM评分
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ComprehensiveScore:
    """综合评分结果"""
    # 传统指标
    bleu: float = 0.0
    chrf: float = 0.0  # ChrF分数
    
    # 神经网络指标
    comet: float = 0.0
    bleurt: float = 0.0
    bertscore_f1: float = 0.0
    
    # 自定义MQM指标
    mqm_adequacy: float = 0.0
    mqm_fluency: float = 0.0
    mqm_terminology: float = 0.0
    mqm_overall: float = 0.0
    
    # 综合评分
    final_score: float = 0.0
    
    # 元数据
    model_info: Dict = None


class CombinedQualityScorer:
    """组合质量评估器"""
    
    def __init__(
        self,
        use_comet: bool = True,
        use_bleurt: bool = False,  # BLEURT较难安装，默认关闭
        use_bertscore: bool = True,
        use_chrf: bool = True,
        comet_model: str = "Unbabel/wmt22-comet-da"
    ):
        """
        初始化组合评估器
        
        Args:
            use_comet: 是否使用COMET
            use_bleurt: 是否使用BLEURT
            use_bertscore: 是否使用BERTScore
            use_chrf: 是否使用ChrF
            comet_model: COMET模型名称
        """
        self.use_comet = use_comet
        self.use_bleurt = use_bleurt
        self.use_bertscore = use_bertscore
        self.use_chrf = use_chrf
        
        # 延迟初始化模型
        self.comet_scorer = None
        self.bleurt_scorer = None
        self.bertscore_scorer = None
        self.chrf_scorer = None
        
        self.comet_model_name = comet_model
    
    def initialize(self):
        """初始化所有评估模型"""
        print("=" * 70)
        print("初始化专业评估模型...")
        print("=" * 70)
        
        success = True
        
        # 初始化COMET
        if self.use_comet:
            print(f"\n🔍 [DEBUG] 开始初始化COMET...")
            print(f"   use_comet配置: {self.use_comet}")
            print(f"   comet_model_name: {self.comet_model_name}")
            try:
                print(f"   [DEBUG] 导入COMETScorer...")
                from .comet_scorer import COMETScorer
                print(f"   [DEBUG] 创建COMETScorer实例...")
                self.comet_scorer = COMETScorer(self.comet_model_name)
                print(f"   [DEBUG] 调用initialize()...")
                init_result = self.comet_scorer.initialize()
                print(f"   [DEBUG] initialize()返回: {init_result}")
                if init_result:
                    print("✅ COMET模型已加载")
                else:
                    print("⚠️  COMET模型加载失败，将跳过")
                    print(f"   [DEBUG] 设置use_comet=False")
                    self.use_comet = False
                    success = False
            except ImportError as e:
                print(f"⚠️  COMET导入失败: {e}")
                import traceback
                traceback.print_exc()
                self.use_comet = False
                success = False
            except Exception as e:
                print(f"⚠️  COMET初始化异常: {e}")
                import traceback
                traceback.print_exc()
                self.use_comet = False
                success = False
        else:
            print(f"   [DEBUG] COMET未启用 (use_comet=False)，跳过初始化")
        
        # 初始化BLEURT
        if self.use_bleurt:
            print(f"\n🔍 [DEBUG] 开始初始化BLEURT...")
            print(f"   use_bleurt配置: {self.use_bleurt}")
            try:
                print(f"   [DEBUG] 导入BLEURTScorer...")
                from .bleurt_scorer import BLEURTScorer
                print(f"   [DEBUG] 创建BLEURTScorer实例...")
                self.bleurt_scorer = BLEURTScorer()
                print(f"   [DEBUG] 调用initialize()...")
                init_result = self.bleurt_scorer.initialize()
                print(f"   [DEBUG] initialize()返回: {init_result}")
                if init_result:
                    print("✅ BLEURT模型已加载")
                else:
                    print("⚠️  BLEURT模型加载失败，将跳过")
                    print(f"   [DEBUG] 设置use_bleurt=False")
                    self.use_bleurt = False
                    success = False
            except ImportError as e:
                print(f"⚠️  BLEURT导入失败: {e}")
                import traceback
                traceback.print_exc()
                self.use_bleurt = False
                success = False
            except Exception as e:
                print(f"⚠️  BLEURT初始化异常: {e}")
                import traceback
                traceback.print_exc()
                self.use_bleurt = False
                success = False
        else:
            print(f"   [DEBUG] BLEURT未启用 (use_bleurt=False)，跳过初始化")
        
        # 初始化BERTScore
        if self.use_bertscore:
            try:
                from .bertscore_scorer import BERTScoreScorer
                self.bertscore_scorer = BERTScoreScorer(lang="zh")
                if self.bertscore_scorer.initialize():
                    print("✅ BERTScore已就绪")
                else:
                    print("⚠️  BERTScore不可用，将跳过")
                    self.use_bertscore = False
                    success = False
            except Exception as e:
                print(f"⚠️  BERTScore不可用: {e}")
                self.use_bertscore = False
                success = False
        
        # 初始化ChrF
        if self.use_chrf:
            try:
                from .chrf_scorer import ChrF2Scorer
                self.chrf_scorer = ChrF2Scorer()
                if self.chrf_scorer.initialize():
                    print("✅ ChrF评估器已就绪")
                else:
                    print("⚠️  ChrF不可用，将跳过")
                    self.use_chrf = False
                    success = False
            except Exception as e:
                print(f"⚠️  ChrF不可用: {e}")
                self.use_chrf = False
                success = False
        
        if not any([self.use_comet, self.use_bleurt, self.use_bertscore, self.use_chrf]):
            print("⚠️  警告: 没有可用的评估模型")
        
        return success
    
    def score(
        self,
        source: str,
        translation: str,
        reference: Optional[str] = None,
        mqm_score: Optional[Dict] = None
    ) -> ComprehensiveScore:
        """
        综合评分
        
        Args:
            source: 源文本
            translation: 翻译文本
            reference: 参考翻译（可选）
            mqm_score: MQM评分（来自Checker）
            
        Returns:
            ComprehensiveScore: 综合评分
        """
        result = ComprehensiveScore()
        
        # 1. 传统指标：BLEU
        if reference:
            result.bleu = self._calculate_bleu(translation, reference)
        
        # 2. COMET评分
        print(f"\n🔍 [DEBUG] COMET计算检查:")
        print(f"   use_comet: {self.use_comet}")
        print(f"   comet_scorer存在: {self.comet_scorer is not None}")
        print(f"   source存在: {source is not None}")
        print(f"   source不为空: {source and source.strip() if source else False}")
        
        if self.use_comet and self.comet_scorer:
            if source and source.strip():  # COMET需要source
                try:
                    print(f"   ✅ 开始计算COMET分数...")
                    print(f"   source: {source[:50]}..." if len(source) > 50 else f"   source: {source}")
                    print(f"   translation: {translation[:50]}..." if len(translation) > 50 else f"   translation: {translation}")
                    comet_score = self.comet_scorer.score_single(source, translation, reference)
                    print(f"   ✅ COMET计算完成: {comet_score:.4f}")
                    result.comet = comet_score
                except Exception as e:
                    print(f"   ❌ COMET计算出错: {e}")
                    import traceback
                    traceback.print_exc()
                    result.comet = 0.0
            else:
                result.comet = 0.0
                print(f"   ⚠️  COMET需要source，但source为空，跳过COMET计算")
                print(f"   source值: {repr(source)}")
        else:
            result.comet = 0.0
            if not self.use_comet:
                print(f"   ⚠️  COMET未启用 (use_comet=False)")
            if not self.comet_scorer:
                print(f"   ⚠️  COMET评估器不存在 (comet_scorer=None)")
        
        # 3. BLEURT评分
        print(f"\n🔍 [DEBUG] BLEURT计算检查:")
        print(f"   use_bleurt: {self.use_bleurt}")
        print(f"   bleurt_scorer存在: {self.bleurt_scorer is not None}")
        print(f"   reference存在: {reference is not None}")
        print(f"   reference不为空: {reference and reference.strip() if reference else False}")
        
        if self.use_bleurt and self.bleurt_scorer:
            if reference and reference.strip():  # 确保reference不为空且不是空白字符串
                try:
                    print(f"   ✅ 开始计算BLEURT分数...")
                    print(f"   translation: {translation[:50]}..." if len(translation) > 50 else f"   translation: {translation}")
                    print(f"   reference: {reference[:50]}..." if len(reference) > 50 else f"   reference: {reference}")
                    bleurt_score = self.bleurt_scorer.score_single(translation, reference)
                    print(f"   ✅ BLEURT计算完成: {bleurt_score:.4f}")
                    result.bleurt = bleurt_score
                except Exception as e:
                    print(f"   ❌ BLEURT计算出错: {e}")
                    import traceback
                    traceback.print_exc()
                    result.bleurt = 0.0
            else:
                # reference为空，BLEURT需要reference，所以设为0
                result.bleurt = 0.0
                print(f"   ⚠️  BLEURT需要reference，但reference为空，跳过BLEURT计算")
                print(f"   reference值: {repr(reference)}")
        else:
            result.bleurt = 0.0
            if not self.use_bleurt:
                print(f"   ⚠️  BLEURT未启用 (use_bleurt=False)")
            if not self.bleurt_scorer:
                print(f"   ⚠️  BLEURT评估器不存在 (bleurt_scorer=None)")
        
        # 4. BERTScore评分
        if self.use_bertscore and self.bertscore_scorer and reference:
            result.bertscore_f1 = self.bertscore_scorer.score_single(translation, reference)
        
        # 5. ChrF评分
        if self.use_chrf and self.chrf_scorer and reference:
            result.chrf = self.chrf_scorer.score_single(translation, reference)
        
        # 6. MQM评分
        if mqm_score:
            result.mqm_adequacy = mqm_score.get('adequacy', 0.0)
            result.mqm_fluency = mqm_score.get('fluency', 0.0)
            result.mqm_terminology = mqm_score.get('terminology', 0.0)
            result.mqm_overall = mqm_score.get('overall', 0.0)
        
        # 7. 计算综合评分（加权平均）
        result.final_score = self._calculate_final_score(result)
        
        return result
    
    def _calculate_bleu(self, candidate: str, reference: str) -> float:
        """计算BLEU分数（字符级）"""
        try:
            from nltk.translate.bleu_score import sentence_bleu
            
            ref_tokens = list(reference)
            cand_tokens = list(candidate)
            
            return sentence_bleu([ref_tokens], cand_tokens)
        except:
            # 简化版：字符匹配率
            ref_chars = set(reference)
            cand_chars = set(candidate)
            if not cand_chars:
                return 0.0
            precision = len(ref_chars & cand_chars) / len(cand_chars)
            recall = len(ref_chars & cand_chars) / len(ref_chars) if ref_chars else 0.0
            if precision + recall == 0:
                return 0.0
            return 2 * (precision * recall) / (precision + recall)
    
    def _calculate_final_score(self, result: ComprehensiveScore) -> float:
        """
        计算最终综合评分（加权平均）
        
        权重分配（自动适应可用模型）：
        开发模式：
        - BERTScore: 50%
        - MQM: 30%
        - BLEU: 20%
        
        论文模式：
        - COMET: 35%
        - BERTScore: 25%
        - MQM: 25%
        - BLEU: 15%
        
        完整模式：
        - COMET: 30%
        - BERTScore: 20%
        - BLEURT: 15%
        - MQM: 25%
        - BLEU: 10%
        """
        scores = []
        weights = []
        
        # 根据可用模型动态分配权重
        if result.comet > 0:
            scores.append(result.comet)
            weights.append(0.35 if result.bleurt == 0 else 0.30)
        
        if result.bertscore_f1 > 0:
            scores.append(result.bertscore_f1)
            # 如果没有COMET，BERTScore权重提高
            if result.comet == 0:
                weights.append(0.50)
            else:
                weights.append(0.25 if result.bleurt == 0 else 0.20)
        
        if result.bleurt > 0:
            scores.append(result.bleurt)
            weights.append(0.15)
        
        if result.mqm_overall > 0:
            scores.append(result.mqm_overall)
            # 如果没有COMET，MQM权重提高
            if result.comet == 0:
                weights.append(0.30)
            else:
                weights.append(0.25)
        
        if result.bleu > 0:
            scores.append(result.bleu)
            # 如果没有COMET，BLEU权重提高
            if result.comet == 0:
                weights.append(0.20)
            else:
                weights.append(0.15 if result.bleurt == 0 else 0.10)
        
        if result.chrf > 0:
            scores.append(result.chrf)
            # ChrF权重（与BLEU类似）
            if result.comet == 0:
                weights.append(0.10)
            else:
                weights.append(0.08 if result.bleurt == 0 else 0.05)
        
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
    ) -> List[ComprehensiveScore]:
        """
        批量评分
        
        Returns:
            List[ComprehensiveScore]: 每个样本的综合评分
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

