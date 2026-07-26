---
name: approve-design
description: 确认设计(唯一人闸):盖承重文档指纹,过门放权进流水线
argument-hint: "[承重文档相对路径,可多个,空则用已钉的设计产出]"
disable-model-invocation: true
---

用户确认设计。这是全流程唯一硬人闸的钥匙,**只有用户手动敲本命令才触发**——用户口头说「可以」不算过门,agent 不得代跑本命令。

## 指令

先定位 mmw:

<!-- BEGIN: locate-mmw -->
会话开头的 mmw 分诊已经报告插件根绝对路径时，直接使用它。没有时按安装位查找（Marketplace / Team Marketplace 安装后通常落在 Cursor plugins 目录；本地试装在 `~/.cursor/plugins/local`）：

```sh
MMW_ROOT=""
if [ -n "${CURSOR_PLUGIN_ROOT:-}" ] && [ -f "$CURSOR_PLUGIN_ROOT/scripts/mmw.sh" ]; then
  MMW_ROOT="$CURSOR_PLUGIN_ROOT"
fi
if [ -z "$MMW_ROOT" ]; then
  for cand in \
    "$HOME/.cursor/plugins/local/multi-model-workflow-cursor" \
    "$(pwd | sed -n 's|\(.*multi-model-workflow\)/.*|\1/cursor-plugin|p')" \
    "$(pwd)/cursor-plugin"
  do
    [ -f "$cand/scripts/mmw.sh" ] || continue
    MMW_ROOT="$cand"
    break
  done
fi
# Marketplace 缓存安装位：按 name 扫一层
if [ -z "$MMW_ROOT" ]; then
  for cand in "$HOME"/.cursor/plugins/*/*/multi-model-workflow-cursor \
              "$HOME"/.cursor/plugins/*/multi-model-workflow-cursor; do
    [ -f "$cand/scripts/mmw.sh" ] || continue
    MMW_ROOT="$cand"
    break
  done
fi
MMW="$MMW_ROOT/scripts/mmw.sh"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败：先从 Cursor Marketplace / Team Marketplace 安装 multi-model-workflow-cursor，或设 CURSOR_PLUGIN_ROOT"
```

`mmw X` 等价于 `bash "$MMW" X`。每个新 shell 都使用回显的绝对路径，不依赖 shell 变量跨调用留存，也不要从 `.pi` / `.claude` / `.factory` 宿主镜像目录取运行时代码。
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
