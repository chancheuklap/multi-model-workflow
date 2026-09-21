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

**实测。**

- 往 design system 写入一个组件（`Lamp`）后，Claude Design 没有重新生成 `_ds_bundle.js` 与 `_ds_manifest.json`；在浏览器里打开它、用它的 id 读系统提示，也都不触发。它的编译器只在它自己的建库对话里运行。
- 但组件包不必由它生成：Claude Code 的 design-sync 就是在本地打包再上传。本地用 esbuild 把 `Lamp` 打成组件包、上传后，设计页用 `x-import` 调出的 DOM 与生产版一致（`<span class="lamp orange" data-ui="…">`），本地和 Claude Design 线上预览都通过。线上第一次报错是因为页面运行时晚于组件包加载 React，改为渲染时才取 React 后解决。

**做法。** design system 全部由本地 agent 完成，用户不参与：在 `prototypes/<task>/design-system/` 写出完整目录，`check_design_system.py` 核对 Claude Design 的全部要求与 MMW 的四条规则，`build_ds_bundle.py` 打包组件，design-sync 工具按本地路径上传。中途一度改为"把建库说明交给用户贴进 Claude Design"，实测本地可以完成后撤回。

### 7. 按新流程建任务板的 design system（本地完成）

**真实产物。** `prototypes/task-board/design-system/`，上传到"MMW Task Board 2"（204 个文件）：

- 令牌与组件样式由生产版 `tokens.css`、`board.css`、`settings.css` 与 `index.html` 按原有分节切开，逐行核对无遗漏；
- 46 个组件，各带 `.d.ts` 与 `.prompt.md`，每组一张组件卡；15 张基础卡；UI kit 两张整页与 5 个起步界面；`readme.md`、`SKILL.md`、两个 Lucide 图标；
- `check_design_system.py` 报告完整；`build_ds_bundle.py` 打出 46 KB 的组件包。

**核对。**

- 用同一份示例数据分别跑生产页面与 UI kit，逐区域比较去掉 `data-ui` 后的 HTML：顶栏、任务列表、详情栏完全相同；画布只差初始平移位置（生产页面先渲染后选中卡片，UI kit 一开始就带着选中），卡片本身相同。
- 本地与 Claude Design 线上预览渲染全部 21 张卡片与起步界面，无报错。
- 未核实：Claude Design 没有根据新文件重新生成 `_ds_manifest.json`（仍是 05:57 的版本），Design System 面板能否显示新卡片，要在浏览器里打开才能看到。设计页与 Claude Design 里的 AI 都不依赖这个文件。

### 8. 设计页改用组件

设计项目的 `_ds/` 换成新样式、字体与组件包；7 个页面里的 5 个 `Component · ` 页改为用 `x-import` 挂组件，页面只负责按 `scene` 算出要显示的数据。`x-import` 在组件外包一层 `display: contents`，不影响排版。所有场景本地渲染无报错；App 页的点任务、点齿轮与画布拖动、缩放、`F` 键都已点测；线上整页无报错。

### 9. 收窄 MMW 在设计上的职责

**为什么。** 用户的决定：真实的设计由用户在 Claude Design 里和它的 AI 完成，MMW 只管把设计拿回仓库、为界面验收做好适配；只有用户要本地 agent 画页面时，本地 agent 才按 Claude Design 的设计师提示词（`get_claude_design_prompt` 返回的工作流、`hifi-design`）去画。试点也不再把任务板当新产品继续模拟。

**依据。** 派 agent 逐条查了 `design-pages`、`prototype`、`wayfinder`、`ask-matt` 里每一条对设计的规定，看 pull、`write-screen-contract` 的 lint、`ui-acceptance` 的四种裁判和 `verify-ticket` 有没有读它。被读到的只有：页面名前缀 `Component · ` / `App · `，文件名与 `dc-import` 名相同，`scene` 枚举（取值不含 `/`），`$preview` 正整数，控件带 `data-ui` 且编辑后不变，每个 id 前缀只属于一个 `Component · ` 页，页面只加载项目里的文件。design system、样式与选择器写法、组件用法、`data-screen-label`、`Overview`、交互核对、每次改完看预览、起步界面，都没有下游读取。

