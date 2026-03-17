#!/usr/bin/env python3
"""
bid-material-search skill 测试脚本

测试新版 MCP-based 实现的功能
"""

import sys
import os
from pathlib import Path
import httpx

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from config import API_BASE, API_TOKEN, _config_source
from search import search_materials_sync, get_document_detail_sync
from extract import extract_company_data_sync, extract_person_data_sync
from replace import replace_placeholder_sync, replace_all_placeholders_sync
from watermark import get_project_name_from_analysis


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_connection():
    """测试 MaterialHub API 连接"""
    print_section("测试 0: 连接检查")

    print(f"\n配置来源: {_config_source}")
    print(f"API 地址: {API_BASE}")
    print(f"API 密钥: {API_TOKEN[:20]}...{API_TOKEN[-4:]}" if API_TOKEN else "API 密钥: <未设置>")

    if not API_TOKEN:
        print("\n✗ 错误: MATERIALHUB_API_KEY 未设置")
        print("请创建 .env 文件并配置:")
        print("  MATERIALHUB_API_URL=http://your-server:8201")
        print("  MATERIALHUB_API_KEY=mh-mcp-xxx...")
        return False

    print("\n测试连接...")
    try:
        headers = {}
        if API_TOKEN:
            headers["Authorization"] = f"Bearer {API_TOKEN}"

        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{API_BASE}/health", headers=headers)
            resp.raise_for_status()
            data = resp.json()

            print(f"✓ 连接成功: {data}")
            return True
    except httpx.ConnectError as e:
        print(f"✗ 连接失败: {e}")
        print(f"\n请检查:")
        print(f"  1. MaterialHub API 是否运行在 {API_BASE}")
        print(f"  2. 防火墙是否允许访问")
        print(f"  3. 网络连接是否正常")
        return False
    except httpx.HTTPStatusError as e:
        print(f"✗ HTTP 错误: {e.response.status_code} {e.response.text}")
        if e.response.status_code == 401:
            print(f"\n请检查 API Key 是否正确")
        return False
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return False


def test_search():
    """测试搜索功能"""
    print_section("测试 1: 材料搜索")

    print("\n1.1 搜索 '营业执照'")
    results = search_materials_sync(query="营业执照", limit=3)

    if results:
        print(f"✓ 找到 {len(results)} 个结果")
        for r in results[:2]:
            print(f"  - [{r['id']}] {r['title']}")
            print(f"    类型: {r['doc_type']['name']}")
            print(f"    状态: {r['status']}")
    else:
        print("✗ 未找到结果")
        return False

    print("\n1.2 按公司名称搜索")
    results = search_materials_sync(query="", company_name="珞信通达", limit=3)

    if results:
        print(f"✓ 找到 {len(results)} 个结果")
        for r in results[:2]:
            print(f"  - [{r['id']}] {r['title']}")
    else:
        print("⚠️ 未找到珞信通达的材料（可能数据库中没有）")

    return True


def test_document_detail():
    """测试文档详情获取"""
    print_section("测试 2: 文档详情")

    # 先搜索一个文档
    results = search_materials_sync(query="", limit=1)
    if not results:
        print("✗ 没有可用的文档进行测试")
        return False

    doc_id = results[0]["id"]
    print(f"\n2.1 获取文档 {doc_id} 的详情")

    detail = get_document_detail_sync(doc_id)
    if detail:
        print(f"✓ 文档详情获取成功")
        print(f"  标题: {detail.get('title')}")
        print(f"  状态: {detail.get('status')}")
        print(f"  类型: {detail.get('doc_type', {}).get('name')}")

        # 检查是否有附件
        rev = detail.get('current_revision')
        if rev and rev.get('files'):
            print(f"  附件数: {len(rev['files'])}")
            for f in rev['files'][:2]:
                print(f"    - {f['filename']} ({f['file_type']})")
        return True
    else:
        print("✗ 获取详情失败")
        return False


