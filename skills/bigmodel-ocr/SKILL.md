---
name: bigmodel-ocr
description: >
  使用智谱 BigModel OCR API 对图片和 PDF 页面进行文字识别。
  支持中英文混排、手写体、印刷体，内置内容级缓存避免重复请求。
  输出为结构化 JSON（含逐页文本、token 估算、表格检测）。
  当用户需要对 PDF 扫描件、证书图片、合同扫描页进行 OCR 文字识别时触发。
  也适用于从营业执照、资质证书、身份证等材料图片中提取文字信息。
---

# BigModel OCR 文字识别

## 概述

基于智谱 BigModel OCR API 的文字识别工具，专为中文文档场景优化。
支持 PDF 扫描件和图片文件，内置缓存机制，避免重复消耗 API 调用。

## 环境要求

- Python 3.9+
- 依赖包：`requests`, `PyMuPDF`（PDF 场景需要）
- 环境变量：`BIGMODEL_API_KEY`（智谱 API 密钥）

安装依赖：
```bash
pip install requests PyMuPDF
```

## 使用方式

### 1. OCR PDF 页面

对 PDF 的指定页面进行 OCR 识别：

```bash
python .claude/skills/bigmodel-ocr/scripts/bigmodel_ocr.py <pdf路径> --pages 1-3 --output ocr_result.json
```

参数说明：
- `<pdf路径>`：PDF 文件路径
- `--pages`：页码范围，支持 `1-3`、`1,3,5`、`1-3,7,10-12` 等格式
- `--output`：输出 JSON 文件路径（不指定则输出到 stdout）
- `--cache-dir`：缓存目录（默认 `.ocr_cache`）
- `--dpi`：渲染 DPI（默认 300，越高越清晰但越慢）
- `--tool-type`：OCR 模式，`hand_write`（手写+印刷混合，默认）或 `ocr`（纯印刷体）

### 2. OCR 单张图片

直接对图片文件进行 OCR：

```bash
python .claude/skills/bigmodel-ocr/scripts/bigmodel_ocr.py <图片路径> --output ocr_result.json
```

支持的图片格式：JPEG、PNG、TIFF、BMP、WebP

### 3. 批量 OCR 多个文件

```bash
python .claude/skills/bigmodel-ocr/scripts/bigmodel_ocr.py file1.pdf file2.jpg file3.png --pages 1-5 --output ocr_result.json
```

对多文件逐一处理，结果合并输出。PDF 使用 `--pages` 指定页码，图片直接识别。

## 输出格式

```json
{
  "results": [
    {
      "source": "document.pdf",
      "type": "pdf",
      "pages": [
        {
          "page": 1,
          "text": "识别出的文本内容...",
          "tokens": 256,
          "has_table": false,
          "cached": false
        }
      ]
    },
    {
      "source": "cert.jpg",
      "type": "image",
      "pages": [
        {
          "page": 1,
          "text": "证书文本内容...",
          "tokens": 128,
          "has_table": false,
          "cached": false
        }
      ]
    }
  ],
  "summary": {
    "total_files": 2,
    "total_pages": 3,
    "success_pages": 3,
    "failed_pages": 0,
    "total_tokens": 384
  }
}
```

## 与 MaterialHub 配合使用

典型流程：

1. **OCR 识别**：使用本 skill 提取文档文字
2. **Claude 分析**：Claude 阅读 OCR 文本，判断文档类型、提取关键信息
3. **入库**：调用 MaterialHub MCP 的 `add_document` 工具，带上分类结果直接入库

示例工作流：
```
# Step 1: OCR
python .claude/skills/bigmodel-ocr/scripts/bigmodel_ocr.py 营业执照.pdf --pages 1 --output ocr.json

# Step 2: 读取 ocr.json，Claude 分析内容，识别为营业执照，提取公司名等信息

# Step 3: 调用 MCP add_document 入库
```

## 缓存机制

- 基于文件内容哈希（文件大小 + 前 8KB SHA256），同一文件不会重复 OCR
- 缓存存储在 `--cache-dir` 指定目录（默认 `.ocr_cache`）
- 输出 JSON 中 `cached: true` 标识命中缓存的页面
- 清除缓存：删除缓存目录即可

## 注意事项

- BigModel OCR API 按调用次数计费，建议合理使用缓存
- 对于多页 PDF，建议只 OCR 关键页面（如前 3 页），避免不必要的消耗
- `hand_write` 模式同时支持手写和印刷体，适合大多数场景
- 图片分辨率越高识别越准确，PDF 默认 300 DPI 渲染
