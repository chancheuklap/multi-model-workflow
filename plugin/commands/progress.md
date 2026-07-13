---
description: 展示当前 multi-model-workflow 任务进度板(投影,从磁盘真相源重建)
argument-hint: ""
---

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——候选(缓存各版本 + 本地源安装)按版本取最高,不许 `head -1` 抓第一个:

```sh
P=~/.claude/plugins
MMW="$( { find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null
  jq -r '.["multi-model-workflow"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/plugin/scripts/mmw.sh|'
  } | while IFS= read -r f; do
    [ -f "$f" ] || continue
    r="${f%/scripts/mmw.sh}"
    v="$(jq -r '.version' "$r/.claude-plugin/plugin.json" 2>/dev/null || echo 0)"
    printf '%s %s\n' "$v" "$f"
  done | sort -V | tail -1 | cut -d' ' -f2- )"
echo "MMW=$MMW"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。
<!-- END: locate-mmw -->

1. 跑 `mmw progress render --stdout` 从 task.json / loop-state.json 重渲染进度板。
2. 若输出 `NO-ACTIVE-RUN`:明确告诉用户当前不在在管任务 worktree、无板可展示,停止,不伪造进度。
3. 有板:把板面内容原样转述给用户(路线/阶段/值守模式/进度度量/计划进度/阻塞/计划外项)。
4. 只汇报板面 + 一个「若需你拍板」的问题(仅当板里有待决项);不自动续跑、不加板外推断。
