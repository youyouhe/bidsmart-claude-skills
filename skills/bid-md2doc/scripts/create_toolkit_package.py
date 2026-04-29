#!/usr/bin/env python3
"""
创建占位符替换工具包压缩包

功能：
1. 将生成的Word文档、占位符清单、替换脚本、说明文档打包成ZIP
2. 生成README.txt快速入门指南
3. 生成install_dependencies脚本（Windows/Linux）
4. 统一交付，便于用户下载和使用

使用方法：
    python create_toolkit_package.py <响应文件目录> <项目名称>

输出：
    {项目名称}-占位符替换工具包.zip
"""

import sys
import os
import zipfile
from pathlib import Path
from datetime import datetime


def create_readme_txt(project_name: str) -> str:
    """生成README.txt快速入门指南"""
    return f"""╔══════════════════════════════════════════════════════════════════╗
║                   占位符替换工具包                                 ║
║                   {project_name:^50}║
╚══════════════════════════════════════════════════════════════════╝

📦 工具包内容
════════════════════════════════════════════════════════════════════

1. {project_name}-投标文件.docx
   原始Word文档（包含占位符，如【此处插入营业执照扫描件】）

2. 占位符清单.xlsx
   需要替换的占位符列表，请在"本地图片路径"列填写您的材料图片路径

3. replace_placeholders.py
   替换脚本，根据Excel清单替换Word中的占位符为图片

4. 占位符替换使用说明.md
   详细的使用指南（建议先阅读）

5. install_dependencies.bat / install_dependencies.sh
   一键安装Python依赖库

6. README.txt
   本文件，快速入门指南


🚀 快速开始（3步完成）
════════════════════════════════════════════════════════════════════

第一步：安装依赖
────────────────────────────────────────────────────────────────────
Windows用户：双击运行 install_dependencies.bat
Linux/Mac用户：运行 bash install_dependencies.sh

或手动安装：
    pip install python-docx openpyxl Pillow


第二步：填写材料路径
────────────────────────────────────────────────────────────────────
1. 打开 占位符清单.xlsx
2. 在"本地图片路径"列填写您电脑上材料图片的完整路径

   示例路径（Windows）：
   C:\\Users\\您的用户名\\Documents\\材料\\营业执照.png

   示例路径（Linux/Mac）：
   /home/用户名/Documents/材料/营业执照.png


第三步：运行替换脚本
────────────────────────────────────────────────────────────────────
打开命令行/终端，切换到本目录，运行：

    python replace_placeholders.py

或：

    python3 replace_placeholders.py


完成后会生成：
    {project_name}-投标文件-已替换.docx


⚠️ 重要提示
════════════════════════════════════════════════════════════════════

✅ 完全本地化处理
   - 所有操作在您的电脑上完成
   - 不需要网络连接
   - 您的材料图片不会上传到任何服务器

✅ 原文档保护
   - 原始Word文档不会被修改
   - 生成新文件（带"-已替换"后缀）

✅ 支持的图片格式
   - PNG（推荐，适合截图和扫描件）
   - JPG/JPEG（推荐，适合照片）


❓ 常见问题
════════════════════════════════════════════════════════════════════

Q: 脚本提示"图片文件不存在"？
A: 检查Excel中填写的路径是否正确，确保图片文件存在

Q: 路径中包含中文怎么办？
A: 支持中文路径，请确保Excel保存为UTF-8编码

Q: 部分占位符没有替换？
A: 查看脚本输出的"未找到"列表，确认Word中是否存在该占位符

Q: 需要Python版本是多少？
A: Python 3.6或更高版本


📞 获取帮助
════════════════════════════════════════════════════════════════════

1. 查看 占位符替换使用说明.md（详细文档）
2. 查看脚本执行时的日志输出
3. 联系技术支持（提供错误信息截图）


📅 生成时间
════════════════════════════════════════════════════════════════════

{datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}


═══════════════════════════════════════════════════════════════════
    SmartBid 标书生成系统 - 占位符替换工具包 v1.0
═══════════════════════════════════════════════════════════════════
"""


def create_install_script_windows() -> str:
    """生成Windows依赖安装脚本"""
    return """@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════════════════════════╗
echo ║          占位符替换工具 - 依赖安装脚本 (Windows)         ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

echo 正在检查Python版本...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到Python，请先安装Python 3.6或更高版本
    echo    下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo.

echo 正在安装依赖库...
echo ────────────────────────────────────────────────────────
pip install python-docx openpyxl Pillow
echo.

if %errorlevel% equ 0 (
    echo ╔══════════════════════════════════════════════════════════╗
    echo ║                  ✅ 安装成功！                           ║
    echo ╚══════════════════════════════════════════════════════════╝
    echo.
    echo 下一步：
    echo 1. 打开 占位符清单.xlsx
    echo 2. 填写"本地图片路径"列
    echo 3. 运行：python replace_placeholders.py
) else (
    echo ❌ 安装失败，请检查网络连接或手动安装
)

echo.
pause
"""


