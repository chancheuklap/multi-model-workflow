---
date: 2026-10-07
amends: [0032]
---

# 从 v3 退回 v2，是在装着的 checkout 里跑一次 `bash mmw-v2/install.sh`；`mmw-v2/` 因此是退路，不只是历史

`mmw-v2/install.sh` 接管 `mmw-v3/install.sh` 装过的机器，和 v3 接管 v2 是同一个机制：指向 `mmw-v3/skills/` 的技能软链算本仓库装的，同名的原地改指 v2，v2 没有的摘掉；`~/.claude/CLAUDE.md` 从 `mmw-v3/prompt/` 改指 v2；v3 挂在 SessionStart 上的 `mode-hook.py` 由 v2 原有的 hook 清扫摘掉；v3 往 `~/.mmw/models.json` 补的 `researcher`、`explainer`、`synthesizer` 三行摘掉，原文件留一份 `.bak-`；`installed-root` 记回 `mmw-v2`。`mmw-v3/tests/install/run.sh` 的 `installrollback` 在一次性家目录里先装 v3、再装 v2，查 v2 的 `--check` 没有缺项，再装回 v3。

## 要修的是什么

- 换成 v3 之前，v2 的安装器认不出指向 `mmw-v3/` 的软链，会报冲突并跳过；`~/.claude/CLAUDE.md` 也一样。v3 第一夜出了问题，没有一条命令能把本机换回去。
- v3 的安装给 `models.json` 补了三个角色，v2 的 `models.py` 只认四个角色，整份配置读不进来，v2 的安装和夜里每次读配置都会失败。

## Considered Options

- **把装着的 checkout 移回换 v3 之前的提交，跑那里的 `install.sh`。** 否决。那一份安装器正是认不出 v3 软链的那一份。
- **让 v2 的 `models.py` 容忍不认识的角色。** 否决。那会改到 v2 每一个读 `models.json` 的地方；只在安装时摘掉 v3 加的三行，改动只在安装器里。
- **不做退路。** 否决，用户决定要。

## Consequences

- 退回只换本机的安装。在 v3 下开着的夜，要在退回之前由 v3 关掉或挂起（Self-hosting boundary）；v2 能不能读懂 v3 写在票上的事件，没有核过。
- 退回丢掉那三行里改过的值，最近一份 `models.json.bak-` 留着；再换回 v3 时，它们按 `mmw-v3/skills/dispatch/hosts.json` 的默认值补回。
- `~/.zshrc` 里加载 `mmw-v3/shell/nmem-space.zsh` 的那一段，v2 的安装器不认识，退回后原样留着；它加载的文件在同一个 checkout 的 `mmw-v3/` 里，所以终端照旧设 `NMEM_SPACE`。
- 只要装着的 checkout 里还有 `mmw-v2/`，这条退路就在；从仓库里删掉 `mmw-v2/`，就没有退路了。
