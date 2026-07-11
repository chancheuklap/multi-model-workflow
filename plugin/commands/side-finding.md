---
description: 手动指定计划外项处置:开 issue 记下,或当场修
argument-hint: "issue | fix"
disable-model-invocation: true
---

用户手动指定当前计划外项的处置。参数 `$ARGUMENTS`:`issue`(开 issue 记下)或 `fix`(当场修)。

## 指令

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`;插件根 = 该路径上两级目录):

<!-- BEGIN: locate-mmw -->
会话开头 SessionStart hook 已报过 mmw 绝对路径的,直接用它(hook 从激活插件根跑,是权威)。没有才跑下面定位块——候选(缓存各版本 + 本地源安装)按版本取最高,不许 `head -1` 抓第一个:

```sh
if [ -n "${DROID_PLUGIN_ROOT:-}" ] || printf %s "$PATH" | grep -q '/.factory/bin'; then P=~/.factory/plugins; else P=~/.claude/plugins; fi
MMW="$( { find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null
  jq -r '.["multi-model-workflow"].installLocation // empty' "$P/known_marketplaces.json" 2>/dev/null | sed 's|$|/plugin/scripts/mmw.sh|'
  } | while IFS= read -r f; do
    [ -f "$f" ] || continue
    r="${f%/scripts/mmw.sh}"
    v="$(jq -r '.version' "$r/.claude-plugin/plugin.json" 2>/dev/null || jq -r '.version' "$r/.factory-plugin/plugin.json" 2>/dev/null || echo 0)"
    printf '%s %s\n' "$v" "$f"
  done | sort -V | tail -1 | cut -d' ' -f2- )"
echo "MMW=$MMW"
```

`mmw X` ≡ `bash "$MMW" X`;每个新 shell 用回显的绝对路径,别指望 shell 变量跨调用留存。
<!-- END: locate-mmw -->

1. 读插件根下 `skills/orchestrate/references/control/steering-commands.md`(计划外分流协议在里面)。
2. 确认当前计划外项的标签(bug/optimize/out-of-scope/needs-evaluation)与一句话摘要。
3. 落盘:
   - `issue` → `mmw side-finding record --tag <t> --disposition issue --finding "<摘要>"`
   - `fix` → `mmw side-finding record --tag <t> --disposition fix --finding "<摘要>"`
4. `fix` 第一刀**不扩大**现有合法修复边界;用户要扩大则单独立项。
5. 板已自动刷新;回报处置结果。
