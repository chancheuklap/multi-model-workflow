# mmw-v2

活的那一层：技能、subagent、安装器。不负责上一代任何东西。

- 没有仓库级测试入口；每个自研技能自带 `mmw-v2/skills/<名>/tests/run.sh`，分别跑。现有三份：`exe-release`、`ui-qa`、`manage-agents-md`。
- `install.sh` 从哪个 checkout 跑，宿主软链就指向哪个路径；在 worktree 里跑会把五个宿主都指到 worktree。只从主 checkout 跑。
- 每份 `mmw-v2/skills/<名>/tests/run.sh` 把输出里出现 `: unbound variable`、`: integer expression expected`、`: command not found`、`syntax error near` 的「通过」当失败，因为这些错在 `$( )` 里只杀子 shell。新加 runner 照抄这段。
- 没装 `uv` 时 runner 退出 1 并点名少跑了哪些，不静默跳过。
- Python 测试没有 `conftest.py`；每个测试文件自己把技能的 scripts 目录放进 `sys.path`。
