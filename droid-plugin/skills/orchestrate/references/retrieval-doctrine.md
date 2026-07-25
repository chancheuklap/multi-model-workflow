# Retrieval Doctrine · 结构候选与亲验

结构性问题包括调用/引用、连接、依赖路径和影响面。图与语言服务器只缩小搜索空间，源码才是证据。

1. **先拿候选。** 上游可用 Serena；Droid 自身有新鲜 `graphify-out/graph.json` 时用 Execute 调 graphify `query` / `affected` / `path` / `explain`。
2. **再亲验。** 每项回目标 checkout 用 Read/Grep 核对。进入 finding、plan、investigating、handoff 或交付物的承重结论必须给 `file:line`。
3. **无损退化。** Serena 不可用、图缺失/过期、歧义、失败或空结果时退到 Graphify + Read/Grep；空结果不证明不存在。

Serena 不能单独证明装饰器 endpoint 的完整调用方、`await import()` 后解构的动态引用，以及跨语言/配置/反射边。命中时记 `unsupported`，用 Graphify 与源码检索补证。

## 候选传输合同

每项精确六字段，无额外字段：

```json
{"tool":"serena|graphify","query":"...","status":"used|not_available|unsupported|failed","locators":["..."],"summary":"...","fallback_reason":"..."}
```

结构派发使用 `--retrieval-candidates <absolute-json-file>`；脚本 fail-closed 校验并把规范化快照嵌入 prompt/brief。省略时固定为 `[]`。内部 investigate 的每个 `topics[]` 使用 `retrieval_candidates`。

候选只表示上游检索，不代表下游调用过工具，也不授予新工具。所有 Droid 定义继续保持 `mcpServers: []`；Droid worker 不声称直接调用 Serena，只能消费上游 Serena 候选并自行 Execute Graphify/源码亲验。resume 沿用原会话和快照。

## 回执

结构任务回执必须单列“结构候选”，分别写上游候选、worker 实际工具调用、源码亲验 locator 和 fallback 原因。冒充调用或缺源码亲验均不合格；主线程按缺 `file:line` 同级打回。

本 doctrine 不授权安装 graphify、启用 hook/strict，也不降低原有证据门。
