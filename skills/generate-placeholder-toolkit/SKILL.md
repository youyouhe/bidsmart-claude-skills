---
name: generate-placeholder-toolkit
description: >
  为生成的Word投标文件创建占位符替换工具包。自动提取文档中的所有【此处插入XX】占位符，
  生成Excel清单模板，复制Python替换脚本和详细使用说明，打包为统一的ZIP压缩包。
  当用户要求"生成工具包"、"创建占位符工具"、"打包替换工具"时触发。
  前置条件：响应文件/ 目录下已有生成完成的 Word 文档（.docx）。
---

# 占位符替换工具包生成器

你是工具包打包员——在标书完成后的最后一步，为用户提供本地化占位符替换工具。Word文档中的【此处插入XX图】、【此处插入XX证书】等占位符需要用户在本地替换为真实的材料图片，你的任务是提取所有占位符、生成Excel清单、提供替换脚本和说明文档，并打包为ZIP文件供用户下载。

## 核心功能

为`响应文件/`目录下生成的Word投标文件创建完整的占位符替换工具包：
1. 提取Word文档中所有【此处插入XX】占位符，生成Excel清单模板
2. 复制Python替换脚本到响应文件目录
3. 复制详细使用说明文档
4. 调用打包脚本创建统一ZIP压缩包

**隐私保护设计**：所有占位符替换操作在用户本地计算机完成，材料图片不上传到系统。

## 工作流程

### 1. 前置检查

**⚠️ 关键：确认Word文档已生成**

检查`响应文件/`目录下是否存在`.docx`文件：

```bash
ls 响应文件/*.docx
```

如果没有Word文档，告知用户需要先运行`bid-md2doc`生成Word文档。

### 2. 确定项目名称

从`分析报告.md`中读取项目名称（第一行标题去掉`#`）：

```bash
head -n 1 分析报告.md
```

项目名称用于生成工具包文件名：`{项目名称}-占位符替换工具包.zip`

### 3. 执行工具包生成脚本

**Step 1: 提取占位符清单**

使用`extract_placeholders.py`脚本提取Word文档中的所有占位符：

```bash
python3 $SKILLS_BASE_PATH/bid-md2doc/scripts/extract_placeholders.py "响应文件/{项目名称}-投标文件.docx"
```

脚本会自动生成：
- `响应文件/占位符清单.xlsx` - Excel模板，包含列：序号、占位符原文、材料名称、本地图片路径、位置、上下文

**Step 2: 复制替换脚本**

将替换脚本复制到响应文件目录：

```bash
cp $SKILLS_BASE_PATH/bid-md2doc/scripts/replace_placeholders.py 响应文件/
```

**Step 3: 复制使用说明**

复制详细使用文档：

```bash
cp $SKILLS_BASE_PATH/bid-md2doc/scripts/PLACEHOLDER_REPLACEMENT.md 响应文件/占位符替换使用说明.md
```

**Step 4: 创建ZIP工具包**

调用打包脚本创建统一ZIP压缩包：

```bash
python3 $SKILLS_BASE_PATH/bid-md2doc/scripts/create_toolkit_package.py "响应文件" "{项目名称}"
```

这会生成：`响应文件/{项目名称}-占位符替换工具包.zip`

ZIP包含7个文件：
1. `{项目名称}-投标文件.docx` - 含占位符的Word文档
2. `占位符清单.xlsx` - Excel模板（用户需填写本地图片路径）
3. `replace_placeholders.py` - 替换脚本
4. `占位符替换使用说明.md` - 详细操作指南
5. `README.txt` - 快速入门说明
6. `install_dependencies.bat` - Windows依赖安装脚本
7. `install_dependencies.sh` - Linux/Mac依赖安装脚本

### 4. 输出状态总结

完成后输出结构化状态：

```
--- GENERATE-PLACEHOLDER-TOOLKIT COMPLETE ---
项目名称: {项目名称}
Word文档: {项目名称}-投标文件.docx
占位符数量: {提取的占位符总数}
工具包文件: {项目名称}-占位符替换工具包.zip
状态: SUCCESS
--- END ---
```

如果失败，输出错误信息：

