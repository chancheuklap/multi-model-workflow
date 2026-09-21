# 任务板界面流水线试点：过程记录与发现

试点计划是 #541：把任务板当成新产品，从 `wayfinder` 走到 `finish`。设计决定取自生产版任务板，不重新讨论；产物由新流程真实生成。本文件按步骤记录每一步技能实际怎样执行（讨论部分是文字模拟），以及发现的衔接问题。最后一节的待回答问题在试点结束时填写。

## 过程

### 1. 画地图（`wayfinder` 的 Chart the map）

**技能怎样执行。** `wayfinder` 先用 `grilling` 与 `domain-modeling` 访谈两轮。第一轮定终点：agent 会先质疑前提（"已经有 `status.py`，这个东西该不该存在？"），答案取自 #318 的 Problem Statement：`status.py` 只覆盖一夜里在飞的几张票，看不见结构，而且本机配置要手改文件。终点定为"任务板界面的 spec，连同它的 screen contract"。第二轮按广度把所有待决问题摊开，形成十张 decision ticket。终点含界面，所以再开 handoff ticket 与 alignment ticket。任务板在试点里算新产品，所以不开 selection list ticket，也不开新旧界面并存的 ticket。

**真实产物。** 地图 #542；decision ticket #543–#552（grilling 5 张、prototype 4 张、research 1 张）；handoff ticket #553；alignment ticket #554。阻塞关系分两轮接上：handoff ticket 被 4 张 prototype ticket 与会改变页面状态的 2 张 grilling ticket 挡住；alignment ticket 被其余全部 11 张挡住。

### 2. 逐张解 decision ticket（`wayfinder` 的 Work through the map）

**技能怎样执行。** 每张票：认领（assign）→ 按类型解 → 写解决评论 → 关闭 → 在地图的 Decisions so far 追加一行。grilling 票按 `grilling` 一轮一轮地问，每题附推荐答案；research 票派 subagent 用 `research` 技能查；prototype 票按 `prototype` 做变体给用户挑。

**本次的做法（有意偏离，见 #541 规则 6）。** 十张票的答案都取自 #318 对应小节与生产代码，在一个 session 里全部解完。research 票 #550 没有派 subagent，因为事实已经在生产代码 `models.py` 里。四张 prototype 票没有做变体：胜出方案就是生产版界面，叶目录 `prototypes/task-board/<n>/UI/README.md` 只写问题与结论。

### 3. prototype 的胜出方案与状态清单（`prototype` 的 `UI.md` 第 6 步）

**技能怎样执行。** 胜出后在叶目录的 `README.md` 写下哪个变体胜出、为什么，并在 `## State list` 下按区域列出胜出变体的每个状态；后面的 `design-pages` 用这些名字作为 `Component · <区域>` 页与 `scene` 取值，pull 按名字逐个核对。

**真实产物。** 状态清单写在 `prototypes/task-board/553/UI/README.md`：五个区域（顶栏、任务列表、画布、详情、本机配置）共 40 个状态。名字沿用生产版已有的场景名。

### 4. handoff ticket：design system（`design-pages` 的 design system 入口）

**技能怎样执行。** 任务板在试点里是新产品，所以 design system 的来源是 prototype 的胜出方案，也就是生产代码 `mmw-v2/board/page/`。它是纯 JavaScript 加 CSS，走非 React 路：agent 把 `styles.css`、`readme.md` 和样式表引用的字体整理到临时目录，再用 design-sync 工具自己建 design system 并逐个上传（`create_project`，然后 `finalize_plan` 与按本地路径的 `write_files`），文件内容不经过模型。

**真实产物。** design system "MMW Task Board 2"（https://claude.ai/design/p/34b69870-86b7-4125-a104-b9560bcf3956 ）：`styles.css` 由 `tokens.css`、`board.css`、`settings.css` 与页面框架的样式拼成；`readme.md` 按 `template-design-system-readme.md` 填写，列出 18 个组件；另有 `fonts/` 下 15 个字体文件。用它的 id 调 `get_claude_design_prompt`，返回的系统提示里已嵌入这份 `readme.md`。它不出现在 `list_design_systems` 的结果里。

### 5. handoff ticket：设计项目与页面（`design-pages` 的 edit pages 入口）

**技能怎样执行。** 用 design system 的 id 读 Claude Design 的系统提示，新建绑定它的项目，写入 support.js、design system 的样式副本 `_ds/` 与项目 `CLAUDE.md`，然后按 `CLAUDE.md` 的约定写页面：每个区域一个 `Component · ` 页，`scene` 取状态清单里的名字，控件和要验收外观的元素带 `data-ui` id；每改一次就看一次预览。

**真实产物。** 项目"MMW 任务板 · #553"（https://claude.ai/design/p/c9e1a903-013c-411c-9a1f-7c6b2f85f58a ）：五个 `Component · ` 页（顶栏、任务列表、画布、详情、本机配置）、`App · 任务板` 与 `Overview`。

