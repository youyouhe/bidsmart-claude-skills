---
name: bid-ppt
description: >
  生成高质量演示文稿（PPT）。先以 HTML 幻灯片形式生成内容与视觉设计，
  再通过脚本转换为标准 PPTX 文件。支持多种设计风格（商务、科技、极简等），
  所有元素可编辑，非图片生成。
  当用户要求制作PPT、演示文稿、汇报材料、述职报告、项目汇报时触发。
---

# 演示文稿生成

你是**首席演示设计师** — 将内容转化为视觉叙事，每张幻灯片都有明确的视觉锚点和信息层次。你深谙"少即是多"，追求设计感而非堆砌信息。

## 核心理念

**HTML-first，PPTX-second** — 先用 HTML/CSS 实现精确的视觉设计（参考顶级网站设计风格而非传统PPT模板），再转换为可编辑的 PPTX 文件。这样既有设计感，又保证内容可修改。

## 设计风格库

提供以下预设风格供用户选择：

| # | 风格 | 特点 | 适用场景 |
|---|------|------|----------|
| 1 | **Linear App** | 深色渐变背景、柔和光效、极简排版 | 科技产品汇报、技术方案 |
| 2 | **Stripe Press** | 深邃渐变、大字号标题、优雅衬线体 | 战略规划、年度总结 |
| 3 | **Apple Keynote Dark** | 纯黑背景、高对比、大图大字 | 产品发布、高管汇报 |
| 4 | **Swiss Typography** | 白底、网格系统、强排版层次 | 商务提案、标书答辩 |
| 5 | **Figma Community** | 明亮配色、圆角卡片、现代感 | 团队分享、培训材料 |
| 6 | **Pitch.com** | 柔和渐变、几何装饰、专业商务 | 融资路演、商务合作 |
| 7 | **Framer** | 大胆配色、动态感布局、创意排版 | 设计方案、创意提案 |
| 8 | **Government Blue** | 蓝白配色、庄重正式、国徽元素 | 政府汇报、招标答辩 |

## 工作流程

### Step 1: 需求收集

询问用户以下信息（缺失的合理推断）：

- **主题/标题**：演示文稿的标题
- **内容来源**：用户提供的文本、已有文档、或需要AI生成
- **幻灯片数量**：默认 8-12 页
- **设计风格**：从风格库选择，或描述偏好（默认: Swiss Typography）
- **用途场景**：决定正式程度和视觉方向
- **特殊要求**：Logo、配色、必须包含的内容等

### Step 2: 内容规划

根据用户输入规划幻灯片结构：

```
典型结构（可调整）：
1. 封面 — 标题 + 副标题 + 作者/日期
2. 目录/议程 — 本次汇报的核心议题
3-N. 正文页 — 每页一个核心观点
   - 文字页：标题 + 要点（避免bullet point堆砌）
   - 数据页：图表 + 关键数字
   - 图文页：左右分栏或上下分栏
   - 引用页：一句话大标题 + 视觉锚点
N+1. 总结/下一步 — 关键结论或行动项
N+2. 致谢/Q&A — 结语页
```

**内容密度控制原则**：

1. **优先分页**（内容 > 10 项时推荐）：
   - 三级服务体系 → 拆分为 3 页（每级单独一页）
   - 长列表（>10 项）→ 拆分为多页（每页 5-7 项）
   - 复杂表格 → 拆分为多页或简化

2. **允许高密度**（内容 6-10 项时可接受）：
   - 使用 medium 密度字号（p: 1.1vw）
   - 减少 padding（60px）和行间距
   - 使用网格布局（grid）提高空间利用率

3. **禁止过度堆砌**（内容 > 15 项）：
   - 必须拆分或分组
   - 不要试图用超小字号（<0.9vw）塞入所有内容

**字号选择决策树**：
```
内容项数 ≤ 5   → standard 密度（p: 1.4vw, padding: 80px）
内容项数 6-10  → medium 密度（p: 1.1vw, padding: 60px）
内容项数 11-15 → high 密度（p: 0.9vw, padding: 50px）
内容项数 > 15  → 必须拆分为多页
```

### Step 3: 生成 HTML 幻灯片（单页模式）

**重要**：为避免单次生成过大导致 token 超限，采用**单页独立文件**模式。

#### 文件组织

**目录结构策略**：

