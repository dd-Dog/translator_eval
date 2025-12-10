# 翻译评估API服务使用指南

## 📋 概述

翻译评估模块现在可以作为独立的API服务运行，通过HTTP接口提供服务。这种架构具有以下优势：

- ✅ **完全解耦**: 评分环境不会污染翻译环境
- ✅ **独立运行**: 评分服务运行在独立的conda环境中
- ✅ **HTTP API**: 翻译Agent通过HTTP调用，无需安装评估依赖
- ✅ **支持并发**: 可以同时处理多个评估请求
- ✅ **易于扩展**: 未来可以多个翻译模型同时评估

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装基础依赖
pip install -e .

# 或安装所有评估器
pip install -e .[all]
```

### 2. 启动API服务器

```bash
# 方法1: 直接运行
python eval_server.py

# 方法2: 使用启动脚本（Windows）
start_server.bat

# 方法3: 使用启动脚本（Linux/Mac）
chmod +x start_server.sh
./start_server.sh

# 方法4: 指定端口和选项
python eval_server.py --port 5001 --use-bleurt
```

**启动参数**:
- `--host`: 监听地址（默认: 0.0.0.0）
- `--port`: 监听端口（默认: 5001）
- `--debug`: 启用调试模式
- `--use-bleurt`: 启用BLEURT评估器（需要TensorFlow）

### 3. 测试API

```bash
# 运行测试脚本
python test_api.py

# 或使用客户端示例
python eval_client.py
```

## 📡 API接口

### 基础信息

- **服务地址**: `http://localhost:5001`
- **API文档**: `http://localhost:5001/`
- **健康检查**: `http://localhost:5001/health`

### 1. 健康检查

**请求**:
```bash
GET http://localhost:5001/health
```

**响应**:
```json
{
    "status": "healthy",
    "evaluator_initialized": true
}
```

### 2. 单个样本评估

**请求**:
```bash
POST http://localhost:5001/eval
Content-Type: application/json

{
    "source": "Machine learning is a subset of AI.",
    "translation": "机器学习是人工智能的一个子集。",
    "reference": "机器学习是人工智能的一个子集。",
    "mqm_score": {
        "adequacy": 0.9,
        "fluency": 0.85,
        "terminology": 0.95,
        "overall": 0.9
    }
}
```

**响应**:
```json
{
    "success": true,
    "score": {
        "bleu": 0.85,
        "comet": 0.92,
        "bleurt": 0.0,
        "bertscore_f1": 0.88,
        "chrf": 0.87,
        "mqm_adequacy": 0.9,
        "mqm_fluency": 0.85,
        "mqm_terminology": 0.95,
        "mqm_overall": 0.9,
        "final_score": 0.89,
        "model_info": {}
    }
}
```

**字段说明**:
- `source`: 源文本（可选）
- `translation`: 翻译文本（必需）
- `reference`: 参考翻译（必需）
- `mqm_score`: MQM评分（可选）

### 3. 批量评估

**请求**:
```bash
POST http://localhost:5001/eval/batch
Content-Type: application/json

{
    "sources": [
        "Machine learning is a subset of AI.",
        "Deep learning is a branch of machine learning."
    ],
    "translations": [
        "机器学习是人工智能的一个子集。",
        "深度学习是机器学习的一个分支。"
    ],
    "references": [
        "机器学习是人工智能的一个子集。",
        "深度学习是机器学习的一个分支。"
    ],
    "mqm_scores": [
        {"overall": 0.9},
        {"overall": 0.85}
    ]
}
```

**响应**:
```json
{
    "success": true,
    "count": 2,
    "scores": [
        {
            "bleu": 0.85,
            "comet": 0.92,
            "bertscore_f1": 0.88,
            "chrf": 0.87,
            "final_score": 0.89
        },
        {
            "bleu": 0.82,
            "comet": 0.90,
            "bertscore_f1": 0.86,
            "chrf": 0.85,
            "final_score": 0.87
        }
    ]
}
```

## 💻 客户端使用

### Python客户端

#### 方法1: 使用EvaluationClient类

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

#### 方法2: 使用简单函数

```python
from eval_client import evaluate_translation

score = evaluate_translation(
    translation="机器学习是 AI 的子集。",
    reference="机器学习是人工智能的一个子集。"
)
print(score)
```

#### 方法3: 直接使用requests

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

### 其他语言

#### cURL

