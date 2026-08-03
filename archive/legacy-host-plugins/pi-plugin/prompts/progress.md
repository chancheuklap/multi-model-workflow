---
description: 展示当前 multi-model-workflow 任务进度板(投影,从磁盘真相源重建)
argument-hint: ""
---

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

1. 跑 `mmw progress render --stdout` 从 task.json / loop-state.json 重渲染进度板。
2. 若输出 `NO-ACTIVE-RUN`:明确告诉用户当前不在在管任务 worktree、无板可展示,停止,不伪造进度。
3. 有板:板面已直出屏幕,不再逐字转述;口头只补一句「当前阻塞 / 待用户拍板项」(没有就说没有)。
4. 只汇报板面 + 一个「若需你拍板」的问题(仅当板里有待决项);不自动续跑、不加板外推断。
