---
description: 当前步骤先放下,继续后面(记 blocked/skipped 留痕)
argument-hint: ""
disable-model-invocation: true
---

用户要放下当前卡住的步骤先继续后面。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——**读实际激活的安装位**(installed_plugins.json),不扫缓存挑版本号(缓存里躺着历史版本,版本号最高 ≠ 正在运行的那个):

```sh
P=~/.factory/plugins
MMW="$( jq -r '.plugins | to_entries[] | select(.key | startswith("multi-model-workflow-droid@")) | .value[0].installPath // empty' \
        "$P/installed_plugins.json" 2>/dev/null | head -1 | sed 's|$|/scripts/mmw.sh|' )"
[ -f "$MMW" ] || MMW="$( jq -r '.["multi-model-workflow"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/droid-plugin/scripts/mmw.sh|' )"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败:插件未装?(装了才有 installed_plugins.json 条目)"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。**别用仓库里的相对路径 `droid-plugin/scripts/mmw.sh` 当运行时**——在旧分支 worktree 里那是旧代码。
<!-- END: locate-mmw -->

1. 先跑 `mmw where` 看现状。
2. 记下放下的是什么、为什么(一句话),落 `mmw side-finding record` 或 `mmw loop softstop` 留痕,别静默跳过。
3. 继续后面的活,说明放下了哪一步、后面从哪续(登记在 open_items,不静默丢)。
4. 刷新板:`mmw progress render`。
