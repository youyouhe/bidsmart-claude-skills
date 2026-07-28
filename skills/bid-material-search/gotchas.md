# bid-material-search - Gotchas

这些是从实践中学到的反直觉知识和常见陷阱。

## Gotchas

### 实体优先，不要只跑一次关键词就放弃

**问题**：既往只用关键词 `search_documents` 盲搜，`kb_search`（语义/多跳）/ `kb_get_entity_graph`（实体图谱）零引用，导致库里明明有的公司/资质搜不到，用户被迫三次催促才搜全。

**解决**：按"实体优先"链路检索——已知公司/人员先 `get_company_complete`/`get_person_complete`，再 `list_entity_documents` 下钻枚举，再关键词 `search_documents`，前三级零命中才上 `kb_search`（语义多跳，能找到关键词搜不到的关联材料），仍零命中用 `kb_get_entity_graph` 探关系。各级命中累积，不互相替代。

---

### 零命中必须显式报告，不得静默保留占位符

**问题**：占位符走完检索链路仍零命中时，既往既不计入 `failed_count`、也不在摘要单列，占位符被原样保留却看起来"完成了"，用户不知道哪些没替换。

**解决**：零命中占位符**必须**列入"未替换占位符清单"，计入 `failed_count`（语义界定为"零命中"而非"下载失败"），完成状态块报告 `未替换占位符: N` 及清单。禁止混入 `ambiguous_count`，禁止静默假装完成。

*（来自 2026-07 一键投标复盘，注入时间：2026-07-28）*
