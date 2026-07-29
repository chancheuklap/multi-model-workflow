---
name: graphify
description: Proactively use during technical work when a non-trivial codebase investigation requires module relationships, dependency paths, reverse impact, routes, IPC, events, or cross-language data flow; ensure the graph is fresh for the current checkout, then query it as a candidate index and verify every conclusion in current source.
---

# Graphify 结构候选检索

本 skill 随 MMW Cursor 插件分发（`skills/graphify/`）。Graphify MCP 是插件自带的包装器（`skills/graphify/scripts/graphify_mcp.py`），与 Serena 并列挂在 `mcp.json`；上游查询引擎来自 `uv tool` 包 `graphifyy` 的 `graphify` CLI。启动时若 CLI 有新版本会先检测再升级，合同自检失败则回滚到上一好用版本，**不会**改用官方 `graphify-mcp`/`graphify.serve`。

Graphify 是跨文件、跨模块和跨语言关系的**默认结构检索入口之一**。几乎每个仓库都应通过它制图并用它做关系/影响面检索；用户通常只描述功能目标或体验问题，Agent 在需要理解调用路径、数据流或影响面时主动查询，不等待用户点名。

## 使用顺序

1. 先读当前仓库规则，确认图谱路径、freshness 判据和项目自有构建入口。仓库规则优先于本 skill 默认值。
2. **优先用 Graphify MCP**（工具名 `graphify`）。一次调用内会 ensure，再按 `action` 查询：
   - `query` — 广泛关系
   - `affected` — 反向影响（可选 `depth`，默认 2）
   - `path` — 两点路径（必填 `to`）
   - `explain` — 节点邻接
3. MCP 不可用时再走 CLI：对本机 `graphify` 查图；ensure 用插件内
   `skills/graphify/scripts/graphify_ensure.py`（由 MCP/启动器自动带上）。
4. 项目声明了自有图谱构建入口时，按仓库规则执行；否则 ensure 用本插件脚本。
5. 记录候选后用 Grep/Read 亲验；只有源码亲验后的结论才能进入交付物。

## 边界

- 空结果不能证明代码中不存在该关系。
- 不安装 watch、Git hook 或后台服务。
- **禁止**改用官方 `graphify-mcp` / `python -m graphify.serve`。
- 静态符号优先 Serena；关系 / 影响面 / 跨语言路径优先 Graphify。
