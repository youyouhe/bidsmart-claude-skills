# bid-system-decomp - Gotchas

这些是从实践中学到的反直觉知识和常见陷阱。

## Gotchas

### 系统编号是全流水线唯一事实源，下游不得重划

**问题**：历史上 tech-proposal 跟招标原文编号走、requirements/POC 跟 S 编号走，两套坐标系从未对齐，导致 S01 臃肿、S02 缺失、POC 子目录跳号，被追问时只能临场编造两套矛盾解释。

**解决**：本 skill 产出的 `system_decomposition.json` 是系统分解的**唯一契约**。S 编号（S01/S02…）在这里首次且唯一地产生，必须连续不跳号。下游 tech-proposal / requirements / poc / poc-screenshots 一律消费此 json，禁止各自重新划分、重命名或跳号。

---

### original_refs 是反幻觉锚点，缺它即捏造

**问题**：系统分解本质是聚类推断，容易凭"行业经验"凭空造出原文没有的系统。

**解决**：每个 system **必须**带 `original_refs`，回溯到 `分析报告.md#技术需求` 的原文章节号/编号（如 `(五)过程管理`、`4.2.1.1`）。列不出 original_refs 的 system 不得写入 json。自检时抽 2 个 system 回读原文核对锚点真实存在。

---

### totals 计数必须可被下游校验

**问题**：曾出现"61项/9▲/3★"被反复断言却从未核实，bid-assembly 也不比对 ▲ 数。

**解决**：完成状态块必须输出 `系统数/功能点/▲/★` 计数，且 `totals.function_points` == 各 system `function_point_count` 之和。这些计数直接喂给 bid-assembly 做 ▲/★ 核对、喂给 bid-manager 做完成度验证——错了会一路传到最终标书。

*（来自 2026-07 一键投标复盘，注入时间：2026-07-28）*
