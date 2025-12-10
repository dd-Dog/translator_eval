# Translation Evaluator

统一翻译质量评估库，支持多种专业评估指标。

## 支持的评估指标

- **BLEU**: 传统n-gram匹配指标
- **COMET**: WMT官方神经网络质量评估模型
- **BLEURT**: Google开发的基于BERT的评估模型
- **BERTScore**: 基于BERT embedding的语义相似度评估
- **MQM**: 多维度质量指标（充分性、流畅性、术语）
- **ChrF**: 字符n-gram F-score（对形态变化丰富的语言友好）

## 安装

### 基础安装
```bash
pip install -e .
```

### 安装所有评估器
```bash
pip install -e .[all]
```

### 选择性安装
```bash
# 只安装BERTScore
pip install -e .[bertscore]

# 只安装COMET
pip install -e .[comet]

# 安装BERTScore和ChrF
pip install -e .[bertscore,chrf]
```

## 使用方法

```python
from translation_evaluator import UnifiedEvaluator

# 初始化评估器
evaluator = UnifiedEvaluator(
    use_bleu=True,
    use_comet=True,
    use_bleurt=False,
    use_bertscore=True,
    use_chrf=True
)

evaluator.initialize()

# 评估单个样本
score = evaluator.score(
    source="Hello, world!",
    translation="你好，世界！",
    reference="你好，世界！",
    mqm_score={"overall": 0.9}  # 可选
)

print(f"BLEU: {score.bleu}")
print(f"COMET: {score.comet}")
print(f"BERTScore: {score.bertscore_f1}")
print(f"ChrF: {score.chrf}")
print(f"综合评分: {score.final_score}")
```

## 项目结构

```
translation_evaluator/
├── translation_evaluator/
│   ├── __init__.py
│   ├── unified_evaluator.py    # 统一评估器
│   ├── bleu_scorer.py          # BLEU评估器
│   ├── comet_scorer.py         # COMET评估器
│   ├── bleurt_scorer.py        # BLEURT评估器
│   ├── bertscore_scorer.py     # BERTScore评估器
│   ├── chrf_scorer.py          # ChrF评估器
│   └── mqm_scorer.py           # MQM评估器
├── setup.py
└── README.md
```

## 许可证

[根据实际情况填写]

