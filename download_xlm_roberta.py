#!/usr/bin/env python
"""
快速下载xlm-roberta-large模型
在有外网的机器上运行此脚本
"""

from huggingface_hub import snapshot_download
import os
import sys

def main():
    print("=" * 80)
    print("下载 xlm-roberta-large 模型")
    print("=" * 80)
    
    model_name = "xlm-roberta-large"
    output_dir = "./models"
    
    # 如果指定了输出目录
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    
    print(f"\n模型名称: {model_name}")
    print(f"输出目录: {output_dir}")
    
    try:
        print(f"\n开始下载...")
        model_path = snapshot_download(
            repo_id=model_name,
            cache_dir=output_dir,
            local_files_only=False
        )
        
        print(f"\n✅ 下载成功！")
        print(f"模型路径: {model_path}")
        print(f"\n💡 下一步:")
        print(f"1. 将模型目录传输到服务器:")
        print(f"   scp -r {model_path} root@server:/root/.cache/huggingface/hub/")
        print(f"\n2. 或者传输整个models目录:")
        print(f"   scp -r {output_dir} root@server:/root/.cache/huggingface/")
        
        return model_path
        
    except ImportError:
        print("\n❌ 请先安装 huggingface_hub:")
        print("   pip install huggingface_hub")
        return None
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
