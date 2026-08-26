# 陷阱

- `install.sh` 只动自己记录在 `.mmw-skills`、`.mmw-agents` 里的链接；同名的别的东西报「冲突」、跳过、退出 1，直到人工删掉。
- 同名技能同时出现在 `~/.claude/skills` 和 `~/.agents/skills` 时，各家取舍不一致且都不报错：Cursor 取 `.claude` 那份，Codex 和 Grok 取 `.agents` 那份。所以 `~/.claude/skills` 里除了 `install.sh` 装的那份，不能再有同名的东西。
- `~/.codex/skills`、`~/.pi/agent/skills`、`~/.cursor/skills`、`~/.grok/skills` 是上一代的技能位置。`install.sh` 每次运行都摘一遍残链；`--check` 见到残留报「残留」并退出 1。
- `install.sh --check` 查的是本机宿主目录，红可能只是没重装；从 worktree 跑会把全部链接报「缺」。
- 改 `install.sh` 时用 `MMW_V2_HOME` 把所有安装位置整体改到一个临时根；`CODEX_HOME`、`PI_CODING_AGENT_DIR`、`PI_HOME` 也认。
- 冻结区：`archive/mmw/install.sh` 没有 `--check`，跑了会把活的安装整个换成上一代；`bash archive/mmw/test.sh` 已经跑不过；`archive/legacy-host-plugins/` 的 marketplace 清单仍然有效，把宿主指过去会装上退役的一代；`archive/mmw-setup/` 移回技能源会重新打破四项校验。
- 测试 runner 只靠退出码说话，输出不要接管道（`| tail`），管道会把红跑成绿。
- Python 测试依赖由各技能 `mmw-v2/skills/<名>/tests/run.sh` 的 `uv run --with` 在命令行传；单跑一个测试文件要照抄那一行。
- Mac 只有 bash 3.2：`"$var，"` 会把全角标点吞进变量名；写 `"${var}，"`。
- `.mmw.json` 只有 `paths.release` 被程序读（`exe-release` 用 jq 取）；其余三项是落点约定，没有读取方。
