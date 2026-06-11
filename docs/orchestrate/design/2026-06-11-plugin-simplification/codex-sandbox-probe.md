# 支撑材料 · Codex 沙箱能力实测

> 本文件是 [`00-overview.md`](00-overview.md) 决策 **D1(codex lane 保留现状)** 的事实依据。2026-06-11 实测,codex-cli 0.138.0,macOS。

## 为什么做这个实验

精简讨论中提出一个根本质疑:这个 plugin 装在 Claude Code 里,**Codex 只是被 `codex exec` 请进来的"访客"**,它跑在自己的沙箱里(cwd 在隔离工作树)。当前 codex lane 却要求 Codex 自己调 `state.sh` 记账、读 plugin 文件、写符合 plugin schema 的 `plan-return.json`——这等于让访客操作住户的基础设施。质疑是:**真实部署下(plugin 装在 `~/.claude/plugins/`,开发的是别的项目),Codex 的沙箱根本够不到这些。**

`test_codex_worker.sh` 用的是**假 codex**(`cat > /dev/null` 吞掉指令、`cp` 一份预置结果冒充),所以"真 Codex 能否在沙箱里调通 `state.sh`"**整套测试从未验证过一次**。只能实跑确认。

## 方法

严格复刻 `codex-worker.sh` 的真实调用:

```
codex exec -C <假项目工作树> --sandbox workspace-write --add-dir <状态目录> -m gpt-5.4 - < probe-prompt
```

- 「已安装的 plugin」副本放在**主目录下、工作树之外、未 `--add-dir`** 的位置(等价于 `~/.claude/plugins/`)。
- 让 Codex 执行 6 条探测命令,**主线程独立复核文件系统真相**(不只信 Codex 自述)。
- 注意:第一版把探测目录放 `/tmp`,结果"未放行写"也成功——因为 **macOS 沙箱默认放行 `/tmp`**。改用主目录路径重测才得到可信结果。

## 结果(主目录版,已独立复核)

| 探测动作 | 结果 | 文件系统复核 |
|---|---|---|
| 读工作树外的 `state.sh` | ✅ 成功 | 读放开 |
| 执行工作树外的 `state.sh` | ✅ 成功(usage 输出) | 能 fork bash 跑外部脚本 |
| `state.sh init` 写 `--add-dir` 状态目录 | ✅ 成功 | 状态文件确实写入 |
| 写未放行的主目录路径 | ⛔ `operation not permitted` | 文件确认未生成 |
| 篡改只读的 plugin 副本 | ⛔ `operation not permitted` | plugin 确认未被改 |
| 写工作树内 | ✅ 成功 | — |

## 结论

`--sandbox workspace-write` 的真实行为:**读整个文件系统放开 · 执行外部脚本允许 · 写仅限工作树 + `--add-dir` 放行目录**。

因此当前 codex lane 让 Codex 调 `state.sh`、读 plugin、写 `--add-dir` 状态目录,**在沙箱层面可行,且已实测验证**。此前"真实部署 Codex 几乎必然够不到 state.sh"的判断**错误,已撤回**。

问题的性质由此从「功能跑不通,必须修」改为「能跑,但耦合重、靠一串假设撑着」:

- 写状态完全依赖 `codex-worker.sh` 记得精确 `--add-dir`;
- 权威 `commit_sha` 靠访客如实上报,而住户本可 `git log` 直接读到更可靠的;
- 访客要懂住户的 schema / 命令名 / `STATE_BASE` 路径前缀,plugin 内部一改就要同步改派工说明。

这些是**可简化的耦合/脆弱性,不是不可用的 bug**。改造优先级因此从「必须修」降为「可选降耦合」,本轮 codex lane 执行通路**保留现状**。
