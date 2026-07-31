---
name: bid-poc
description: >
  基于需求规格书自动生成每个系统的系统原型前端页面（内部代号 POC，产出到 poc/ 目录）。
  不属于 web-builder 交互式流程，而是 bid-manager pipeline 的专用 AUTO_MODE skill——
  从需求文档直接生成完整 HTML/CSS/JS 原型，无需用户输入。逐系统处理，产出到 poc/{SXX}-{Name}/ 目录。
  当用户要求"自动生成POC"、"自动生成原型"、"批量生成原型"时触发；由 bid-manager S8 自动调用。
  前置条件：bid-requirements 已完成，项目文档/01-需求分析/ 下有系统需求文档。
tools: [read, write, bash]
---

# 自动 POC 生成

## 工作模式

**AUTO_MODE 专用** — 不向用户提问、不等待确认、不要求设计偏好。一切从需求规格文档驱动。

## 前置检查

1. 确认需求规格 metadata 存在：
   ```bash
   test -f 项目文档/01-需求分析/_metadata.md && echo "OK" || echo "MISSING"
   ```
   如果 MISSING，输出 `状态: SKIPPED, 原因: 需求规格未完成` 并结束。

2. 从 metadata 提取系统清单（`## 系统拆分计划` 表格），过滤出需要 POC 的系统。

   **判定规则**：功能原型分类中属于以下原型的系统**需要 POC**：
   - 数据录入/维护（CRUD 表单界面）
   - 统计/分析/报表（仪表盘/图表界面）
   - 管理/配置/权限（后台管理界面）
   - 流程/闭环/审批（工作流界面）
   - 移动端/扫码（移动端界面）

   不属于以上类别的系统（如纯集成/同步/对接类，或文书/报告类）**不需要 POC**，
   在状态摘要中标记为 `无UI原型` 并跳过。

3. 列出需要生成的 POC 清单。

## 工作流程

### 0. 初始化

在 `<workDir>/poc/` 目录下创建 `.gitkeep` 标记文件（如果目录不存在则先创建目录）。

0.1 读取 system_decomposition.json，提取所有 systems[].code 与 name，作为子系统目录命名的唯一事实源。

0.2 幂等清理（每次运行必做）：列出 poc/ 下已有子目录，凡目录名（按 S0x 前缀 + 名称，名称先按 0.3 的归一化规则处理）不在 systems 列表中的，一律 rm -rf 删除——这是上次错位运行的遗留物，会污染下游截图与正文引用。

0.3 目录命名硬约束：每个子目录名必须为 {code}-{name}。name 取自 system_decomposition.json，但**文件系统不安全字符（/ \\ : * ? " < > | 及空格）须统一替换为连字符 -** 后再作为目录名（例：name 为 `Mini-CEX/DOPS评价系统` 时，目录名为 `S07-Mini-CEX-DOPS评价系统`）。清理比对与命名时，两侧都先做同一归一化再比较，避免因 `/`→`-` 误判为孤儿目录而误删。不得自行改写系统名，不得编造 system_decomposition.json 中不存在的系统（如把数字教材/医学数据库当作独立子系统目录）。

### 1. 逐系统生成

对每个需要 POC 的系统，按以下步骤执行：

#### 1.1 读取需求规格

```
read 项目文档/01-需求分析/{SXX}-{Name}.md
```

从需求文档中提取：
- **系统名称和编号**（如 S04-性能预报系统）
- **核心功能点**（P1/P2 优先级，每个功能点的 UI 特征）
- **功能原型分类**（从 metadata 获取，决定页面布局模式）
- **关联角色**（决定导航和权限视觉）
- **数据实体**（决定表格列、图表维度、表单字段）

#### 1.2 确定布局模式

| 原型分类 | 布局模式 | 典型组件 |
|---------|---------|---------|
| 数据录入/维护 | 表单+表格双栏 | 搜索筛选栏、CRUD 表单、分页表格、导入导出按钮 |
| 统计/分析/报表 | 仪表盘 KPI 卡片+图表网格 | 数字卡片、Chart.js 图表、时间范围选择器、下钻表格 |
| 管理/配置/权限 | 侧边栏导航+表单区 | 树形权限表、配置开关/滑块、角色标签、审计日志表格 |
| 流程/闭环/审批 | 流程看板+详情抽屉 | 状态列、拖拽卡片、审批按钮、时间线、评论框 |
| 移动端/扫码 | 全屏卡片+底部导航 | 扫码按钮、卡片列表、Big Number 展示、下拉刷新 |

#### 1.3 生成 POC 文件

依次用 `write` 工具写入以下文件到 `poc/{SXX}-{Name}/`：

1. **`index.html`**（先写）— 完整的单页 HTML，包含：
   - 系统标题 + 导航/标签切换
   - 按 P1/P2 组织的功能区域
   - TailwindCSS CDN + Chart.js CDN（如有图表）
   - 内联的 Alpine.js 状态管理（轻量，不新建 .js 文件即可运行）
   - 页面级样式注入（`<style>` 标签）

2. **`style.css`** — 补充的自定义 CSS：
   - 配色变量（深蓝/indigo 主题）
   - 自定义滚动条
   - 卡片毛玻璃/阴影效果
   - 过渡动画

