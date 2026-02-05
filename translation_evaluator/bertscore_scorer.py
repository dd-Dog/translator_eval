"""
BERTScore
基于BERT embedding的语义相似度评估
"""

from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')


class BERTScoreScorer:
    """BERTScore评估模型"""
    
    def __init__(self, lang: str = None, model_type: str = None):
        """
        初始化BERTScore
        
        Args:
            lang: 语言代码 (zh, en, ja等)。如果为None，使用多语言模型自动检测
            model_type: BERT模型类型（可选）
                - 中文: "bert-base-chinese"
                - 多语言: "bert-base-multilingual-cased" (推荐，支持更多语言)
                - 如果未指定且lang为None，默认使用多语言模型
        """
        self.lang = lang
        # 如果未指定model_type且lang为None，使用多语言模型
        if model_type is None and lang is None:
            model_type = "bert-base-multilingual-cased"
        self.model_type = model_type
        self._initialized = False
    
    def initialize(self):
        """检查依赖"""
        if self._initialized:
            return True
        
        try:
            import bert_score
            import os
            
            # 设置HuggingFace离线模式（如果无法访问外网）
            # 检查环境变量
            if os.environ.get("HF_HUB_OFFLINE") != "1":
                # 检查HF_HOME是否存在，如果存在且包含模型，设置为离线模式
                hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
                # 检查是否有bert-base-multilingual-cased模型
                model_path = os.path.join(hf_home, "hub", "models--bert-base-multilingual-cased")
                if os.path.exists(model_path):
                    # 如果模型存在，设置为离线模式
                    os.environ["HF_HUB_OFFLINE"] = "1"
                    os.environ["TRANSFORMERS_OFFLINE"] = "1"
                    print(f"🔧 检测到本地BERT模型，已启用离线模式")
                else:
                    print(f"⚠️  未找到本地bert-base-multilingual-cased模型")
                    print(f"   模型路径: {model_path}")
                    print(f"   提示: 如果无法访问外网，需要手动下载模型")
            
            self._initialized = True
            print(f"✓ BERTScore已就绪")
            return True
        except ImportError:
            print("❌ 请安装BERTScore: pip install bert-score")
            return False
    
    def score(
        self,
        translations: List[str],
        references: List[str]
    ) -> Dict:
        """
        计算BERTScore
        
        Args:
            translations: 翻译文本列表
            references: 参考翻译列表
            
        Returns:
            Dict: 包含P, R, F1的字典
        """
        if not self._initialized:
            if not self.initialize():
                return {"P": [], "R": [], "F1": [], "error": "Not initialized"}
        
        try:
            from bert_score import score
            import os
            
            # 构建参数
            score_kwargs = {
                "verbose": False
            }
            
            # 如果指定了model_type，使用它（优先级更高）
            if self.model_type:
                score_kwargs["model_type"] = self.model_type
            elif self.lang:
                score_kwargs["lang"] = self.lang
            else:
                # 默认使用多语言模型
                score_kwargs["model_type"] = "bert-base-multilingual-cased"
            
            # 设置离线模式（如果环境变量已设置）
            if os.environ.get("HF_HUB_OFFLINE") == "1":
                # bert_score内部使用transformers，离线模式会自动生效
                print(f"      🔍 [DEBUG] 使用离线模式")
            
            print(f"      🔍 [DEBUG] 调用bert_score.score，参数: {score_kwargs}")
            
            # 尝试加载模型
            try:
                P, R, F1 = score(
                    translations,
                    references,
                    **score_kwargs
                )
            except Exception as network_error:
                error_msg = str(network_error)
                # 如果是网络错误，尝试使用本地模型
                if "huggingface.co" in error_msg or "connection" in error_msg.lower() or "offline" in error_msg.lower():
                    print(f"      ⚠️  网络错误，尝试使用本地模型...")
                    # 检查本地模型路径
                    hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
                    model_name = score_kwargs.get("model_type", score_kwargs.get("lang", "bert-base-multilingual-cased"))
                    
                    # 尝试强制使用本地文件
                    os.environ["HF_HUB_OFFLINE"] = "1"
                    os.environ["TRANSFORMERS_OFFLINE"] = "1"
                    
                    try:
                        P, R, F1 = score(
                            translations,
                            references,
                            **score_kwargs
                        )
                        print(f"      ✅ 使用本地模型成功")
                    except Exception as local_error:
                        print(f"      ❌ 本地模型也失败: {local_error}")
                        raise local_error
                else:
                    raise network_error
            
            print(f"      🔍 [DEBUG] bert_score.score返回:")
            print(f"         P类型: {type(P)}, 形状: {P.shape if hasattr(P, 'shape') else 'N/A'}")
            print(f"         R类型: {type(R)}, 形状: {R.shape if hasattr(R, 'shape') else 'N/A'}")
            print(f"         F1类型: {type(F1)}, 形状: {F1.shape if hasattr(F1, 'shape') else 'N/A'}")
            print(f"         F1值: {F1}")
            
            # 转换为列表
            try:
                P_list = P.tolist() if hasattr(P, 'tolist') else list(P)
                R_list = R.tolist() if hasattr(R, 'tolist') else list(R)
                F1_list = F1.tolist() if hasattr(F1, 'tolist') else list(F1)
                mean_f1 = F1.mean().item() if hasattr(F1, 'mean') else float(sum(F1_list) / len(F1_list))
            except Exception as e:
                print(f"      ⚠️  转换tensor到list失败: {e}")
                # 尝试直接使用
                P_list = list(P) if hasattr(P, '__iter__') else [float(P)]
                R_list = list(R) if hasattr(R, '__iter__') else [float(R)]
                F1_list = list(F1) if hasattr(F1, '__iter__') else [float(F1)]
                mean_f1 = float(sum(F1_list) / len(F1_list)) if F1_list else 0.0
            
            print(f"      🔍 [DEBUG] 转换后的结果:")
            print(f"         P_list: {P_list}")
            print(f"         R_list: {R_list}")
            print(f"         F1_list: {F1_list}")
            print(f"         mean_F1: {mean_f1}")
            
            return {
                "P": P_list,  # Precision
                "R": R_list,  # Recall
                "F1": F1_list,  # F1 score
                "mean_F1": mean_f1,
                "lang": self.lang,
                "model_type": self.model_type
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"   ⚠️  BERTScore计算异常: {error_msg}")
            return {"P": [], "R": [], "F1": [], "error": error_msg}
    
    def score_single(self, translation: str, reference: str) -> float:
        """
        计算单个样本的BERTScore F1
        
        Returns:
            float: F1分数
        """
        print(f"      🔍 [DEBUG] BERTScore.score_single调用:")
        print(f"         translation长度: {len(translation)}")
        print(f"         reference长度: {len(reference)}")
        print(f"         model_type: {self.model_type}")
        print(f"         lang: {self.lang}")
        
        result = self.score([translation], [reference])
        
        if result.get("error"):
            print(f"      ❌ BERTScore错误: {result.get('error')}")
            return 0.0
        
        f1_scores = result.get("F1", [])
        print(f"      🔍 [DEBUG] BERTScore返回结果:")
        print(f"         F1 scores: {f1_scores}")
        print(f"         F1 scores类型: {type(f1_scores)}")
        print(f"         F1 scores长度: {len(f1_scores) if f1_scores else 0}")
        
        if f1_scores and len(f1_scores) > 0:
            f1_value = f1_scores[0]
            print(f"         F1值: {f1_value} (类型: {type(f1_value)})")
            # 确保是float类型
            if isinstance(f1_value, (int, float)):
                return float(f1_value)
            else:
                print(f"      ⚠️  F1值不是数字类型: {f1_value}")
                return 0.0
        else:
            print(f"      ⚠️  F1 scores为空或长度为0")
            # 尝试使用mean_F1
            mean_f1 = result.get("mean_F1")
            if mean_f1 is not None:
                print(f"      使用mean_F1: {mean_f1}")
                return float(mean_f1)
            return 0.0

