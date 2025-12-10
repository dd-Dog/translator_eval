# Translation Evaluator

统一翻译质量评估库，支持多种专业评估指标。

## 支持的评估指标

- **BLEU**: 传统n-gram匹配指标
- **COMET**: WMT官方神经网络质量评估模型（自动下载模型）
- **BLEURT**: Google开发的基于BERT的评估模型（**支持自动下载模型** ✨）
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

### 完整环境安装（推荐）

如果需要使用所有评估器，建议使用conda环境：

```bash
conda create -n translator_eval
conda activate translator_eval
# 安装指定版本的numpy，因为comet和bleurt自动安装会有numpy版本冲突
conda install numpy=1.23.5 -y
# 安装pytorch,comet依赖pytorch
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y
pip install unbabel-comet
# 安装bleurt,它没有在pypi库中，需要自己从github下载后编译
git clone https://github.com/google-research/bleurt.git
cd bleurt
# 执行编译安装,绝对要禁止自动安装/更新依赖
pip install . --no-deps
cd ..
# 安装本项目
pip install -e .
```

### BLEURT模型自动下载

**新功能**: BLEURT模型现在支持自动下载，无需手动下载！

- 首次使用时，如果模型不存在会自动下载
- 需要网络连接和TensorFlow
- 支持BLEURT-20和BLEURT-20-D12

## 使用方法

### 基础使用

```python
from translation_evaluator import UnifiedEvaluator

# 初始化评估器
evaluator = UnifiedEvaluator(
    use_bleu=True,
    use_comet=True,
    use_bleurt=False,  # 设置为True时，模型不存在会自动下载
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

### BLEURT自动下载功能

BLEURT评估器支持自动下载模型，无需手动下载：

```python
from translation_evaluator import BLEURTScorer

# 启用自动下载（默认）
scorer = BLEURTScorer(checkpoint="BLEURT-20", auto_download=True)
scorer.initialize()  # 如果模型不存在，会自动下载（需要网络连接）

# 禁用自动下载
scorer = BLEURTScorer(checkpoint="BLEURT-20", auto_download=False)
scorer.initialize()  # 如果模型不存在，会提示手动下载

# 使用本地已下载的模型
scorer = BLEURTScorer(checkpoint="./models/BLEURT-20")
scorer.initialize()
```

**注意**: 
- 自动下载需要网络连接（访问Google Cloud Storage）
- 需要安装TensorFlow: `pip install tensorflow`
- BLEURT-20模型约500MB，下载可能需要几分钟

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