**做法。** 项目 `CLAUDE.md` 模板只留上面那些约定；`edit-pages.md` 改为建项目、写约定、处理转给 Claude 的评论、被要求时才画、记录定稿；`design-system.md` 改为可选入口，写明它对 Claude Design 有用、对验收没用、什么时候值得建、两种建法；handoff ticket 的固定句不再点名 design system 入口。

### 10. 项目约定、绑定副本与拉回（`design-pages` 的 edit pages 与 pull）

**做法。** 项目 `CLAUDE.md` 换成新模板，其中写明画页或改页前先读 `state-list.md`；`state-list.md` 由 handoff ticket 叶目录的状态清单生成，写进项目。Claude Design 在用户第一次打开项目时放进来的 `_ds/mmw-task-board-2-…/` 只有样式、字体和一个 315 字节的空组件包，用 `copy_files` 从 design system 拷全（组件包、令牌、组件、字体、图标），页面改从这里加载，原先手工放在 `_ds/` 根目录的副本删掉。

**核对。** 在线整页渲染无报错、282 个 `data-ui`、47 个组件挂在 `MMWTaskBoard2_34b698` 下：Claude Design 自己编译的 598 KB 组件包与本地打包的用法相同。

**真实产物。** 交接包 `prototypes/task-board/claude-design/`（提交 `8b089dff`）：195 个文件，44 个场景离线渲染通过；`pull-report.md` 的 `覆盖` 一节对上全部 40 个状态，另有 104 行"带文字但没有 `data-ui`"的提示（表头、分隔点、代码片段），`改动分类` 为首次。拉回前先按 pull 的规定把 `list_files` 的结果存成文件：195 行，只能由 agent 逐行抄进文件。

**本试点的偏离。** 拉回在用户说定稿之前做：设计页取自生产版，拉回可以重做；用户在 Claude Design 里改过之后再拉一次。第 7 步拆 scaffolding 不适用：胜出方案就是生产版，没有挂载点。

### 11. 写屏幕合同（alignment ticket #554，`write-screen-contract`）

**做法。** 派一个 agent 按技能从头写到 gap list：从交接包抽出控件骨架（44 个场景 × 5 个视口，239 个控件），逐行对照 #543–#552 的决定与生产代码。任务板是标准库写的服务器，没有 OpenAPI 导出，agent 照 `server.py`、`board_data.py`、`settings_api.py` 的路由手写了只含五个接口的 `openapi.json`。gap list 两条交用户裁决：整页刷新按生产版写；保存时配置锁被占用不设界面状态（用户：本机单人写配置，不会发生）。

**真实产物。** `docs/specs/task-board/screen-contract.yaml`，68 行（顶栏 4、任务列表 1、画布 8、详情 16、本机配置 22，整页跨区域 17），lint 0 错误、5 条提示（设计稿没有画到的状态）。旧合同 222 行，由新流程产物替换。

**生产代码做得比决定少的地方**（交给实现票，不是合同缺口）：读 GitHub 失败时顶栏显示的是失败的时间而不是旧数据的时间（`board_data.py` 的 `read_failed.at`），与 #544 相反。起草合同的 agent 另报了两处，写 spec 时核对后不算：打开本机配置 503、重新扫描失败时无提示，合同行本来就写"不提示"，没有决定要求提示；子 issue 编号不能点，因为子 issue 在画布上没有卡片（#545），"票号可点"指跳到那张卡片（#318 第 7 节）。

### 12. 写 spec（`to-spec`），与 scene input

**做法。** 派一个 agent 按技能从地图 #542、#543–#554、屏幕合同与生产代码起草 spec。判断为一个 spec：全部决定落在同一个 seam（board 页面与五个接口）上。

