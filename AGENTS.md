# AGENTS.md

这个仓库是用户跨宿主、跨仓库、跨电脑共用的工作流工具箱：技能和 subagent。里面的技能是
交付物，不是你的工作指南；写任何东西都站在将来要用它的全新 agent 的角度。

## 布局

只有 `mmw-v2/` 是活的。`mmw/`、`archive/` 和根上其余文件是上一代，冻结：不改、不加、不当事实。

| 位置 | 是什么 |
| --- | --- |
| `mmw-v2/upstream/` | `mattpocock/skills` 的 git subtree（squash）。**可编辑**的工作副本 |
| `mmw-v2/skills/<名>/` | 自研技能，自带脚本与测试 |
| `mmw-v2/skills.txt` | 装哪些技能。加减技能只改这里 |
| `mmw-v2/agents/<名>/` | 自研 subagent：`body.md` 是正文，`agent.json` 是 name、description 与五宿主各自的模型和工具；`out/` 是装配成品，进 git |
| `mmw-v2/merge-notes/<技能>.md` | 我们改过的上游技能，每段的意图和冲突时的取舍 |
| `mmw-v2/install.sh` | 唯一安装入口，把技能和 subagent 成品软链进五个宿主。`--check` 只看不动 |

## 改技能

宿主软链直接指向源目录，改完下一次调用即生效。只有 frontmatter 的 `description` 是宿主启动时
扫进去的，改它要重开会话。

subagent 的正文和 `agent.json` 改完要重跑 `mmw-v2/agents/assemble.py`（或 `install.sh`），
宿主读的是 `out/` 里的成品。description 写给主线程（何时派、prompt 装什么），`body.md` 写给
subagent（怎么答）。三个 subagent 都只读。

拉上游并解冲突：

```bash
git subtree pull --prefix mmw-v2/upstream https://github.com/mattpocock/skills main --squash
```

冲突先读对应的 merge-note。改了上游技能就写或更新它的 merge-note。

会产出文档的技能，在「开始写」那一句点名 `readable-docs`；写完派 `claim-checker` 核对。

`exe-release/scripts/` 改了就跑 `exe-release/tests/run.sh`。Mac 上没有 PowerShell，
`tests/check-generated-powershell.sh` 与 `tests/check-template-behaviour.sh` 要送构建机跑。

## 五宿主平权

技能正文对五个宿主是同一份。描述、默认值、示例不把任何宿主当默认或首选，不按宿主名分支；
能力差异用按能力判断的自然语言写。

只许人触发的技能同时设两处：`SKILL.md` 的 `disable-model-invocation: true` 和技能目录内
`agents/openai.yaml` 的 `policy.allow_implicit_invocation: false`。两处同设或同不设——只设
前者，Codex 会把这个技能从模型可见列表里整个过滤掉。

## 规则

- 改技能前读完整 `SKILL.md` 及其链接的 reference；写法以 `writing-for-agents` 为准。
- 只实现请求范围内的行为。脚本异常非零退出或留下结构化告警。
- 机械校验只判机器能直接判定的事实：语法、结构、路径、配置完整性、产物一致性。质量、方法、
  语义和完成度由技能和主 agent 判断；校验越界就删掉它，不加例外。
- 正式改动在独立 worktree，合回用 `git merge --no-ff`。本地提交和合并可自主做；
  `git push`、远端合并、发布、删除或覆盖现有发布入口要用户明确授权。禁用 `--no-verify`。
