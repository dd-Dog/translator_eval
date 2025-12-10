"""
调试ChrF分数为0的问题
"""

from translation_evaluator import ChrF2Scorer

scorer = ChrF2Scorer()
scorer.initialize()

# 测试1: 完全相同的文本
translation = "机器学习是人工智能的一个子集。"
reference = "机器学习是人工智能的一个子集。"

result = scorer.score([translation], [reference])
print("测试1: 完全相同的文本")
print(f"结果: {result}")
print(f"分数: {result.get('scores', [])}")

# 测试2: 英文文本
translation_en = "Machine learning is a subset of artificial intelligence."
reference_en = "Machine learning is a subset of artificial intelligence."

result_en = scorer.score([translation_en], [reference_en])
print("\n测试2: 英文文本（完全相同）")
print(f"结果: {result_en}")
print(f"分数: {result_en.get('scores', [])}")

# 测试3: 不同的文本
translation_diff = "你好，世界！"
reference_diff = "Hello, world!"

result_diff = scorer.score([translation_diff], [reference_diff])
print("\n测试3: 不同的文本")
print(f"结果: {result_diff}")
print(f"分数: {result_diff.get('scores', [])}")

