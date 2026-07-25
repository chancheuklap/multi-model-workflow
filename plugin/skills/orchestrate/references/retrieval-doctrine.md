# Retrieval Doctrine · 结构候选与亲验

结构性问题包括：谁调用或引用某符号、什么与什么连接、依赖路径，以及改动影响面。图与语言服务器只负责缩小搜索空间，源码才是证据。

## 顺序

1. **先拿候选。** Serena 可用时用符号工具取候选；仓库有新鲜 `graphify-out/graph.json` 时，可用 graphify `query` / `affected` / `path` / `explain`。按问题选一个合适入口，不为形式重复跑。
2. **再亲验。** 每个候选必须回目标 checkout 用 Read/`rg` 核对。写进 finding、plan、investigating、handoff 或交付物的承重结论必须给 `file:line`；验不过就删除或标未验证。
3. **无损退化。** Serena 不可用、图缺失或过期、查询歧义、工具失败或无结果时，直接退到 Graphify + Read/`rg`，不阻塞。空结果不等于不存在。

## 已知不支持模式

Serena 当前不能单独证明以下结构完整：

- 装饰器注册的 endpoint 全部调用方；
- `await import()` 后解构出来的动态引用；
- 跨语言、配置、字符串注册和运行时反射边。

命中这些模式时，把 Serena 状态记为 `unsupported`，并用 Graphify 与源码检索补证。

## 候选传输合同

主线程给内部 topic、worker 或 reviewer 传一个 JSON 数组。每项必须精确包含六字段，不能多也不能少：

```json
{"tool":"serena|graphify","query":"...","status":"used|not_available|unsupported|failed","locators":["..."],"summary":"...","fallback_reason":"..."}
```

结构派发使用 `--retrieval-candidates <absolute-json-file>`；脚本校验后把规范化快照写入派发状态目录并嵌入 prompt/brief。没有结构问题可以省略，脚本会固定为 `[]`；一旦传入，非绝对路径、坏 JSON、额外字段或错误类型一律 fail-closed。内部 investigate 的每个 `topics[]` 使用 `retrieval_candidates` 字段。

候选快照只说明**上游已做过什么检索**，不代表下游 worker 调过这些工具，也不授予新工具。resume 沿用原会话与落盘快照，不重新解释或静默丢失候选。

## 回执

计划、实现、调查和审查回执必须单列“结构候选”，分别写：

- 上游候选及状态；
- 本 worker 自己实际调用的工具；
- 源码亲验 locator；
- fallback 原因。

把上游候选冒充自己的工具调用，或缺少源码亲验，均视为不合格。主线程收到缺少“结构候选”行的结构任务回执时打回，效力与缺少 `file:line` 同级。

本 doctrine 不授权安装 graphify、启用 hook/strict，也不降低原有证据门。
