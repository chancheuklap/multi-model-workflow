---
description: 手动指定计划外项处置:开 issue 记下,或当场修
argument-hint: "issue | fix"
disable-model-invocation: true
---

用户手动指定当前计划外项的处置。参数 `$ARGUMENTS`:`issue`(开 issue 记下)或 `fix`(当场修)。

## 指令

先定位 mmw(无需环境变量;记住返回的绝对路径,下文 `mmw X` 即 `bash <该路径> X`;插件根 = 该路径上两级目录):

<!-- BEGIN: locate-mmw -->
会话开头的 mmw 分诊已经报告插件根绝对路径时，直接使用它。没有时读 pi 的实际安装配置；本地路径安装不会复制，`packages` 中的路径就是插件根：

```sh
MMW_ROOT="$(jq -r '
  .packages[]?
  | if type=="string" then . elif type=="object" then (.source // "") else "" end
  | select(test("(^|/)pi-plugin/?$"))
' ~/.pi/agent/settings.json 2>/dev/null | head -1)"
[ -d "$MMW_ROOT" ] || MMW_ROOT="$(pwd | sed -n 's|\(.*multi-model-workflow/pi-plugin\).*|\1|p')"
MMW="$MMW_ROOT/scripts/mmw.sh"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败：先确认 pi install <multi-model-workflow/pi-plugin 绝对路径> 已完成"
```

`mmw X` 等价于 `bash "$MMW" X`。每个新 shell 都使用回显的绝对路径，不依赖 shell 变量跨调用留存，也不要从其他宿主镜像目录取运行时代码。
<!-- END: locate-mmw -->

1. 读插件根下 `skills/orchestrate/references/control/steering-commands.md`(计划外分流协议在里面)。
2. 确认当前计划外项的标签(bug/optimize/out-of-scope/needs-evaluation)与一句话摘要。
3. 落盘:
   - `issue` → `mmw side-finding record --tag <t> --disposition issue --finding "<摘要>"`
   - `fix` → `mmw side-finding record --tag <t> --disposition fix --finding "<摘要>"`
4. `fix` 第一刀**不扩大**现有合法修复边界;用户要扩大则单独立项。
5. 板已自动刷新;回报处置结果。
