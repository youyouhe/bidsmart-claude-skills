#!/usr/bin/env python3
"""演示认证凭据获取逻辑

展示交互式输入和环境变量优先级。
"""

import getpass
import os


def get_credentials():
    """获取认证凭据（优先环境变量，否则交互式输入）"""
    username = os.getenv("MATERIALHUB_USERNAME")
    password = os.getenv("MATERIALHUB_PASSWORD")

    # 显示当前环境变量状态
    print("\n当前环境变量状态:")
    print(f"  MATERIALHUB_USERNAME: {username if username else '未设置'}")
    print(f"  MATERIALHUB_PASSWORD: {'已设置' if password else '未设置'}")
    print()

    # 如果环境变量未设置，提示用户输入
    if not username or not password:
        print("认证信息未在环境变量中找到，请输入：")
        print("=" * 60)
        print("MaterialHub 认证")
        print("=" * 60)

        if not username:
            try:
                username = input("用户名 [默认: admin]: ").strip()
                if not username:
                    username = "admin"
                    print("  → 使用默认值: admin")
            except (EOFError, KeyboardInterrupt):
                print("\n用户取消输入，使用默认值: admin")
                username = "admin"

        if not password:
            try:
                password = getpass.getpass("密码: ")
                if not password:
                    print("  → 密码为空，使用默认值")
                    password = "admin123"
            except (EOFError, KeyboardInterrupt):
                print("\n用户取消输入，使用默认值")
                password = "admin123"

        print("=" * 60)

    return username, password


def main():
    """主函数"""
    print("MaterialHub 认证凭据获取演示")
    print()

    username, password = get_credentials()

    print("\n✅ 获取到的认证凭据:")
    print(f"  用户名: {username}")
    print(f"  密码: {'*' * len(password)}")
    print()


if __name__ == "__main__":
    main()