**发现的根本问题。** story 页面按规则只能从 scene data 进入状态，而 scene data 是 pull 记下的按 `data-ui` id 的显示文字：灯的颜色、画布的阻塞边与分列、下拉选中的哪一项都不在里面。任务列表、画布、详情、整页四页的 element parity 因此无法判出通过（#541 待回答问题 6）。设计页本身是从交接包里 `GET /api/board` 形状的数据文件画出来的。决定（工程判断）：屏幕合同的 scene 声明加可选的 `input`（数据文件、其中的值、页面在其上另设的字段 `with`），story adapter 从这同一份值喂产品组件。改动在 `write-screen-contract`（格式、lint 与测试、第 3 步）、`ui-acceptance` 的 `story-parity.md` 与词表的 **scene input**。任务板合同为 44 个 scene 全部声明了 input，逐个核对值存在。

### 13. 切票（`to-tickets`）并发布

**做法。** 派一个 agent 按技能起草票并扫歧义；歧义里两处归用户（顶栏从未读成功时写什么、旧数据的时间写法）、一处关于时机（人工看板在 night 中看试运行版），用户已决定并写进 spec #555 与合同。共用样式 `board.css`、`tokens.css` 归顶栏票所有，其余四个区域票等它落地（工程判断：灯色与令牌在这两个文件里，先定再比）。

**真实产物。** #556（contract ticket）、#557 顶栏、#558 任务列表、#559 画布、#560 详情、#561 本机配置、#562 整页、#563 `settings-save` 验收、#564 人工看板（`ready-for-human`）；发布前用新增的草稿 lint、发布后用 `--lint 555` 各查一遍，0 错误。次序：#556 → #557 → #558–#561 → #562 → #563、#564。

## 发现

