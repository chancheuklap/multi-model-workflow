---
name: serena
description: Proactively use during technical work when understanding unfamiliar code requires symbol definitions, direct references, implementations, or file symbol overviews; use Serena's read-only symbol results as candidates and verify them in current source.
---

# Serena 静态符号候选检索

本 skill 随 MMW Cursor 插件分发（`skills/serena/`）。Serena MCP 由同一插件的 `mcp.json` + `scripts/serena-mcp.sh` 启动；上游二进制来自 `uv tool` 包 `serena-agent`，启动时若有新版本会先检测再升级，并通过合同自检保证四个只读工具仍在。

Serena 通过语言服务器读取当前 checkout 的静态符号。用户只需描述功能目标、体验问题或设计方向；当调查需要理解陌生符号、实现或直接引用时，Agent 主动使用，不等待用户提出技术检索问题。简单且路径明确的局部改动无需形式化调用。

## 四个只读工具

| 目的 | 工具 | 关键输入 |
| --- | --- | --- |
| 找定义或读取符号体 | `find_symbol` | 符号名；已知文件时传仓库相对路径 |
| 找静态引用 | `find_referencing_symbols` | 定义符号名与定义文件相对路径 |
| 看文件符号概览 | `get_symbols_overview` | 文件相对路径，不传目录 |
| 找接口或类型实现 | `find_implementations` | 定义符号名与定义文件相对路径 |

工具名可能带 MCP 前缀，语义不变。结果只作为候选：记录符号和相对路径，再用 `grep` 定位并用 Read 阅读当前源码。只有源码亲验后的结论才能进入设计、计划、审查、修复或交付说明。

## 转交边界

- 空结果不能证明仓库中不存在目标。
- 语言服务器不支持 implementation 查询时，诚实记录失败并回源码检索。
- 装饰器注册、运行时反射、字符串协议、跨服务 route、IPC、事件主题和动态导入关系转交 Graphify，并继续源码亲验。
