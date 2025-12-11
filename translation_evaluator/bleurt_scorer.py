"""
BLEURT (Bilingual Evaluation Understudy with Representations from Transformers)
基于BERT的翻译质量评估模型
"""

from typing import List, Dict, Optional
import os
import sys
import zipfile
import tempfile
import warnings
warnings.filterwarnings('ignore')

# 尝试导入下载相关的库
try:
    import urllib.request
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class BLEURTScorer:
    """BLEURT质量评估模型"""
    
    def __init__(self, checkpoint: str = "BLEURT-20", auto_download: bool = True):
        """
        初始化BLEURT模型
        
        Args:
            checkpoint: BLEURT检查点路径或名称
                - "BLEURT-20" (推荐，需要先下载)
                - "BLEURT-20-D12"
                - 或本地路径，如: "./BLEURT-20" 或 "/path/to/BLEURT-20"
            auto_download: 如果检查点不存在，是否自动下载（默认True）
                需要网络连接。如果为False，将提示手动下载。
                
        注意: 如果检查点不存在且auto_download=True，将自动尝试下载。
        下载地址: https://storage.googleapis.com/bleurt-oss-21/BLEURT-20.zip
        """
        self.checkpoint = checkpoint
        self.scorer = None
        self._initialized = False
        self._auto_download = auto_download
    
    def _download_checkpoint(self, checkpoint_name: str, download_dir: str = ".") -> Optional[str]:
        """
        自动下载BLEURT检查点
        
        Args:
            checkpoint_name: 检查点名称，如 "BLEURT-20"
            download_dir: 下载目录
            
        Returns:
            解压后的检查点路径，如果失败返回None
        """
        # 已知的检查点下载URL
        download_urls = {
            "BLEURT-20": "https://storage.googleapis.com/bleurt-oss-21/BLEURT-20.zip",
            "BLEURT-20-D12": "https://storage.googleapis.com/bleurt-oss-21/BLEURT-20-D12.zip"
        }
        
        if checkpoint_name not in download_urls:
            print(f"⚠️  未知的检查点名称: {checkpoint_name}")
            print(f"   支持的检查点: {', '.join(download_urls.keys())}")
            return None
        
        url = download_urls[checkpoint_name]
        zip_filename = f"{checkpoint_name}.zip"
        zip_path = os.path.join(download_dir, zip_filename)
        extract_path = os.path.join(download_dir, checkpoint_name)
        
        # 如果已经存在，直接返回
        if os.path.exists(extract_path):
            print(f"✓ 检查点已存在: {extract_path}")
            return extract_path
        
        print(f"📥 正在下载 {checkpoint_name}...")
        print(f"   下载地址: {url}")
        
        try:
            # 优先使用requests（如果可用），否则使用urllib
            if HAS_REQUESTS:
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                
                with open(zip_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                sys.stdout.write(f"\r   进度: {percent:.1f}% ({downloaded}/{total_size} bytes)")
                                sys.stdout.flush()
                print()  # 换行
            elif HAS_URLLIB:
                def show_progress(block_num, block_size, total_size):
                    if total_size > 0:
                        percent = min(100, (block_num * block_size / total_size) * 100)
                        sys.stdout.write(f"\r   进度: {percent:.1f}%")
                        sys.stdout.flush()
                
                urllib.request.urlretrieve(url, zip_path, reporthook=show_progress)
                print()  # 换行
            else:
                print("❌ 无法下载: 需要安装 requests 或 urllib")
                return None
            
            print(f"✓ 下载完成: {zip_path}")
            
            # 解压文件
            print(f"📦 正在解压 {zip_filename}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(download_dir)
            
            # 删除zip文件
            try:
                os.remove(zip_path)
            except:
                pass  # 如果删除失败，不影响使用
            
            if os.path.exists(extract_path):
                print(f"✓ 解压完成: {extract_path}")
                return extract_path
            else:
                print(f"❌ 解压失败: 未找到 {extract_path}")
                return None
                
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            # 清理可能的部分下载文件
            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except:
                    pass
            return None
    
    def initialize(self):
        """延迟初始化模型"""
        if self._initialized:
            return True
        
        try:
            # 先检查 TensorFlow（BLEURT 的依赖）
            try:
                import tensorflow
            except ImportError:
                print("❌ BLEURT需要TensorFlow，但未安装")
                print("   请安装TensorFlow: pip install tensorflow")
                print("   或使用CPU版本: pip install tensorflow-cpu")
                return False
            
            from bleurt import score as bleurt_score
            
            # 检查检查点是否存在
            checkpoint_path = self.checkpoint
            if not os.path.isabs(checkpoint_path) and not os.path.exists(checkpoint_path):
                # 尝试自动下载
                if self._auto_download:
                    print(f"⚠️  BLEURT模型检查点未找到: {self.checkpoint}")
                    print("   正在尝试自动下载...")
                    downloaded_path = self._download_checkpoint(self.checkpoint)
                    if downloaded_path:
                        checkpoint_path = downloaded_path
                    else:
                        print("\n❌ 自动下载失败，请手动下载:")
                        print(f"   下载地址: https://storage.googleapis.com/bleurt-oss-21/{self.checkpoint}.zip")
                        print(f"   解压后使用完整路径初始化，例如:")
                        print(f"      BLEURTScorer(checkpoint='./{self.checkpoint}')")
                        print("\n   更多信息: https://github.com/google-research/bleurt")
                        return False
                else:
                    # 不自动下载，提供手动下载说明
                    print(f"❌ BLEURT模型检查点未找到: {self.checkpoint}")
                    print("\n📥 请手动下载BLEURT模型:")
                    print(f"   1. 下载地址: https://storage.googleapis.com/bleurt-oss-21/{self.checkpoint}.zip")
                    print(f"   2. 解压到当前目录或指定路径")
                    print(f"   3. 使用完整路径初始化，例如:")
                    print(f"      BLEURTScorer(checkpoint='./{self.checkpoint}')")
                    print(f"   或使用命令行下载 (Linux/Mac):")
                    print(f"      wget https://storage.googleapis.com/bleurt-oss-21/{self.checkpoint}.zip")
                    print(f"      unzip {self.checkpoint}.zip")
                    print(f"   或使用 PowerShell (Windows):")
                    print(f"      Invoke-WebRequest -Uri https://storage.googleapis.com/bleurt-oss-21/{self.checkpoint}.zip -OutFile {self.checkpoint}.zip")
                    print(f"      Expand-Archive -Path {self.checkpoint}.zip -DestinationPath .")
                    print("\n   更多信息: https://github.com/google-research/bleurt")
                    return False
            
            print(f"正在加载BLEURT模型: {checkpoint_path}...")
            self.scorer = bleurt_score.BleurtScorer(checkpoint_path)
            
            self._initialized = True
            print(f"✓ BLEURT模型加载成功")
            return True
            
        except ImportError as e:
            if "tensorflow" in str(e).lower():
                print("❌ BLEURT需要TensorFlow，但未安装")
                print("   请安装TensorFlow: pip install tensorflow")
                print("   或使用CPU版本: pip install tensorflow-cpu")
            else:
                print("❌ 请安装BLEURT: pip install bleurt")
                print("   或参考: https://github.com/google-research/bleurt")
            return False
        except Exception as e:
            error_msg = str(e)
            if "tensorflow" in error_msg.lower() or "No module named 'tensorflow'" in error_msg:
                print("❌ BLEURT需要TensorFlow，但未安装")
                print("   请安装TensorFlow: pip install tensorflow")
                print("   或使用CPU版本: pip install tensorflow-cpu")
            elif "Could not find" in error_msg or "checkpoint" in error_msg.lower() or "not found" in error_msg.lower() or "No such file" in error_msg:
                # 如果自动下载已启用但失败，提供手动下载说明
                if self._auto_download:
                    print(f"❌ BLEURT模型检查点未找到: {self.checkpoint}")
                    print("\n📥 自动下载失败，请手动下载BLEURT模型:")
                else:
                    print(f"❌ BLEURT模型检查点未找到: {self.checkpoint}")
                    print("\n📥 请手动下载BLEURT模型:")
                print(f"   1. 下载地址: https://storage.googleapis.com/bleurt-oss-21/{self.checkpoint}.zip")
                print(f"   2. 解压到当前目录或指定路径")
                print(f"   3. 使用完整路径初始化，例如:")
                print(f"      BLEURTScorer(checkpoint='./{self.checkpoint}')")
                print(f"   或使用命令行下载 (Linux/Mac):")
                print(f"      wget https://storage.googleapis.com/bleurt-oss-21/{self.checkpoint}.zip")
                print(f"      unzip {self.checkpoint}.zip")
                print(f"   或使用 PowerShell (Windows):")
                print(f"      Invoke-WebRequest -Uri https://storage.googleapis.com/bleurt-oss-21/{self.checkpoint}.zip -OutFile {self.checkpoint}.zip")
                print(f"      Expand-Archive -Path {self.checkpoint}.zip -DestinationPath .")
                print("\n   更多信息: https://github.com/google-research/bleurt")
            else:
                print(f"❌ BLEURT模型加载失败: {e}")
            return False
    
    def score(
        self,
        translations: List[str],
        references: List[str]
    ) -> Dict:
        """
        计算BLEURT分数
        
        Args:
            translations: 翻译文本列表
            references: 参考翻译列表
            
        Returns:
            Dict: 包含scores的字典
        """
        print(f"        [BLEURT.score] 开始计算，样本数: {len(translations)}")
        
        if not self._initialized:
            print(f"        [BLEURT.score] 未初始化，尝试初始化...")
            if not self.initialize():
                print(f"        [BLEURT.score] ❌ 初始化失败")
                return {"scores": [], "error": "Model not initialized"}
        
        if not self.scorer:
            print(f"        [BLEURT.score] ❌ scorer为None")
            return {"scores": [], "error": "Scorer not initialized"}
        
        try:
            print(f"        [BLEURT.score] 调用bleurt.scorer.score...")
            scores = self.scorer.score(
                references=references,
                candidates=translations
            )
            print(f"        [BLEURT.score] ✅ 计算完成，返回{len(scores) if scores else 0}个分数")
            print(f"        [BLEURT.score] 分数值: {scores[:3] if scores and len(scores) > 3 else scores}")
            
            return {
                "scores": scores,
                "mean_score": sum(scores) / len(scores) if scores else 0.0,
                "model": self.checkpoint
            }
            
        except Exception as e:
            print(f"        [BLEURT.score] ❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            return {"scores": [], "error": str(e)}
    
    def score_single(self, translation: str, reference: str) -> float:
        """
        计算单个样本的BLEURT分数
        
        Returns:
            float: BLEURT分数
        """
        print(f"      [BLEURT] 调用score_single")
        print(f"      [BLEURT] 初始化状态: {self._initialized}")
        print(f"      [BLEURT] scorer存在: {self.scorer is not None}")
        
        if not self._initialized:
            print(f"      [BLEURT] 评估器未初始化，尝试初始化...")
            if not self.initialize():
                print(f"      [BLEURT] ❌ 初始化失败")
                return 0.0
        
        if not self.scorer:
            print(f"      [BLEURT] ❌ scorer为None")
            return 0.0
        
        try:
            print(f"      [BLEURT] 调用score方法...")
            result = self.score([translation], [reference])
            
            if result.get("error"):
                print(f"      [BLEURT] ❌ 计算返回错误: {result.get('error')}")
                return 0.0
            
            scores = result.get("scores", [])
            if not scores:
                print(f"      [BLEURT] ⚠️  返回的scores为空")
                return 0.0
            
            final_score = scores[0] if scores else 0.0
            print(f"      [BLEURT] ✅ 计算成功，分数: {final_score:.4f}")
            return final_score
        except Exception as e:
            print(f"      [BLEURT] ❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            return 0.0