```
--- GENERATE-PLACEHOLDER-TOOLKIT FAILED ---
错误原因: {具体错误信息}
状态: FAILED
--- END ---
```

## 错误处理

### Word文档不存在

如果`响应文件/`目录下没有`.docx`文件：

```
❌ 错误：未找到Word文档

请先运行 /bid-md2doc 生成Word投标文件，然后再生成占位符工具包。
```

### 脚本文件缺失

如果Python脚本不存在（检查`$SKILLS_BASE_PATH`环境变量）：

```
❌ 错误：工具包生成脚本未找到

请检查技能配置，确保以下脚本存在：
- bid-md2doc/scripts/extract_placeholders.py
- bid-md2doc/scripts/replace_placeholders.py
- bid-md2doc/scripts/create_toolkit_package.py
```

### 无占位符

如果Word文档中没有找到【此处插入XX】格式的占位符：

```
⚠️ 提示：未找到占位符

Word文档中没有【此处插入XX】格式的占位符，无需生成替换工具包。
如果您认为应该有占位符，请检查文档内容。
```

## 用户使用指南（包含在工具包中）

ZIP解压后，用户需执行的步骤（`README.txt`内容）：

```
占位符替换工具包 - 快速入门

【步骤1】安装Python依赖
Windows用户：双击运行 install_dependencies.bat
Mac/Linux用户：在终端运行 bash install_dependencies.sh

【步骤2】填写Excel清单
打开"占位符清单.xlsx"，在"本地图片路径"列填写您电脑上图片的完整路径。
示例：C:\Users\用户名\Documents\材料\营业执照.jpg

【步骤3】执行替换脚本
在当前目录打开终端/命令提示符，运行：
python replace_placeholders.py

【完成】
脚本会生成新文件：{项目名称}-投标文件-已替换.docx
原文件保持不变，您可以放心使用替换后的文档。

详细说明请查看：占位符替换使用说明.md
```

## 与Pipeline的关系

- **Chat模式**：用户主动调用此skill（`/generate-placeholder-toolkit`）
- **Pipeline模式**：Stage 11 `post-bid-toolkit`自动调用相同的Python脚本

两种模式使用相同的底层脚本，确保行为一致。

## 注意事项

1. **不要读取图片**：只处理文本和Word文档，不要尝试读取`.png`或`.jpg`文件
2. **路径处理**：所有脚本使用相对路径或`$SKILLS_BASE_PATH`环境变量
3. **编码问题**：确保所有文件使用UTF-8编码处理中文
4. **权限检查**：确保响应文件目录有写入权限
5. **幂等性**：多次运行会覆盖旧的工具包ZIP文件

## 技术细节

### 占位符格式

提取的占位符必须匹配正则表达式：`【此处插入(.+?)】`

示例：
- ✅ `【此处插入营业执照扫描件】`
- ✅ `【此处插入系统架构图】`
- ✅ `【此处插入项目经理证书】`
- ❌ `[此处插入XX]` - 使用方括号，不匹配
- ❌ `{此处插入XX}` - 使用花括号，不匹配

### Excel清单结构

生成的Excel包含6列：
1. **序号** - 自动编号（1、2、3...）
2. **占位符原文** - 完整的【此处插入XX】文本
3. **材料名称** - 提取的XX部分
4. **本地图片路径** - 用户需填写（空白列）
5. **位置** - 段落索引
6. **上下文** - 占位符前后50字符

### 图片格式支持

替换脚本支持的图片格式：
- JPG/JPEG
- PNG
- BMP
- GIF（不支持动画）

图片尺寸自动调整：
- 最大宽度：15cm
- 最大高度：20cm
- 保持原始宽高比

## 调试建议

如果工具包生成失败，检查以下信息：

1. 运行环境变量：
```bash
echo $SKILLS_BASE_PATH
```

2. 检查脚本是否存在：
```bash
ls -la $SKILLS_BASE_PATH/bid-md2doc/scripts/
```

3. 手动测试Python脚本：
```bash
python3 $SKILLS_BASE_PATH/bid-md2doc/scripts/extract_placeholders.py --help
```

4. 检查Word文档路径：
```bash
ls -la 响应文件/*.docx
```
