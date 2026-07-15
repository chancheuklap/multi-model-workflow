---
description: 手动指定计划外项处置:开 issue 记下,或当场修
argument-hint: "issue | fix"
disable-model-invocation: true
---

用户手动指定当前计划外项的处置。参数 `$ARGUMENTS`:`issue`(开 issue 记下)或 `fix`(当场修)。

## 指令

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`;插件根 = 该路径上两级目录):

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——**读实际激活的安装位**(installed_plugins.json),不扫缓存挑版本号(缓存里躺着历史版本,版本号最高 ≠ 正在运行的那个):

```sh
P=~/.claude/plugins
MMW="$( jq -r '.plugins | to_entries[] | select(.key | startswith("multi-model-workflow@")) | .value[0].installPath // empty' \
        "$P/installed_plugins.json" 2>/dev/null | head -1 | sed 's|$|/scripts/mmw.sh|' )"
[ -f "$MMW" ] || MMW="$( jq -r '.["multi-model-workflow"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/plugin/scripts/mmw.sh|' )"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败:插件未装?(装了才有 installed_plugins.json 条目)"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。**别用仓库里的相对路径 `plugin/scripts/mmw.sh` 当运行时**——在旧分支 worktree 里那是旧代码。
<!-- END: locate-mmw -->

1. 读插件根下 `skills/orchestrate/references/control/steering-commands.md`(计划外分流协议在里面)。
2. 确认当前计划外项的标签(bug/optimize/out-of-scope/needs-evaluation)与一句话摘要。
3. 落盘:
   - `issue` → `mmw side-finding record --tag <t> --disposition issue --finding "<摘要>"`
   - `fix` → `mmw side-finding record --tag <t> --disposition fix --finding "<摘要>"`
4. `fix` 第一刀**不扩大**现有合法修复边界;用户要扩大则单独立项。
5. 板已自动刷新;回报处置结果。
