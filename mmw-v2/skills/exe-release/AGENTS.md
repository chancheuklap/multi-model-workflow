# mmw-v2/skills/exe-release

出包引擎。不负责被打包产品的代码。

## 关键约定

- 整个仓库同一时间只有一个产品在 release；先 `<engine> close` 再下一个 `init`。
- 交付记录写到主 checkout 根的 `<release dir>/delivered/`（release dir 取 `.mmw.json` 的 `paths.release`），不写到任务 worktree。
- release key 里的 `${RELEASE_PLUGIN_DIR}` 在运行时展开成引擎自己的 `scripts/` 目录，替换只发生在 `scripts/release-flow.sh` 一处。

## 陷阱

- `bash mmw-v2/skills/exe-release/tests/run.sh` 要两分多钟，120 秒的命令超时会把它杀在半路，放后台或加大超时。
- Mac 上没有 PowerShell，`tests/check-generated-powershell.sh <构建机> <release.ps1>` 与 `tests/check-template-behaviour.sh <构建机>` 要送构建机跑；语法过了不代表判得对。

## 命令

| 命令 | 干什么 |
| --- | --- |
| `bash mmw-v2/skills/exe-release/tests/run.sh` | `scripts/` 改了就跑 |
| `uv run --quiet --with pytest --with 'pydantic>=2' python -m pytest <文件> -q` | 单跑一个 Python 测试 |
