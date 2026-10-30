---
date: 2026-10-30
amends: [0007]
---

# 两个 CLI 的用户级提示词都软链接到已安装版本的 shared.md

MMW v4 的 Claude Code 与 Codex CLI 使用各自原生用户级入口，均软链接到已安装 checkout 的 `mmw-v4/prompt/shared.md`。正文只保留一份，删除 Codex 生成器与持续同步任务。开发分支不直接连接 host；已安装源只随主人明确授权的发布更新，运行中的 watch 继续遵守 Self-hosting boundary。

## 依据与迁移

0007 以 Codex 没有导入语法为由采用生成文件。0049 收窄到两个 host 后，v4 的生成器只加来源哈希，不再拼接专属正文。缺少导入语法不妨碍读取软链接。2026-10-30 用 Codex CLI 0.165.0 的 `debug prompt-input` 在隔离目录验证：普通用户级文件、指向项目外源的软链接均加载指令，源修改后的下一次加载只包含新内容。验证未发起模型请求。

安装先停掉并移除旧同步任务，再迁移提示词，避免旧生成器沿新链接写入源。旧 Codex 文件只有来源标记与正文哈希匹配才会被替换；手改文件和外来入口保留并报冲突。`--check` 只报告，`--back` 先摘掉两家的 v4 链接再交旧版接管。

## Considered Options

- 发布时写两份普通文件。可行，且适合 Claude Cowork，但当前 CLI 范围内多保留了正文副本和一致性检查。
- host 原生导入。Claude Code 支持导入，两个 host 没有已确认的共用接口，仍需两种适配。
- 启动时注入。要覆盖手动启动和每一种 runner，现有原生入口已经足够。
- 后台监听并生成。正文相同且不需转换，持续同步只增加中间状态。

## Consequences

两家读取同一正文，安装负责链接与一次性迁移，不再维护生成副本。源变化何时进入会话仍由 host 的加载机制决定。

该决定只覆盖两个 CLI。[Claude Code 的指令文档](https://code.claude.com/docs/en/memory)说明 Cowork 跳过用户级软链接；将 Cowork 纳入服务范围时需重审方案。[Codex 的指令文档](https://learn.chatgpt.com/docs/agent-configuration/agents-md)说明全局入口位于 `CODEX_HOME`，并在一次运行构建指令链。
