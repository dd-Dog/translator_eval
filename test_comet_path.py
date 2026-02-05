#!/usr/bin/env python
"""
测试COMET模型路径配置
用于验证环境变量和路径是否正确
"""

import os
import sys

def test_comet_path():
    """测试COMET模型路径"""
    print("=" * 80)
    print("COMET模型路径测试")
    print("=" * 80)
    
    # 1. 检查环境变量
    comet_path = os.environ.get("COMET_MODEL_PATH")
    print(f"\n1. 环境变量 COMET_MODEL_PATH:")
    if comet_path:
        print(f"   ✅ 已设置: {comet_path}")
    else:
        print(f"   ❌ 未设置")
        print(f"   提示: export COMET_MODEL_PATH=/path/to/comet/model")
        return False
    
    # 2. 检查路径是否存在
    print(f"\n2. 路径存在性检查:")
    if os.path.exists(comet_path):
        print(f"   ✅ 路径存在: {comet_path}")
    else:
        print(f"   ❌ 路径不存在: {comet_path}")
        print(f"   当前工作目录: {os.getcwd()}")
        return False
    
    # 3. 检查是否为目录
    print(f"\n3. 路径类型检查:")
    if os.path.isdir(comet_path):
        print(f"   ✅ 是目录")
    elif os.path.isfile(comet_path):
        print(f"   ⚠️  是文件，将使用父目录")
        comet_path = os.path.dirname(comet_path)
    else:
        print(f"   ❌ 既不是目录也不是文件")
        return False
    
    # 4. 列出目录内容
    print(f"\n4. 目录内容:")
    try:
        files = os.listdir(comet_path)
        print(f"   文件/目录数量: {len(files)}")
        print(f"   前10个文件/目录:")
        for i, f in enumerate(files[:10]):
            file_path = os.path.join(comet_path, f)
            file_type = "目录" if os.path.isdir(file_path) else "文件"
            print(f"     {i+1}. {f} ({file_type})")
        if len(files) > 10:
            print(f"     ... 还有 {len(files) - 10} 个文件/目录")
    except Exception as e:
        print(f"   ❌ 无法读取目录: {e}")
        return False
    
    # 5. 检查关键文件和checkpoints目录
    print(f"\n5. 关键文件检查:")
    key_files = ["checkpoint", "pytorch_model.bin", "config.json", "model.ckpt"]
    found_files = []
    for key_file in key_files:
        key_path = os.path.join(comet_path, key_file)
        if os.path.exists(key_path):
            found_files.append(key_file)
            print(f"   ✅ 找到: {key_file}")
        else:
            # 检查是否有类似的文件
            matching = [f for f in files if key_file.lower() in f.lower()]
            if matching:
                print(f"   ⚠️  未找到 {key_file}，但找到类似文件: {matching[0]}")
    
    # 检查checkpoints目录
    checkpoints_dir = os.path.join(comet_path, "checkpoints")
    if os.path.exists(checkpoints_dir) and os.path.isdir(checkpoints_dir):
        print(f"\n5.1. 检查checkpoints目录:")
        try:
            checkpoint_files = os.listdir(checkpoints_dir)
            print(f"   checkpoints目录内容 ({len(checkpoint_files)} 个文件/目录):")
            for f in checkpoint_files[:10]:
                f_path = os.path.join(checkpoints_dir, f)
                f_type = "目录" if os.path.isdir(f_path) else "文件"
                print(f"     - {f} ({f_type})")
            
            # 查找可能的checkpoint文件
            checkpoint_candidates = []
            for f in checkpoint_files:
                f_lower = f.lower()
                if any(keyword in f_lower for keyword in ["checkpoint", "model", ".ckpt", ".pt", ".pth", ".bin"]):
                    checkpoint_candidates.append(f)
            
            if checkpoint_candidates:
                print(f"\n   可能的checkpoint文件:")
                for candidate in checkpoint_candidates:
                    print(f"     ✅ {candidate}")
                    found_files.append(f"checkpoints/{candidate}")
        except Exception as e:
            print(f"   ❌ 无法读取checkpoints目录: {e}")
    
    if not found_files:
        print(f"   ⚠️  未找到常见的关键文件，但目录存在，将尝试加载")
    
    # 6. 检查HuggingFace模型
    print(f"\n6. HuggingFace模型检查:")
    hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
    hf_cache = os.path.join(hf_home, "hub")
    xlm_model_path = os.path.join(hf_cache, "models--xlm-roberta-large")
    
    print(f"   HF_HOME: {hf_home}")
    print(f"   HuggingFace缓存: {hf_cache}")
    print(f"   xlm-roberta-large路径: {xlm_model_path}")
    
    if os.path.exists(xlm_model_path):
        print(f"   ✅ xlm-roberta-large模型目录存在")
        # 查找snapshots目录
        snapshots_dir = os.path.join(xlm_model_path, "snapshots")
        if os.path.exists(snapshots_dir):
            snapshots = os.listdir(snapshots_dir)
            if snapshots:
                snapshot_path = os.path.join(snapshots_dir, snapshots[0])
                tokenizer_config = os.path.join(snapshot_path, "tokenizer_config.json")
                if os.path.exists(tokenizer_config):
                    print(f"   ✅ 找到tokenizer配置文件: {tokenizer_config}")
                else:
                    print(f"   ⚠️  未找到tokenizer_config.json")
                    print(f"   快照路径: {snapshot_path}")
            else:
                print(f"   ⚠️  snapshots目录为空")
        else:
            print(f"   ⚠️  未找到snapshots目录")
    else:
        print(f"   ❌ xlm-roberta-large模型目录不存在")
        print(f"   💡 需要下载模型，请参考COMET_离线部署指南.md")
    
    # 7. 尝试导入COMET
    print(f"\n7. COMET库检查:")
    try:
        from comet import load_from_checkpoint
        print(f"   ✅ COMET库已安装")
    except ImportError:
        print(f"   ❌ COMET库未安装: pip install unbabel-comet")
        return False
    
    # 8. 设置离线模式
    print(f"\n8. 设置HuggingFace离线模式:")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    print(f"   ✅ 已设置离线模式")
    
    # 9. 尝试加载模型
    print(f"\n9. 模型加载测试:")
    
    # 尝试多个可能的路径
    test_paths = [
        comet_path,  # 原始路径
        os.path.join(comet_path, "checkpoints"),  # checkpoints目录
    ]
    
    # 如果checkpoints目录存在，尝试其中的文件
    checkpoints_dir = os.path.join(comet_path, "checkpoints")
    if os.path.exists(checkpoints_dir):
        try:
            checkpoint_files = os.listdir(checkpoints_dir)
            # 查找可能的checkpoint文件
            for f in checkpoint_files:
                f_path = os.path.join(checkpoints_dir, f)
                if os.path.isfile(f_path):
                    f_lower = f.lower()
                    if any(keyword in f_lower for keyword in ["checkpoint", "model", ".ckpt", ".pt", ".pth", ".bin"]):
                        test_paths.append(f_path)
                elif os.path.isdir(f_path):
                    # 如果是目录，也尝试
                    test_paths.append(f_path)
        except:
            pass
    
    success = False
    for test_path in test_paths:
        try:
            print(f"   正在尝试加载模型: {test_path}...")
            model = load_from_checkpoint(test_path)
            print(f"   ✅ 模型加载成功！使用路径: {test_path}")
            print(f"\n   💡 正确的COMET模型路径是: {test_path}")
            success = True
            break
        except Exception as e:
            print(f"   ❌ 失败: {str(e)[:100]}")
            continue
    
    if not success:
        print(f"\n   ❌ 所有路径尝试均失败")
        print(f"   💡 提示: COMET模型路径应该是包含checkpoint文件的目录或文件")
        print(f"   💡 请检查模型是否正确下载，或查看COMET文档了解正确的模型格式")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_comet_path()
    print("\n" + "=" * 80)
    if success:
        print("✅ 所有测试通过！COMET模型路径配置正确。")
    else:
        print("❌ 测试失败，请检查上述问题。")
    print("=" * 80)
    sys.exit(0 if success else 1)
