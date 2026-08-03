---
description: 确认设计(唯一人闸):盖承重文档指纹,过门放权进流水线
argument-hint: "[承重文档相对路径,可多个,空则用已钉的设计产出]"
disable-model-invocation: true
---

用户确认设计。这是全流程唯一硬人闸的钥匙,**只有用户手动敲本命令才触发**——用户口头说「可以」不算过门,agent 不得代跑本命令。

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

然后:

1. 确定承重文档:`$ARGUMENTS` 给了路径就用它(可多个,worktree 相对路径:主设计文档 + 被引用的合同文档);没给则不带 `--report`(引擎回落到 design 阶段已钉产出)。
2. 跑(每个路径一个 `--report`):
   ```bash
   mmw approve [--report <路径>]...
   ```
3. 照回执行动:
   - `APPROVED ... NEXT_PHASE=<X>` = 过门成功:值守已自动切 afk(放权自主跑),向用户一句话确认「设计已确认,进入 <X>,后面自主推进、出大事才来找你」,然后 `mmw where` 继续。
   - `RE-APPROVED` = 设计修订后的重新确认:指纹已更新,回到刚才被 approval_stale 挡住的动作继续。
   - `ERROR: 承重文档不存在/为空` = 设计文档还没落盘或没钉:先把设计文档写好、`mmw pin --phase design --produced <路径>` 钉上,再请用户重敲本命令。

过门后设计承重文档再被改动,引擎会在推进时硬停(approval_stale)——那时把改动摆给用户,请他重敲本命令重新确认,或回退改动。