def test_extract_company():
    """测试公司数据提取"""
    print_section("测试 3: 公司数据提取")

    print("\n3.1 提取公司数据（使用聚合 API）")
    company_name = "珞信通达"  # 测试公司

    data = extract_company_data_sync(company_name)

    if "error" in data:
        print(f"⚠️ {data['error']}")
        if "matches" in data:
            print("可选的公司：")
            for m in data["matches"]:
                print(f"  - [{m['id']}] {m['name']}")
        return False

    print(f"✓ 成功提取公司数据")
    print(f"  公司名称: {data['company']['name']}")

    if data.get('license'):
        print(f"  信用代码: {data['license'].get('credit_code', 'N/A')}")
        print(f"  法定代表人: {data['license'].get('legal_person', 'N/A')}")
        print(f"  注册资本: {data['license'].get('registered_capital', 'N/A')}")

    if data.get('statistics'):
        print(f"  材料总数: {data['statistics'].get('total_materials', 0)}")
        print(f"  员工总数: {data['statistics'].get('total_employees', 0)}")

    if data.get('persons'):
        print(f"  员工数: {len(data['persons'])}")
        for p in data['persons'][:2]:
            print(f"    - {p['name']} ({p.get('education', 'N/A')})")

    return True


def test_placeholder_replacement():
    """测试占位符替换"""
    print_section("测试 4: 占位符替换")

    # 创建测试文件
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)

    test_file = test_dir / "test.md"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("# 测试文档\n\n")
        f.write("公司营业执照：【此处插入营业执照扫描件】\n")

    print(f"\n4.1 创建测试文件: {test_file}")
    print("    内容: 公司营业执照：【此处插入营业执照扫描件】")

    print("\n4.2 替换占位符")
    result = replace_placeholder_sync(
        target_file=str(test_file),
        placeholder="【此处插入营业执照扫描件】",
        query="营业执照",
        project_name="测试项目",
        output_dir=str(test_dir)
    )

    if result["success"]:
        print(f"✓ 替换成功")
        print(f"  图片路径: {result.get('image_path')}")

        # 读取更新后的文件
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"  更新后内容: {content.split('：')[1].strip()}")
        return True
    else:
        print(f"✗ 替换失败: {result['message']}")
        return False


def test_watermark():
    """测试水印功能"""
    print_section("测试 5: 水印提取")

    # 创建测试分析报告
    test_analysis = Path("test_分析报告.md")
    with open(test_analysis, "w", encoding="utf-8") as f:
        f.write("# 分析报告\n\n")
        f.write("项目名称：清华房屋土地数智化平台\n\n")

    print(f"\n5.1 从分析报告提取项目名称")
    project_name = get_project_name_from_analysis(str(test_analysis))

    if project_name:
        print(f"✓ 提取成功: {project_name}")

        # 清理
        test_analysis.unlink()
        return True
    else:
        print("✗ 提取失败")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪" * 30)
    print("bid-material-search Skill 测试套件")
    print("🧪" * 30)

    results = {
        "搜索功能": False,
        "文档详情": False,
        "公司数据提取": False,
        "占位符替换": False,
        "水印提取": False,
    }

    try:
        results["搜索功能"] = test_search()
    except Exception as e:
        print(f"\n✗ 搜索测试异常: {e}")

    try:
        results["文档详情"] = test_document_detail()
    except Exception as e:
        print(f"\n✗ 文档详情测试异常: {e}")

    try:
        results["公司数据提取"] = test_extract_company()
    except Exception as e:
        print(f"\n✗ 公司数据提取测试异常: {e}")

    try:
        results["占位符替换"] = test_placeholder_replacement()
    except Exception as e:
        print(f"\n✗ 占位符替换测试异常: {e}")

    try:
        results["水印提取"] = test_watermark()
    except Exception as e:
        print(f"\n✗ 水印提取测试异常: {e}")

    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}  {name}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        return 1


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  bid-material-search Skill 测试套件")
    print("=" * 60)

    # 先测试连接
    if not test_connection():
        print("\n⚠️ 连接测试失败，无法继续")
        return 1

    # 运行功能测试
    return run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
