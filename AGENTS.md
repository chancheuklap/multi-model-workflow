# AGENTS.md

这个仓库是用户的一整套工作流集合工具箱。它不是一个简单的技能仓库。任何有可能在不同的 agent harness、不同的仓库、不同的电脑上面使用的通用工作流工具，都应该由这个仓库管理，而不是写到某一个项目仓库里面。

这个仓库是里面的技能和工具，不是你的工作指南。永远站在要使用它们的全新 agent 的角度去思考问题和撰写文档。

写给用户的任何文字都遵守 [`communication-rule.md`](./communication-rule.md)。

## 仓库范围

`mmw-v2/` 是唯一活跃的多模型工作流（Multi-Model Workflow，MMW）。

`mmw/` 是上一代，已从本机全部卸载，留在仓库里只作为搬运来源：一件一件挑出还有用的东西搬进
`mmw-v2/`，搬完即止。不要往 `mmw/` 里加东西，也不要修它。根上的 `README.md`、`CONTEXT-MAP.md`
及其 `docs/context/` 下的 leaf、`mmw-skill-map.html`、`TESTING.md` 描述的都是上一代，尚未重写，
读它们时按史料对待，不作为 `mmw-v2/` 的事实。

`archive/` 是冻结归档。

## mmw-v2 怎么工作

技能不复制、不物化、不打包。上游那一份就是工作副本，宿主软链直接指进去。

| 位置 | 是什么 |
| --- | --- |
| `mmw-v2/upstream/` | 上游 `mattpocock/skills` 的 Git subtree（squash）。**可编辑**，不是只读供应商目录 |
| `mmw-v2/skills.txt` | 装哪些技能。加减技能只改这一处 |
| `mmw-v2/.mcp.json` | 装哪些检索服务器。服务器定义的唯一事实来源 |
| `mmw-v2/install.sh` | 唯一安装入口：技能软链加 MCP 写配置。`--check` 只看不动 |

```bash
bash mmw-v2/install.sh            # 装
bash mmw-v2/install.sh --check    # 齐了回 0，缺东西回 1
python3 mmw-v2/mcp/probe.py       # 真起一次三台服务器，握手并列工具
```

技能装进五个宿主自己的用户级目录：`~/.claude/skills`、`~/.codex/skills`、`~/.pi/agent/skills`、
`~/.cursor/skills`、`~/.grok/skills`。目录不存在就当这个宿主没装，跳过。

**改技能就直接改 `mmw-v2/upstream/skills/<桶>/<名>/` 下的文件。** 宿主读的就是它，下一次调用即
生效，不用重装。只有 frontmatter 的 `description` 是宿主启动时扫进系统提示的，改它要重开会话。

上游更新走一条命令，你的改动和上游改动由 git 三方合并，冲突照常解：

```bash
git subtree pull --prefix mmw-v2/upstream https://github.com/mattpocock/skills main --squash
```

「我们改了什么」不另立台账，跟基线 diff 即可：

```bash
git diff <上一个 Squashed 提交> -- mmw-v2/upstream/skills/engineering/wayfinder/
```

## 检索

三台 MCP 服务器装进五个宿主各自的配置：**serena**（符号定义、引用、实现、文件概览）、
**graphify**（模块关系、依赖路径、反向影响、跨语言数据流）、**context7**（第三方库文档）。

技能是软链，MCP 是写进宿主自己的配置文件——形状不同，所以是两个脚本，`install.sh` 统一调用。
写进去的是**绝对路径**，指向这个 checkout：要从主检出装，不要从任务 worktree 装，worktree
合并后会删掉，写进去的路径就断了。换仓库位置也要重跑安装器。

| 位置 | 是什么 |
| --- | --- |
| `mmw-v2/mcp/resolve.py` | 唯一的展开器。`${MMW_ROOT}` 与密钥占位符都在这里换成真值 |
| `mmw-v2/mcp/install-mcp.sh` | 写进五个宿主的配置。只加不删，同名才覆盖 |
| `mmw-v2/mcp/graphify_mcp.py` | graphify 服务器本体。查询前先保证图对得上当前 checkout |
| `mmw-v2/config/serena-readonly.yml` | serena 的只读白名单。上游默认 29 个工具，含任意命令执行和写文件 |
| `mmw-v2/config/serena-connection-prompt.yml` | serena 下发的服务器说明。装到 `~/.serena/prompt_templates/`，**不是** `serena-readonly.yml` 里的 `prompt` |
| `mmw-v2/config/retrieval-contract.json` | 裁剪面的唯一事实来源。`probe.py` 拿真实工具列表跟它**集合相等**比对 |

密钥不进仓库：`.mcp.json` 只写 `${VAR}` 声明，值从进程环境或 `~/.mmw/secrets.env` 取。

**服务器说明是让 agent 主动调用检索的唯一渠道**——五个宿主都在握手时把它读进上下文（逐一实测过），
而技能正文里一个字都不提这两台服务器。改说明就是改这一层，改一处五家全生效。改完用
`mmw-v2/mcp/probe.py` 起一次真服务器复核，不要只看文件。

## 宿主边界

五个宿主平权。没有主力宿主，也没有参考宿主：描述、默认值和文档示例都不得把某一个宿主当成默认或
首选，也不得只给一个宿主写路径。

技能正文对所有宿主是同一份，**按宿主名称分支的写法不进技能正文**。宿主能力差异用按能力判断的
自然语言表达。

用户触发与模型触发的开关五家共用同一个字段：`SKILL.md` frontmatter 的 `disable-model-invocation`
（Claude Code、Cursor、Grok、Pi 都读它），Codex 另读技能目录内的 `agents/openai.yaml` 的
`policy.allow_implicit_invocation`。两个开关必须同时设或同时不设，一个技能要么在所有宿主上都只
许人叫，要么都不是。两份文件都在技能目录里，软链一并带过去，所以安装器没有按宿主分支的逻辑。

这个字段不在 [Agent Skills 规范](https://agentskills.io/specification)里，是 Claude Code 的扩展、
其余几家跟进实现的惯例。给一个本该模型可触发的技能设上它，Codex 会把它从模型可见的技能列表里
整个过滤掉，于是 description 再怎么写都触发不了。

## 修改规则

- 改技能前读完整 `SKILL.md` 及其链接的 reference。技能写作规范以 `writing-for-agents` 及其链接的
  `SKILL-MECHANICS.md` 为准。
- 只实现请求范围内行为；不用归档残留、兼容目录或静默默认值掩盖错误。
- 脚本异常必须非零退出或留下结构化告警。
- 机械校验只覆盖机器能直接判定的事实：语法与固定结构可解析、路径与文件安全、配置完整性和生成
  产物一致性。产物质量、方法选择、语义真实性和完成度由技能与主 agent 判断。不用计数、列表形状、
  固定阈值或豁免清单伪装成机械校验。已有校验越过这条边界时删除该校验，不增加例外分支。

## Git 与安全

- 正式改动在独立 worktree；合回主分支使用 `git merge --no-ff`，禁止 squash。
- 本地提交和合并可自主执行。`git push`、远端合并、部署和正式发布必须得到用户明确授权。
- 删除、覆盖、归档或移动现有发布入口前确认用户授权。
- 禁止使用 `--no-verify`。
