---
description: 展示当前 multi-model-workflow 任务进度板(投影,从磁盘真相源重建)
argument-hint: ""
---

## 指令

先定位 mmw:

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

1. 跑 `mmw progress render --stdout` 从 task.json / loop-state.json 重渲染进度板。
2. 若输出 `NO-ACTIVE-RUN`:明确告诉用户当前不在在管任务 worktree、无板可展示,停止,不伪造进度。
3. 有板:板面已直出屏幕,不再逐字转述;口头只补一句「当前阻塞 / 待用户拍板项」(没有就说没有)。
4. 只汇报板面 + 一个「若需你拍板」的问题(仅当板里有待决项);不自动续跑、不加板外推断。