def create_install_script_linux() -> str:
    """生成Linux/Mac依赖安装脚本"""
    return """#!/bin/bash
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       占位符替换工具 - 依赖安装脚本 (Linux/Mac)          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "正在检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.6或更高版本"
    exit 1
fi

python3 --version
echo ""

echo "正在安装依赖库..."
echo "────────────────────────────────────────────────────────"
pip3 install python-docx openpyxl Pillow

if [ $? -eq 0 ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                  ✅ 安装成功！                           ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "下一步："
    echo "1. 打开 占位符清单.xlsx"
    echo "2. 填写"本地图片路径"列"
    echo "3. 运行：python3 replace_placeholders.py"
else
    echo "❌ 安装失败，请检查网络连接或手动安装"
fi

echo ""
"""


def create_toolkit_package(response_dir: str, project_name: str) -> str:
    """
    创建工具包压缩包

    Args:
        response_dir: 响应文件目录路径
        project_name: 项目名称

    Returns:
        生成的ZIP文件路径
    """
    response_path = Path(response_dir)

    # 定义需要打包的文件
    docx_file = response_path / f"{project_name}-投标文件.docx"
    excel_file = response_path / "占位符清单.xlsx"
    script_file = response_path / "replace_placeholders.py"
    doc_file = response_path / "占位符替换使用说明.md"

    # 检查必需文件是否存在
    required_files = {
        'Word文档': docx_file,
        '占位符清单': excel_file,
        '替换脚本': script_file,
    }

    missing_files = []
    for name, file_path in required_files.items():
        if not file_path.exists():
            missing_files.append(name)

    if missing_files:
        raise FileNotFoundError(f"缺少必需文件: {', '.join(missing_files)}")

    # 生成ZIP文件名
    zip_filename = f"{project_name}-占位符替换工具包.zip"
    zip_path = response_path / zip_filename

    print(f"\n📦 正在创建工具包: {zip_filename}")
    print("=" * 60)

    # 创建ZIP文件
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Word文档
        zipf.write(docx_file, docx_file.name)
        print(f"✓ {docx_file.name}")

        # 2. 占位符清单
        zipf.write(excel_file, excel_file.name)
        print(f"✓ {excel_file.name}")

        # 3. 替换脚本
        zipf.write(script_file, script_file.name)
        print(f"✓ {script_file.name}")

        # 4. 使用说明（如果存在）
        if doc_file.exists():
            zipf.write(doc_file, doc_file.name)
            print(f"✓ {doc_file.name}")

        # 5. README.txt
        readme_content = create_readme_txt(project_name)
        zipf.writestr("README.txt", readme_content.encode('utf-8'))
        print("✓ README.txt")

        # 6. Windows安装脚本
        install_bat_content = create_install_script_windows()
        zipf.writestr("install_dependencies.bat", install_bat_content.encode('utf-8'))
        print("✓ install_dependencies.bat")

        # 7. Linux/Mac安装脚本
        install_sh_content = create_install_script_linux()
        zipf.writestr("install_dependencies.sh", install_sh_content.encode('utf-8'))
        print("✓ install_dependencies.sh")

    print("=" * 60)
    print(f"✅ 工具包创建成功: {zip_path}")
    print(f"📊 文件大小: {zip_path.stat().st_size / 1024:.1f} KB")

    return str(zip_path)


def main():
    if len(sys.argv) < 3:
        print("用法: python create_toolkit_package.py <响应文件目录> <项目名称>")
        print("示例: python create_toolkit_package.py ./响应文件 清华房屋土地数智化平台")
        sys.exit(1)

    response_dir = sys.argv[1]
    project_name = sys.argv[2]

    if not Path(response_dir).exists():
        print(f"❌ 目录不存在: {response_dir}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("📦 占位符替换工具包生成器 v1.0")
    print("=" * 60)

    try:
        zip_path = create_toolkit_package(response_dir, project_name)

        print("\n" + "=" * 60)
        print("🎉 工具包已准备完毕！")
        print("=" * 60)
        print(f"\n📁 文件位置: {zip_path}")
        print("\n用户可以下载此ZIP文件，解压后按照README.txt操作")
        print()

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 创建工具包失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