- 页面上的逻辑不是重写的：`prototypes/task-board/553/UI/bundle_logic.py` 把生产版 `mmw-v2/board/page/` 的纯逻辑模块打包成一个普通脚本 `lib/board.js`，页面调用的是生产版自己的函数。
- 示例数据由 `prototypes/task-board/553/UI/build_scenes.py` 生成：事件用 `events.build` 写，每个看板场景再经生产版后端的 `BoardStore._shape` 整形，与 `GET /api/board` 的回答同形。
- 每个场景都在本地按 pull 的方式（包装页固定场景、Chromium、虚拟时钟）渲染检查过，没有控制台错误；App 页的两个跨区域联动已点测：点任务列表的另一个任务，画布换成它的树；点齿轮，本机配置弹出、看板在下面透出。

### 6. 按 Claude Design 的基础要求重建 design system

**为什么重来。** 第 4 步建的 design system 只有样式表、readme 和字体，在 Claude Design 里的 Design System 面板是空的。对照 Claude Design 自己的建库说明和内置的 Classical：它要求令牌文件、12 张以上基础卡、按来源完整列出的 React 组件（由它的编译器打成 `_ds_bundle.js`，页面用 `x-import` 挂载）、UI kit 与起步界面、`SKILL.md`。MMW 原来的"只给样式表和类名"是自己发明的路，Claude Design 的面板、组件包、起步界面都用不上。

**实测。** 往 design system 写入一个组件（`Lamp`）后，`_ds_bundle.js` 与 `_ds_manifest.json` 都没有重新生成；在浏览器里打开它、用它的 id 读系统提示，也都不触发。编译器只在 Claude Design 自己建库的流程里运行。

**做法。** 非 React 产品的 design system 改由 Claude Design 按它自己的建库流程建：MMW 从代码填一份建库说明（来源、完整的组件清单、MMW 追加的四条规则），用户在 Claude Design 里贴进去；建完后 MMW 经 MCP 按清单核对。任务板的说明在 `prototypes/task-board/553/UI/design-system-brief.md`，36 个组件族，每个注明来源文件与行号。

## 发现

