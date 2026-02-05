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

### COMET模型本地路径支持

**新功能**: 支持使用手动下载的本地COMET模型，解决网络问题！

如果服务器无法访问外网，可以手动下载COMET模型后使用本地路径：

#### 方法1: 使用环境变量
```bash
export COMET_MODEL_PATH=/path/to/comet/model
python eval_server.py
```

#### 方法2: 使用命令行参数
```bash
python eval_server.py --comet-model /path/to/comet/model
```

#### 方法3: 在代码中指定
```python
from translation_evaluator import UnifiedEvaluator

evaluator = UnifiedEvaluator(
    use_comet=True,
    comet_model="/path/to/comet/model"  # 本地模型路径
)
evaluator.initialize()
```

#### COMET模型路径说明
- COMET模型通常下载到: `~/.cache/comet/` 目录下
- 模型目录应包含完整的checkpoint文件
- 支持的路径格式:
  - 绝对路径: `/home/user/comet/wmt22-comet-da`
  - 相对路径: `./models/comet/wmt22-comet-da`
  - COMET缓存路径: `~/.cache/comet/wmt22-comet-da`

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

## API服务模式（独立运行）

### 架构优势

- ✅ **完全解耦**: 评分环境不会污染翻译环境
- ✅ **独立运行**: 评分服务运行在独立的conda环境中
- ✅ **HTTP API**: 翻译Agent通过HTTP调用，无需安装评估依赖
- ✅ **支持并发**: 可以同时处理多个评估请求
- ✅ **易于扩展**: 未来可以多个翻译模型同时评估

### 启动API服务器

```bash
# 在translator_eval环境中
conda activate translator_eval
python eval_server.py

# 启用BLEURT评估器（需要TensorFlow和模型文件）
python eval_server.py --use-bleurt

# 或指定端口和其他选项
python eval_server.py --port 5001 --use-bleurt --debug
```

**启动参数**:
- `--host`: 监听地址（默认: 0.0.0.0）
- `--port`: 监听端口（默认: 5001）
- `--debug`: 启用Flask调试模式
- `--use-bleurt`: **启用BLEURT评估器**（需要TensorFlow和BLEURT模型）
- `--no-api-debug`: 禁用API请求调试日志（默认开启）

**注意**: 
- 默认情况下BLEURT是关闭的（因为需要TensorFlow）
- 使用`--use-bleurt`参数可以启用BLEURT
- 首次使用BLEURT会自动下载模型（约500MB）
- **API请求调试日志默认开启**，所有请求的详细信息会保存到`logs/`文件夹

### API接口

#### 1. 健康检查
```bash
GET http://localhost:5001/health
```

#### 2. 单个样本评估
```bash
POST http://localhost:5001/eval
Content-Type: application/json

{
    "source": "Machine learning is a subset of AI.",
    "translation": "机器学习是人工智能的一个子集。",
    "reference": "机器学习是人工智能的一个子集。",
    "mqm_score": {
        "overall": 0.9
    }  // 可选
}
```

**响应**:
```json
{
    "success": true,
    "score": {
        "bleu": 0.85,
        "comet": 0.92,
        "bertscore_f1": 0.88,
        "chrf": 0.87,
        "final_score": 0.89
    }
}
```

#### 3. 批量评估
```bash
POST http://localhost:5001/eval/batch
Content-Type: application/json

{
    "sources": ["源文本1", "源文本2"],
    "translations": ["翻译1", "翻译2"],
    "references": ["参考1", "参考2"]
}
```

### 客户端使用

#### Python客户端

```python
from eval_client import EvaluationClient

# 创建客户端
client = EvaluationClient(base_url="http://localhost:5001")

# 单个样本评估
result = client.evaluate(
    translation="机器学习是人工智能的一个子集。",
    reference="机器学习是人工智能的一个子集。",
    source="Machine learning is a subset of AI."
)

if result.get("success"):
    score = result["score"]
    print(f"综合评分: {score['final_score']:.4f}")

# 批量评估
batch_result = client.evaluate_batch(
    translations=["翻译1", "翻译2"],
    references=["参考1", "参考2"]
)
```

#### 简单函数调用（向后兼容）

```python
from eval_client import evaluate_translation

score = evaluate_translation(
    translation="机器学习是 AI 的子集。",
    reference="机器学习是人工智能的一个子集。"
)
print(score)
```