```bash
curl -X POST http://localhost:5001/eval \
  -H "Content-Type: application/json" \
  -d '{
    "translation": "机器学习是人工智能的一个子集。",
    "reference": "机器学习是人工智能的一个子集。",
    "source": "Machine learning is a subset of AI."
  }'
```

#### JavaScript/Node.js

```javascript
const axios = require('axios');

async function evaluateTranslation(translation, reference, source = '') {
    const response = await axios.post('http://localhost:5001/eval', {
        source: source,
        translation: translation,
        reference: reference
    });
    return response.data;
}

// 使用示例
evaluateTranslation(
    '机器学习是人工智能的一个子集。',
    '机器学习是人工智能的一个子集。'
).then(score => {
    console.log('综合评分:', score.score.final_score);
});
```

## 🔧 配置说明

### 评估器配置

在 `eval_server.py` 中可以配置启用的评估器：

```python
evaluator = UnifiedEvaluator(
    use_bleu=True,      # BLEU评估
    use_comet=True,     # COMET评估（需要模型下载）
    use_bleurt=False,   # BLEURT评估（需要TensorFlow）
    use_bertscore=True, # BERTScore评估
    use_mqm=True,       # MQM评估
    use_chrf=True       # ChrF评估
)
```

### 端口配置

默认端口为5001，可以通过参数修改：

```bash
python eval_server.py --port 8080
```

### 跨域配置

API服务器默认启用CORS，允许跨域请求。如需修改，编辑 `eval_server.py`：

```python
CORS(app, resources={r"/*": {"origins": "*"}})  # 允许所有来源
# 或
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000"]}})  # 指定来源
```

## 🐛 故障排除

### 1. 无法连接到服务器

**问题**: `Connection refused` 或 `无法连接到API服务器`

**解决**:
- 检查服务器是否启动: `python eval_server.py`
- 检查端口是否被占用
- 检查防火墙设置

### 2. 评估器初始化失败

**问题**: 部分评估器无法初始化

**解决**:
- 检查依赖是否安装: `pip install -e .[all]`
- 检查COMET模型是否下载
- 检查TensorFlow是否安装（如果使用BLEURT）

### 3. 请求超时

**问题**: 评估请求超时

**解决**:
- 首次使用COMET需要下载模型，需要等待
- 增加超时时间: `requests.post(url, json=data, timeout=300)`
- 检查网络连接

## 📊 性能优化

### 1. 模型预加载

评估器在服务器启动时初始化，模型已加载到内存，响应速度快。

### 2. 批量评估

使用批量评估接口可以提高效率，减少HTTP请求次数。

### 3. 并发处理

Flask默认支持多线程，可以同时处理多个请求。

## 🔐 安全建议

### 生产环境部署

1. **使用生产级WSGI服务器**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5001 eval_server:app
   ```

2. **添加认证**:
   - 使用API密钥
   - 使用JWT认证
   - 使用OAuth2

3. **限制访问**:
   - 使用反向代理（Nginx）
   - 配置防火墙规则
   - 限制CORS来源

4. **监控和日志**:
   - 添加日志记录
   - 监控服务器状态
   - 设置告警

## 📝 示例场景

### 场景1: 翻译Agent调用

```python
# 在翻译Agent中
import requests

def evaluate_translation(translation, reference):
    response = requests.post(
        "http://localhost:5001/eval",
        json={
            "translation": translation,
            "reference": reference
        }
    )
    result = response.json()
    if result.get("success"):
        return result["score"]["final_score"]
    return 0.0

# 使用
score = evaluate_translation("翻译文本", "参考翻译")
print(f"翻译质量评分: {score:.4f}")
```

### 场景2: 批量评估翻译结果

```python
from eval_client import EvaluationClient

client = EvaluationClient()

# 批量评估
results = client.evaluate_batch(
    translations=["翻译1", "翻译2", "翻译3"],
    references=["参考1", "参考2", "参考3"]
)

# 分析结果
if results.get("success"):
    scores = results["scores"]
    avg_score = sum(s["final_score"] for s in scores) / len(scores)
    print(f"平均评分: {avg_score:.4f}")
```

## 🎯 总结

API服务模式让翻译评估模块可以：

1. **独立运行**: 不依赖翻译环境
2. **灵活调用**: 通过HTTP接口调用
3. **易于扩展**: 支持多个客户端同时使用
4. **稳定可靠**: 服务独立，不会相互影响

这种架构完美解决了环境冲突、模型存储、跨环境调用等问题！

