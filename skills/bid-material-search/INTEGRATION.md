# bid-material-search 集成指南

## 从 bid-manager 调用新版 bid-material-search

bid-manager 在 **S7: 扫描件** 阶段需要调用 bid-material-search 进行批量占位符替换。

### 旧版本调用方式 (v2.x - 已废弃)

```python
# 1. 启动 FastAPI 服务
os.system("cd skills/bid-material-search/scripts && uvicorn app:app --host 0.0.0.0 --port 9000 &")

# 2. 等待服务启动
time.sleep(3)

# 3. HTTP 调用
import requests
response = requests.post("http://localhost:9000/api/replace", json={
    "directory": "响应文件",
    "project_name": project_name
})
result = response.json()
```

**问题**：
- 需要启动独立服务
- 需要等待服务启动
- 需要 HTTP 调用
- 服务可能启动失败

---

### 新版本调用方式 (v3.0 - 推荐)

#### 方式 1: 直接 Python 导入（推荐）

如果 bid-manager 有 Python 脚本：

```python
import sys
sys.path.insert(0, "c:/material-hub/.claude/skills/bid-material-search/scripts")

from replace import replace_all_placeholders_sync

# S7 阶段：批量替换占位符
result = replace_all_placeholders_sync(
    directory="响应文件",
    project_name=project_name  # 从 pipeline_progress.json 读取
)

print(f"✓ 成功替换: {result['replaced_count']} 个占位符")
print(f"✗ 失败: {result['failed_count']} 个")

# 更新进度
pipeline_progress['stages']['S7']['status'] = 'completed'
pipeline_progress['stages']['S7']['replaced_count'] = result['replaced_count']
pipeline_progress['stages']['S7']['failed_count'] = result['failed_count']
```

#### 方式 2: LLM 驱动调用（bid-manager 无脚本时）

如果 bid-manager 是纯 LLM 驱动的 skill：

在 bid-manager 的 SKILL.md 的 S7 阶段添加：

```markdown
### S7: 扫描件

**实现方式（v3.0）**：

1. 读取项目名称：
   ```python
   import json
   with open("pipeline_progress.json") as f:
       progress = json.load(f)
   project_name = progress.get("project_name", "")
   ```

2. 调用 bid-material-search 的批量替换功能：
   ```python
   import sys
   sys.path.insert(0, "c:/material-hub/.claude/skills/bid-material-search/scripts")
   from replace import replace_all_placeholders_sync

   result = replace_all_placeholders_sync("响应文件", project_name)
   ```

3. 检查结果：
   - 如果 `result['replaced_count'] > 0`：继续到 S8
   - 如果 `result['failed_count'] > 0`：输出失败清单，询问用户是否继续

4. 更新进度文件
```

---

## 完整的 S7 阶段实现示例

```python
def execute_stage_7_scan_materials(pipeline_progress: dict) -> dict:
    """
    S7: 扫描件阶段 - 批量替换占位符

    使用新版 bid-material-search (v3.0) 直接调用 API
    """
    print("\n" + "="*60)
    print("S7: 扫描件 - 批量替换占位符")
    print("="*60)

    # 1. 读取项目名称
    project_name = pipeline_progress.get("project_name", "")
    if not project_name:
        # 尝试从分析报告提取
        try:
            with open("分析报告.md", "r", encoding="utf-8") as f:
                content = f.read()
                if "项目名称：" in content:
                    start = content.find("项目名称：") + len("项目名称：")
                    end = content.find("\n", start)
                    project_name = content[start:end].strip()
        except:
            pass

    print(f"项目名称: {project_name or '未设置（将不添加水印）'}")

    # 2. 检查响应文件目录
    import os
    if not os.path.exists("响应文件"):
        print("⚠️ 响应文件目录不存在，跳过此阶段")
        return {
            "status": "skipped",
            "message": "响应文件目录不存在"
        }

    # 3. 调用 bid-material-search
    try:
        import sys
        sys.path.insert(0, "c:/material-hub/.claude/skills/bid-material-search/scripts")
        from replace import replace_all_placeholders_sync

        print("\n开始批量替换占位符...")
        result = replace_all_placeholders_sync(
            directory="响应文件",
            project_name=project_name
        )

        # 4. 输出结果
        print(f"\n替换完成:")
        print(f"  ✓ 成功: {result['replaced_count']} 个")
        print(f"  ✗ 失败: {result['failed_count']} 个")
        print(f"  📁 处理文件: {result['total_files']} 个")

        # 5. 输出详情
        if result['failed_count'] > 0:
            print(f"\n失败详情:")
            for detail in result['details']:
                if detail['status'] == 'failed':
                    print(f"  - {detail['placeholder']}: {detail['error']}")

        # 6. 返回结果
        return {
            "status": "completed",
            "replaced_count": result['replaced_count'],
            "failed_count": result['failed_count'],
            "details": result['details']
        }

    except ImportError as e:
        print(f"✗ 导入 bid-material-search 失败: {e}")
        print("请确保 bid-material-search skill 已安装到项目中")
        return {
            "status": "failed",
            "error": f"导入失败: {e}"
        }
    except Exception as e:
        print(f"✗ 替换失败: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }
```

