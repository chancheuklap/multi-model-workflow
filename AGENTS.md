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
而技能正文里一个字都不提这两台服务器。改说明就是改这一层，一处改动五家共用。

技能改完下次调用就生效，**服务器说明不是**：改完要重跑 `bash mmw-v2/install.sh`。Pi 把握手拿到的
说明缓存在 `~/.pi/agent/mcp-cache.json`，判失效只看配置哈希（command、args、env、cwd、工具过滤），
说明正文不在里面，条目七天才过期——不重装它就一直端上一版，另外四家已经换了，没有一处会说出来。
安装器会清掉我们那几台的缓存条目；`probe.py` 起真服务器拿到下发的说明，跟 Pi 缓存对不上时当场报出来。

## 语言工具

这台机器上的检查器和语言服务器**只有一份**，由 MMW 装、由 MMW 升级，位置是
`mmw-v2/tools/`。

| 位置 | 是什么 |
| --- | --- |
| `mmw-v2/tools/tools.json` | 清单。每个工具是什么、给谁用、怎么装、怎么跑 |
| `mmw-v2/tools/install.sh` | 装齐并把 serena 指过来。`--check` 只看不动 |
| `mmw-v2/tools/serena-language-servers.py` | 写 serena 的 `ls_specific_settings` |
| `mmw-v2/tools/bin`、`mmw-v2/tools/node` | 装出来的东西。不入库，删掉重跑安装器就回来 |

**语言服务器和检查器写在同一张清单里，不分两张。** `pyright` 那一条本来就既是命令行检查器
（`pyright`）又是语言服务器（`pyright-langserver`），同一个包的两个入口；分两张表就会出现
同一个引擎两个版本。

两个消费者读同一张表：编辑后诊断读 `checker` 那一段，serena 读 `language_server` 那一段。
**它们拿到的是同一个可执行文件，不只是同一个版本号。**

覆盖 serena 的口子按语言分两种，清单里的 `lookup` 字段说明是哪一种：

| `lookup` | serena 那边长什么样 | 我们做什么 |
| --- | --- | --- |
| `ls_path`（缺省） | 走 `create_launch_command`，读 `ls_specific_settings.<语言>.ls_path` | 写这个键，指到 `mmw-v2/tools/` |
| `path` | 命令写死成 `ProcessLaunchInfo(cmd="gopls")`，不经过那条路径 | 只保证 PATH 上有且只有一个 |

`lookup: path` 那一类**不写配置**：`ls_path` 对它是空转，写了就造出「配了但没生效」的假象。

serena 默认自己下一份——`pyright` 走 uvx 且版本钉死在它源码里（实测 1.1.403），`typescript`
与 `bash` 下载到 `~/.serena/language_servers/`。`ls_path` 指过来之后它就不再自己下、也不再用
那个旧版本。`probe.py` 会真调一次 `find_symbol` 验它答不答得出来——**工具列表对得上不等于
答得出来**，而 serena 现在跑在跟上游钉死版本不同的 pyright 上。

**装了不等于跑。** 检查器是一次性进程，改一次文件跑一次就退出。语言服务器只在 serena 打开
一个项目、且那个项目 `.serena/project.yml` 的 `languages:` 里列了那门语言时才起——那份列表是
serena 按仓库里的文件数自动定的，不是把装了的全起一遍。

覆盖的语言：

| 语言 | 检查 | 符号 |
| --- | --- | --- |
| Python | `ruff` + `pyright` | `pyright-langserver`（`ls_path`） |
| TypeScript / JavaScript | `oxlint`（带 `oxlint-tsgolint`） | `typescript-language-server`（带 `typescript`，`ls_path`） |
| Vue | `oxlint`，规则在 `oxlintrc.json` 的 `plugins` 里开 `vue` | 不接，见下 |
| Shell | `shellcheck` | `bash-language-server`（`ls_path`） |
| Swift | `swiftlint` | `/usr/bin/sourcekit-lsp`（`path`，Xcode 命令行工具自带） |
| Go | 无 | `gopls`（`path`） |
| Rust | 无 | `rust-analyzer`（`ls_path`） |
| 全部 | 密钥扫描，纯正则，不限后缀 | — |