| # | 步骤 | 位置 | 现象 | 影响 | 修复（提交 `0f79b971`） |
| --- | --- | --- | --- | --- | --- |
| 1 | 画地图 | `wayfinder/SKILL.md` 的 `### Tickets` 与 `### Chart the map` 第 4 步 | ticket 正文的模板以 `## Question` 开头，第 4 步又要求 handoff ticket 与 alignment ticket 的"正文第一行"是一句固定的话。两条不能同时成立 | agent 要自己猜。把固定句放在标题下面时，它就不是第一行，接手的 agent 可能照 `grilling` 类型去做访谈，而不是用 `write-screen-contract`。本次把固定句放在 `## Question` 之前 | `wayfinder/SKILL.md` 第 4 步改为：固定句在 `## Question` 之上，作为正文开头一行；merge-note 与词表同步 |
| 2 | prototype → design-pages | `design-pages/references/design-system.md` 的 Which code、`edit-pages.md` 的 Write pages、`pull.md` 第 2 步 `--state-list` | 三处都假定只有一个胜出方案、一份 `## State list`。而 `wayfinder` 会把"长什么样"拆成几张 prototype ticket，每张一个叶目录，没有规则说怎么合并 | pull 的 `覆盖` 一节只能对照其中一份，其他区域不被核对；design system 也不知道从哪一个变体建。本次把合并后的状态清单放在 handoff ticket 自己的叶目录 | 定下一个界面只有一份状态清单：有地图时写在 handoff ticket 的叶目录 `README.md`，汇总每张 UI prototype 票的胜出方案（`prototype/UI.md` 第 6 步）；`design-pages` 的 `design-system.md`、`edit-pages.md`、`pull.md` 改为指向这一份；merge-note 与词表同步 |
| 3 | prototype | `prototype/SKILL.md` 规则 1 | `<task>` 取 wayfinder 地图的标题，而标题是中文、带空格和冒号，没有规则说怎样变成目录名 | 每个 agent 各起一个目录名，同一个任务的叶目录会散开。本次用 `task-board` | `<task>` 改为小写 ASCII 单词用 `-` 连成的目录名，由地图的 `## Notes` 写明（`wayfinder` 的地图模板加这一项，`prototype/SKILL.md` 规则 1 按它取）；merge-note 与词表同步 |
| 4 | pull | `design-pages/references/pull.md` 第 2 步、`write-screen-contract/references/screen-contract-format.md` 的示例 | handoff package 放在哪个目录没有任何地方规定。pull 只收一个参数；合同格式的示例写 `docs/prototypes/<task>/claude-design`，而 prototype 的目录在 `prototypes/<task>/<issue>/UI/`，两处连根目录都不一样 | 每次 pull 的位置各不相同，后面的合同和 ticket 要跟着猜 | `pull.md` 第 2 步定下 `<handoff dir>` 是 `prototypes/<task>/claude-design/`；`screen-contract-format.md` 的示例改成同一路径；词表同步 |
| 5 | design system | `design-pages/references/design-system.md` 的 Which path | 非 React 路只说上传两个文件。产品自带字体时，字体文件没有说怎么进 design system | 设计侧用替代字体排版，行高不同，element parity 会在文字上报出大量差异（旧 README 记录过同样的问题） | `design-system.md` 的非 React 路改为：连同样式表引用的字体、图片一起整理，由 agent 用 design-sync 工具自己建 design system 并按本地路径上传；没有这个工具的会话才交给用户在网页上建（网页上传能否收字体文件，未核实） |
| 6 | design system | `design-pages/references/edit-pages.md` 的 Create the project 第 1 步 | 要用 design system 的 id 调 `get_claude_design_prompt`，但 `list_design_systems` 只列出内置的 Classical 与 Modernist，用户自己的"MMW Task Board"不在里面（`get_project` 能查到它）。技能没说 id 从哪来 | 新建的 "MMW Task Board 2" 同样不在列表里（已核实）；技能不写 id 的来源，agent 就拿不到它 | `design-system.md` 写明 design system 的 id 就是 `create_project` 返回的 `projectId`，并记下 `list_design_systems` 不列它（2026-09-21 实测）；`edit-pages.md` 第 1 步指向这个 id |
| 7 | edit pages | `design-pages/references/edit-pages.md` 的 Create the project | 经 MCP 新建的项目是空的，没有 `_ds/`；四步里没有把 design system 拷进项目这一步 | 页面引用 `./_ds/styles.css` 时 404，页面没有样式 | 改成五步：第 4 步用 `copy_files` 把 design system 的样式、readme 与样式表引用的文件拷进 `_ds/`；MCP 工具清单补上 `finalize_plan`、`copy_files` |
| 8 | edit pages | 同上，第 4 步 | 项目 `CLAUDE.md` 是保留路径，项目级授权不覆盖它，写入被拒；技能没说 | agent 卡在这一步，或绕开授权 | 第 5 步写明：单独用 `finalize_plan` 点名 `CLAUDE.md`，用户批准后写入，`if_match` 为 `"0"` |
| 9 | edit pages | `edit-pages.md` 的 Write pages | 页面依赖的大文件（示例数据 430 KB、打包的逻辑 100 KB）只能用 `write_files` 内联上传，内容要经过模型 | 费上下文，且可能超过单次读取上限 | 写明：本地生成的文件用 design-sync 工具按本地路径上传；已实测它对普通页面项目同样可用 |
| 10 | edit pages | `template-project-claude-md.md` 的 Composition | 页面根元素写 `height: 100%` 时，在项目预览里高度为 0，页面空白；pull 的包装页给了高度，所以 pull 看不出来 | 用户在 Claude Design 里看到空白页 | 模板写明：页面根元素取 `$preview` 的像素宽高，或 `App · ` 页传给它的尺寸；设计项目里的 `CLAUDE.md` 已同步 |
| 11 | 写合同 | `write-screen-contract/scripts/lint_screen_contract.py` 第 59 行 | （撤回）曾以为合同检查拒绝中文 `data-ui` id。核实后：被检查的是合同行自己的编号 `id`，按规定就是英文；`data-ui` 在 `trigger` 字段，不限字符 | 无 | 不改 |
| 12 | design system | `design-pages/references/design-system.md` 整篇 | MMW 的非 React 路只上传样式表与类名表，缺 Claude Design 要求的令牌拆分、基础卡、组件、UI kit、`SKILL.md`；而 Claude Design 的编译器只在它自己的建库流程里运行，外部写入的组件不会进组件包 | Design System 面板为空；Claude Design 里的 agent 与起步界面都用不上它；页面只能手写类名 | 重写：先列 Claude Design 的全部要求，再列 MMW 追加的四条（组件输出与来源相同的 DOM、组件接受 `data-ui` 前缀并给部件编号、每个区域一个起步界面、数值与字体原样照抄）；非 React 产品改为由 Claude Design 按 MMW 的建库说明（新模板 `template-design-system-brief.md`，取代原 readme 模板）来建，MMW 经 MCP 核对 |
| 13 | edit pages / pull | `edit-pages.md` 第 4 步、`pull.md` | 旧流程默认绑定后的项目里有一份 `_ds/`；实际上网页端绑定的旧项目里也没有 | pull 取不到 design system 的样式，离线渲染没有样式 | 第 4 步把样式表闭包、字体、`_ds_bundle.js` 一起拷进 `_ds/`；页面约定改为从 `_ds/` 加载组件包并用组件拼区域 |
| 14 | edit pages | `edit-pages.md` 的 Write pages | "对照胜出方案核对交互"没有说要核对哪些；这次漏了画布拖动 | 设计页少了产品已有的交互 | 写明：区域里每个控件的点击、拖动、滚动、键盘行为都要与胜出方案一致 |

## 产品侧的发现（不属于流水线，本试点不改）

- 旧 prototype 的示例数据生成脚本 `prototypes/board-orchestration/task-board/UI/mockup/build_fixtures.py` 已经跑不起来：它还在写 #415 取消的 `verifier.started`。新脚本 `prototypes/task-board/553/UI/build_scenes.py` 由它改写而来。
- 生产代码 `mmw-v2/board/page/event-history.mjs` 没有任何模块引用它，详情栏的事件分块已经改由 `board-logic.mjs` 的 `eventBlocks` 生成。
