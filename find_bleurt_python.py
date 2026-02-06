#!/usr/bin/env python
"""
查找BLEURT conda环境的Python路径
"""

import os
import subprocess
import sys

def find_conda_envs():
    """查找所有conda环境"""
    envs = {}
    try:
        result = subprocess.run(
            ["conda", "info", "--envs"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    env_name = parts[0]
                    env_path = parts[-1]
                    python_path = os.path.join(env_path, "bin", "python")
                    if os.path.exists(python_path):
                        envs[env_name] = python_path
    except Exception as e:
        print(f"⚠️  无法运行conda info: {e}")
    
    return envs

def find_bleurt_env():
    """查找BLEURT相关的conda环境"""
    envs = find_conda_envs()
    
    # 查找包含bleurt的环境
    bleurt_envs = {}
    for name, path in envs.items():
        if 'bleurt' in name.lower() or 'translator_eval_bleurt' in name:
            bleurt_envs[name] = path
    
    return bleurt_envs, envs

def main():
    print("=" * 60)
    print("BLEURT Python环境查找工具")
    print("=" * 60)
    print()
    
    # 查找BLEURT环境
    bleurt_envs, all_envs = find_bleurt_env()
    
    if bleurt_envs:
        print("✅ 找到BLEURT相关环境:")
        for name, path in bleurt_envs.items():
            print(f"   环境名: {name}")
            print(f"   Python路径: {path}")
            print(f"   路径存在: {'✅' if os.path.exists(path) else '❌'}")
            print()
        
        # 推荐使用第一个找到的环境
        first_name = list(bleurt_envs.keys())[0]
        first_path = bleurt_envs[first_name]
        print("=" * 60)
        print("推荐配置:")
        print("=" * 60)
        print(f"export BLEURT_PYTHON_ENV={first_path}")
        print()
    else:
        print("⚠️  未找到BLEURT相关环境")
        print()
        print("所有可用的conda环境:")
        for name, path in all_envs.items():
            print(f"   {name}: {path}")
        print()
        print("如果环境不存在，请创建:")
        print("   conda create -n translator_eval_bleurt python=3.9 -y")
        print("   conda activate translator_eval_bleurt")
        print("   pip install tensorflow-cpu bleurt")
    
    # 检查当前设置的环境变量
    print()
    print("=" * 60)
    print("当前环境变量:")
    print("=" * 60)
    current_env = os.environ.get("BLEURT_PYTHON_ENV")
    if current_env:
        print(f"BLEURT_PYTHON_ENV={current_env}")
        print(f"路径存在: {'✅' if os.path.exists(current_env) else '❌'}")
        if not os.path.exists(current_env):
            print("⚠️  当前设置的路径不存在！")
    else:
        print("BLEURT_PYTHON_ENV 未设置")
    
    print()

if __name__ == "__main__":
    main()
