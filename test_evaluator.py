"""
测试共享评估库
验证所有评估器是否能正确调用
"""

import sys
from pathlib import Path

def test_imports():
    """测试导入"""
    print("=" * 80)
    print("测试1: 导入评估库")
    print("=" * 80)
    
    try:
        from translation_evaluator import (
            UnifiedEvaluator,
            COMETScorer,
            BERTScoreScorer,
            ChrF2Scorer,
            ComprehensiveScore,
            PaperGradeScore
        )
        print("✅ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bertscore():
    """测试BERTScore"""
    print("\n" + "=" * 80)
    print("测试2: BERTScore评估器")
    print("=" * 80)
    
    try:
        from translation_evaluator import BERTScoreScorer
        
        scorer = BERTScoreScorer(lang="zh")
        if not scorer.initialize():
            print("⚠️  BERTScore未安装，跳过测试")
            return False
        
        result = scorer.score_single(
            translation="机器学习是人工智能的一个子集。",
            reference="机器学习是人工智能的一个子集。"
        )
        
        print(f"✅ BERTScore测试成功")
        print(f"   翻译: 机器学习是人工智能的一个子集。")
        print(f"   参考: 机器学习是人工智能的一个子集。")
        print(f"   分数: {result:.4f}")
        
        return True
    except Exception as e:
        print(f"❌ BERTScore测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chrf():
    """测试ChrF"""
    print("\n" + "=" * 80)
    print("测试3: ChrF评估器")
    print("=" * 80)
    
    try:
        from translation_evaluator import ChrF2Scorer
        
        scorer = ChrF2Scorer()
        if not scorer.initialize():
            print("⚠️  ChrF未安装，跳过测试")
            return False
        
        result = scorer.score_single(
            translation="机器学习是人工智能的一个子集。",
            reference="机器学习是人工智能的一个子集。"
        )
        
        print(f"✅ ChrF测试成功")
        print(f"   翻译: 机器学习是人工智能的一个子集。")
        print(f"   参考: 机器学习是人工智能的一个子集。")
        print(f"   分数: {result:.4f}")
        
        return True
    except Exception as e:
        print(f"❌ ChrF测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_evaluator():
    """测试统一评估器"""
    print("\n" + "=" * 80)
    print("测试4: UnifiedEvaluator（统一评估器）")
    print("=" * 80)
    
    try:
        from translation_evaluator import UnifiedEvaluator
        
        # 初始化评估器（开发模式：只用BERTScore和ChrF）
        evaluator = UnifiedEvaluator(
            use_bleu=True,
            use_comet=False,      # 开发模式：不使用COMET
            use_bleurt=False,     # 开发模式：不使用BLEURT
            use_bertscore=True,
            use_mqm=False,        # 单模型系统没有MQM
            use_chrf=True
        )
        
        print("正在初始化评估器...")
        evaluator.initialize()
        
        # 测试评估
        print("\n测试评估...")
        score = evaluator.score(
            source="Machine learning is a subset of artificial intelligence.",
            translation="机器学习是人工智能的一个子集。",
            reference="机器学习是人工智能的一个子集。",
            mqm_score=None  # 单模型系统没有MQM
        )
        
        print(f"✅ UnifiedEvaluator测试成功")
        print(f"\n评估结果:")
        print(f"  BLEU: {score.bleu:.4f}")
        print(f"  COMET: {score.comet:.4f} (未启用)")
        print(f"  BLEURT: {score.bleurt:.4f} (未启用)")
        print(f"  BERTScore: {score.bertscore_f1:.4f}")
        print(f"  MQM: {score.mqm_overall:.4f} (未启用)")
        print(f"  ChrF: {score.chrf:.4f}")
        print(f"  综合评分: {score.final_score:.4f}")
        
        # 验证ChrF字段
        if hasattr(score, 'chrf'):
            print(f"  ✅ ChrF字段存在: {score.chrf:.4f}")
        else:
            print(f"  ❌ ChrF字段不存在")
            return False
        
        return True
    except Exception as e:
        print(f"❌ UnifiedEvaluator测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_combined_scorer():
    """测试CombinedQualityScorer（基础评估器）"""
    print("\n" + "=" * 80)
    print("测试5: CombinedQualityScorer（基础评估器）")
    print("=" * 80)
    
    try:
        from translation_evaluator import CombinedQualityScorer
        
        scorer = CombinedQualityScorer(
            use_comet=False,
            use_bleurt=False,
            use_bertscore=True,
            use_chrf=True
        )
        
        print("正在初始化评估器...")
        scorer.initialize()
        
        # 测试评估
        result = scorer.score(
            source="Hello, world!",
            translation="你好，世界！",
            reference="你好，世界！",
            mqm_score=None
        )
        
        print(f"✅ CombinedQualityScorer测试成功")
        print(f"\n评估结果:")
        print(f"  BLEU: {result.bleu:.4f}")
        print(f"  BERTScore: {result.bertscore_f1:.4f}")
        print(f"  ChrF: {result.chrf:.4f}")
        print(f"  综合评分: {result.final_score:.4f}")
        
        # 验证ChrF字段
        if hasattr(result, 'chrf'):
            print(f"  ✅ ChrF字段存在: {result.chrf:.4f}")
        else:
            print(f"  ❌ ChrF字段不存在")
            return False
        
        return True
    except Exception as e:
        print(f"❌ CombinedQualityScorer测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("共享评估库测试")
    print("=" * 80)
    
    results = []
    
    # 测试1: 导入
    results.append(("导入测试", test_imports()))
    
    # 测试2: BERTScore
    results.append(("BERTScore", test_bertscore()))
    
    # 测试3: ChrF
    results.append(("ChrF", test_chrf()))
    
    # 测试4: UnifiedEvaluator
    results.append(("UnifiedEvaluator", test_unified_evaluator()))
    
    # 测试5: CombinedQualityScorer
    results.append(("CombinedQualityScorer", test_combined_scorer()))
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！共享评估库可以正常使用。")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

