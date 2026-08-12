---
date: 2026-08-13
amends: []
---

# 界面 QA 的三个运行时依赖装在 runtime 外面，入口是独立命令不是 mmw 子命令

界面 QA 要三个 npm 包：浏览器自动化框架、可访问性规则引擎、设计系统格式校验器。它们由 `mmw/install.sh` 装进 `$MMW_RUNTIME_HOME/ui-qa`——跟 runtime 平级，不在 runtime 里面。技能通过 `mmw-ui-qa` 这个独立命令定位它们，命令跟 `mmw` 一样装进 `BIN_DIR`。

## Considered Options

**装进 runtime 里面**，否决，三条理由：Codex 与 Claude Code 运行的是 `plugins/cache` 里的副本，`node_modules` 跟着复制会把插件撑大几百 MB，而它们并不需要这份副本；`install.sh` 的 `require_version_bump` 逐字 diff runtime 与已装副本，装在里面会因 `node_modules` 的差异误报「内容变了要升版本号」；依赖版本由 `deps.json` 管，跟产品版本号是两件事，不该绑在一起升。

**做成 `mmw` 的子命令**，否决。`mmw/cli/mmw` 开头写着准入判据：一个动作要么是多请求编排、要么是护栏、要么是宿主机械差异的落点、要么是没有 API 的固定套路。转发到三个已装好的 npm 包一条都不占。

**技能正文直接写依赖路径**，否决。`MMW_RUNTIME_HOME` 可配，写死就锁死了一种安装布局。技能正文写命令名、路径由命令当场算，跟技能正文写 `mmw artifact path` 而不写 `docs/specs/…` 是同一种做法。
