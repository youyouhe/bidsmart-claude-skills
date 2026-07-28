# bid-poc - Gotchas

这些是从实践中学到的反直觉知识和常见陷阱。

## Gotchas

### 系统清单/编号取自 _metadata.md（镜像自 system_decomposition.json）

**问题**：POC 子目录命名（`poc/S04-XX/`）曾与 tech-proposal 占位符里的系统编号对不上，因为两套坐标系各自划分。

**解决**：POC 子目录的 `S\d{2}` 编号**必须**与 `system_decomposition.json` 一致（经 `_metadata.md` 的 `## 系统拆分计划` 镜像传入）。不要自行重新编号系统。只读 `_metadata.md` 的系统表生成 POC；若 `_metadata.md` 缺失，先确认上游 system_decomposition.json / bid-requirements 是否跑过，不要自己临时分系统。

---

### ui_prototype 决定是否生成原型

**问题**：给纯集成/同步/文书类系统也生成了 POC，浪费工时且无意义。

**解决**：只对有 UI 界面的系统（数据录入/统计报表/管理配置/流程审批/移动端扫码）生成 POC。`system_decomposition.json` 的 `ui_prototype` 字段已做判定，直接消费，不要自行二次判断导致漂移。

*（来自 2026-07 一键投标复盘，注入时间：2026-07-28）*
