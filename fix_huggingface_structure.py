#!/usr/bin/env python
"""
修复HuggingFace模型目录结构
如果模型文件在根目录，创建正确的snapshots结构
"""

import os
import sys
import shutil
import hashlib

def fix_huggingface_structure():
    """修复HuggingFace模型目录结构"""
    print("=" * 80)
    print("修复HuggingFace模型目录结构")
    print("=" * 80)
    
    # 确定模型路径
    hf_home = os.environ.get("HF_HOME", "/root/bianjb/huggingface")
    hf_cache = os.path.join(hf_home, "hub")
    xlm_model_path = os.path.join(hf_cache, "models--xlm-roberta-large")
    
    print(f"\n模型路径: {xlm_model_path}")
    
    if not os.path.exists(xlm_model_path):
        print(f"❌ 模型目录不存在: {xlm_model_path}")
        return False
    
    # 检查根目录下的文件
    root_files = os.listdir(xlm_model_path)
    print(f"\n根目录文件: {root_files}")
    
    # 检查是否有tokenizer文件
    tokenizer_files = [f for f in root_files if any(x in f.lower() for x in ['tokenizer', 'vocab', 'merges', 'sentencepiece', 'config.json'])]
    
    if not tokenizer_files:
        print(f"❌ 未找到tokenizer文件")
        return False
    
    print(f"\n找到tokenizer相关文件: {tokenizer_files}")
    
    # 检查snapshots目录
    snapshots_dir = os.path.join(xlm_model_path, "snapshots")
    
    if os.path.exists(snapshots_dir):
        snapshots = os.listdir(snapshots_dir)
        if snapshots:
            print(f"\n✅ snapshots目录已存在，包含: {snapshots}")
            snapshot_path = os.path.join(snapshots_dir, snapshots[0])
            print(f"使用现有快照: {snapshot_path}")
            return True
        else:
            print(f"\n⚠️  snapshots目录为空，将创建")
    else:
        print(f"\n⚠️  snapshots目录不存在，将创建")
    
    # 创建snapshots目录和hash
    # 使用目录名或时间戳作为hash（简化处理）
    import time
    snapshot_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    snapshot_path = os.path.join(snapshots_dir, snapshot_hash)
    
    print(f"\n创建snapshots结构...")
    os.makedirs(snapshot_path, exist_ok=True)
    
    # 移动或复制文件到snapshots目录
    print(f"\n复制文件到snapshots目录...")
    moved_count = 0
    for file in root_files:
        # 跳过特殊目录
        if file in ['.git', 'snapshots', 'refs']:
            continue
        
        src_path = os.path.join(xlm_model_path, file)
        dst_path = os.path.join(snapshot_path, file)
        
        if os.path.isfile(src_path):
            if not os.path.exists(dst_path):
                shutil.copy2(src_path, dst_path)
                print(f"  ✅ 复制: {file}")
                moved_count += 1
            else:
                print(f"  ⚠️  已存在: {file}")
        elif os.path.isdir(src_path) and file not in ['snapshots', 'refs']:
            if not os.path.exists(dst_path):
                shutil.copytree(src_path, dst_path)
                print(f"  ✅ 复制目录: {file}")
                moved_count += 1
    
    if moved_count > 0:
        print(f"\n✅ 成功复制 {moved_count} 个文件/目录到snapshots")
        print(f"快照路径: {snapshot_path}")
        return True
    else:
        print(f"\n⚠️  没有文件需要复制")
        return False

if __name__ == "__main__":
    success = fix_huggingface_structure()
    print("\n" + "=" * 80)
    if success:
        print("✅ 目录结构修复完成！")
        print("\n💡 现在可以运行:")
        print("   export HF_HUB_OFFLINE=1")
        print("   export TRANSFORMERS_OFFLINE=1")
        print("   python check_huggingface_model.py")
    else:
        print("❌ 修复失败，请检查错误信息。")
    print("=" * 80)
    sys.exit(0 if success else 1)