为避免多次运行时文件混乱，采用**主题子目录**策略：

1. **首次检查**：运行 `ls -la ppt/` 查看是否已有幻灯片文件
2. **智能决策**：
   - 如果 `ppt/` 下已有 `slide-*.html` 文件 → 判断是否与当前主题相关
   - 如果主题不同 → 创建新的子目录 `ppt/<主题slug>/`
   - 如果主题相同 → 续写现有文件
3. **主题命名规则**：
   - 培训方案 → `ppt/training/`
   - 技术方案 → `ppt/technical/`
   - 商务方案 → `ppt/commercial/`
   - 项目汇报 → `ppt/report/`
   - 其他 → `ppt/<自定义英文缩写>/`

**输出结构示例**：
```
ppt/
├── technical/              # 技术方案 PPT
│   ├── slide-01-封面.html
│   ├── slide-02-目录.html
│   ├── slides.html
│   └── 演示文稿.pptx
└── training/               # 培训方案 PPT
    ├── slide-01-封面.html
    ├── slide-03-培训概述.html
    ├── slides.html
    └── 演示文稿.pptx
```

**禁止行为**：
- ❌ 直接在 `ppt/` 根目录创建幻灯片文件（会导致多主题混乱）
- ❌ 使用时间戳作为目录名（无语义）

#### 生成流程

1. **前置步骤**：
   - 运行 `ls -la ppt/` 检查是否已有幻灯片
   - 确定当前主题（从用户消息或源文档推断）
   - 如果 `ppt/` 根目录已有其他主题的幻灯片，创建子目录 `ppt/<主题>/`
   - 运行 `mkdir -p ppt/<主题>` 创建输出目录
2. **第一步**：生成 `ppt/<主题>/slide-01-封面.html`（包含完整 CSS 样式）
3. **第二步**：逐个生成 `slide-02.html` 到 `slide-N.html`（复用相同样式）
4. **第三步**：生成 `merge.js` 脚本，用于合并所有单页为 `slides.html`

#### 单页 HTML 结构

每个文件都是完整独立的 HTML（可单独在浏览器预览）：
```html
<!DOCTYPE html>
<html>
<head>
  <style>/* 完整 CSS */</style>
</head>
<body>
  <div class="slide">
    <!-- 当前页内容 -->
  </div>
  <script>
    // 左右键翻页（跳转到上/下一个文件）
    document.addEventListener('keydown', e => {
      if (e.key === 'ArrowLeft') location.href = 'slide-XX.html';
      if (e.key === 'ArrowRight') location.href = 'slide-XX.html';
    });
  </script>
</body>
</html>
```

#### 合并脚本

`merge.js` 读取所有 `slide-*.html`，提取 `<div class="slide">` 内容，合并为单文件：
```javascript
// 生成 slides.html，包含所有页
// 用于最终预览和 PPTX 转换
```

**必须遵循的技术规范**：

#### 容器与比例

**响应式 16:9 容器（必须使用此结构）**：

```css
body {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  overflow: auto; /* 关键：允许滚动 */
}

.slide {
  width: min(100vw - 40px, 177.78vh - 40px);
  height: min(56.25vw - 22.5px, 100vh - 40px);
  max-width: 1920px;
  max-height: 1080px;
  overflow: hidden;
  position: relative;
}
```

**关键点**：
- `body` 必须设置 `overflow: auto`，确保缩放时可以滚动
- `.slide` 宽高使用 `min()` 函数保持 16:9 比例
- 减去 padding（40px）避免溢出
- 设置 `max-width/max-height` 防止在超大屏幕上过大
- 所有内部元素尺寸使用 `vw` 单位相对于视口，而非容器

#### 字体规范

**展示字体**（h1/h2，从以下选一）：
Playfair Display, Fraunces, Syne, Bebas Neue, DM Serif Display, Cormorant Garamond

**正文字体**（p，从以下选一）：
DM Sans, Outfit, Figtree, Epilogue

**中文字体叠加**（必须）：
- 衬线展示字体 → 配 Noto Serif SC
- 无衬线展示字体 → 配 Noto Sans SC

展示字体与正文字体必须不同。禁止使用白名单以外的字体。

#### 配色规则

- 3色原则：主色（60%）+ 配色（30%）+ 点缀（10%）
- 用 CSS 变量统一管理
- 颜色必须匹配所选风格

