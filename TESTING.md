# TESTING.md(仓库薄层)

> 测试写作权威在 plugin 随身携带的 test-quality 基线(worker 派发时注入;人读:`plugin/skills/worktree-build/references/tests.md`)。本文只写本仓库事实,不重复方法论。

## 目录分层

| 层 | 位置 | 测什么 |
| --- | --- | --- |
| 脚本行为 | `plugin/scripts/tests/test_*.sh` | mmw 各子脚本:跑真命令,断 stdout / 退出码 / 状态文件(`task.json`、`loop-state.json`、`review-brief.md`) |
| 构建注入 | `plugin/build/tests/test_build.sh` | fragments 单源注入:--apply 传播、--check 抓 DRIFT、锚点结构 |
| release 合同 | `plugin/scripts/tests/test_release_*.sh` + `test_release_*.py` | 出包子系统:stage 推进、远端构建合同、脚本装配 |
| droid 镜像 | `droid-plugin/**` 同构目录 | 同一套,宿主路径与 hook 事件不同 |

## 断什么、不断什么(本仓库特有边界)

- skill / reference / command 的 prose 就是行为面:断**结构**(锚点在、注入频次、段落顺序)与**短语义键**(如「独立任务边界」),不逐字锁整句——润色不该红。
- hook / CLI 的 stdout 是外部可观察面,可断语义键;不 grep 脚本源码文本。
- 状态文件字段走 `jq` 断具体值,不做字段全集镜像。

## 外部接缝(允许打桩的边界)

- `codex` CLI:worker 测试用 stub bin(PATH 前插)。
- ssh / schtasks 远端(release):fake transport 脚本,记录调用序列。
- Claude 会话内工具(Agent/sub-agent):不在 shell 测试范围,测到 brief/prompt 生成为止。

## 权威源指针

- 阶段/闸位/结论词:`plugin/state-schema/routes.json`。
- 共用片段:`plugin/build/fragments/*`(改后必须 `--apply` 再 `--check`)。
- 版本号:`plugin/.claude-plugin/plugin.json` 与根 `marketplace.json`(双处同步;droid 侧另两处)。

## 门控

```bash
for t in plugin/scripts/tests/test_*.sh; do bash "$t" || break; done
bash plugin/build/tests/test_build.sh
python3 -m json.tool plugin/state-schema/routes.json >/dev/null
```

已知慢测试:`test_release_flow.sh` 约 90 秒(远端构建墙钟轮询用例),不是挂起。
