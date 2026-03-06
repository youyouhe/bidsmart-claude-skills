# bid-md2doc 增强脚本

优化后的Markdown转Word文档工具，修复了CRLF换行符等常见问题。

## generate_docx.js

将`响应文件/`目录下的Markdown文件合并转换为一个格式化的Word (.docx) 文档。

### 主要特性

- ✅ **支持CRLF和LF混合换行符** - 修复了CRLF导致标题识别失败的bug
- ✅ **标题自动识别** - Markdown标题转换为Word标题样式（含字号和层级）
- ✅ **HTML注释过滤** - 自动过滤评分信息等辅助注释
- ✅ **列表项合并** - 列表标题与缩进内容自动合并
- ✅ **图片嵌入** - 自动读取并嵌入图片，支持PNG和JPEG
- ✅ **表格支持** - Markdown表格转换为Word表格
- ✅ **页眉页脚** - 自动添加项目名称页眉和公司名称页脚
- ✅ **分页符** - 附件之间自动插入分页符

### 依赖

```bash
npm install docx
```

### 配置

编辑文件顶部的`CONFIG`区域（位于`// === CONFIG START ===`和`// === CONFIG END ===`之间）：

```javascript
const CONFIG = {
  inputDir: 'C:\\Users\\Administrator\\Documents\\bid\\TC261901F1\\响应文件',
  outputFile: '响应文件-琪信通达-清华房屋土地数智化平台.docx',
  headerText: '清华大学房屋土地数智化管理平台采购项目 响应文件',
  footerCompany: '琪信通达（北京）科技有限公司',
  excludeFiles: ['核对报告.md', '装订指南.md'],
};
```

**字段说明**：
- `inputDir`: 响应文件目录的绝对路径
- `outputFile`: 输出Word文档的文件名
- `headerText`: 页眉文字
- `footerCompany`: 页脚公司名称
- `excludeFiles`: 排除的Markdown文件列表

### 使用方法

```bash
node generate_docx.js
```

### 输出示例

```
============================================================
Markdown 转 Word 文档生成器
============================================================
输入目录: C:\Users\Administrator\Documents\bid\TC261901F1\响应文件
输出文件: 响应文件-琪信通达-清华房屋土地数智化平台.docx

找到 26 个 Markdown 文件

处理: 00-目录.md
处理: 01-投标人资格声明书.md
处理: 02-投标保证金凭证.md
...
处理: 25-系统演示视频说明.md

共处理 26 个文件
嵌入 21 张图片

============================================================
生成完成！
============================================================
输出文件: C:\Users\Administrator\Documents\bid\TC261901F1\响应文件\响应文件-琪信通达-清华房屋土地数智化平台.docx
文件大小: 11142.07 KB
MD文件数: 26
图片数: 21
排除文件: 核对报告.md, 装订指南.md
状态: SUCCESS
============================================================
```

### 修复记录

#### v1.1 - 2026-03-06
**修复CRLF换行符导致标题识别失败的bug**

**问题描述**：
- 部分Markdown文件使用CRLF换行符（Windows风格）
- 原代码使用`content.split('\n')`分割行
- 导致每行末尾残留`\r`字符
- 正则表达式`/^(#{1,6})\s+(.+)$/`无法匹配带`\r`的行
- 结果：标题在Word中显示为原始`## 标题`文本，而非标题样式

**修复方案**：
```javascript
// 修改前
const lines = content.split('\n');

// 修改后（第192行）
const lines = content.split(/\r?\n/);  // 同时支持CRLF和LF
```

**验证结果**：
- ✅ 所有标题正确识别（包括03-投标书.md的6个标题）
- ✅ 标题在Word中显示为正确的标题样式（加粗+字号+层级）
- ✅ 兼容CRLF和LF混合的文件

#### 其他优化
- 添加HTML注释过滤（第206-209行）
- 优化标题字体大小配置（第221-228行）
- 增强列表项合并逻辑（第263-320行）

### 排除规则

以下文件不转换为Word：
- `核对报告.md` - 内部质检文件
- `装订指南.md` - 内部参考文件
- 用户在`excludeFiles`中指定的其他文件

### 图片处理

支持Markdown图片语法`![alt](file.png)`：
- 自动读取图片文件并嵌入Word
- 图片宽度不超过页面内容区（约15cm）
- 支持PNG和JPEG格式
- 图片不存在时插入红色`[图片缺失: filename]`占位文字

### 注意事项

1. **运行前确认**：
   - 响应文件目录存在且有`.md`文件
   - `docx` npm包已安装（`npm list docx`）
   - CONFIG配置正确

2. **只编辑CONFIG区域**：
   - 不要修改`CONFIG START`和`CONFIG END`之间以外的代码
   - 使用绝对路径（Windows路径需要双反斜杠`\\`）

3. **文件编码**：
   - 确保Markdown文件使用UTF-8编码
   - 如遇到乱码，使用`bid-assembly/scripts/normalize_markdown.py`规范化

4. **图片路径**：
   - 相对路径从Markdown文件所在目录计算
   - 建议图片与Markdown文件放在同一目录

### 故障排查

#### 问题：标题显示为`## 标题`而非标题样式
**原因**：Markdown文件使用CRLF换行符
**解决**：运行`python normalize_markdown.py 响应文件/`

#### 问题：图片无法加载
**原因**：图片路径错误或文件不存在
**解决**：检查图片文件是否存在，路径是否正确

#### 问题：表格解析失败
**原因**：表格格式不符合Markdown规范
**解决**：运行`python validate_structure.py 响应文件/`检查表格格式

---

## 最佳实践

### 1. 生成前规范化文件
```bash
# 使用bid-assembly工具规范化
python ../bid-assembly/scripts/normalize_markdown.py 响应文件/
```

### 2. 运行生成
```bash
node generate_docx.js
```

### 3. 验证生成结果
```bash
# 使用bid-assembly工具验证
python ../bid-assembly/scripts/verify_docx.py 响应文件/响应文件-XX-XX.docx
```

---

## 完整工作流

结合`bid-assembly`工具的完整质检流程：

```bash
# 1. 规范化Markdown文件
python ../bid-assembly/scripts/normalize_markdown.py 响应文件/

# 2. 验证结构
python ../bid-assembly/scripts/validate_structure.py 响应文件/

# 3. 检测占位符
python ../bid-assembly/scripts/detect_placeholders.py 响应文件/

# 4. 生成Word文档
node generate_docx.js

# 5. 验证Word文档
python ../bid-assembly/scripts/verify_docx.py 响应文件/响应文件-XX-XX.docx
```

或使用一键命令：
```bash
# 在项目根目录运行
python skills/bid-assembly/scripts/enhanced_assembly.py .
```

---

## License

MIT
