---
description: 保留已完成,重做后续计划
argument-hint: ""
disable-model-invocation: true
---

用户要保留已完成部分、重做后续计划。

## 指令

先定位 mmw:

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

1. 先跑 `mmw where` + 看 progress board,确认哪些 plan/step 已完成(done)。
2. 已完成的不动;回流 plan 阶段,只重写未完成部分的计划。
3. 说明保留了哪些、重做哪些,给新的执行序。
4. 刷新板:`mmw progress render`。
