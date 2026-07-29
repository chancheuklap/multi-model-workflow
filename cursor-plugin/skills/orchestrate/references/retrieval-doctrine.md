# Retrieval Doctrine · 结构候选与亲验

用户通常只给业务目标、体验问题或设计方向；主线程和 worker 在自己的调查、设计落地、计划、实现、调试和审查中遇到陌生代码、所有权、数据流、调用链或影响面时主动检索，不等待用户提出技术问题。简单明确的任务不为形式双跑。结构性问题包括调用/引用、连接、依赖路径和影响面；图与语言服务器只缩小搜索空间，源码才是证据。

1. **先拿候选。** 符号问题用 Serena MCP；关系 / 影响面 / 调用链 / 跨模块问题用 Graphify MCP（工具 `graphify`，`action=query|affected|path|explain`；服务器内先 ensure）。二者由本插件 `mcp.json` 并列提供。按问题选合适入口，不为形式重复跑。
2. **再亲验。** 每项回目标 checkout 用 read/grep 核对。进入 finding、plan、investigating、handoff 或交付物的承重结论必须给 `file:line`。
3. **无损退化。** Serena / Graphify MCP 不可用、ensure/查询失败、歧义或空结果时退到另一工具 + read/grep；MCP 都不可用时 Graphify 才退 CLI（插件内 ensure 脚本 + 本机 `graphify`）。空结果不证明不存在。

Serena 不能单独证明装饰器 endpoint 的完整调用方、`await import()` 后解构的动态引用，以及跨语言/配置/反射边。命中时记 `unsupported`，用 Graphify 与源码检索补证。

## 候选传输合同

每项精确六字段，无额外字段：

```json
{"tool":"serena|graphify","query":"...","status":"used|not_available|unsupported|failed","locators":["..."],"summary":"...","fallback_reason":"..."}
```

结构派发使用 `--retrieval-candidates <absolute-json-file>`；脚本 fail-closed 校验并把规范化快照嵌入 prompt/brief。省略时固定为 `[]`。内部 investigate 的每个 `topics[]` 使用 `retrieval_candidates`。

候选只表示上游检索，不代表下游调用过工具，也不授予新工具。Cursor 只有 agents 花名册明确列出的角色可直接用 Serena 四个符号工具与 Graphify `graphify`（由本插件 `mcp.json` 提供）；synthesizer 不得获得。investigate-topic 另可使用 Context7（`resolve-library-id` / `query-docs`）做外部库文档取证。工人 / 任务 wt 初始化仍可预热图谱（项目 `.cursor/worktree-init.sh` 优先，否则插件内 ensure 脚本）；查询走 Graphify MCP，不另起一套官方 `graphify-mcp`/`graphify.serve`。resume 沿用原会话和快照。

## 回执

结构任务回执必须单列“结构候选”，分别写上游候选、worker 实际工具调用、源码亲验 locator 和 fallback 原因。冒充调用或缺源码亲验均不合格；主线程按缺 `file:line` 同级打回。

本 doctrine 不授权安装 graphify、启用 hook/strict，也不降低原有证据门。
