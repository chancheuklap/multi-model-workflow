会话开头的 mmw 分诊已经报告插件根绝对路径时，直接使用它。没有时，从本轮已加载的 `orchestrate/SKILL.md` source locator 取绝对路径；plugin root 永远是该文件向上两级。这样定位到的是 Codex 实际安装 cache，不会误跑 marketplace 源码：

```sh
ORCHESTRATE_SKILL="<本轮 skill source locator 给出的 orchestrate/SKILL.md 绝对路径>"
MMW_ROOT="$(cd "$(dirname "$ORCHESTRATE_SKILL")/../.." && pwd)"
MMW="$MMW_ROOT/scripts/mmw.sh"
[ -f "$MMW" ] && echo "MMW=$MMW" || echo "MMW 定位失败：确认 multi-model-workflow plugin 已安装并重开 Codex task"
```

`mmw X` 等价于 `bash "$MMW" X`。每个新 shell 都使用回显的绝对路径，不依赖 shell 变量跨调用留存，也不要从 marketplace 源码或其他宿主镜像目录取运行时代码。