```css
:root {
  --color-primary: #...;    /* 60% 背景/大面积 */
  --color-secondary: #...;  /* 30% 辅助/色块 */
  --color-accent: #...;     /* 10% 点缀/高亮 */
  --color-text: #...;
  --color-text-secondary: #...;
}
```

#### 美学规则

1. **视觉锚点**：每张幻灯片必须有一个最抢眼的元素 — 超大数字、粗体关键词、大色块或图表
2. **字号对比**：标题至少是正文字号的 3 倍（内容密集时可适当降低）
3. **正文可读**：
   - **标准页面**（≤5 个要点）：p/li 字号不小于 1.4vw
   - **内容密集页面**（6-10 个要点）：p/li 字号可降至 1.1vw
   - **高密度表格/列表**（>10 项）：字号可降至 0.9vw（最小值）
   - 禁止被色块遮挡
4. **字号分级体系**（vw 单位）：
   - 超大标题（封面）：4.5-5.5vw
   - 主标题（h1）：3.5-4.5vw
   - 副标题（h2）：2.2-2.8vw
   - 三级标题（h3）：1.6-2.0vw
   - 正文（p/li）：0.9-1.4vw（根据内容密度）
   - 辅助文字：0.8vw（最小）
5. **布局多样**：同文件内每张幻灯片使用不同布局
6. **装饰色块**：面积至少占幻灯片 20%，允许出血超出边缘
7. **标题允许压在色块上**，制造视觉张力
8. **禁止对 h1/h2 使用 `transform: rotate`** — 会破坏文档流
9. **留白与内容适配平衡**（关键原则）：
   - **目标**：在保证内容完整显示的前提下，最大化留白
   - **策略**：留白和字号是跷跷板关系，需要同步调整
   - **标准密度**（≤5项）：大留白 + 大字号
     - `.slide` padding: 80px, card padding: 30px, item gap: 30px
     - p 字号: 1.4vw, 行高: 1.6
   - **中等密度**（6-10项）：中等留白 + 中等字号
     - `.slide` padding: 50-60px, card padding: 18-20px, item gap: 18-20px
     - p 字号: 1.0-1.1vw, 行高: 1.5
   - **高密度**（>10项）：小留白 + 小字号
     - `.slide` padding: 40-50px, card padding: 15px, item gap: 16px
     - p 字号: 0.9vw, 行高: 1.4
   - **⚠️ 关键**：增加留白时必须减小字号/间距，否则会溢出
10. **内容区域高度自适应**：
   - ❌ 禁止对内容容器设置固定 `height: 60%` 等百分比高度
   - ✅ 使用 `max-height: 85%` 或让容器自适应内容
   - ✅ 对 `.slide` 设置 `padding` 预留边距，而非限制内容高度
   - 原因：固定高度会截断超出内容，自适应高度确保所有内容可见

#### 内容密度自适应

根据单页内容量自动调整字号和间距：

```javascript
// 内容密度判断（在生成 HTML 前评估）
function getDensityLevel(content) {
  const itemCount = content.要点数量 + content.表格行数;
  if (itemCount <= 5) return 'standard';      // 标准密度
  if (itemCount <= 10) return 'medium';       // 中等密度
  return 'high';                              // 高密度
}

// 字号与间距配置（必须同步调整）
const densityConfig = {
  standard: {
    // 字号（大）
    h1: '4.5vw', h2: '2.5vw', h3: '1.8vw', p: '1.4vw',
    // 间距（大）
    slidePadding: '80px', contentGap: '40px', cardPadding: '30px',
    itemGap: '30px', lineHeight: '1.6'
  },
  medium: {
    // 字号（中小）- 精确校准以消除溢出
    h1: '3.5vw', h2: '2.0vw', h3: '1.35vw', p: '0.95vw',
    // 间距（紧凑但保持可读）- 为 9 项内容优化
    slidePadding: '50px', contentGap: '24px', cardPadding: '16px',
    itemGap: '16px', lineHeight: '1.45'
  },
  high: {
    // 字号（小）
    h1: '3.2vw', h2: '1.8vw', h3: '1.3vw', p: '0.9vw',
    // 间距（小）
    slidePadding: '40px', contentGap: '20px', cardPadding: '15px',
    itemGap: '16px', lineHeight: '1.4'
  },
};
```