3. **`script.js`** — 交互逻辑：
   - Chart.js 图表初始化和模拟数据
   - Tab 切换（必须用 `switchTab(tabId)` 函数，tabId 在 manifest 中声明）
   - 模态框/抽屉开关
   - 表单验证
   - 搜索过滤
   - 模拟实时数据更新

   **Chart.js 硬约束（违反会导致预览页面无限拉高）**：每个 `<canvas>` 必须包在**显式固定高度的容器**里：
   ```html
   <div class="relative h-64"><canvas id="trendChart"></canvas></div>
   ```
   禁止把 `<canvas>` 直接放进卡片 div、禁止用 `height="200"` 属性代替容器。原因：`responsive: true, maintainAspectRatio: false` 时 Chart.js 会把 canvas 高度撑到父容器高度；父容器高度若由 canvas 内容决定，resize 检测会形成正反馈——canvas 每帧长高一点，下方控件逐步下移、整个页面逐渐拉高。`height` 属性会被 Chart.js 的内联 style 覆盖，不起约束作用。

4. **`.manifest.json`**（最后写）— **功能点-Tab 映射契约**，供下游 `bid-poc-screenshots` 精确截图：

   ```json
   {
     "system": "S04-性能预报系统",
     "functionPoints": [
       {
         "id": "S04-001",
         "name": "实时性能预报",
         "tabId": "realtime",
         "tabLabel": "实时性能预报",
         "priority": "P1",
         "switchMethod": "switchTab('realtime')"
       },
       {
         "id": "S04-002",
         "name": "多方案优化比选",
         "tabId": "optimization",
         "tabLabel": "多方案优化比选",
         "priority": "P2",
         "switchMethod": "switchTab('optimization')"
       }
     ]
   }
   ```

   **manifest 规则：**
   - `id` / `name`：从需求规格书逐字复制功能编号和名称
   - `tabId`：POC 中该功能对应 Tab 的 id（与 `tabs` 数组 / `switchTab()` 参数一致）
   - `tabLabel`：Tab 按钮上显示的文字（截图时用于匹配技术方案小节标题）
   - `switchMethod`：切换到该视图的可执行 JS（如 `switchTab('realtime')`）
   - **每个 P1 功能点必须有一条 manifest 记录**，P2 功能点如有独立 Tab 也记录
   - **tabId 唯一性（强制）**：manifest 中每个 functionPoint 必须对应唯一 tabId，不得让多个 functionPoint 共享同一 tabId。若一个 tab 承载多个功能点，必须拆分为独立 tab（如 dashboard-arch / dashboard-security），或对该 tab 只记录一次并把多个功能点 id 关联到同一截图。违反将导致下游 screenshot-poc.js 重复截图。

   这个文件是 POC 和截图之间的**显式契约**，确保截图能精确定位到每个功能视图。

#### 1.4 质量检查（生成后立即执行）

```
read poc/{SXX}-{Name}/index.html
```

确认：
- HTML 结构完整（`<!DOCTYPE html>` → `</html>`）
- 引用的 `style.css` 和 `script.js` 已生成
- 没有 `[TODO]`、`[PLACEHOLDER]`、`[待实现]` 残留
- 所有 P1 功能点有对应的 UI 区域
- 每个 `<canvas>` 都有固定高度容器包裹（见 1.3 Chart.js 硬约束）

如果检查不通过，修复后重新写入。

#### 1.5 进度汇报

每完成一个系统，输出进度块：

```markdown
--- BID-POC PROGRESS ---
系统: S04-性能预报系统
状态: SUCCESS
文件: index.html (12KB), style.css (3KB), script.js (8KB)
进度: 已完成 1/3, 下一个: S05-系统管理平台
--- END ---
```

如果生成失败：

```markdown
--- BID-POC PROGRESS ---
系统: S04-性能预报系统
状态: FAILED
原因: [具体错误信息]
--- END ---
```

## 设计规范

### 默认设计系统

AUTO_MODE 下使用统一的设计参数：

- 主色: `#4F46E5` (indigo-600)
- 辅助色: `#10B981` (emerald-500)
- 背景: `bg-gray-950` 深色主题
- 卡片: `bg-gray-900` + `border-gray-800`
- 字体: Inter (sans) + JetBrains Mono (mono)
- 圆角: `rounded-lg` / `rounded-xl`
- 阴影: `shadow-2xl` 用于模态框

### 功能区域标注

每个 P1 功能模块用一个独立的卡片/面板呈现：
- 卡片标题使用功能点名称（与需求规格一致）
- 在卡片右上角用小字标注 `S04-001` 功能编号
- P2 功能可合并到次要区域或折叠面板

### 页面措辞（截图会进标书，评委可见）

生成页面的 `<title>`、页头标题、角落标注中**禁止出现 "POC"、"Demo"、"概念验证" 字样**——这些页面截图会直接插入标书正文。页面自称用系统名称即可（如"S04 性能预报系统"），需要强调性质时用"系统原型"。

### 数据模拟

所有图表和表格使用模拟数据（不依赖后端 API）：
- 数字范围合理（如性能数据 0-100，用户数 100-10000）
- 包含至少 8-12 个数据点（够填满一个图表）
- 表格至少 5 行

## 完成状态

```markdown
--- BID-POC COMPLETE ---
状态: SUCCESS
POC 系统总数: 5
成功: 5 (S01, S02, S03, S04, S05)
跳过（无UI原型）: 1 (S06-数据同步，集成类)
失败: 0
POC 目录: <workDir>/poc/
S7 POC截图 可继续执行。
--- END ---
```

如果没有任何系统需要 POC：

```markdown
--- BID-POC COMPLETE ---
状态: SKIPPED
原因: 所有系统均为无UI原型类型，无需POC
--- END ---
```
