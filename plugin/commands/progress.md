---
description: 展示当前 multi-model-workflow 任务进度板(投影,从磁盘真相源重建)
argument-hint: ""
---

## 指令

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`):

```sh
if [ -n "${DROID_PLUGIN_ROOT:-}" ] || printf %s "$PATH" | grep -q '/.factory/bin'; then P=~/.factory/plugins; else P=~/.claude/plugins; fi
find "$P" -type f -path '*multi-model-workflow*/scripts/mmw.sh' 2>/dev/null | head -1
```

1. 跑 `mmw progress render --stdout` 从 task.json / loop-state.json 重渲染进度板。
2. 若输出 `NO-ACTIVE-RUN`:明确告诉用户当前不在在管任务 worktree、无板可展示,停止,不伪造进度。
3. 有板:把板面内容原样转述给用户(路线/阶段/值守模式/进度度量/计划进度/阻塞/计划外项)。
4. 只汇报板面 + 一个「若需你拍板」的问题(仅当板里有待决项);不自动续跑、不加板外推断。