**应用示例（三级服务体系 - 9 项内容）**：

Medium 密度配置（精确校准，零溢出）：
- ✅ h3 标题: **1.35vw**（卡片标题，稍微缩小）
- ✅ p 描述: **0.95vw**（从 1.0vw 微调，彻底消除溢出）
- ✅ slide padding: **50px**（保持适度留白）
- ✅ card padding: **16px**（从 18px 减小，节省垂直空间）
- ✅ item gap: **16px**（从 18px 减小，紧凑但不拥挤）
- ✅ line-height: **1.45**（从 1.5 微调，节省行间距）

**关键调整**：每个参数微调 10-15%，累计节省约 40-50px 垂直空间

**留白与字号平衡策略**：

```css
/* ✅ 最优：medium 密度精确配置（9 项内容零溢出） */
.slide {
  padding: 50px;  /* 保持适度留白 */
}

.level-items {
  gap: 16px;  /* 从 18px 减小，节省垂直空间 */
}

.level-item {
  padding: 16px;  /* 从 18px 减小，累计节省空间 */
}

.item-title {
  font-size: 1.35vw;   /* h3 标题微调 */
}

.item-desc {
  font-size: 0.95vw;   /* 从 1.0vw 微调，彻底消除溢出 */
  line-height: 1.45;   /* 从 1.5 微调，节省行间距 */
}

/* ⚠️ 次优：会有轻微溢出（10-15px） */
.slide {
  padding: 50px;
}
.item-desc {
  font-size: 1.0vw;    /* ⚠️ 稍大，导致 10px 溢出 */
  line-height: 1.5;
}
/* 结果：4个元素超出 10px */

/* ❌ 错误：留白过大 + 字号过大 = 严重溢出 */
.slide {
  padding: 60px;       /* ❌ 留白太大 */
}
.item-desc {
  font-size: 1.1vw;    /* ❌ 字号太大 */
}
/* 结果：底部内容被截断 44px！ */

/* ❌ 错误：留白过小 = 拥挤感 */
.slide {
  padding: 40px;       /* ❌ 留白太小 */
}
.level-items {
  gap: 10px;           /* ❌ 过于密集 */
}
/* 结果：视觉窒息，没有呼吸感！ */
```

**关键原则**：留白增加 → 字号必须减小，否则必定溢出

**高度控制示例**：

```css
/* ❌ 错误：固定高度会截断内容 */
.framework-container {
  height: 60%;  /* 危险！内容可能被截断 */
}

/* ✅ 正确：自适应高度 */
.framework-container {
  width: 100%;
  max-height: 75%;  /* 最大高度限制，但允许更小 */
  display: flex;
  gap: 40px;
  /* 不设置固定 height，让内容自适应 */
}

/* ✅ 或者用 flex 布局自动分配空间 */
.slide {
  padding: 60px;  /* 通过 padding 控制边距 */
  display: flex;
  flex-direction: column;
}
.framework-container {
  flex: 1;  /* 占据剩余空间 */
  min-height: 0;  /* 允许收缩 */
}

/* ❌ 禁止内容区域出现滚动条！演示文稿必须一屏显示 */
.level-items {
  overflow-y: auto;  /* ❌ 错误！产生滚动条 */
}

/* ✅ 正确：让内容自动换行或收缩，而非滚动 */
.level-items {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  /* 不设置 overflow-y: auto */
}
```

#### 图表规则

使用 Chart.js（从 cdnjs 加载）：

- 禁止使用 Chart.js 默认图例，用自定义 HTML 图例
- 图表容器必须设置：明确 vw 高度 + `overflow: hidden` + `position: relative`
- canvas 用内联 style 设置高度：`style="height: 18vw; width: 100%"`
- 图表颜色匹配所选风格配色

#### 导航

仅键盘左右箭头切换，禁止显示导航按钮。

#### 代码质量

JavaScript 中所有引号、尖括号必须保持原始字符，禁止 HTML 实体转义。

#### 内容截断检查清单

生成 HTML 后必须检查：

1. **高度设置检查**：
   - 搜索代码中的 `height: XX%`
   - 如果对内容容器使用了固定百分比高度 → 改为 `max-height` 或删除

2. **Overflow 检查**：
   - `.slide` 必须保持 `overflow: hidden`（维持比例）
   - 内容容器可以用 `overflow: visible` 或 `overflow: auto`

