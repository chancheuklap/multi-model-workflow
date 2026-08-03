# Retrieval Doctrine · 结构候选与亲验

用户通常只给业务目标、体验问题或设计方向；主线程和 worker 在自己的调查、设计落地、计划、实现、调试和审查中遇到陌生代码、所有权、数据流、调用链或影响面时主动检索，不等待用户提出技术问题。简单明确的任务不为形式双跑。结构性问题包括调用/引用、连接、依赖路径和影响面；图与语言服务器只缩小搜索空间，源码才是证据。

1. **先拿候选。** Serena 可用时用符号工具；有新鲜 `graphify-out/graph.json` 时用 graphify `query` / `affected` / `path` / `explain`。按问题选合适入口。
2. **再亲验。** 每项回目标 checkout 用 read/grep 核对。进入 finding、plan、investigating、handoff 或交付物的承重结论必须给 `file:line`。
3. **无损退化。** Serena 不可用、图缺失/过期、歧义、失败或空结果时退到 Graphify + read/grep；空结果不证明不存在。

Serena 不能单独证明装饰器 endpoint 的完整调用方、`await import()` 后解构的动态引用，以及跨语言/配置/反射边。命中时记 `unsupported`，用 Graphify 与源码检索补证。

## 候选传输合同

每项精确六字段，无额外字段：

```json
{"tool":"serena|graphify","query":"...","status":"used|not_available|unsupported|failed","locators":["..."],"summary":"...","fallback_reason":"..."}
```

结构派发使用 `--retrieval-candidates <absolute-json-file>`；脚本 fail-closed 校验并把规范化快照嵌入 prompt/brief。省略时固定为 `[]`。内部 investigate 的每个 `topics[]` 使用 `retrieval_candidates`。

候选只表示上游检索，不代表下游调用过工具，也不授予新工具。Pi 只有花名册明确列出的角色可直接用四个 Serena 符号工具；synthesizer 不得获得。动态 workflow child 只消费候选，实际工具仍以其运行时白名单为准。resume 沿用原会话和快照。

## 回执

结构任务回执必须单列“结构候选”，分别写上游候选、worker 实际工具调用、源码亲验 locator 和 fallback 原因。冒充调用或缺源码亲验均不合格；主线程按缺 `file:line` 同级打回。

本 doctrine 不授权安装 graphify、启用 hook/strict，也不降低原有证据门。
