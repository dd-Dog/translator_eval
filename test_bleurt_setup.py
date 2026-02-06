#!/usr/bin/env python
"""
BLEURT设置诊断脚本
检查BLEURT子进程模式的所有配置
"""

import os
import subprocess
import sys

def check_file(path, name):
    """检查文件是否存在"""
    if os.path.exists(path):
        print(f"✅ {name}: {path}")
        return True
    else:
        print(f"❌ {name}不存在: {path}")
        return False

def check_python_env(python_env):
    """检查Python环境"""
    if not python_env:
        print("❌ BLEURT_PYTHON_ENV未设置")
        return False
    
    if not os.path.exists(python_env):
        print(f"❌ Python环境不存在: {python_env}")
        return False
    
    print(f"✅ Python环境存在: {python_env}")
    
    # 测试Python版本
    try:
        result = subprocess.run(
            [python_env, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"   Python版本: {result.stdout.strip()}")
        else:
            print(f"   ⚠️  无法获取Python版本")
    except Exception as e:
        print(f"   ⚠️  测试Python失败: {e}")
    
    # 测试bleurt是否可用
    try:
        result = subprocess.run(
            [python_env, "-c", "import bleurt; print('✅ BLEURT可用')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"   ✅ BLEURT库可用")
            if result.stdout:
                print(f"   {result.stdout.strip()}")
        else:
            print(f"   ❌ BLEURT库不可用")
            if result.stderr:
                print(f"   错误: {result.stderr.strip()}")
    except Exception as e:
        print(f"   ⚠️  测试BLEURT失败: {e}")
    
    return True

def test_worker_script(python_env, worker_script, checkpoint):
    """测试worker脚本"""
    print(f"\n🔍 测试worker脚本...")
    
    if not os.path.exists(worker_script):
        print(f"❌ Worker脚本不存在: {worker_script}")
        return False
    
    print(f"✅ Worker脚本存在: {worker_script}")
    
    # 测试worker脚本
    test_data = {
        "translations": ["Hello world"],
        "references": ["Hello world"]
    }
    
    try:
        import json
        process = subprocess.Popen(
            [python_env, worker_script, "--checkpoint", checkpoint],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        request_json = json.dumps(test_data)
        stdout, stderr = process.communicate(input=request_json, timeout=60)
        
        if process.returncode == 0:
            try:
                response = json.loads(stdout.strip())
                if response.get("error"):
                    print(f"❌ Worker返回错误: {response.get('error')}")
                    if stderr:
                        print(f"   stderr: {stderr[:500]}")
                    return False
                else:
                    scores = response.get("scores", [])
                    if scores:
                        print(f"✅ Worker测试成功，分数: {scores[0]:.4f}")
                        return True
                    else:
                        print(f"⚠️  Worker返回空分数")
                        return False
            except json.JSONDecodeError as e:
                print(f"❌ 无法解析worker响应: {e}")
                print(f"   stdout: {stdout[:500]}")
                if stderr:
                    print(f"   stderr: {stderr[:500]}")
                return False
        else:
            print(f"❌ Worker进程退出码: {process.returncode}")
            if stderr:
                print(f"   stderr: {stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Worker测试超时（60秒）")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Worker测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("BLEURT设置诊断")
    print("=" * 60)
    print()
    
    # 读取环境变量
    python_env = os.environ.get("BLEURT_PYTHON_ENV")
    worker_script = os.environ.get("BLEURT_WORKER_SCRIPT", "bleurt_worker.py")
    checkpoint = os.environ.get("BLEURT_CHECKPOINT", "BLEURT-20")
    use_subprocess = os.environ.get("BLEURT_USE_SUBPROCESS", "false").lower() == "true"
    
    print("环境变量:")
    print(f"  BLEURT_USE_SUBPROCESS: {use_subprocess}")
    print(f"  BLEURT_PYTHON_ENV: {python_env}")
    print(f"  BLEURT_WORKER_SCRIPT: {worker_script}")
    print(f"  BLEURT_CHECKPOINT: {checkpoint}")
    print()
    
    # 检查文件
    print("文件检查:")
    all_ok = True
    
    if use_subprocess:
        if not python_env:
            print("❌ BLEURT_PYTHON_ENV未设置")
            all_ok = False
        else:
            if not check_python_env(python_env):
                all_ok = False
        
        if not check_file(worker_script, "Worker脚本"):
            all_ok = False
    
    if not check_file(checkpoint, "BLEURT检查点"):
        all_ok = False
    else:
        # 检查检查点内的关键文件
        key_files = [
            "saved_model.pb",
            "bert_config.json",
            "bleurt_config.json",
            "sent_piece.model",
            "variables/variables.data-00000-of-00001"
        ]
        print("  检查点内文件:")
        for key_file in key_files:
            file_path = os.path.join(checkpoint, key_file)
            if os.path.exists(file_path):
                print(f"    ✅ {key_file}")
            else:
                print(f"    ❌ {key_file} 缺失")
                all_ok = False
    
    print()
    
    # 测试worker脚本
    if use_subprocess and python_env and all_ok:
        if test_worker_script(python_env, worker_script, checkpoint):
            print("\n✅ 所有检查通过，BLEURT应该可以正常工作")
        else:
            print("\n❌ Worker脚本测试失败")
    elif not use_subprocess:
        print("⚠️  未使用子进程模式，跳过worker测试")
    else:
        print("⚠️  跳过worker测试（配置不完整）")
    
    print()

if __name__ == "__main__":
    main()
