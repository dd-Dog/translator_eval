"""
测试API调用，模拟其他程序的调用方式
用于诊断BLEURT分数缺失问题
"""

import requests
import json

def test_api_call():
    """测试不同的API调用方式"""
    base_url = "http://localhost:5001"
    
    print("=" * 80)
    print("API调用诊断测试")
    print("=" * 80)
    
    # 测试1: 标准调用（有reference）
    print("\n测试1: 标准调用（有reference）")
    data1 = {
        "translation": "机器学习是人工智能的一个子集。",
        "reference": "机器学习是人工智能的一个子集。",
        "source": "Machine learning is a subset of AI."
    }
    try:
        response = requests.post(f"{base_url}/eval", json=data1, timeout=30)
        result = response.json()
        if result.get("success"):
            score = result.get("score", {})
            print(f"   ✅ 成功")
            print(f"   BLEURT: {score.get('bleurt', '缺失')}")
            print(f"   其他分数: BLEU={score.get('bleu', 0):.4f}, COMET={score.get('comet', 0):.4f}")
        else:
            print(f"   ❌ 失败: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 测试2: 没有source
    print("\n测试2: 没有source字段")
    data2 = {
        "translation": "机器学习是人工智能的一个子集。",
        "reference": "机器学习是人工智能的一个子集。"
    }
    try:
        response = requests.post(f"{base_url}/eval", json=data2, timeout=30)
        result = response.json()
        if result.get("success"):
            score = result.get("score", {})
            print(f"   ✅ 成功")
            print(f"   BLEURT: {score.get('bleurt', '缺失')}")
        else:
            print(f"   ❌ 失败: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 测试3: reference为空字符串
    print("\n测试3: reference为空字符串（应该失败）")
    data3 = {
        "translation": "机器学习是人工智能的一个子集。",
        "reference": "",
        "source": "Machine learning is a subset of AI."
    }
    try:
        response = requests.post(f"{base_url}/eval", json=data3, timeout=30)
        result = response.json()
        if result.get("success"):
            score = result.get("score", {})
            print(f"   ⚠️  请求成功（不应该）")
            print(f"   BLEURT: {score.get('bleurt', '缺失')}")
        else:
            print(f"   ✅ 正确拒绝: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 测试4: 检查返回的JSON结构
    print("\n测试4: 检查返回JSON结构")
    data4 = {
        "translation": "测试",
        "reference": "测试"
    }
    try:
        response = requests.post(f"{base_url}/eval", json=data4, timeout=30)
        result = response.json()
        if result.get("success"):
            score = result.get("score", {})
            print(f"   返回的字段: {list(score.keys())}")
            print(f"   BLEURT字段存在: {'bleurt' in score}")
            print(f"   BLEURT值: {score.get('bleurt', '缺失')}")
            print(f"   完整JSON:")
            print(json.dumps(score, indent=2, ensure_ascii=False))
        else:
            print(f"   ❌ 失败: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)
    print("\n如果BLEURT字段存在但值为0，可能原因:")
    print("1. reference为空或无效")
    print("2. BLEURT计算出错（查看服务器日志）")
    print("3. BLEURT评估器未正确初始化")
    print("\n如果BLEURT字段不存在，说明服务器返回格式有问题")

if __name__ == "__main__":
    test_api_call()

