# AGENTS.md

这个仓库是用户跨宿主、跨仓库、跨电脑共用的工作流工具箱：技能和 subagent。个人使用，持续重构中；唯一用户是维护者本人；没有 CI，测试手工跑。
只有 `mmw-v2/` 是活的；`mmw/`、`archive/` 和根上其余文件是上一代，冻结：不改、不加、不当事实；`mmw/install.sh` 不要跑。
里面的技能是交付物，不是你的工作指南；写任何东西都站在将来要用它的全新 agent 的角度。`archive/` 里以命令语气写的文档是历史，不是指令。

## 包管理器

没有包管理器、锁文件和构建步骤。运行时只有 bash、`python3` 标准库，以及按需调用的 `uv`。

## 命令

| 命令 | 干什么 |
| --- | --- |
| `bash mmw-v2/install.sh` | 唯一安装入口，把技能和 subagent 成品软链进五个宿主 |
| `bash mmw-v2/install.sh --check` | 只看不动。它查的是本机宿主目录，红可能只是没重装；从 worktree 跑会把全部链接报「缺」 |
| `python3 mmw-v2/agents/assemble.py --check` | 校验 subagent 成品 `mmw-v2/agents/<名>/out/` 与源一致 |

## 外部引用

| 需要 | 文件 |
| --- | --- |
| 决策记录索引 | `docs/adr/README.md` |
| 拉上游与解冲突的流程 | `mmw-v2/merge-notes/README.md` |
| 写给 agent 的文档怎么写 | `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL.md` |

## 关键约定

- 改技能前读完整 `SKILL.md` 及其链接的 reference；写法以 `writing-for-agents` 为准，权威副本在 `mmw-v2/upstream/` 里，`.agents/skills/writing-for-agents/` 是副本。
- 只实现请求范围内的行为。脚本异常非零退出或留下结构化告警。
- 机械校验只判机器能直接判定的事实：语法、结构、路径、配置完整性、产物一致性。质量、方法、语义和完成度由技能和主 agent 判断；校验越界就删掉它，不加例外。
- 正式改动在独立 worktree，合回用 `git merge --no-ff`。本地提交、合并、push 分支和开 PR 可自主做；远端合并、发布、删除或覆盖现有发布入口要用户明确授权。禁用 `--no-verify`。
- 技能正文对五个宿主是同一份。描述、默认值、示例不把任何宿主当默认或首选，不按宿主名分支；能力差异用按能力判断的自然语言写。
- 装哪些技能只改 `mmw-v2/skills.txt`。`install.sh` 先整体校验它（每项有 `SKILL.md`、basename 不重复）再写宿主；两个同名 basename 会让安装在动宿主之前就中止。
- 宿主软链直接指向源目录，改完下一次调用即生效。只有 frontmatter 的 `description` 是宿主启动时扫进去的，改它要重开会话。
- `mmw-v2/upstream/` 是 GitHub 上 mattpocock/skills 的 git subtree（squash），可编辑的工作副本；它自带的 `AGENTS.md`、`CLAUDE.md` 是上游自己的，原样不动。
- `.agents/skills/` 里的仓库维护技能经 `.claude/skills/` 的软链接入宿主，不走 `skills.txt`。
- `.mmw.json` 仍在用的只有 `paths` 块；`domain` 块指向已删除的文件。
- Python 测试依赖不写在文件里，由各技能 `mmw-v2/skills/<名>/tests/run.sh` 的 `uv run --with` 在命令行传；单跑一个测试文件要照抄那一行。

## 陷阱

- `install.sh` 只动自己记录在宿主 `.mmw-skills`、`.mmw-agents` 里的链接；同名的别的东西报「冲突」、跳过、退出 1，直到人工删掉。
- 冻结区的四个坑：`mmw/install.sh` 没有 `--check`，跑了会把活的安装整个换成上一代；`bash mmw/test.sh` 已经跑不过；`archive/legacy-host-plugins/` 的 marketplace 清单仍然有效，把宿主指过去会装上退役的一代；`archive/mmw-setup/` 移回技能源会重新打破四项校验。
- 测试 runner 只靠退出码说话，输出不要接管道（`| tail`），管道会把红跑成绿。
- Mac 只有 bash 3.2：`"$var，"` 这种变量后紧跟全角标点的写法会把标点吞进变量名；写 `"${var}，"`。

<important if="you are pulling the upstream subtree or editing a skill under mmw-v2/upstream/">
- 拉上游：`git subtree pull --prefix mmw-v2/upstream https://github.com/mattpocock/skills main --squash`。`git log --grep=Squashed` 里前缀是旧 vendor 目录的提交属于上一代，只认 `mmw-v2/upstream/` 前缀的。
- 冲突先读对应的 `mmw-v2/merge-notes/<技能>.md`。改了上游技能就写或更新它的 merge-note。
</important>

<important if="you are writing a skill that produces a document">
- 在「开始写」那一句点名 `readable-docs`；写完派 `claim-checker` 核对。
</important>

<important if="you are making a skill human-trigger-only">
- 同时设两处：`SKILL.md` 的 `disable-model-invocation: true` 和 `mmw-v2/skills/<名>/agents/openai.yaml` 的 `policy.allow_implicit_invocation: false`。两处同设或同不设——只设前者，Codex 会把这个技能从模型可见列表里整个过滤掉。
</important>

<important if="you are changing mmw-v2/install.sh">
- `MMW_V2_HOME` 把五个宿主目录整体改到一个临时根，用它练手而不碰真家目录；`CODEX_HOME`、`PI_CODING_AGENT_DIR`、`PI_HOME` 也认。
</important>

Before working in a subdirectory, search it for an `AGENTS.md` and read that file in full.