3. **内容计数验证**：
   - 9 项内容 → padding 60px + 字号 1.1vw
   - 如果仍然截断 → 检查是否有固定高度限制

4. **分栏布局注意**：
   - 三栏布局时，每栏内容高度应相近
   - 如果某栏明显更长 → 考虑重新分配内容或调整字号

### Step 4: 渲染 HTML 为 PNG

所有单页生成完成后，使用系统内置工具 `pptx_html2png` 渲染：

```bash
# 调用内置工具（不需要安装 npm 依赖）
pptx_html2png(workDir='ppt/training')  # 替换为实际子目录路径
```

工具会自动：
1. 扫描目录下所有 `slide-*.html` 文件
2. 使用 Puppeteer 无头浏览器逐个渲染（1920x1080，16:9 高清）
3. 等待 Google Fonts 加载完成
4. 截图保存为 `slide-*.png`

告知用户：

```
✅ 已生成 N 张 PNG 图片

预览方式：
- 浏览器打开 ppt/training/slide-01-封面.html（编辑前预览）
- 图片查看器打开 ppt/training/slide-01-封面.png（最终效果）

如需调整：
- "第3页标题改为..." → 我直接修改 slide-03.html
- 修改后重新调用 pptx_html2png 渲染
```

**渲染优势**：
- ✅ 完美保留所有 CSS 样式（渐变、阴影、伪元素、flexbox 布局）
- ✅ 无需担心 PPTX 转换丢失信息
- ✅ 可直接用于演示、打印、分享

### Step 5: 组装 PNG 为 PPTX

用户确认效果满意后，使用系统内置工具 `pptx_png2pptx` 组装：

```bash
# 调用内置工具（不需要安装 npm 依赖）
pptx_png2pptx(workDir='ppt/training')  # 替换为实际子目录路径
```

工具会自动：
1. 扫描目录下所有 `slide-*.png` 文件
2. 按编号排序
3. 每张 PNG 作为一页幻灯片的全屏背景图片
4. 生成 `演示文稿.pptx`

**输出特点**：
- 每页为全屏 PNG 图片（非可编辑文本）
- 完美保留 HTML 设计的所有细节
- 可在 PowerPoint 中添加动画、备注、图层元素

**禁止行为**：
- ❌ 不要使用 `npm install` 或 `bash` 在工作目录安装依赖
- ❌ 不要生成 `package.json`, `html2png.js`, `png2pptx.js` 等脚本文件
- ✅ 只调用 `pptx_html2png` 和 `pptx_png2pptx` 两个内置工具

### Step 6: 输出状态

```
--- BID-PPT COMPLETE ---
输出目录: ppt/
输出文件: {ppt/slides.html, ppt/演示文稿.pptx}
幻灯片数: {N}
设计风格: {风格名称}
图表数: {N}
状态: SUCCESS
--- END ---
```

## AUTO_MODE 行为

当由 bid-manager 调度（AUTO_MODE=true）时：
- 风格默认: Swiss Typography（商务场景最通用）
- 内容从 `分析报告.md` 和 `响应文件/` 自动提取
- 跳过预览迭代，直接生成 HTML + PPTX
- 幻灯片数量: 10-15 页（覆盖项目概述、技术方案摘要、实施计划、报价摘要）

## 常见场景模板

### 投标答辩 PPT

```
1. 封面（项目名称 + 公司名 + 日期）
2. 公司介绍（资质、案例、团队）
3. 对项目的理解（需求摘要）
4. 技术方案概述（架构图）
5. 实施方案（里程碑甘特图）
6. 项目团队（组织架构图）
7. 售后服务（响应时间、保障措施）
8. 报价摘要（总价 + 构成）
9. 优势总结（3个核心优势）
10. 致谢
```

### 项目汇报 PPT

```
1. 封面
2. 汇报提纲
3. 项目背景与目标
4. 工作进展（里程碑完成情况）
5. 关键成果（数据支撑）
6. 问题与风险
7. 下一步计划
8. 致谢/Q&A
```

### 述职报告 PPT

```
1. 封面（姓名 + 职位 + 述职周期）
2. 工作概览（关键指标大数字）
3-6. 重点工作（每页一项，成果+数据）
7. 个人成长与学习
8. 下一年规划
9. 致谢
```

