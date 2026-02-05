#!/usr/bin/env python
"""
修复git下载的HuggingFace模型目录结构
将git clone下载的文件组织成HuggingFace Hub的缓存结构
"""

import os
import sys
import shutil
import hashlib

def fix_git_downloaded_model():
    """修复git下载的模型结构"""
    print("=" * 80)
    print("修复git下载的HuggingFace模型结构")
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
    print(f"\n根目录文件/目录: {root_files}")
    
    # 检查是否已经有snapshots目录
    snapshots_dir = os.path.join(xlm_model_path, "snapshots")
    if os.path.exists(snapshots_dir):
        snapshots = os.listdir(snapshots_dir)
        if snapshots:
            print(f"\n✅ snapshots目录已存在，包含: {snapshots}")
            print(f"   如果文件已正确组织，可以跳过此步骤")
            response = input("   是否继续修复？(y/n): ").strip().lower()
            if response != 'y':
                return True
    
    # 创建snapshots目录
    # 使用一个固定的hash（可以基于模型名称生成）
    # 或者使用git commit hash（如果有）
    snapshot_hash = "main"  # 对于git下载，通常使用main作为hash
    snapshot_path = os.path.join(snapshots_dir, snapshot_hash)
    
    print(f"\n创建snapshots结构...")
    print(f"快照路径: {snapshot_path}")
    
    # 如果snapshots目录不存在，创建它
    if not os.path.exists(snapshots_dir):
        os.makedirs(snapshots_dir, exist_ok=True)
        print(f"✅ 创建snapshots目录")
    
    # 如果快照目录已存在，检查是否需要移动文件
    if os.path.exists(snapshot_path):
        existing_files = os.listdir(snapshot_path)
        print(f"⚠️  快照目录已存在，包含 {len(existing_files)} 个文件")
        # 检查是否已有tokenizer文件
        has_tokenizer = any('tokenizer' in f.lower() for f in existing_files)
        if has_tokenizer:
            print(f"✅ 快照目录中已有tokenizer文件")
            return True
    
    # 创建快照目录
    os.makedirs(snapshot_path, exist_ok=True)
    
    # 需要移动的文件类型
    files_to_move = []
    dirs_to_move = []
    
    for item in root_files:
        # 跳过特殊目录和文件
        if item in ['.git', 'snapshots', 'refs', '.gitattributes', 'README.md', 'LICENSE']:
            continue
        
        item_path = os.path.join(xlm_model_path, item)
        
        if os.path.isfile(item_path):
            files_to_move.append(item)
        elif os.path.isdir(item_path):
            # 跳过.git目录
            if item != '.git':
                dirs_to_move.append(item)
    
    print(f"\n需要移动的文件: {files_to_move}")
    print(f"需要移动的目录: {dirs_to_move}")
    
    if not files_to_move and not dirs_to_move:
        print(f"\n⚠️  没有文件需要移动")
        return False
    
    # 移动文件
    moved_count = 0
    for file in files_to_move:
        src_path = os.path.join(xlm_model_path, file)
        dst_path = os.path.join(snapshot_path, file)
        
        if not os.path.exists(dst_path):
            shutil.copy2(src_path, dst_path)
            print(f"  ✅ 复制文件: {file}")
            moved_count += 1
        else:
            print(f"  ⚠️  已存在: {file}")
    
    # 移动目录
    for dir_name in dirs_to_move:
        src_path = os.path.join(xlm_model_path, dir_name)
        dst_path = os.path.join(snapshot_path, dir_name)
        
        if not os.path.exists(dst_path):
            shutil.copytree(src_path, dst_path)
            print(f"  ✅ 复制目录: {dir_name}")
            moved_count += 1
        else:
            print(f"  ⚠️  已存在: {dir_name}")
    
    if moved_count > 0:
        print(f"\n✅ 成功处理 {moved_count} 个项目")
        print(f"快照路径: {snapshot_path}")
        
        # 验证关键文件
        print(f"\n验证关键文件...")
        required_files = [
            "tokenizer_config.json",
            "tokenizer.json",
            "sentencepiece.bpe.model",
            "vocab.json",
            "merges.txt"
        ]
        
        found_count = 0
        for file in required_files:
            file_path = os.path.join(snapshot_path, file)
            if os.path.exists(file_path):
                print(f"  ✅ {file}")
                found_count += 1
            else:
                print(f"  ⚠️  {file} (未找到)")
        
        if found_count >= 3:
            print(f"\n✅ 找到 {found_count}/{len(required_files)} 个关键文件，应该可以工作")
            return True
        else:
            print(f"\n⚠️  只找到 {found_count}/{len(required_files)} 个关键文件")
            return False
    else:
        print(f"\n⚠️  没有文件被移动")
        return False

if __name__ == "__main__":
    success = fix_git_downloaded_model()
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
