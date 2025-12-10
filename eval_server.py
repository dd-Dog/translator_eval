"""
翻译评估API服务器
提供HTTP API接口，支持独立运行
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from translation_evaluator import UnifiedEvaluator, PaperGradeScore

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局评估器实例和配置
evaluator = None
evaluator_config = {
    "use_bleu": True,
    "use_comet": True,
    "use_bleurt": True,  # 默认关闭，需要TensorFlow
    "use_bertscore": True,
    "use_mqm": True,
    "use_chrf": True
}


def init_evaluator(use_bleurt=None, force_reinit=False):
    """
    初始化评估器
    
    Args:
        use_bleurt: 是否使用BLEURT（None表示使用全局配置）
        force_reinit: 是否强制重新初始化（即使已初始化）
    """
    global evaluator, evaluator_config
    
    # 如果指定了use_bleurt，更新配置
    if use_bleurt is not None:
        evaluator_config["use_bleurt"] = use_bleurt
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
        
        evaluator = UnifiedEvaluator(
            use_bleu=evaluator_config["use_bleu"],
            use_comet=evaluator_config["use_comet"],
            use_bleurt=evaluator_config["use_bleurt"],
            use_bertscore=evaluator_config["use_bertscore"],
            use_mqm=evaluator_config["use_mqm"],
            use_chrf=evaluator_config["use_chrf"]
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
    
    return jsonify({
        "status": "healthy",
        "evaluator_initialized": evaluator is not None,
        "evaluator_status": evaluator_status
    })


@app.route("/eval", methods=["POST"])
def eval_text():
    """
    单个样本评估
    
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
    
    Response:
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
            "final_score": 0.89
        }
    }
    """
    try:
        # 确保评估器已初始化
        if evaluator is None:
            init_evaluator()
        
        # 获取请求数据
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "请求体不能为空"
            }), 400
        
        # 验证必需字段
        if "translation" not in data:
            return jsonify({
                "success": False,
                "error": "缺少必需字段: translation"
            }), 400
        
        if "reference" not in data:
            return jsonify({
                "success": False,
                "error": "缺少必需字段: reference"
            }), 400
        
        # 执行评估
        score = evaluator.score(
            source=data.get("source", ""),
            translation=data["translation"],
            reference=data["reference"],
            mqm_score=data.get("mqm_score")
        )
        
        # 转换为字典（处理dataclass）
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
        
        return jsonify({
            "success": True,
            "score": score_dict
        })
        
    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"评估错误: {error_msg}")
        print(traceback_str)
        
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
    try:
        # 确保评估器已初始化
        if evaluator is None:
            init_evaluator()
        
        # 获取请求数据
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "请求体不能为空"
            }), 400
        
        # 验证必需字段
        if "translations" not in data:
            return jsonify({
                "success": False,
                "error": "缺少必需字段: translations"
            }), 400
        
        if "references" not in data:
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
            return jsonify({
                "success": False,
                "error": f"translations和references长度不匹配: {len(translations)} vs {len(references)}"
            }), 400
        
        # 执行批量评估
        results = evaluator.batch_score(
            sources=sources,
            translations=translations,
            references=references,
            mqm_scores=mqm_scores if mqm_scores else None
        )
        
        # 转换为字典列表
        scores_list = []
        for score in results:
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
        
        return jsonify({
            "success": True,
            "count": len(scores_list),
            "scores": scores_list
        })
        
    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"批量评估错误: {error_msg}")
        print(traceback_str)
        
        return jsonify({
            "success": False,
            "error": error_msg,
            "traceback": traceback_str if app.debug else None
        }), 500


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="翻译评估API服务器")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5001, help="监听端口 (默认: 5001)")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--use-bleurt", action="store_true", help="启用BLEURT评估器")
    
    args = parser.parse_args()
    
    # 初始化评估器（传递use_bleurt参数）
    init_evaluator(use_bleurt=args.use_bleurt)
    
    print(f"\n🚀 启动API服务器...")
    print(f"   地址: http://{args.host}:{args.port}")
    print(f"   调试模式: {args.debug}")
    print(f"\n📖 API文档: http://{args.host}:{args.port}/")
    print(f"💚 健康检查: http://{args.host}:{args.port}/health")
    print(f"📊 评估接口: http://{args.host}:{args.port}/eval")
    print(f"📦 批量评估: http://{args.host}:{args.port}/eval/batch")
    print("\n按 Ctrl+C 停止服务器\n")
    
    app.run(host=args.host, port=args.port, debug=args.debug)