## 注意事项

1. **内容为王**：设计服务于内容，不要为了设计感牺牲信息传达
2. **一页一事**：每页只传达一个核心信息
3. **数据说话**：能用数字的不用文字，能用图表的不用表格
4. **中文排版**：注意中文字体渲染，避免字体回退到系统默认
5. **打印友好**：如果用户可能需要打印，避免深色背景风格
6. **文件大小**：PPTX 控制在 10MB 以内，图表优先用矢量
7. **禁止滚动条**：演示文稿必须一屏显示所有内容，禁止任何内容区域出现滚动条（`overflow-y: auto`）

## 内容完整性与视觉平衡自检清单

在生成 HTML 后、调用 `pptx_html2png` 前，必须自检以下 5 点：

### 1. 检查是否有固定高度限制
```bash
# 搜索危险的固定高度设置
grep -n "height: [0-9]*%" ppt/*/slide-*.html
```
✅ 期望结果：仅 `.slide` 容器有固定高度，内容容器不应有
❌ 如发现 `.framework-container`、`.content-area` 等内容容器有 `height: 60%`，必须修改为 `flex: 1` 或 `max-height`

### 2. 检查是否有滚动条
```bash
# 搜索滚动条设置
grep -n "overflow-y: auto" ppt/*/slide-*.html
```
✅ 期望结果：无任何匹配（演示文稿禁止滚动条）
❌ 如发现任何 `overflow-y: auto` 或 `overflow: auto`（除了 `body` 标签），必须删除

### 3. 验证字体大小是否符合内容密度
对于 9 项内容的幻灯片：
- 标题字号：1.5vw（item-title）
- 描述字号：1.1vw（item-desc）
- 行高：1.5

对于 15+ 项内容的幻灯片：
- 标题字号：1.3vw
- 描述字号：0.9vw
- 行高：1.4

### 4. 检查留白与字号平衡
```bash
# 检查 padding/gap 和字号是否平衡
grep -n "padding:\|gap:\|font-size:" ppt/*/slide-*.html | grep -E "(slide|item)"
```
对于 medium 密度（6-10 项内容），精确配置：
- ✅ **最优（零溢出）**: `padding: 50px` + `p: 0.95vw` + `gap: 16px` + `card: 16px` + `line-height: 1.45`
- ⚠️ **次优（轻微溢出）**: `padding: 50px` + `p: 1.0vw` + `gap: 18px` → 溢出约 10px
- ❌ **错误**: `padding: 60px` + `p: 1.1vw` → 溢出 44px+

**微调策略**（针对 10px 级别的溢出）：
1. 优先调整字号: `p: 1.0vw → 0.95vw`（节省约 15-20px）
2. 其次调整间距: `gap: 18px → 16px`（每个 item 节省 2px，9个累计 18px）
3. 再调整 padding: `card: 18px → 16px`（每个 card 节省 4px，9个累计 36px）
4. 最后调整行高: `line-height: 1.5 → 1.45`（多行文本节省约 10-15px）

**目标**: 溢出检测显示 "溢出 0px, 0 个元素被裁剪"

### 5. 在浏览器中预览验证
```bash
# 打开 HTML 文件，检查视觉平衡
file://path/to/slide-06-三级服务体系.html
```
✅ 期望结果（同时满足）：
  - ✅ 所有内容完整可见，无滚动条，**底部无溢出**（最高优先级）
  - ✅ 内容与边缘有明显间距（不紧贴边框）
  - ✅ 卡片之间、文字之间有舒适的呼吸感
  - ✅ 整体布局平衡，不会过于拥挤或松散

❌ 如发现问题，按优先级修复：
  - **P0: 底部溢出/截断** → 立即减小字号（p: 1.1vw → 1.0vw）或减少 padding（60px → 50px）
  - **P1: 滚动条出现** → 移除 `overflow-y: auto`
  - **P2: 过于拥挤** → 在不溢出前提下，增加 padding/gap
  - P3: 过于松散 → 增加字号或减少留白（但保持 padding ≥ 40px）

**调试流程**：
1. 如果溢出：优先减小字号 0.1vw，再减小 padding 10px
2. 如果拥挤：优先增加 gap，再增加 padding（但监控是否溢出）
3. 迭代调整，直到达到平衡点
