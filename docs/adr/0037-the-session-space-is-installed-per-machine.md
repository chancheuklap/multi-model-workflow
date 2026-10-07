---
date: 2026-10-07
amends: [0035]
---

# 终端里的 `NMEM_SPACE` 由 `mmw-v3/install.sh` 每台机器装一次；仓库的 Space 仍由 `setup-mmw` 建，它只报告会话的 `NMEM_SPACE` 对不对

会话写 Memory 要两样东西：仓库的 Space，和会话环境里指向它的 `NMEM_SPACE`。前者每个仓库一次，`setup-mmw` 第 6 步建。后者对所有仓库是同一段 shell 代码：`mmw-v3/shell/nmem-space.zsh` 在终端进入一个仓库、以及每次出提示符之前，按 origin 把 `NMEM_SPACE` 设成这个仓库的 Space。`mmw-v3/install.sh` 的第十样东西是 `~/.zshrc` 里加载它的一段，两行标记夹着；以前手写在 `~/.zshrc` 里的同一段，安装时原地换掉。`setup-mmw` 的 `scripts/check.py` 多一行 `session NMEM_SPACE`，只报告（`note`），并说明这个会话写的 Memory 落在哪里。

## 要修的是什么

- 那一段只手写在一台机器的 `~/.zshrc` 里，没有安装器装它，也没有检查报它缺；换一台机器，所有会话静默写进 Default。
- 它把「这个仓库没有 Space」记一辈子：`setup-mmw` 刚建好 Space，跑它的终端和之后从这个终端开的会话仍然没有 `NMEM_SPACE`。现在没找到的 30 秒后再问，新建的 Space 在下一个提示符就生效。
- `setup-mmw` 建完 Space 不说这件事，它的检查也看不出会话不对。

## Considered Options

- **做成 `setup-mmw` 的一步。** 否决。这段代码对每个仓库都一样，每台机器一次；放进 `setup-mmw` 就要在每个仓库重复，或者让一个仓库级的技能去改用户的 shell 配置。`check.py` 的 machine 层本来就只报不装。
- **direnv，每个仓库一份 `.envrc`。** 否决。本机没有 direnv；每个仓库还要一份文件和一次 `direnv allow`，而 Space 的 id 本来就能从 origin 算出来。
- **nmem 自己按目录选 Space。** 不存在：nmem 0.10.89 只认 `NMEM_SPACE` 和每条命令的 `--space`。
- **会话 `NMEM_SPACE` 不对时，`check.py` 报 `missing`。** 否决。那是会话的环境，不是仓库的配置；第一次配置的会话永远不对，报 `missing` 会让每次配置都以 `SETUP INCOMPLETE` 收尾。开夜时 `dispatch.sh` 照旧拒绝（0035）。

## Consequences

- `install.sh` 写 `~/.zshrc`，改之前留一份 `~/.zshrc.bak-`。手写那一段认不全时，安装报冲突，不动文件。
- 只有在终端上的 zsh 运行它；脚本和 agent 的工具 shell 不运行，它们带着起来时的环境。从不经过终端开的会话仍然没有 `NMEM_SPACE`，0035 的拒绝照旧。
- 每个提示符前多一次 `git remote get-url`；仓库没有 Space 时，每 30 秒多一次 `nmem spaces show`，约 0.1 秒。