**Vue 的语言服务器不接。** serena 的 `VueLanguageServer` 在构造函数里直接拼
`ProcessLaunchInfo(cmd=vue_lsp_executable_path)`，完全不走 `create_launch_command`，而且它要
三个包（`@vue/language-server`、`typescript`、`typescript-language-server`）版本互相配合。
`ls_path` 在这里既是空转，强接还会把服务器弄挂。检查那一面 `oxlint` 已经覆盖 `.vue`。

**Go 与 Rust 没有检查器。** `go vet` 与 `cargo clippy` 都以包／crate 为单位，而编辑后诊断是
按文件跑的，两者对不上。装的是符号那一面。

`gopls` 走 Homebrew 不走 `go install`：后者装进 `~/go/bin`，而那个目录不在这台机器的 PATH
上，serena 找不到。

**不锁版本，每次安装都升到最新稳定版。** 锁住换来的"一致"只保证两个陈旧副本相同。

装在 MMW 自己的目录里，不碰机器的全局环境，也不碰 `~/dev-environment`：那个控制平面管的是
**用户自己敲的命令**（brew、shell 启动、你用的 CLI），这里管的是 agent 的工具。两边互不影响。

找可执行文件是固定的三段顺序：**仓库自带的 → MMW 装的 → PATH 上的**。仓库排第一是因为
那是它自己锁定、CI 也在用的那一个；用别的版本，编辑时看到的错和门禁判的对不上。

## 编辑后诊断

agent 改完一个文件，立刻对这个文件跑检查器，把**落在改动行上**的问题交回它。存量另行
计数：一个有历史债的仓库如果每次都把几十条旧账倒一遍，报三次之后就没有人再看，这个
通道就废了。

| 位置 | 是什么 |
| --- | --- |
| `mmw-v2/diagnostics/check.py` | 跑检查器、过滤到改动行。五个宿主调的都是它 |
| `mmw-v2/diagnostics/config/` | ruff 与 oxlint 的规则。**用命令行传给检查器，不往被检查的仓库写文件** |
| `mmw-v2/diagnostics/hooks/` | 四个宿主的适配器，共用 `core.sh` |
| `mmw-v2/diagnostics/extension-pi/` | pi 那一份。pi 至今没有 hook，只有扩展 |
| `mmw-v2/diagnostics/install-hooks.sh` | 注册进五个宿主。只加不删 |

检查器有哪些、从哪儿来，看下一节「语言工具」。

各家挂在哪不一样，都是在本机实测出来的，不是照抄上一代：

| 宿主 | 挂在哪 | 诊断怎么回到 agent |
| --- | --- | --- |
| Claude Code | `settings.json` 的 PostToolUse | 退出码 2 加 stderr |
| Codex | `hooks.json` 的 PostToolUse | 同上 |
| Cursor | `hooks.json` 的 postToolUse | stdout 的 `additional_context` |
| Grok | `hooks/` 下单独一份 json，Stop 与 SubagentStop | stdout 的 `additionalContext` |
| pi | `extensions/` 下一个扩展，`tool_result` | 直接改工具结果的内容 |

**Grok 那一格有两个坑，都实测过。** 它的 PostToolUse 会触发、载荷收得到，但写到 stdout
的 `additionalContext` 到不了模型，所以只能挂 Stop。而 Stop hook 一回内容它就再跑一轮，
跑完又停又触发——同一次实测里同一段话被送回 8 次。适配器必须读载荷里的 `stopHookActive`，
为真就闭嘴。

跟技能和 MCP 一样，宿主配置里写的是指向这个 checkout 的绝对路径：**改适配器或 `check.py`
下次调用就生效，改注册位置才要重跑安装器。**

安装器会关掉 Claude Code 的 `pyright-lsp` 与 `typescript-lsp` 两个官方插件。那两个插件写死
走 PATH 拿全局版本，而 `check.py` 是仓库自带的优先，两条路会给出不同判定。关掉之后 Claude Code
的 `LSP` 工具还在工具表里，但没有语言服务器，调用会报错——**符号级的问题在五个宿主上都走
serena，调用层级走 graphify。**

诊断只覆盖 agent 用编辑工具改过的文件。用 shell 命令改的（`cat >>`、`sed -i`）拿不到文件路径，
不在覆盖范围里；手改的、别的电脑改的也不在。补这个缺口的正确落点是 git 的 pre-commit，不是 CI。

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
