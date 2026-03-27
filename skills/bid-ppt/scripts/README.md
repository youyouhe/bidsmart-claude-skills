# bid-ppt 脚本

## generate_pptx.js

将 `slides.html` 转换为 PPTX 文件。

### 安装依赖

```bash
npm install pptxgenjs cheerio
```

### 使用

1. 先由 AI 生成 `slides.html`
2. 编辑脚本顶部 CONFIG 区域（输入/输出路径、字体等）
3. 运行：

```bash
node generate_pptx.js
```

### CONFIG 说明

| 字段 | 说明 | 默认值 |
|------|------|--------|
| inputFile | HTML 幻灯片路径 | `./slides.html` |
| outputFile | 输出 PPTX 路径 | `./演示文稿.pptx` |
| slideWidth | 幻灯片宽度（英寸） | 13.33 (16:9) |
| slideHeight | 幻灯片高度（英寸） | 7.5 (16:9) |
| defaultFontFace | 默认字体 | Microsoft YaHei |
| titleFontSize | 标题字号 pt | 36 |
| bodyFontSize | 正文字号 pt | 16 |

### 工作原理

1. 用 cheerio 解析 HTML，找到所有 `.slide` 元素
2. 提取 CSS 变量中的配色方案
3. 解析每张幻灯片的标题、正文、数据等
4. 用 pptxgenjs 生成对应布局的 PPTX
5. 图表区域生成占位框（需在 PowerPoint 中替换）

### 注意事项

- 图表（Chart.js）无法直接转为 PPTX 原生图表，会生成占位提示
- 建议在 PowerPoint 中手动替换图表，或截图嵌入
- 中文字体需要系统已安装 Microsoft YaHei 或其他中文字体
