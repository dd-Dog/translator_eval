#!/usr/bin/env python
"""
下载HuggingFace模型脚本
用于在能访问外网的机器上下载模型，然后传输到服务器
"""

import os
import sys
from huggingface_hub import snapshot_download

def download_xlm_roberta_large(cache_dir=None):
    """
    下载xlm-roberta-large模型
    
    Args:
        cache_dir: 缓存目录，默认为~/.cache/huggingface/
    """
    model_name = "xlm-roberta-large"
    
    print(f"=" * 80)
    print(f"下载HuggingFace模型: {model_name}")
    print(f"=" * 80)
    
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        print(f"使用自定义缓存目录: {cache_dir}")
    else:
        cache_dir = os.path.expanduser("~/.cache/huggingface/")
        print(f"使用默认缓存目录: {cache_dir}")
    
    try:
        print(f"\n开始下载模型...")
        model_path = snapshot_download(
            repo_id=model_name,
            cache_dir=cache_dir,
            local_files_only=False
        )
        
        print(f"\n✅ 模型下载成功！")
        print(f"模型路径: {model_path}")
        print(f"\n💡 下一步:")
        print(f"1. 将整个模型目录复制到服务器:")
        print(f"   scp -r {model_path} user@server:/path/to/huggingface/models/")
        print(f"\n2. 在服务器上设置环境变量:")
        print(f"   export HF_HOME=/path/to/huggingface")
        print(f"   或者")
        print(f"   export TRANSFORMERS_CACHE=/path/to/huggingface/hub")
        
        return model_path
        
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="下载HuggingFace模型")
    parser.add_argument("--cache-dir", type=str, default=None,
                       help="缓存目录（默认: ~/.cache/huggingface/）")
    parser.add_argument("--output-dir", type=str, default=None,
                       help="输出目录（如果指定，会复制到该目录）")
    
    args = parser.parse_args()
    
    model_path = download_xlm_roberta_large(cache_dir=args.cache_dir)
    
    if model_path and args.output_dir:
        import shutil
        print(f"\n复制模型到输出目录: {args.output_dir}")
        os.makedirs(args.output_dir, exist_ok=True)
        output_path = os.path.join(args.output_dir, "xlm-roberta-large")
        if os.path.exists(output_path):
            shutil.rmtree(output_path)
        shutil.copytree(model_path, output_path)
        print(f"✅ 模型已复制到: {output_path}")
