"""
COMET (Crosslingual Optimized Metric for Evaluation of Translation)
基于神经网络的翻译质量评估模型
"""

from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class COMETScorer:
    """COMET质量评估模型"""
    
    def __init__(self, model_name: str = "Unbabel/wmt22-comet-da"):
        """
        初始化COMET模型
        
        Args:
            model_name: COMET模型名称或本地路径
                - 模型名称（自动下载）:
                  - "Unbabel/wmt22-comet-da" (推荐，有参考翻译)
                  - "Unbabel/wmt22-cometkiwi-da" (无参考翻译)
                  - "Unbabel/XCOMET-XL" (最新，最强)
                - 本地路径（手动下载的模型）:
                  - "/path/to/comet/model" (模型目录路径)
                  - "/home/user/.cache/comet/wmt22-comet-da" (COMET默认缓存路径)
        """
        self.model_name = model_name
        self.model = None
        self._initialized = False
    
    def initialize(self):
        """延迟初始化模型（避免启动时加载）"""
        if self._initialized:
            return True
        
        try:
            from comet import download_model, load_from_checkpoint
            import os
            from pathlib import Path
            
            # 设置HuggingFace离线模式（如果无法访问外网）
            # 如果环境变量未设置，尝试设置离线模式
            if os.environ.get("HF_HUB_OFFLINE") != "1":
                # 检查HF_HOME是否存在，如果存在且包含模型，设置为离线模式
                hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
                xlm_model_path = os.path.join(hf_home, "hub", "models--xlm-roberta-large")
                if os.path.exists(xlm_model_path):
                    # 如果模型存在，设置为离线模式
                    os.environ["HF_HUB_OFFLINE"] = "1"
                    os.environ["TRANSFORMERS_OFFLINE"] = "1"
                    print(f"🔧 检测到本地HuggingFace模型，已启用离线模式")
                else:
                    print(f"⚠️  未找到本地xlm-roberta-large模型，将尝试在线下载")
                    print(f"   提示: 如果无法访问外网，请下载模型到: {xlm_model_path}")
            
            # 检查是否是本地路径（以/开头或包含路径分隔符，且路径存在）
            model_input = self.model_name
            is_local_path = False
            
            print(f"🔍 [DEBUG] COMET模型输入: {model_input}")
            print(f"🔍 [DEBUG] 路径分隔符检查: '{os.path.sep}' in '{model_input}' = {os.path.sep in model_input}")
            print(f"🔍 [DEBUG] 绝对路径检查: starts with '/' = {model_input.startswith('/')}")
            print(f"🔍 [DEBUG] 相对路径检查: starts with '.' = {model_input.startswith('.')}")
            
            # 判断是否为本地路径
            if os.path.sep in model_input or model_input.startswith('/') or model_input.startswith('.'):
                # 展开用户目录（~）
                if model_input.startswith('~'):
                    model_input = os.path.expanduser(model_input)
                    print(f"🔍 [DEBUG] 展开用户目录后: {model_input}")
                
                # 转换为绝对路径
                if not os.path.isabs(model_input):
                    model_input = os.path.abspath(model_input)
                    print(f"🔍 [DEBUG] 转换为绝对路径: {model_input}")
                
                # 检查路径是否存在
                print(f"🔍 [DEBUG] 检查路径是否存在: {model_input}")
                print(f"🔍 [DEBUG] os.path.exists: {os.path.exists(model_input)}")
                
                if os.path.exists(model_input):
                    if os.path.isdir(model_input):
                        is_local_path = True
                        print(f"✅ 检测到本地模型目录: {model_input}")
                    elif os.path.isfile(model_input):
                        # 如果是文件，尝试使用父目录
                        model_input = os.path.dirname(model_input)
                        if os.path.exists(model_input):
                            is_local_path = True
                            print(f"✅ 检测到本地模型文件，使用目录: {model_input}")
                    else:
                        print(f"⚠️  路径存在但不是目录也不是文件: {model_input}")
                else:
                    print(f"⚠️  路径不存在: {model_input}")
                    print(f"   当前工作目录: {os.getcwd()}")
            
            # 如果是本地路径，尝试加载
            if is_local_path:
                # 尝试多个可能的checkpoint路径
                checkpoint_paths_to_try = [model_input]
                
                # 如果是一个目录，尝试查找checkpoint文件
                if os.path.isdir(model_input):
                    # 1. 优先检查checkpoints子目录中的checkpoint文件
                    checkpoints_dir = os.path.join(model_input, "checkpoints")
                    if os.path.exists(checkpoints_dir) and os.path.isdir(checkpoints_dir):
                        # 查找checkpoints目录中的文件
                        try:
                            checkpoint_files = os.listdir(checkpoints_dir)
                            # 优先查找常见的checkpoint文件（.ckpt文件优先）
                            ckpt_files = []
                            other_files = []
                            for f in checkpoint_files:
                                f_path = os.path.join(checkpoints_dir, f)
                                f_lower = f.lower()
                                # 查找checkpoint相关的文件
                                if any(keyword in f_lower for keyword in [".ckpt", ".pt", ".pth", ".bin"]):
                                    if f_lower.endswith(('.ckpt', '.pt', '.pth', '.bin')):
                                        ckpt_files.append(f_path)
                                    else:
                                        other_files.append(f_path)
                                elif os.path.isdir(f_path):
                                    # 如果是目录，也尝试
                                    other_files.append(f_path)
                            
                            # 优先使用.ckpt文件
                            checkpoint_paths_to_try = ckpt_files + other_files
                            # 也尝试整个checkpoints目录（作为备选）
                            if checkpoints_dir not in checkpoint_paths_to_try:
                                checkpoint_paths_to_try.append(checkpoints_dir)
                        except Exception as e:
                            print(f"🔍 [DEBUG] 无法读取checkpoints目录: {e}")
                    
                    # 2. 检查根目录下的checkpoint文件
                    try:
                        root_files = os.listdir(model_input)
                        for f in root_files:
                            f_path = os.path.join(model_input, f)
                            f_lower = f.lower()
                            if any(keyword in f_lower for keyword in ["checkpoint", "model", ".ckpt", ".pt", ".pth", ".bin"]) and os.path.isfile(f_path):
                                if f_path not in checkpoint_paths_to_try:
                                    checkpoint_paths_to_try.append(f_path)
                    except:
                        pass
                    
                    # 3. 最后尝试整个目录（如果前面都失败）
                    if model_input not in checkpoint_paths_to_try:
                        checkpoint_paths_to_try.append(model_input)
                
                # 尝试所有可能的路径
                last_error = None
                for checkpoint_path in checkpoint_paths_to_try:
                    try:
                        print(f"📦 正在尝试从路径加载COMET模型: {checkpoint_path}...")
                        self.model = load_from_checkpoint(checkpoint_path)
                        self._initialized = True
                        self.model_name = checkpoint_path  # 更新实际使用的模型路径
                        print(f"✓ COMET模型加载成功 (本地路径): {checkpoint_path}")
                        return True
                    except Exception as e:
                        last_error = e
                        print(f"🔍 [DEBUG] 路径 {checkpoint_path} 加载失败: {str(e)[:100]}")
                        continue
                
                # 所有路径都失败了
                print(f"❌ 从本地路径加载COMET模型失败")
                print(f"   尝试的路径:")
                for path in checkpoint_paths_to_try:
                    print(f"     - {path}")
                print(f"   最后错误: {last_error}")
                print(f"   提示: COMET模型路径应该是包含checkpoint文件的目录或文件")
                print(f"   请检查模型是否正确下载，或查看COMET文档了解正确的模型格式")
                import traceback
                traceback.print_exc()
                return False
            
            # 如果不是本地路径，尝试下载或使用模型名称
            # 尝试的模型名称列表（按优先级排序）
            model_candidates = [
                self.model_name,  # 用户指定的模型
                "wmt22-comet-da",  # 不带Unbabel前缀
                "Unbabel/wmt22-comet-da",  # 完整名称
                "wmt21-comet-da",  # 备选模型
                "Unbabel/wmt21-comet-da",  # 备选模型完整名称
            ]
            
            # 去重但保持顺序
            seen = set()
            unique_candidates = []
            for model in model_candidates:
                if model not in seen:
                    seen.add(model)
                    unique_candidates.append(model)
            
            last_error = None
            for model_name in unique_candidates:
                try:
                    print(f"正在尝试加载COMET模型: {model_name}...")
                    
                    # 方法1: 尝试使用download_model
                    try:
                        model_path = download_model(model_name)
                        print(f"模型下载成功: {model_path}")
                    except Exception as download_error:
                        # 如果download_model失败，尝试直接使用模型名称加载
                        print(f"download_model失败，尝试直接加载: {download_error}")
                        # 某些版本的COMET可以直接使用模型名称
                        try:
                            self.model = load_from_checkpoint(model_name)
                            self._initialized = True
                            self.model_name = model_name  # 更新实际使用的模型名称
                            print(f"✓ COMET模型加载成功 (直接加载): {model_name}")
                            return True
                        except:
                            # 如果直接加载也失败，继续尝试下一个模型
                            raise download_error
                    
                    # 方法2: 使用下载的路径加载
                    print(f"正在从检查点加载模型: {model_path}...")
                    self.model = load_from_checkpoint(model_path)
                    
                    self._initialized = True
                    self.model_name = model_name  # 更新实际使用的模型名称
                    print(f"✓ COMET模型加载成功: {model_name}")
                    return True
                    
                except Exception as e:
                    last_error = e
                    print(f"⚠️  模型 {model_name} 加载失败: {e}")
                    continue
            
            # 所有模型都失败了
            print(f"❌ 所有COMET模型加载尝试均失败")
            print(f"   最后错误: {last_error}")
            print(f"   提示1: 如果是网络问题，可以手动下载模型后使用本地路径")
            print(f"   提示2: 请检查COMET库版本，可能需要更新: pip install --upgrade unbabel-comet")
            print(f"   提示3: 使用本地模型路径格式: /path/to/comet/model")
            return False
            
        except ImportError:
            print("❌ 请安装COMET: pip install unbabel-comet")
            return False
        except Exception as e:
            print(f"❌ COMET初始化异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def score(
        self,
        sources: List[str],
        translations: List[str],
        references: Optional[List[str]] = None
    ) -> Dict:
        """
        计算COMET分数
        
        Args:
            sources: 源文本列表
            translations: 翻译文本列表
            references: 参考翻译列表（可选，但推荐提供）
            
        Returns:
            Dict: 包含scores和system_score的字典
        """
        if not self._initialized:
            if not self.initialize():
                return {"scores": [], "system_score": 0.0, "error": "Model not initialized"}
        
        try:
            # 构建数据
            data = []
            for i in range(len(sources)):
                item = {
                    "src": sources[i],
                    "mt": translations[i]
                }
                if references and i < len(references):
                    item["ref"] = references[i]
                data.append(item)
            
            # 预测
            output = self.model.predict(data, batch_size=8, gpus=0)
            
            return {
                "scores": output.scores,  # 每个样本的分数
                "system_score": output.system_score,  # 整体分数
                "model": self.model_name
            }
            
        except Exception as e:
            return {"scores": [], "system_score": 0.0, "error": str(e)}
    
    def score_single(
        self,
        source: str,
        translation: str,
        reference: Optional[str] = None
    ) -> float:
        """
        计算单个样本的COMET分数
        
        Returns:
            float: COMET分数 (0-1)
        """
        result = self.score([source], [translation], [reference] if reference else None)
        
        if result.get("error"):
            return 0.0
        
        scores = result.get("scores", [])
        return scores[0] if scores else 0.0


class COMETKiwiScorer(COMETScorer):
    """COMET-Kiwi: 无参考翻译的QE模型"""
    
    def __init__(self):
        super().__init__(model_name="Unbabel/wmt22-cometkiwi-da")
    
    def score(self, sources: List[str], translations: List[str], references: Optional[List[str]] = None):
        """无参考翻译评估"""
        # COMET-Kiwi不需要参考翻译
        return super().score(sources, translations, references=None)