#### 使用requests直接调用

```python
import requests

def evaluate_translation(translation, reference, source=""):
    r = requests.post(
        "http://localhost:5001/eval",
        json={
            "source": source,
            "translation": translation,
            "reference": reference
        }
    )
    return r.json()

# 使用示例
score = evaluate_translation(
    "机器学习是 AI 的子集。",
    "机器学习是人工智能的一个子集。"
)
print(score)
```

### API请求调试日志

**新功能**: API服务器现在支持详细的请求调试日志，默认开启！

- 所有API请求的详细信息会自动记录到`logs/`文件夹
- 日志文件按日期命名：`logs/api_YYYYMMDD.log`
- 记录内容包括：
  - 请求数据（translation、reference、source等）
  - 评估器状态（哪些评估器启用/可用）
  - 每个评估器的评分结果
  - 计算耗时
  - 返回结果
  - 错误信息（如有）

**禁用调试日志**:
```bash
python eval_server.py --no-api-debug
```

**日志示例**:
```
2025-12-11 13:16:20 | INFO | 📥 [请求ID: 20251211_131620_293721] 收到单个样本评估请求
2025-12-11 13:16:20 | INFO | [请求ID: 20251211_131620_293721] 📋 请求数据:
2025-12-11 13:16:20 | INFO |   - translation长度: 15
2025-12-11 13:16:20 | INFO |   - reference长度: 15
2025-12-11 13:16:27 | INFO | [请求ID: 20251211_131620_293721] 📊 评估结果:
2025-12-11 13:16:27 | INFO |   - BLEU: 1.000000
2025-12-11 13:16:27 | INFO |   - COMET: 0.979368
2025-12-11 13:16:27 | INFO |   - BLEURT: 0.976430
2025-12-11 13:16:27 | INFO |   - BERTScore F1: 1.000000
2025-12-11 13:16:27 | INFO |   - ChrF: 1.000000
2025-12-11 13:16:27 | INFO |   - 综合评分: 0.989133
```

### 综合评分计算方式

综合评分采用**加权平均**方式计算，权重分配如下：

| 指标 | 权重 | 说明 |
|------|------|------|
| **COMET** | 25% | 神经网络评估模型 |
| **BERTScore** | 20% | 基于BERT的语义相似度 |
| **BLEURT** | 15% | 神经网络评估模型 |
| **MQM** | 20% | 人工评估指标（如果提供） |
| **BLEU** | 10% | 传统n-gram匹配指标 |
| **ChrF** | 10% | 字符级F-score |

**权重自适应机制**:
- 如果某些指标不可用（分数为0），权重会自动归一化
- 例如：如果COMET不可用，其他指标的权重会按比例增加
- 确保即使部分指标缺失，也能得到合理的综合评分

**计算示例**:
```
假设评估结果：
- COMET: 0.85 (权重25%)
- BERTScore: 0.90 (权重20%)
- BLEURT: 0.80 (权重15%)
- MQM: 0.75 (权重20%)
- BLEU: 0.70 (权重10%)
- ChrF: 0.65 (权重10%)

综合评分 = 0.85×0.25 + 0.90×0.20 + 0.80×0.15 + 0.75×0.20 + 0.70×0.10 + 0.65×0.10
         = 0.7975
```

### 架构图

```
翻译 Agent（translator_online）
        │
        ▼ HTTP 请求
评分服务（translator_eval）
        │
        ├─► 记录详细日志到 logs/
        │
        ▼
返回 BLEU / COMET / BLEURT / BERTScore 分数
```

## 项目结构

```
translation_evaluator/
├── translation_evaluator/
│   ├── __init__.py
│   ├── unified_evaluator.py    # 统一评估器
│   ├── bleu_scorer.py          # BLEU评估器
│   ├── comet_scorer.py         # COMET评估器
│   ├── bleurt_scorer.py        # BLEURT评估器（支持自动下载）
│   ├── bertscore_scorer.py     # BERTScore评估器
│   ├── chrf_scorer.py          # ChrF评估器
│   ├── combined_scorer.py      # 组合评估器
│   └── mqm_scorer.py           # MQM评估器
├── eval_server.py              # API服务器（独立运行）
├── eval_client.py              # API客户端（调用示例）
├── setup.py
└── README.md
```

## 许可证

[根据实际情况填写]

