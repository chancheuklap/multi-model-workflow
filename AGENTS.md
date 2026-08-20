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

**MMW 只管技能。** 检索服务器、语言服务器、检查器和编辑后诊断都已经从这个仓库和这台机器上
整个移除，不要再加回来。

技能不复制、不物化、不打包。上游那一份就是工作副本，宿主软链直接指进去。

| 位置 | 是什么 |
| --- | --- |
| `mmw-v2/upstream/` | 上游 `mattpocock/skills` 的 Git subtree（squash）。**可编辑**，不是只读供应商目录 |
| `mmw-v2/skills/` | 我们自己写的技能。一个目录一个技能，自带脚本与测试 |
| `mmw-v2/skills.txt` | 装哪些技能。加减技能只改这一处。`self/<名>` 指自研的，其余指上游的 |
| `mmw-v2/install.sh` | 唯一安装入口：把技能软链进五个宿主。`--check` 只看不动 |

```bash
bash mmw-v2/install.sh            # 装
bash mmw-v2/install.sh --check    # 齐了回 0，缺东西回 1
```

技能装进五个宿主自己的用户级目录：`~/.claude/skills`、`~/.codex/skills`、`~/.pi/agent/skills`、
`~/.cursor/skills`、`~/.grok/skills`。目录不存在就当这个宿主没装，跳过。

**改技能就直接改源目录下的文件**——上游的在 `mmw-v2/upstream/skills/<桶>/<名>/`，自研的在
`mmw-v2/skills/<名>/`。宿主读的就是它，下一次调用即生效，不用重装。只有 frontmatter 的
`description` 是宿主启动时扫进系统提示的，改它要重开会话。

技能自带的脚本用相对路径引用，跟着软链一起进五个宿主，**不装命令、不进 PATH**。

上游更新走一条命令，你的改动和上游改动由 git 三方合并，冲突照常解：

```bash
git subtree pull --prefix mmw-v2/upstream https://github.com/mattpocock/skills main --squash
```

「我们改了什么」不另立台账，跟基线 diff 即可：

```bash
git diff <上一个 Squashed 提交> -- mmw-v2/upstream/skills/engineering/wayfinder/
```

## 出包

`mmw-v2/skills/exe-release/` 让 agent 用当前分支的代码，对指定产品出一个正式安装包。

| 位置 | 是什么 |
| --- | --- |
| `SKILL.md` | 判断层：这次要出哪几个产品、包出来之后交给谁 |
| `driving.md` | 驱动合同：`where` 说什么就做什么 |
| `key.md` | 怎么写一把钥匙，以及每个字段是被哪次失败逼出来的 |
| `new-product.md` | 一个还没出过包的产品，仓库里要先有什么 |
| `scripts/release-flow.sh` | 引擎。状态机、标准流水线、P0/P1/P2 分级、路径闸、同根因熔断、轮次预算、pause/resume/receipt、派修 |
| `scripts/release_contracts.py` | 钥匙（`*.release-adapter.json`）与事件的合同 |
| `scripts/builders/`、`scripts/release_templates/`、`scripts/release_script_assembler.py` | 按钥匙装配 Windows 出包脚本 |
| `scripts/diagnose_core.py` | 把失败日志翻成根因。引擎和模板自己打印的那些话由它认 |
| `scripts/fix_dispatch.py` | 没有自动修复后端时，把 findings 写成简报交给驱动 agent |
| `scripts/verify_key.py` | 出发前把钥匙对着仓库核一遍，秒级，挡的是编译四十分钟之后才发现路径写错 |
| `tests/run.sh` | 全部测试。改了 `scripts/` 下任何东西之后跑一次 |

产品仓库提供一把钥匙：`*.release-adapter.json`，一个产品一把。**加一个产品就是写一把钥匙，
不写 Python。** 钥匙说不出来的事，答案是给钥匙加字段或给技能加能力，不是在产品仓库里加脚本——
那是把出包知识抄一份，下一个产品还得再抄一次。

流水线（`verify_key` → `assemble` → `build`）与日志翻译都由引擎和技能提供。钥匙的 `stages`
只写它出发前要在自己仓库里跑的事，引擎把这三段追加在后面。**这三个名字是保留字，钥匙用不了。**
从前允许钥匙用同名接管整条，于是抄来的一句 `assemble` 把引擎的验钥匙整段关掉，而日志每一步
都是绿的。产品真需要不一样的装配或构建，那是技能缺能力，给技能加。

出包踩过的坑归拢在技能里：Nuitka 的命令、编译期挪开前端依赖、abi3 DLL 落在 `.pyd` 自己的目录、
GUI 关控制台、编译产物的导入冒烟。产品仓库只留两件真属于它自己的：取嵌入式运行时，和它自己
发明的交付格式（自更新源、语义特殊的手写 NSIS）。

Mac 上装配好的 `release.ps1` 是构建机上唯一跑的东西，技能的 Python 不上构建机。生成的脚本
在 Mac 上验不了语法，`tests/check-generated-powershell.sh <构建机> <脚本>` 送过去让
PowerShell 自己解析。

**引擎跑不动的时候会自己修再来。** 这套自愈的唯一存在理由就是这个：出包失败 → 诊断 →
按分级派修 → 重跑那一阶段。P0 与保护路径不自动修，停下来交人。

远端构建机（Windows）两个事实的来源顺序是：`RELEASE_REMOTE_HOST` / `RELEASE_REMOTE_ROOT`
两个环境变量优先，都为空时回落到钥匙旁边的 `remote-build.json`。那份文件里还有另外两样
**属于这台机器、不属于任何一把钥匙**的事实：`delivery_root`（安装包收拢到哪，缺省
`<root>-delivered`）与 `build_env`（镜像地址、ccache 装在哪，构建脚本第一步就应用）。
落成文件是为了没有人需要记住它；环境变量留着，是临时换一台构建机的唯一手段。

出包不在两台机器上留过程：源码 zip 传完即删，构建成功且安装包已收进交付目录之后整个构建目录
删掉。**失败的留着**，每个产品留最近两个——现场只存在于那里。

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
