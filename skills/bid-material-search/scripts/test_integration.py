#!/usr/bin/env python3
"""MaterialHub 集成测试脚本

快速验证 bid-material-search 升级后的功能。
"""

import getpass
import os
import sys
import time
from pathlib import Path

import requests

# 全局认证凭据
username = None
password = None


def test_materialhub_connection():
    """测试 MaterialHub API 连接"""
    print("=== 测试 MaterialHub API 连接 ===")

    # 测试内部地址
    internal_url = os.getenv("MATERIALHUB_INTERNAL_URL", "http://localhost:8201")
    try:
        resp = requests.get(f"{internal_url}/health", timeout=5)
        if resp.status_code == 200:
            print(f"✅ 内部地址可访问: {internal_url}")
            return internal_url
        else:
            print(f"❌ 内部地址返回错误: {resp.status_code}")
    except Exception as e:
        print(f"❌ 内部地址连接失败: {e}")

    # 测试外部地址
    external_url = os.getenv("MATERIALHUB_EXTERNAL_URL", "http://senseflow.club:3100")
    try:
        resp = requests.get(f"{external_url}/health", timeout=5)
        if resp.status_code == 200:
            print(f"✅ 外部地址可访问: {external_url}")
            return external_url
        else:
            print(f"❌ 外部地址返回错误: {resp.status_code}")
    except Exception as e:
        print(f"❌ 外部地址连接失败: {e}")

    print("❌ 所有 MaterialHub 地址均不可用")
    return None


def test_materialhub_login(base_url):
    """测试 MaterialHub 登录"""
    print("\n=== 测试 MaterialHub 登录 ===")

    # 使用全局变量中的凭据
    try:
        resp = requests.post(
            f"{base_url}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data["token"]
            print(f"✅ 登录成功: {username}")
            print(f"   Token: {token[:20]}...")
            return token
        else:
            print(f"❌ 登录失败: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求异常: {e}")
        return None


def test_materialhub_search(base_url, token):
    """测试 MaterialHub 搜索"""
    print("\n=== 测试 MaterialHub 搜索 ===")

    try:
        resp = requests.get(
            f"{base_url}/api/materials",
            headers={"Authorization": f"Bearer {token}"},
            params={"status": "all"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            materials = data.get("results", [])
            print(f"✅ 搜索成功: 找到 {len(materials)} 个材料")
            if materials:
                print(f"   示例: {materials[0].get('title', 'N/A')}")
            return materials
        else:
            print(f"❌ 搜索失败: {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ 搜索请求异常: {e}")
        return []


def test_bid_material_search_service():
    """测试 bid-material-search 服务"""
    print("\n=== 测试 bid-material-search 服务 ===")

    service_url = "http://localhost:9000"

    # 测试健康检查
    try:
        resp = requests.get(f"{service_url}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ 服务健康检查通过")
            print(f"   状态: {data.get('status')}")
            print(f"   MaterialHub 连接: {data.get('materialhub_connected')}")
            print(f"   MaterialHub URL: {data.get('materialhub_url')}")
        else:
            print(f"❌ 健康检查失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务连接失败: {e}")
        print(f"   请确保服务已启动: uvicorn app:app --host 0.0.0.0 --port 9000")
        return False

    # 测试搜索端点
    try:
        resp = requests.get(f"{service_url}/api/search", params={"q": "营业执照"}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            print(f"✅ 搜索端点正常: 找到 {len(results)} 个结果")
            if results:
                print(f"   示例: {results[0].get('label', 'N/A')}")
        else:
            print(f"⚠️  搜索端点返回: {resp.status_code}")
    except Exception as e:
        print(f"❌ 搜索端点异常: {e}")

    return True


def _get_credentials():
    """获取认证凭据（优先环境变量，否则交互式输入）

    Returns:
        tuple: (username, password)
    """
    username = os.getenv("MATERIALHUB_USERNAME")
    password = os.getenv("MATERIALHUB_PASSWORD")

    # 如果环境变量未设置，提示用户输入
    if not username or not password:
        print("\n" + "=" * 60)
        print("MaterialHub 认证信息")
        print("=" * 60)

        if not username:
            try:
                username = input("用户名 [默认: admin]: ").strip()
                if not username:
                    username = "admin"
            except (EOFError, KeyboardInterrupt):
                print("\n用户取消输入，使用默认值: admin")
                username = "admin"

        if not password:
            try:
                password = getpass.getpass("密码: ")
                if not password:
                    print("密码为空，使用默认值")
                    password = "admin123"
            except (EOFError, KeyboardInterrupt):
                print("\n用户取消输入，使用默认值")
                password = "admin123"

        print("=" * 60 + "\n")

    return username, password


def main():
    """主测试流程"""
    print("MaterialHub 集成测试\n")
    print("环境变量:")
    print(f"  MATERIALHUB_INTERNAL_URL: {os.getenv('MATERIALHUB_INTERNAL_URL', '未设置')}")
    print(f"  MATERIALHUB_EXTERNAL_URL: {os.getenv('MATERIALHUB_EXTERNAL_URL', '未设置')}")
    username_env = os.getenv('MATERIALHUB_USERNAME')
    print(f"  MATERIALHUB_USERNAME: {username_env if username_env else '未设置（将提示输入）'}")
    print()

    # 获取认证凭据
    global username, password
    username, password = _get_credentials()

    # 1. 测试 MaterialHub 连接
    base_url = test_materialhub_connection()
    if not base_url:
        print("\n❌ MaterialHub API 不可用，测试终止")
        return 1

    # 2. 测试登录
    token = test_materialhub_login(base_url)
    if not token:
        print("\n❌ MaterialHub 登录失败，测试终止")
        return 1

    # 3. 测试搜索
    materials = test_materialhub_search(base_url, token)

    # 4. 测试 bid-material-search 服务
    if not test_bid_material_search_service():
        print("\n⚠️  bid-material-search 服务测试失败")
        return 1

    print("\n" + "=" * 50)
    print("✅ 所有测试通过！")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
