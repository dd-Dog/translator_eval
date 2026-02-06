"""
翻译评估API服务器
提供HTTP API接口，支持独立运行
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from translation_evaluator import UnifiedEvaluator, PaperGradeScore

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# Debug模式配置（默认开启）
DEBUG_MODE = True
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# 配置日志记录器
def setup_logger():
    """设置日志记录器"""
    logger = logging.getLogger('api_debug')
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建文件handler，按日期命名
    log_file = LOGS_DIR / f"api_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 创建格式
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger

api_logger = setup_logger()

# 全局评估器实例和配置
evaluator = None
evaluator_config = {
    "use_bleu": True,
    "use_comet": True,
    "use_bleurt": False,  # 默认关闭，需要TensorFlow或子进程模式
    "use_bertscore": True,
    "use_mqm": True,
    "use_chrf": True,
    "comet_model": None  # None表示使用默认模型名称，也可以指定本地路径
}

# 请求队列管理器（单线程处理，避免并发压力）
request_queue = None
USE_QUEUE = os.environ.get("USE_REQUEST_QUEUE", "true").lower() in ("true", "1", "yes")  # 默认启用队列

def init_from_env():
    """
    从环境变量初始化配置（用于gunicorn等场景）
    """
    import os
    
    print(f"\n🔍 [DEBUG] 开始从环境变量读取配置...")
    print(f"   当前工作目录: {os.getcwd()}")
    
    # 从环境变量读取USE_BLEURT
    use_bleurt_env = os.environ.get("USE_BLEURT", "")
    print(f"   USE_BLEURT环境变量值: {repr(use_bleurt_env)}")
    if use_bleurt_env.lower() in ("true", "1", "yes"):
        evaluator_config["use_bleurt"] = True
        print(f"🔧 从环境变量启用BLEURT: USE_BLEURT={use_bleurt_env}")
    else:
        print(f"   ⚠️  USE_BLEURT未设置或值不正确，BLEURT将保持关闭状态")
        print(f"   请设置: export USE_BLEURT=true")
    
    # 从环境变量读取COMET模型路径
    comet_model_env = os.environ.get("COMET_MODEL_PATH")
    if comet_model_env:
        evaluator_config["comet_model"] = comet_model_env
        print(f"🔧 从环境变量读取COMET模型: {comet_model_env}")
    
    # 设置BLEURT子进程模式环境变量（如果已设置）
    if os.environ.get("BLEURT_USE_SUBPROCESS", "").lower() == "true":
        print(f"🔧 启用BLEURT子进程模式")
        if os.environ.get("BLEURT_PYTHON_ENV"):
            print(f"   Python环境: {os.environ.get('BLEURT_PYTHON_ENV')}")
        if os.environ.get("BLEURT_WORKER_SCRIPT"):
            print(f"   工作脚本: {os.environ.get('BLEURT_WORKER_SCRIPT')}")
        if os.environ.get("BLEURT_CHECKPOINT"):
            print(f"   检查点: {os.environ.get('BLEURT_CHECKPOINT')}")
    
    # 设置HuggingFace缓存目录
    if os.environ.get("HF_HOME"):
        hf_home = os.environ.get("HF_HOME")
        if "TRANSFORMERS_CACHE" not in os.environ:
            os.environ["TRANSFORMERS_CACHE"] = os.path.join(hf_home, "hub")
        print(f"🔧 使用环境变量HF_HOME: {hf_home}")
    
    print(f"🔍 [DEBUG] 最终配置: use_bleurt={evaluator_config['use_bleurt']}")
    
    # 注意：不在这里初始化评估器，因为init_evaluator函数还未定义
    # 评估器将在首次请求时或模块完全加载后初始化
    if evaluator_config["use_bleurt"]:
        print(f"   ✅ BLEURT已配置，将在首次请求时初始化")
    else:
        print(f"   ⚠️  BLEURT未启用，跳过初始化")

# 在模块加载时从环境变量初始化（用于gunicorn）
# 注意：此时只读取配置，不初始化评估器（因为init_evaluator还未定义）
init_from_env()


def init_evaluator(use_bleurt=None, comet_model=None, force_reinit=False):
    """
    初始化评估器
    
    Args:
        use_bleurt: 是否使用BLEURT（None表示使用全局配置）
        comet_model: COMET模型名称或本地路径（None表示使用全局配置）
        force_reinit: 是否强制重新初始化（即使已初始化）
    """
    global evaluator, evaluator_config
    
    # 如果指定了use_bleurt，更新配置
    if use_bleurt is not None:
        evaluator_config["use_bleurt"] = use_bleurt
        # 如果配置改变且评估器已初始化，需要重新初始化
        if evaluator is not None:
            force_reinit = True
    
    # 如果指定了comet_model，更新配置
    if comet_model is not None:
        evaluator_config["comet_model"] = comet_model
        # 如果配置改变且评估器已初始化，需要重新初始化
        if evaluator is not None:
            force_reinit = True
    
    if evaluator is None or force_reinit:
        if force_reinit and evaluator is not None:
            print("⚠️  检测到配置变更，重新初始化评估器...")
            evaluator = None
        print("=" * 80)
        print("初始化翻译评估器...")
        print("=" * 80)
        
        if evaluator_config["use_bleurt"]:
            print("⚠️  启用BLEURT评估器（需要TensorFlow和模型文件）")
        
        # 获取COMET模型配置（优先使用传入参数，其次环境变量，最后使用配置）
        import os
        comet_model_to_use = comet_model
        if comet_model_to_use is None:
            # 检查环境变量
            comet_model_to_use = os.environ.get("COMET_MODEL_PATH")
            if comet_model_to_use:
                print(f"🔍 [DEBUG] 从环境变量读取COMET_MODEL_PATH: {comet_model_to_use}")
        if comet_model_to_use is None:
            # 使用配置中的值（可能是None，表示使用默认）
            comet_model_to_use = evaluator_config.get("comet_model")
            if comet_model_to_use:
                print(f"🔍 [DEBUG] 从配置读取comet_model: {comet_model_to_use}")
        
        if comet_model_to_use:
            print(f"📦 使用COMET模型: {comet_model_to_use}")
            # 验证路径是否存在
            if os.path.exists(comet_model_to_use):
                print(f"✅ COMET模型路径存在: {comet_model_to_use}")
            else:
                print(f"⚠️  COMET模型路径不存在: {comet_model_to_use}")
                print(f"   当前工作目录: {os.getcwd()}")
        else:
            print(f"🔍 [DEBUG] 未指定COMET模型，将使用默认模型名称")
        
        evaluator = UnifiedEvaluator(
            use_bleu=evaluator_config["use_bleu"],
            use_comet=evaluator_config["use_comet"],
            use_bleurt=evaluator_config["use_bleurt"],
            use_bertscore=evaluator_config["use_bertscore"],
            use_mqm=evaluator_config["use_mqm"],
            use_chrf=evaluator_config["use_chrf"],
            comet_model=comet_model_to_use if comet_model_to_use else "Unbabel/wmt22-comet-da"
        )
        
        success = evaluator.initialize()
        
        # 显示实际启用的评估器状态
        print("\n" + "=" * 80)
        print("评估器状态:")
        print("=" * 80)
        
        enabled = []
        failed = []
        
        if evaluator_config["use_bleu"]:
            enabled.append("BLEU")
        
        if evaluator_config["use_comet"]:
            if evaluator.use_comet and evaluator.comet_scorer:
                enabled.append("COMET ✅")
            else:
                failed.append("COMET ❌")
        
        if evaluator_config["use_bleurt"]:
            if evaluator.use_bleurt and evaluator.bleurt_scorer:
                enabled.append("BLEURT ✅")
            else:
                failed.append("BLEURT ❌ (可能缺少TensorFlow或模型文件)")
        
        if evaluator_config["use_bertscore"]:
            if evaluator.use_bertscore and evaluator.bertscore_scorer:
                enabled.append("BERTScore ✅")
            else:
                failed.append("BERTScore ❌")
        
        if evaluator_config["use_chrf"]:
            if evaluator.use_chrf and evaluator.chrf_scorer:
                enabled.append("ChrF ✅")
            else:
                failed.append("ChrF ❌")
        
        if evaluator_config["use_mqm"]:
            enabled.append("MQM")
        
        if enabled:
            print(f"✅ 已启用: {', '.join(enabled)}")
        if failed:
            print(f"⚠️  初始化失败: {', '.join(failed)}")
        
        if success:
            print("\n✅ 评估器初始化完成！")
        else:
            print("\n⚠️  部分评估器初始化失败，但服务仍可运行")
        
        print("=" * 80)
        print("API服务已就绪")
        print("=" * 80)
        
        # 初始化请求队列（如果启用）
        if USE_QUEUE:
            global request_queue
            from translation_evaluator.request_queue import RequestQueue
            max_queue_size = int(os.environ.get("MAX_QUEUE_SIZE", "50"))
            request_timeout = int(os.environ.get("REQUEST_TIMEOUT", "600"))
            request_queue = RequestQueue(max_queue_size=max_queue_size, request_timeout=request_timeout)
            
            # 设置处理回调
            def process_eval_request(request_data):
                """处理评估请求的回调函数"""
                global evaluator
                if evaluator is None:
                    init_evaluator(
                        use_bleurt=evaluator_config.get("use_bleurt", False),
                        comet_model=evaluator_config.get("comet_model")
                    )
                
                source = request_data.get("source", "")
                translation = request_data.get("translation")
                reference = request_data.get("reference")
                mqm_score = request_data.get("mqm_score")
                
                if not translation or not reference:
                    return {
                        "success": False,
                        "error": "translation和reference不能为空"
                    }
                
                score = evaluator.score(
                    source=source,
                    translation=translation,
                    reference=reference,
                    mqm_score=mqm_score
                )
                
                # 转换为字典
                if isinstance(score, PaperGradeScore):
                    score_dict = {
                        "bleu": score.bleu,
                        "comet": score.comet,
                        "bleurt": score.bleurt,
                        "bertscore_f1": score.bertscore_f1,
                        "chrf": score.chrf,
                        "mqm_adequacy": score.mqm_adequacy,
                        "mqm_fluency": score.mqm_fluency,
                        "mqm_terminology": score.mqm_terminology,
                        "mqm_overall": score.mqm_overall,
                        "final_score": score.final_score,
                        "model_info": score.model_info
                    }
                else:
                    score_dict = score.__dict__ if hasattr(score, '__dict__') else {}
                
                return {
                    "success": True,
                    "score": score_dict
                }
            
            request_queue.set_process_callback(process_eval_request)
            request_queue.start()
            print(f"✅ 请求队列已启用 (最大队列长度: {max_queue_size}, 超时: {request_timeout}秒)")
        else:
            print(f"⚠️  请求队列未启用，将直接处理请求（可能导致并发压力）")
    
    return evaluator


@app.route("/", methods=["GET"])
def index():
    """API首页"""
    return jsonify({
        "service": "Translation Evaluator API",
        "version": "1.0.0",
        "endpoints": {
            "/": "API信息",
            "/health": "健康检查",
            "/eval": "单个样本评估 (POST)",
            "/eval/batch": "批量评估 (POST)"
        },
        "usage": {
            "single": {
                "url": "/eval",
                "method": "POST",
                "body": {
                    "source": "源文本（可选）",
                    "translation": "翻译文本（必需）",
                    "reference": "参考翻译（必需）",
                    "mqm_score": "MQM评分（可选）"
                }
            },
            "batch": {
                "url": "/eval/batch",
                "method": "POST",
                "body": {
                    "sources": ["源文本列表"],
                    "translations": ["翻译文本列表"],
                    "references": ["参考翻译列表"],
                    "mqm_scores": ["MQM评分列表（可选）"]
                }
            }
        }
    })


@app.route("/health", methods=["GET"])
def health():
    """健康检查"""
    evaluator_status = {}
    if evaluator is not None:
        evaluator_status = {
            "use_bleu": evaluator.use_bleu,
            "use_comet": evaluator.use_comet and evaluator.comet_scorer is not None,
            "use_bleurt": evaluator.use_bleurt and evaluator.bleurt_scorer is not None,
            "use_bertscore": evaluator.use_bertscore and evaluator.bertscore_scorer is not None,
            "use_chrf": evaluator.use_chrf and evaluator.chrf_scorer is not None,
            "use_mqm": evaluator.use_mqm
        }
    
    queue_status_info = {}
    if request_queue:
        queue_status_info = request_queue.get_stats()
    
    return jsonify({
        "status": "healthy",
        "evaluator_initialized": evaluator is not None,
        "evaluator_status": evaluator_status,
        "queue_enabled": USE_QUEUE and request_queue is not None,
        "queue_stats": queue_status_info
    })


@app.route("/queue/status/<request_id>", methods=["GET"])
def queue_status(request_id):
    """查询请求状态"""
    if not request_queue:
        return jsonify({
            "success": False,
            "error": "请求队列未启用"
        }), 400
    
    status = request_queue.get_request_status(request_id)
    if status is None:
        return jsonify({
            "success": False,
            "error": "请求ID不存在"
        }), 404
    
    return jsonify({
        "success": True,
        **status
    })


@app.route("/queue/stats", methods=["GET"])
def queue_stats():
    """获取队列统计信息"""
    if not request_queue:
        return jsonify({
            "success": False,
            "error": "请求队列未启用"
        }), 400
    
    return jsonify({
        "success": True,
        **request_queue.get_stats()
    })


@app.route("/eval", methods=["POST"])
def eval_text():
    """
    单个样本评估（支持队列模式）
    
    Request Body:
    {
        "source": "源文本（可选）",
        "translation": "翻译文本（必需）",
        "reference": "参考翻译（必需）",
        "mqm_score": {
            "adequacy": 0.9,
            "fluency": 0.85,
            "terminology": 0.95,
            "overall": 0.9
        }  // 可选
    }
    
    Response (队列模式):
    {
        "success": true,
        "request_id": "uuid",
        "status": "queued",
        "queue_position": 1,
        "message": "请求已加入队列，当前排队位置: 1"
    }
    
    Response (直接模式):
    {
        "success": true,
        "score": {
            "bleu": 0.85,
            "comet": 0.92,
            ...
        }
    }
    """
    # 如果启用队列模式，使用队列处理
    if USE_QUEUE and request_queue:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "请求体不能为空"
            }), 400
        
        # 验证必需字段
        if "translation" not in data or "reference" not in data:
            return jsonify({
                "success": False,
                "error": "缺少必需字段: translation 或 reference"
            }), 400
        
        # 提交到队列
        result = request_queue.submit_request(data)
        
        if result.get("success"):
            return jsonify(result), 202  # 202 Accepted - 请求已接受，正在处理
        else:
            return jsonify(result), 503  # 503 Service Unavailable - 队列已满
    
    # 直接处理模式（原有逻辑）
    request_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    
    try:
        if DEBUG_MODE:
            api_logger.info("=" * 100)
            api_logger.info(f"📥 [请求ID: {request_id}] 收到单个样本评估请求")
            api_logger.info("=" * 100)
        # 确保评估器已初始化
        if evaluator is None:
            # 使用配置中的值初始化（可能已从环境变量读取）
            init_evaluator(
                use_bleurt=evaluator_config.get("use_bleurt", False),
                comet_model=evaluator_config.get("comet_model")
            )
        
        # 获取请求数据
        data = request.json
        if not data:
            if DEBUG_MODE:
                api_logger.error(f"[请求ID: {request_id}] 请求体为空")
            return jsonify({
                "success": False,
                "error": "请求体不能为空"
            }), 400
        
        # 记录请求数据
        if DEBUG_MODE:
            api_logger.info(f"[请求ID: {request_id}] 📋 请求数据:")
            api_logger.info(f"  - translation长度: {len(data.get('translation', ''))}")
            api_logger.info(f"  - reference长度: {len(data.get('reference', ''))}")
            api_logger.info(f"  - source长度: {len(data.get('source', ''))}")
            api_logger.info(f"  - 是否有mqm_score: {'mqm_score' in data and data['mqm_score'] is not None}")
            if DEBUG_MODE:
                # 记录完整数据（截断长文本）
                log_data = data.copy()
                for key in ['translation', 'reference', 'source']:
                    if key in log_data and len(log_data[key]) > 200:
                        log_data[key] = log_data[key][:200] + f"... (总长度: {len(data[key])})"
                api_logger.debug(f"[请求ID: {request_id}] 完整请求数据: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
        
        # 验证必需字段
        if "translation" not in data:
            if DEBUG_MODE:
                api_logger.error(f"[请求ID: {request_id}] 缺少必需字段: translation")
            return jsonify({
                "success": False,
                "error": "缺少必需字段: translation"
            }), 400
        
        if "reference" not in data:
            if DEBUG_MODE:
                api_logger.error(f"[请求ID: {request_id}] 缺少必需字段: reference")
            return jsonify({
                "success": False,
                "error": "缺少必需字段: reference"
            }), 400
        
        # 执行评估
        reference = data["reference"]
        translation = data["translation"]
        source = data.get("source", "")
        mqm_score = data.get("mqm_score")
        
        # 记录评估器状态
        if DEBUG_MODE:
            api_logger.info(f"[请求ID: {request_id}] 🔧 评估器状态:")
            api_logger.info(f"  - use_bleu: {evaluator.use_bleu}")
            api_logger.info(f"  - use_comet: {evaluator.use_comet}")
            api_logger.info(f"  - use_bleurt: {evaluator.use_bleurt}")
            api_logger.info(f"  - use_bertscore: {evaluator.use_bertscore}")
            api_logger.info(f"  - use_chrf: {evaluator.use_chrf}")
            api_logger.info(f"  - use_mqm: {evaluator.use_mqm}")
            api_logger.info(f"  - COMET评估器存在: {evaluator.comet_scorer is not None}")
            api_logger.info(f"  - BLEURT评估器存在: {evaluator.bleurt_scorer is not None}")
            api_logger.info(f"  - BERTScore评估器存在: {evaluator.bertscore_scorer is not None}")
            api_logger.info(f"  - ChrF评估器存在: {evaluator.chrf_scorer is not None}")
        
        # 验证reference不为空
        if not reference or not reference.strip():
            if DEBUG_MODE:
                api_logger.error(f"[请求ID: {request_id}] reference为空")
            return jsonify({
                "success": False,
                "error": "reference不能为空（BLEURT等评估器需要reference）"
            }), 400
        
        # 开始评估
        if DEBUG_MODE:
            api_logger.info(f"[请求ID: {request_id}] 🚀 开始评估...")
            start_time = datetime.now()
        
        score = evaluator.score(
            source=source,
            translation=translation,
            reference=reference,
            mqm_score=mqm_score
        )
        
        # 记录评估结果
        if DEBUG_MODE:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            api_logger.info(f"[请求ID: {request_id}] ✅ 评估完成 (耗时: {duration:.3f}秒)")
            api_logger.info(f"[请求ID: {request_id}] 📊 评估结果:")
            api_logger.info(f"  - BLEU: {score.bleu:.6f}")
            api_logger.info(f"  - COMET: {score.comet:.6f}")
            api_logger.info(f"  - BLEURT: {score.bleurt:.6f}")
            api_logger.info(f"  - BERTScore F1: {score.bertscore_f1:.6f}")
            api_logger.info(f"  - ChrF: {score.chrf:.6f}")
            api_logger.info(f"  - MQM Adequacy: {score.mqm_adequacy:.6f}")
            api_logger.info(f"  - MQM Fluency: {score.mqm_fluency:.6f}")
            api_logger.info(f"  - MQM Terminology: {score.mqm_terminology:.6f}")
            api_logger.info(f"  - MQM Overall: {score.mqm_overall:.6f}")
            api_logger.info(f"  - 综合评分: {score.final_score:.6f}")
            if hasattr(score, 'model_info') and score.model_info:
                api_logger.info(f"  - 模型信息: {score.model_info}")
        
        # 转换为字典（处理dataclass）
        if isinstance(score, PaperGradeScore):
            score_dict = {
                "bleu": score.bleu,
                "comet": score.comet,
                "bleurt": score.bleurt,  # 确保BLEURT总是包含在返回结果中
                "bertscore_f1": score.bertscore_f1,
                "chrf": score.chrf,
                "mqm_adequacy": score.mqm_adequacy,
                "mqm_fluency": score.mqm_fluency,
                "mqm_terminology": score.mqm_terminology,
                "mqm_overall": score.mqm_overall,
                "final_score": score.final_score,
                "model_info": score.model_info
            }
            # 调试信息：如果BLEURT为0但评估器已启用，记录日志
            if evaluator.use_bleurt and score.bleurt == 0.0:
                if DEBUG_MODE:
                    api_logger.warning(f"[请求ID: {request_id}] ⚠️  BLEURT已启用但分数为0")
        else:
            score_dict = score.__dict__ if hasattr(score, '__dict__') else {}
            # 确保BLEURT字段存在
            if "bleurt" not in score_dict:
                score_dict["bleurt"] = 0.0
        
        # 记录返回结果
        if DEBUG_MODE:
            api_logger.info(f"[请求ID: {request_id}] 📤 返回结果:")
            api_logger.debug(f"[请求ID: {request_id}] 完整返回数据: {json.dumps(score_dict, ensure_ascii=False, indent=2)}")
            api_logger.info(f"[请求ID: {request_id}] " + "=" * 100)
        
        return jsonify({
            "success": True,
            "score": score_dict
        })
        
    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        if DEBUG_MODE:
            api_logger.error(f"[请求ID: {request_id}] ❌ 评估错误: {error_msg}")
            api_logger.error(f"[请求ID: {request_id}] 错误堆栈:\n{traceback_str}")
            api_logger.info(f"[请求ID: {request_id}] " + "=" * 100)
        
        return jsonify({
            "success": False,
            "error": error_msg,
            "traceback": traceback_str if app.debug else None
        }), 500


@app.route("/eval/batch", methods=["POST"])
def eval_batch():
    """
    批量评估
    
    Request Body:
    {
        "sources": ["源文本1", "源文本2", ...],
        "translations": ["翻译1", "翻译2", ...],
        "references": ["参考1", "参考2", ...],
        "mqm_scores": [
            {"overall": 0.9},
            {"overall": 0.85}
        ]  // 可选
    }
    
    Response:
    {
        "success": true,
        "scores": [
            {
                "bleu": 0.85,
                "comet": 0.92,
                ...
            },
            ...
        ]
    }
    """
    request_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    
    try:
        if DEBUG_MODE:
            api_logger.info("=" * 100)
            api_logger.info(f"📥 [请求ID: {request_id}] 收到批量评估请求")
            api_logger.info("=" * 100)
        # 确保评估器已初始化
        if evaluator is None:
            # 使用配置中的值初始化（可能已从环境变量读取）
            init_evaluator(
                use_bleurt=evaluator_config.get("use_bleurt", False),
                comet_model=evaluator_config.get("comet_model")
            )
        
        # 获取请求数据
        data = request.json
        if not data:
            if DEBUG_MODE:
                api_logger.error(f"[请求ID: {request_id}] 请求体为空")
            return jsonify({
                "success": False,
                "error": "请求体不能为空"
            }), 400
        
        # 记录请求数据
        if DEBUG_MODE:
            api_logger.info(f"[请求ID: {request_id}] 📋 请求数据:")
            api_logger.info(f"  - translations数量: {len(data.get('translations', []))}")
            api_logger.info(f"  - references数量: {len(data.get('references', []))}")
            api_logger.info(f"  - sources数量: {len(data.get('sources', []))}")
            api_logger.info(f"  - mqm_scores数量: {len(data.get('mqm_scores', []))}")
        
        # 验证必需字段
        if "translations" not in data:
            if DEBUG_MODE:
                api_logger.error(f"[请求ID: {request_id}] 缺少必需字段: translations")
            return jsonify({
                "success": False,
                "error": "缺少必需字段: translations"
            }), 400
        
        if "references" not in data:
            if DEBUG_MODE:
                api_logger.error(f"[请求ID: {request_id}] 缺少必需字段: references")
            return jsonify({
                "success": False,
                "error": "缺少必需字段: references"
            }), 400
        
        translations = data["translations"]
        references = data["references"]
        sources = data.get("sources", [""] * len(translations))
        mqm_scores = data.get("mqm_scores", [None] * len(translations))
        
        # 验证长度
        if len(translations) != len(references):
            if DEBUG_MODE:
                api_logger.error(f"[请求ID: {request_id}] 长度不匹配: translations={len(translations)}, references={len(references)}")
            return jsonify({
                "success": False,
                "error": f"translations和references长度不匹配: {len(translations)} vs {len(references)}"
            }), 400
        
        # 记录评估器状态
        if DEBUG_MODE:
            api_logger.info(f"[请求ID: {request_id}] 🔧 评估器状态:")
            api_logger.info(f"  - use_bleu: {evaluator.use_bleu}")
            api_logger.info(f"  - use_comet: {evaluator.use_comet}")
            api_logger.info(f"  - use_bleurt: {evaluator.use_bleurt}")
            api_logger.info(f"  - use_bertscore: {evaluator.use_bertscore}")
            api_logger.info(f"  - use_chrf: {evaluator.use_chrf}")
            api_logger.info(f"  - use_mqm: {evaluator.use_mqm}")
        
        # 开始批量评估
        if DEBUG_MODE:
            api_logger.info(f"[请求ID: {request_id}] 🚀 开始批量评估...")
            start_time = datetime.now()
        
        results = evaluator.batch_score(
            sources=sources,
            translations=translations,
            references=references,
            mqm_scores=mqm_scores if mqm_scores else None
        )
        
        # 转换为字典列表
        scores_list = []
        for i, score in enumerate(results):
            if isinstance(score, PaperGradeScore):
                score_dict = {
                    "bleu": score.bleu,
                    "comet": score.comet,
                    "bleurt": score.bleurt,
                    "bertscore_f1": score.bertscore_f1,
                    "chrf": score.chrf,
                    "mqm_adequacy": score.mqm_adequacy,
                    "mqm_fluency": score.mqm_fluency,
                    "mqm_terminology": score.mqm_terminology,
                    "mqm_overall": score.mqm_overall,
                    "final_score": score.final_score
                }
            else:
                score_dict = score.__dict__ if hasattr(score, '__dict__') else {}
            scores_list.append(score_dict)
            
            # 记录每个样本的评估结果
            if DEBUG_MODE:
                api_logger.info(f"[请求ID: {request_id}] 📊 样本 {i+1}/{len(results)} 评估结果:")
                api_logger.info(f"  - BLEU: {score_dict.get('bleu', 0):.6f}")
                api_logger.info(f"  - COMET: {score_dict.get('comet', 0):.6f}")
                api_logger.info(f"  - BLEURT: {score_dict.get('bleurt', 0):.6f}")
                api_logger.info(f"  - BERTScore F1: {score_dict.get('bertscore_f1', 0):.6f}")
                api_logger.info(f"  - ChrF: {score_dict.get('chrf', 0):.6f}")
                api_logger.info(f"  - 综合评分: {score_dict.get('final_score', 0):.6f}")
        
        if DEBUG_MODE:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            api_logger.info(f"[请求ID: {request_id}] ✅ 批量评估完成 (总耗时: {duration:.3f}秒, 平均: {duration/len(results):.3f}秒/样本)")
            api_logger.info(f"[请求ID: {request_id}] 📤 返回 {len(scores_list)} 个评估结果")
            api_logger.info(f"[请求ID: {request_id}] " + "=" * 100)
        
        return jsonify({
            "success": True,
            "count": len(scores_list),
            "scores": scores_list
        })
        
    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        if DEBUG_MODE:
            api_logger.error(f"[请求ID: {request_id}] ❌ 批量评估错误: {error_msg}")
            api_logger.error(f"[请求ID: {request_id}] 错误堆栈:\n{traceback_str}")
            api_logger.info(f"[请求ID: {request_id}] " + "=" * 100)
        
        return jsonify({
            "success": False,
            "error": error_msg,
            "traceback": traceback_str if app.debug else None
        }), 500


if __name__ == "__main__":
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="翻译评估API服务器")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5001, help="监听端口 (默认: 5001)")
    parser.add_argument("--debug", action="store_true", help="启用Flask调试模式")
    parser.add_argument("--use-bleurt", action="store_true", help="启用BLEURT评估器")
    parser.add_argument("--bleurt-subprocess", action="store_true", 
                       help="使用子进程模式运行BLEURT（避免环境冲突）")
    parser.add_argument("--bleurt-python-env", type=str, default=None,
                       help="BLEURT的Python环境路径 (例如: /path/to/bleurt_env/bin/python)")
    parser.add_argument("--bleurt-worker-script", type=str, default=None,
                       help="BLEURT工作脚本路径 (默认: ./bleurt_worker.py)")
    parser.add_argument("--bleurt-checkpoint", type=str, default=None,
                       help="BLEURT检查点路径 (默认: BLEURT-20)")
    parser.add_argument("--comet-model", type=str, default=None, 
                       help="COMET模型名称或本地路径 (例如: /path/to/comet/model 或 Unbabel/wmt22-comet-da)")
    parser.add_argument("--hf-home", type=str, default=None,
                       help="HuggingFace缓存目录 (例如: /root/.cache/huggingface)")
    parser.add_argument("--no-api-debug", action="store_true", help="禁用API请求调试日志（默认开启）")
    
    args = parser.parse_args()
    
    # 设置BLEURT环境变量（子进程模式）
    if args.bleurt_subprocess:
        os.environ["BLEURT_USE_SUBPROCESS"] = "true"
        if args.bleurt_python_env:
            os.environ["BLEURT_PYTHON_ENV"] = args.bleurt_python_env
        if args.bleurt_worker_script:
            os.environ["BLEURT_WORKER_SCRIPT"] = args.bleurt_worker_script
        if args.bleurt_checkpoint:
            os.environ["BLEURT_CHECKPOINT"] = args.bleurt_checkpoint
        print(f"🔧 启用BLEURT子进程模式")
        if args.bleurt_python_env:
            print(f"   Python环境: {args.bleurt_python_env}")
        if args.bleurt_worker_script:
            print(f"   工作脚本: {args.bleurt_worker_script}")
        if args.bleurt_checkpoint:
            print(f"   检查点: {args.bleurt_checkpoint}")
    
    # 设置HuggingFace环境变量（用于离线模式）
    # 注意：TRANSFORMERS_CACHE已弃用，使用HF_HOME
    if args.hf_home:
        os.environ["HF_HOME"] = args.hf_home
        # TRANSFORMERS_CACHE已弃用，但为了兼容性仍设置
        if "TRANSFORMERS_CACHE" not in os.environ:
            os.environ["TRANSFORMERS_CACHE"] = os.path.join(args.hf_home, "hub")
        print(f"🔧 设置HuggingFace缓存目录: {args.hf_home}")
    elif os.environ.get("HF_HOME"):
        hf_home = os.environ.get("HF_HOME")
        if "TRANSFORMERS_CACHE" not in os.environ:
            os.environ["TRANSFORMERS_CACHE"] = os.path.join(hf_home, "hub")
        print(f"🔧 使用环境变量HF_HOME: {hf_home}")
    else:
        # 使用默认路径
        default_hf_home = os.path.expanduser("~/.cache/huggingface")
        if os.path.exists(default_hf_home):
            os.environ["HF_HOME"] = default_hf_home
            if "TRANSFORMERS_CACHE" not in os.environ:
                os.environ["TRANSFORMERS_CACHE"] = os.path.join(default_hf_home, "hub")
            print(f"🔧 使用默认HuggingFace缓存目录: {default_hf_home}")
        else:
            # 即使目录不存在也设置，让库创建
            os.environ["HF_HOME"] = default_hf_home
            print(f"🔧 设置HuggingFace缓存目录（将创建）: {default_hf_home}")
    
    # 设置DEBUG_MODE
    DEBUG_MODE = not args.no_api_debug
    
    # 初始化评估器（传递use_bleurt和comet_model参数）
    # 优先级：命令行参数 > 环境变量 > 配置默认值
    import os
    use_bleurt = args.use_bleurt if args.use_bleurt else (
        os.environ.get("USE_BLEURT", "").lower() in ("true", "1", "yes") or 
        evaluator_config.get("use_bleurt", False)
    )
    comet_model = args.comet_model if args.comet_model else (
        os.environ.get("COMET_MODEL_PATH") or None
    )
    
    print(f"\n🔍 [DEBUG] 配置信息:")
    print(f"   BLEURT: {use_bleurt}")
    if comet_model:
        print(f"   COMET模型: {comet_model}")
    else:
        import os
        env_comet = os.environ.get("COMET_MODEL_PATH")
        if env_comet:
            print(f"   COMET模型 (环境变量): {env_comet}")
        else:
            print(f"   COMET模型: 使用默认")
    
    init_evaluator(use_bleurt=use_bleurt, comet_model=comet_model)
    
    print(f"\n🚀 启动API服务器...")
    print(f"   地址: http://{args.host}:{args.port}")
    print(f"   Flask调试模式: {args.debug}")
    print(f"   API请求调试日志: {'开启' if DEBUG_MODE else '关闭'}")
    print(f"   日志目录: {LOGS_DIR}")
    if DEBUG_MODE:
        log_file = LOGS_DIR / f"api_{datetime.now().strftime('%Y%m%d')}.log"
        print(f"   日志文件: {log_file}")
    print(f"\n📖 API文档: http://{args.host}:{args.port}/")
    print(f"💚 健康检查: http://{args.host}:{args.port}/health")
    print(f"📊 评估接口: http://{args.host}:{args.port}/eval")
    print(f"📦 批量评估: http://{args.host}:{args.port}/eval/batch")
    print("\n按 Ctrl+C 停止服务器\n")
    
    app.run(host=args.host, port=args.port, debug=args.debug)