---

## 更新 bid-manager SKILL.md

在 `bid-manager/SKILL.md` 的 S7 部分更新如下：

```markdown
### S7: 扫描件

```
输入: 响应文件/*.md（含扫描件占位符）
输出: 响应文件中的占位符替换为图片引用 + 带水印的图片
调用: bid-material-search v3.0（直接 Python 调用）
前置: MaterialHub API 已运行，材料已上传
```

**实现逻辑（v3.0 更新）**：

1. **检查前置条件**：
   - MaterialHub API 运行状态（`curl http://localhost:8201/health`）
   - 响应文件目录存在

2. **读取项目名称**：
   - 从 `pipeline_progress.json` 的 `project_name` 字段
   - 或从 `分析报告.md` 自动提取

3. **调用新版 bid-material-search**：
   ```python
   from bid_material_search.replace import replace_all_placeholders_sync
   result = replace_all_placeholders_sync("响应文件", project_name)
   ```

4. **处理结果**：
   - 成功：继续到 S8
   - 部分失败：输出失败清单，询问用户是否继续
   - 完全失败：标记阶段为 failed，提示用户检查 MaterialHub

5. **更新进度**：
   ```json
   {
     "S7": {
       "status": "completed",
       "replaced_count": 12,
       "failed_count": 0,
       "output": "响应文件/*.png (带水印)"
     }
   }
   ```

**与旧版本（v2.x）的区别**：

| 特性 | 旧版本 (v2.x) | 新版本 (v3.0) |
|------|-------------|--------------|
| 调用方式 | HTTP POST 到 localhost:9000 | 直接 Python 函数调用 |
| 启动服务 | 需要 `uvicorn app:app` | 无需启动服务 |
| 等待时间 | 3秒（等待服务启动） | 0秒 |
| 依赖 | FastAPI, uvicorn | httpx, python-dotenv, Pillow |
| 可靠性 | 服务可能启动失败 | 无服务依赖，更可靠 |
```

---

## 测试新集成

在实现 S7 阶段后，可以这样测试：

```bash
# 1. 确保 MaterialHub API 运行
curl http://localhost:8201/health

# 2. 准备测试数据
mkdir -p 响应文件
echo "公司营业执照：【此处插入营业执照扫描件】" > 响应文件/test.md
echo "项目名称：测试项目" > 分析报告.md

# 3. 测试 Python 调用
python3 -c "
import sys
sys.path.insert(0, 'c:/material-hub/.claude/skills/bid-material-search/scripts')
from replace import replace_all_placeholders_sync

result = replace_all_placeholders_sync('响应文件', '测试项目')
print(f'成功: {result[\"replaced_count\"]}')
print(f'失败: {result[\"failed_count\"]}')
"

# 4. 验证结果
cat 响应文件/test.md
# 应该看到：公司营业执照：![营业执照](营业执照_XX公司.png)

ls 响应文件/*.png
# 应该看到下载的图片文件
```

---

## 故障排查

### 问题 1: ImportError: No module named 'replace'

**原因**：Python 路径未正确设置

**解决**：
```python
import sys
import os
skill_path = os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "skills", "bid-material-search", "scripts")
sys.path.insert(0, os.path.abspath(skill_path))
```

### 问题 2: "MaterialHub API 连接失败"

**原因**：MaterialHub 未运行或环境变量未设置

**解决**：
```bash
# 1. 启动 MaterialHub
cd c:/material-hub
bash start.sh

# 2. 检查环境变量
cat .env | grep MATERIALHUB_API_KEY

# 3. 测试连接
curl -H "Authorization: Bearer $MATERIALHUB_API_KEY" http://localhost:8201/api/v2/search?limit=1
```

### 问题 3: "未找到材料"

**原因**：MaterialHub 中没有对应的材料

**解决**：
```bash
# 使用 MCP tool 检查材料
# 在 Claude Code 中：搜索 "营业执照"
```

---

## 性能对比

### 旧版本（FastAPI）流程耗时
```
启动服务: 3秒
HTTP 调用: 0.1秒/次 × 10次 = 1秒
总计: 4秒
```

### 新版本（直接调用）流程耗时
```
导入模块: 0.01秒
API 调用: 0.1秒/次 × 10次 = 1秒
总计: 1秒
```

**提升**: 75% 时间节省

---

## 总结

新版 bid-material-search (v3.0) 通过移除 FastAPI 中间层，简化了集成：

- ✅ 无需启动独立服务
- ✅ 更快的执行速度
- ✅ 更简单的调用方式
- ✅ 更好的错误处理
- ✅ 与 MCP 统一配置

bid-manager 可以直接导入 Python 函数，实现无缝集成。