| # | 步骤 | 位置 | 现象 | 影响 | 修复（第 1–10 行在提交 `0f79b971`） |
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
| 12 | design system | `design-pages/references/design-system.md` 整篇 | MMW 的非 React 路只上传样式表与类名表，缺 Claude Design 要求的令牌拆分、基础卡、组件、UI kit、`SKILL.md`；而 Claude Design 的编译器只在它自己的建库流程里运行，外部写入的组件不会进组件包 | Design System 面板为空；Claude Design 里的 agent 与起步界面都用不上它；页面只能手写类名 | 重写：先列 Claude Design 的全部要求，再列 MMW 追加的四条（组件输出与来源相同的 DOM、组件接受 `data-ui` 并给部件编号、每个区域一个起步界面、数值与字体原样照抄），再列本地 agent、Claude Design 里的 AI、用户三方各能读写什么；步骤全部归本地 agent。新增 `scripts/check_design_system.py`（核对目录）与 `scripts/build_ds_bundle.py`（打包组件），各带测试 |
| 13 | edit pages / pull | `edit-pages.md` 第 4 步、`pull.md` | 旧流程默认绑定后的项目里有一份 `_ds/`；实际上网页端绑定的旧项目里也没有 | pull 取不到 design system 的样式，离线渲染没有样式 | 第 4 步把样式表闭包、字体、`_ds_bundle.js` 一起拷进 `_ds/`；页面约定改为从 `_ds/` 加载组件包并用组件拼区域 |
| 14 | edit pages | `edit-pages.md` 的 Write pages | "对照胜出方案核对交互"没有说要核对哪些；这次漏了画布拖动 | 设计页少了产品已有的交互 | 写明：区域里每个控件的点击、拖动、滚动、键盘行为都要与胜出方案一致 |
| 15 | edit pages | `edit-pages.md` 的 Write pages | 本地生成的页面按本地路径上传时，上传工具不带版本号核对，技能只写了"每次写入都带 `if_match`" | 可能覆盖用户刚在编辑器里做的修改 | 写明：先 `list_files`，版本号仍等于上次写入留下的才上传 |
| 16 | pull | `design-pages/scripts/pull_design.py` 的 `contract_input` | 重新 pull 时带 `--contract`，脚本把合同行的 `trigger` 当作带 `name` 的映射来读；合同里 `trigger` 是 `data-ui` id 字符串。每一行都被跳过，合同行文字的比对从来没有运行；测试用的也是旧格式 | 设计改了合同行引用的文字，`改动分类` 不报 | 按 `data-ui` id 取上次与这次渲染里该 id 的文字比较；测试改成合同的真实格式 |
| 17 | 写合同 | `write-screen-contract/scripts/lint_screen_contract.py` 的 `stylesheet_breakpoints` | 只读交接包里 `styles/*.css`；页面的样式在 `_ds/<folder>/` 或页面自己的 `<style>` 里 | 视口正好落在断点上时不报，这条检查形同虚设 | 改为读交接包里全部 `.css` 和页面的 `<style>`；加测试；`screen-contract-format.md` 同步 |
| 18 | pull | `pull_design.py` 的 `selector_audit` | "编辑器点不中的选择器"检查读全部 `.css`，包括照抄来源的 `_ds/`，却不读页面自己的 `<style>` | 报告里全是 design system 的行，页面自己的写法反而没查 | 只查页面自己的样式（`_ds/` 以外的 `.css` 与页面 `<style>`），作为提示写进报告；加测试 |
| 19 | 写合同 | `lint_screen_contract.py` 的 `handoff_page_errors` | "`Component · ` 页没有 `scene`"只在 `scenes.json` 列出的页上查，而没有 `scene` 的页不会进 `scenes.json` | 一整个区域没有 `scene`、不被验收时，lint 不报 | 改为查交接包里全部 `Component · ` 页；加测试 |
| 20 | pull | `pull_design.py` 的 `page_inventory` | 没有前缀的页面（笔记、`Overview`）也被报"没有 `scene`" | 报告里有无关的行 | 只报 `Component · ` / `App · ` 页；加测试 |
| 21 | design system | `check_design_system.py` | 要求每个 UI kit 至少一个起步界面；Claude Design 并不要求 | 多一条无下游用处的硬要求 | 改为只统计、不要求；测试同步 |
| 22 | 第 7、13、14 行的修复被第 9 步取代 | `edit-pages.md` | 手工把 design system 上传到项目 `_ds/`、页面必须用组件拼、逐项核对交互，都是 MMW 替设计者定的做法 | 与"设计交给用户"冲突；手工副本还与 Claude Design 自己放的 `_ds/<folder>/` 重复 | 删去；绑定后的副本由 Claude Design 在用户第一次打开项目时放入，pull 一并拉回 |
| 23 | edit pages | `template-project-claude-md.md` 的 `scene` 一节 | 模板只写"项目里若有 `state-list.md`，按这样读"；Claude Design 的 AI 不会主动去找，用户也会忘记它存在；试点项目里也还没写这个文件 | 状态清单写了也没人读 | 改为明确指令：画页或改页前先读 `state-list.md`，页面与清单不一致时问用户，不自己改清单；试点项目已写入 `state-list.md` 与新 `CLAUDE.md` |
| 24 | edit pages | `design-system.md` 的 After the design system changes | 用 `copy_files` 刷新绑定副本原先写着"未实际跑过" | 无法确认刷新办法可用 | 已在试点项目实跑：拷贝成功，页面改用绑定文件夹后线上正常；Claude Design 首次放入的副本只有样式与空组件包，这一点写进 `edit-pages.md` 第 4 步 |
| 25 | pull | `pull_design.py` 的 `strip_injected_head` | 预览服务器现在注入 `\n<style…><script…>\n`，去掉标签后多留一个换行，每个页面都与清单大小差 1 字节 | 7 个页面全部要求补读，pull 走不通 | 去掉标签后若恰好多 1 字节且 `<head>` 后是换行，一并去掉；按实测形状加测试 |
| 26 | pull | `pull_design.py` 的清单读取 | `.thumbnail` 是 Claude Design 的项目卡片图，改页后会自己重新生成（清单 5357 字节，几分钟后下载 11128 字节），而二进制文件没有补读办法 | pull 直接拒绝，改一次页面就要重列清单 | 不再拉 `.thumbnail`；加测试 |
| 27 | pull | `pull_design.py` 的补读提示 | 补读清单嵌在拒绝语句里，被固定长度截断（第三个文件名后是"…"） | agent 不知道要补读哪些文件 | 补读的路径逐行完整打印在拒绝语句上方；加测试 |
| 28 | pull | `pull_design.py` 的 `state_list_regions` | 状态名只在空格处截断；中文清单写"名字：说明"，整串被当作状态名 | `覆盖` 一节把 40 个状态全报缺失 | 状态名在空格、英文或中文冒号、带空格的破折号处截断；加测试 |
| 29 | pull | `pull_design.py` 的 `fetch` | 约 200 个文件里有一个下载时连接出错一次，整次 pull 失败 | 要人工重跑 | 连接错误重试两次，HTTP 状态码不重试；加测试 |
| 30 | pull | `pull.md` 第 1 步、`pull_design.py` 的清单读取 | 要求把 `list_files` 的完整结果（本次 195 行，含字节数与版本号）原样存成文件，而它只在 MCP 回复里，agent 只能逐行抄写；随后按字节数逐个核对、不符就补读 | 费上下文、抄错就对不上；逐文件核对是重复防御（服务器给的就是原文件，只有页面被插了预览脚本） | 拉回只收页面名单（`--pages`），其余文件从页面引用和离线渲染时的请求里找出来；页面只查插入的脚本已去干净；去掉字节数核对、补读与版本号。实跑任务板：拉回 41 个文件，与之前提交的逐字节相同，44 个场景渲染通过，合同 lint 0 错误；页面不加载的文件（组件源码、卡片、`CLAUDE.md`、`state-list.md`）不再拉回。同时去掉"没有自身文字的控件未核对"这类无意义的报告行 |
| 31 | 写合同 | `write-screen-contract/SKILL.md` 的 Inputs | 交接包的内容列表还写 `styles/`，实际样式在 `_ds/<folder>/` | 读者按旧目录找样式 | 改为"项目里的其他文件（绑定的 design system 在 `_ds/<folder>/`）" |
| 32 | 写合同 | `lint_screen_contract.py` 的 `repo_root` | 合同还在 scratch 时不在任何仓库里，lint 静默改用当前目录，从 scratch 跑就报 `baselines.look` 不存在、`.mmw/target.json` 缺失，两条都是假的 | agent 以为合同有错 | 合同不在仓库里时，从 lint 的运行目录往上找仓库；第 7 步写明在仓库里运行；加测试 |
| 33 | 写合同 | `write-screen-contract/SKILL.md` 第 1 步 | `locale` 没有来源，交接包里也没有语言信息 | agent 只能猜 | 写明取产品自己的 `<html lang>`，没有就由用户给 |
| 34 | 写合同 | 同上 Inputs | `openapi.json` 只给了导出器和 app factory 两条路，标准库服务器两者都没有 | agent 不知道能否手写 | 写明可以照路由代码手写 |
| 35 | 写合同 | 同上第 2 步 | `component` 只说"已有的功能目录"，任务板是一个功能一个文件 | agent 要自己判断 | 改为"功能目录或模块文件" |
| 36 | 写合同 | `screen-contract-format.md` 的 A cross-component row | "每处回调一行"与"按控件编号区分行"冲突；没说控件同时影响本区域时要不要另写一行、整页从不画这个控件时 `scenes` 填什么 | agent 各自定规矩 | 改为每个控件一行；影响本区域的另留区域页那一行；整页没画到时 `scenes` 为 `[]` 并由 lint 提示 |
| 37 | 写合同 | 同上 Pages … states | `states` 只说领域状态，缩放、展开、关闭弹窗这类本地视图变化无处可写 | agent 自己造了 9 个名字又不确定是否合规 | 写明本地视图状态也放在 `states` |
| 38 | 写合同 | `extract_skeleton.py`、格式的 `viewports` | 视口是一张平表，每个场景在每个视口都渲染一遍（236 宽的任务列表也按 1440x52 渲染），用时是按页面尺寸的三倍，还产生没人要的截断渲染 | 慢；不影响行的正确性 | 合同加 `pages.<page>.viewports`，这一页的场景只在自己的尺寸渲染与比对；共用渲染器、骨架与 story judge 都按它走，lint 查格式与断点；各加测试。任务板合同改为四个区域各用自己的尺寸：渲染从 220 次降到 44 次，148 秒降到 30 秒，控件数不变 |
| 39 | 写合同 | 格式的 `on_failure`、`shows` | `on_failure` 没有写法规定、lint 也不查；`shows` 的"表达式"没有语法 | 各 agent 写法不一 | 定写法：`shows` 是绑定（`字段@接口`）加可选的 ` → ` 说明，数字检查只查绑定；`on_failure` 每项是去向（行 id、场景、状态、`stay` 或 `toast:<KEY>`）加可选的 ` — ` 说明，lint 查去向；加测试；任务板合同 15 处全部合规 |
| 40 | 写合同 | `extract_skeleton.py` 的输出 | 骨架只记控件"能否交互"，不记"在哪个场景里被禁用"，而技能要求禁用状态单独成行 | agent 要读生产代码推出来，lint 查不到这些行的场景 | 渲染器记下控件是否禁用，骨架记 `disabled_in`，lint 要求每个禁用的场景都有一行 `calls: [none]`、`next: stay` 列出它；加测试。对任务板合同一跑就查出一处漏写：整页空场景里"需要你"是禁用的，没有行，已补 |
| 41 | 写合同 | 各决定票的解决评论 | 决定票以上一代 spec #318 为依据；地图上没有一张票管左侧任务列表，合同只能引 #318 | 已被取代的 spec 能否当来源，技能没说 | `write-screen-contract/SKILL.md` 的 Decision sources 写明：决定票引为依据的旧 spec 可以引用，先引决定票，决定票没覆盖的才引旧 spec |
| 42 | story 验收 | `ui-acceptance/references/story-parity.md`、词表 **scene data** / **story adapter** | story adapter 只能读 scene data（显示文字），状态靠类名与计算布局的组件（灯色、画布）进不了设计页的状态 | 四个页面的 element parity 永远判不出通过 | 屏幕合同加 `scenes.<name>.input`，story adapter 从设计页自己用的数据喂组件；lint 查形状与文件在交接包内；加测试；词表加 **scene input** |
| 43 | 切票 | `to-tickets/references/cutting-interface-tickets.md` 的 contract ticket | "`--check` 什么都不缺就不切"：`--check` 只看答案在不在，看不出 story 服务读的是旧交接包、helper 不按 `data-ui` id 找控件、`start` 没有 break switch | 照原文本批一张 contract ticket 都不切，四种裁判都跑不起来 | 写明这几种也算缺，由 spec 的 How a test arrives at a state 写出；merge-note 同步 |
| 44 | 写 spec | `to-spec/SKILL.md` 的 How a test arrives at a state | 写"三个机制都归 contract ticket"，而 `story-parity.md` 与词表写"contract ticket 建第一个 adapter，之后每页的 ticket 加自己的" | 两条规则冲突 | 与 `story-parity.md` 对齐；已有 `.mmw/` 的产品，缺的包括为别一代建的答案；merge-note 同步 |
| 45 | 写 spec | `to-spec/SKILL.md` 的 Sources | 决定票引为依据的旧 spec 算不算上游 spec 没写 | agent 要猜 | 写明算 |
| 46 | 切票 | `cutting-interface-tickets.md` 的 design-system ticket | `_ds/` 本来就是从产品自己的样式表建的，照规则仍要切一张"抄回产品"的票 | 多一张什么都不改的票 | 写明这种情况不切；merge-note 同步 |
| 47 | journey | `product-answers.md` 的 `leaves_machine`、`target_config.py` | 没有检查能看出 journey 保存配置时会写这台机器真的 `~/.mmw/models.json` | 一次验收就改掉本机配置 | `product-answers.md` 的 `start` 写明：产品默认读写的每个用户级位置（配置目录、XDG 目录、用户设置文件）由 `start` 指到 `MMW_DATA_DIR` 里并放好初值，挪不走的列进 `leaves_machine`；spec #555 第 12 节对任务板提同样要求 |
| 48 | 切票 | `verify-ticket.py --lint` | 只能读已发布的票，而技能要求发布后才 lint，一批票没法在上线前查 | 错票先上线再改 | 加 `--lint --drafts <dir>`，并写明哪几项草稿查不了；to-tickets 第 7 步先查草稿、第 8 步发布后再查；加测试 |
| 49 | 切票 | `critical_flows()` | 读不懂"第 6、8、9 节"的写法，还一路读进下一条 | 关键流程被误读 | 只读到自己那一段为止；唯一接受的写法写进报错与 to-spec 模板；spec #555 改成该写法；加测试 |
| 50 | 切票 | `cutting-interface-tickets.md` 的 contract ticket | 静态守卫放在 contract ticket 上，而它们扫全仓库，其他票落地前必然失败 | 第一张票过不了 | 判据放到最后一张票，与 harness guard 同理 |
| 51 | 切票 | 同上 | 没说 contract ticket 是否给先例组件写 `data-ui` | 两张票都以为是对方的 | 写明 contract ticket 写，第一张区域票的判据来判 |
| 52 | 切票 | `boundary_test_paths` | 只认完整路径，`-s 目录 -p 文件` 写法永远报"还没写" | 假警告 | 认目录加文件的几种写法；加测试 |
| 53 | 切票 | `boundary-check.md` | `detail.close` 与 `detail.close-event` 在 `-k` 子串匹配下互相命中 | 一条判据跑两条测试 | 写明两头锚定的选择方式与发布前的自检 |
| 54 | 切票 | to-tickets 模板的 `## Parent` 与 `source_findings` | 合同行引旧 spec 时，Parent 该怎么写两边说法不一 | lint 报错或取错 spec | Parent 先写所属 spec，再写旧 spec 的小节；lint 查次序；加测试 |
| 55 | 切票 | `cutting-interface-tickets.md` 的 component page ticket | `next` 是别的页面的场景时，区域票的测试断言什么没写 | 各写各的 | 区域票断言交出去的事件，另一页进入场景由整页票断言 |
| 56 | 切票 | `sub-issues.md` 第 5 问与 to-tickets 第 5 步 | 一边允许改 Owns 以外的文件，一边要求同时可跑的票不重叠 | 共用文件在夜里撞车 | 统一为：同时可跑的票不写同一个文件，共用文件归一张票、其余被它挡；implement 同步 |
| 57 | 切票 | `person-ticket.md` | 人工看板要"一个能打开的链接"，而本仓库常驻的是冻结的安装版 | 看到的是旧界面 | 自托管仓库给一条命令，在租约上用测试数据起新版并打印地址 |
| 58 | 切票 | to-tickets 第 6 步 | 要求扫歧义的子 agent 只读，但宿主可能没有按次限制工具的能力 | 无法照做 | 写明在提示里说明只读，前后用 `git status` 核对 |
| 59 | 切票 | lint 输出 | 先打印 `LINT OK`，后面才列出错误 | 读的人以为通过了 | 每张票的结论行放在它所有发现之后并反映它们；加测试 |

## 产品侧的发现（不属于流水线）

- 旧 prototype 的示例数据生成脚本 `prototypes/board-orchestration/task-board/UI/mockup/build_fixtures.py` 跑不起来（它还在写 #415 取消的 `verifier.started`），已删除；那份 mockup 里的数据写明为固定数据。新脚本 `prototypes/task-board/553/UI/build_scenes.py` 由它改写而来。
- 生产代码 `mmw-v2/board/page/event-history.mjs` 没有任何模块引用它（详情栏的事件分块由 `board-logic.mjs` 的 `eventBlocks` 生成），已删除；board 测试集通过。
