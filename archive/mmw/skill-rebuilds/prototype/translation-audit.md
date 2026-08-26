# `prototype` 1.2.2 翻译审查

## 本技能术语应用

共享术语只由 [上游技能翻译共享术语](../translation-terms.md) 定义。下表记录本技能的术语应用和独有术语，不建立第二份定义。

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| prototype | `prototype` | 上游技能和产物名称 |
| throwaway | 一次性 | 同一约束跨主技能、Logic 和 UI 保持一致 |
| logic、UI | 逻辑、`UI` | 逻辑有准确中文译名；UI 是行业缩写 |
| variant | 变体 | 有准确中文译名，并与 active MMW 一致 |
| free-play | `free-play` | 没有稳定中文方法术语，并与 active MMW 一致 |
| guided walkthrough | `guided walkthrough` | 没有稳定中文方法术语，并与 active MMW 一致 |
| scenario | 场景 | 有准确中文译名，并与 active MMW 一致 |
| state、action、transition | 状态、动作、转移 | 有准确中文译名；代码标识符仍保留英文 |
| pure module、reducer、state machine | 纯 `module`、`reducer`、状态机 | `module` 与 `reducer` 是既有方法或代码术语 |
| primary source | 一手来源 | 与 ask-matt 术语一致 |
| sub-shape | 子形态 | 两种 UI 承载形态的固定称呼 |
| switcher | 切换器 | 有准确中文译名，并与 active MMW 一致 |
| route、page、memory、database | 路由、页面、内存、数据库 | 使用正统中文技术术语 |
| primary affordance | `primary affordance` | 设计术语没有稳定且等价的中文专名；不缩成操作方式或按钮 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。下表逐一登记其他每一行，包括 TSX 示例。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | `name: prototype` 字面量已保留 |
| `SKILL.md:3` | 一次性 prototype、回答设计问题、状态模型或 logic sanity-check 和探索 UI 外观均已保留 |
| `SKILL.md:4` | YAML 结束分隔符已保留 |
| `SKILL.md:6` | `Prototype` 标题已保留 |
| `SKILL.md:8` | prototype 是回答问题的一次性代码，以及问题决定形态均已保留 |
| `SKILL.md:10` | 选择分支标题已保留 |
| `SKILL.md:12` | 从用户 prompt、周围代码或询问在线用户识别问题均已保留 |
| `SKILL.md:14` | logic 或状态模型问题、LOGIC 链接、单一可分享 HTML、自由按钮、tab 走查、困难状态机情形和非开发者可操作均已保留 |
| `SKILL.md:15` | 外观问题、UI 链接、单 route、多个截然不同 variant、URL 参数和底部悬浮栏均已保留 |
| `SKILL.md:17` | 两分支产物差异、选错浪费、含混且用户不在线时按周边代码默认、两类映射和顶部说明假设均已保留 |
| `SKILL.md:19` | 两分支共同规则标题已保留 |
| `SKILL.md:21` | 首日起一次性、清晰标记、靠近实际用途、两个位置例子、命名区分 production、遵守 routing 约定和不自创顶层结构均已保留 |
| `SKILL.md:22` | 极易运行、UI 从 task runner 单命令启动、三个命令例子、logic 双击单 HTML 和启动无需思考均已保留 |
| `SKILL.md:23` | 默认无持久化、memory state、持久化是检查对象而非依赖、database 例外、scratch DB 和明确 wipe 文件均已保留 |
| `SKILL.md:24` | 跳过润色、无测试、只保留可运行错误处理、无抽象和快速学习目的均已保留 |
| `SKILL.md:25` | 每次 logic action 或 UI variant 切换后呈现完整相关 state 均已保留 |
| `SKILL.md:26` | 验证决定进真实代码、prototype 作为一手来源、main 外 branch、issue 指针、保存结论和问题、main 只留验证决定均已保留 |
| `LOGIC.md:1` | `Logic Prototype` 标题已保留 |
| `LOGIC.md:3` | 单一自包含 HTML、可分享 demo、按钮驱动状态模型、三类问题和纸面合理但真实案例暴露问题均已保留 |
| `LOGIC.md:5` | 单文件无安装、交给三类非开发者、亲自感受模型和使用其语言而非代码语言均已保留 |
| `LOGIC.md:7` | 适合形态标题已保留 |
| `LOGIC.md:9` | 状态机处理 X 后 Y 边界例句已保留 |
| `LOGIC.md:10` | 数据模型能否表达某情形例句已保留 |
| `LOGIC.md:11` | 写 API 前体验形态例句已保留 |
| `LOGIC.md:12` | 按按钮观察状态变化的概括已保留 |
| `LOGIC.md:14` | 外观问题属于错误分支并转 UI 已保留 |
| `LOGIC.md:16` | 流程标题已保留 |
| `LOGIC.md:18` | 第 1 步说明问题已保留 |
| `LOGIC.md:20` | 写代码前记录模型与问题、一段可见介绍、不可只写 comment、错问题纯浪费、显式问题供当前或 AFK 后续检查均已保留 |
| `LOGIC.md:22` | 第 2 步隔离可移植 module 已保留 |
| `LOGIC.md:24` | 回答问题的实际 logic、单 script block、小型 pure module、可移入真实代码、page 一次性和 module 非一次性均已保留 |
| `LOGIC.md:26` | 正确形态取决于问题的引导已保留 |
| `LOGIC.md:28` | pure reducer 签名、离散 event 和单一 state value 适用条件均已保留 |
| `LOGIC.md:29` | 状态机、显式 state 与 transition，以及合法 action 是问题时适用均已保留 |
| `LOGIC.md:30` | 普通 data type 上 pure function 集合，以及无隐式 current state 只有 transformation 的条件均已保留 |
| `LOGIC.md:31` | class 或 module、清晰方法集合和持续 internal state 条件均已保留 |
| `LOGIC.md:33` | 按问题而非接 page 难度选形态、pure 禁止三项、单向调用，以及验证 logic 可独立移入真实 module 均已保留 |
| `LOGIC.md:35` | 第 3 步构建可分享 HTML 已保留 |
| `LOGIC.md:37` | 单文件、原生三技术、无三类工具、全部内联、双击、email 后运行和任何人可打开均已保留 |
| `LOGIC.md:39` | 面向非开发者、label 用领域语言、button 和 state 像业务而非 reducer、直白解释均已保留 |
| `LOGIC.md:41` | 自上而下清晰层级已保留 |
| `LOGIC.md:43` | 标题、一行说明、探索内容和第 1 步问题均已保留 |
| `LOGIC.md:44` | 当前完整 state、可读 panel、label field 非 JSON dump、每次 click 重渲染和必要时指出变化均已保留 |
| `LOGIC.md:45` | 每 action 一个自由按钮、始终可用、任意顺序、dispatch 和重渲染均已保留 |
| `LOGIC.md:46` | 引导式走查、每 tab 一个 scenario、说明情形与观察点、顺序按钮、真实 button 执行动作进入下一步和重置已知初态均已保留 |
| `LOGIC.md:48` | scenario 选择、happy path、棘手边界、不合法尝试和纸面难推理均已保留 |
| `LOGIC.md:50` | 美观克制、三项视觉要求、无 animation 花招和不争夺 state button 注意力均已保留 |
| `LOGIC.md:52` | 第 4 步交给用户已保留 |
| `LOGIC.md:54` | 发文件或打开、用户异步走查与自由操作、两句关键反馈、想法中的 bug、加入新 action scenario 和 prototype 演进均已保留 |
| `LOGIC.md:56` | 第 5 步保存答案和 prototype 已保留 |
| `LOGIC.md:58` | 回答后先存答案再按主技能存 prototype、验证 logic 进入真实 module、HTML shell 进一次性 branch 作一手来源和仍易运行均已保留 |
| `LOGIC.md:60` | 反模式标题已保留 |
| `LOGIC.md:62` | 禁止测试和需要测试则不再是 prototype 已保留 |
| `LOGIC.md:63` | 禁止真实 database 和持久化问题例外已保留 |
| `LOGIC.md:64` | 禁止泛化、未来 X 例句和只答一问均已保留 |
| `LOGIC.md:65` | 禁止 logic page 混合、三类引用会破坏可移植性和 page 作为 pure module 薄 shell 均已保留 |
| `LOGIC.md:66` | 禁止 framework、bundler、server，单文件双击和 React 或 dev server 破坏分享均已保留 |
| `LOGIC.md:67` | 禁止 HTML shell 进 production、page 为手动走查优化和只保留 logic module 均已保留 |
| `UI.md:1` | `UI Prototype` 标题已保留 |
| `UI.md:3` | 单 route、多截然不同 variant、底部栏、浏览器切换、选一个或组合和丢弃其余均已保留 |
| `UI.md:5` | logic 或 state 问题属于错分支并转 LOGIC 已保留 |
| `UI.md:7` | 适合形态标题已保留 |
| `UI.md:9` | page 外观例句已保留 |
| `UI.md:10` | dashboard 决定前三个选项例句已保留 |
| `UI.md:11` | settings screen 不同 layout 例句已保留 |
| `UI.md:12` | 用户原本耗时在三个脑中模糊 mockup 选择的情形已保留 |
| `UI.md:14` | 两个子形态和强烈优先 A 已保留 |
| `UI.md:16` | 紧贴 app 更易判断、四类真实环境、孤立 route 真空、现有 host 默认 A 和无邻近归宿才 B 均已保留 |
| `UI.md:18` | 子形态 A 调整现有 page 和首选已保留 |
| `UI.md:20` | 现有 route、同 route variant、URL 参数控制、保留 fetching params auth、只换 rendering 和默认条件均已保留 |
| `UI.md:22` | 尚无 page 但自然属于现有 page、三个例子、仍算 A 和挂载 host page 均已保留 |
| `UI.md:24` | 子形态 B 新 page 和最后手段已保留 |
| `UI.md:26` | 确实无现有 page、全新顶层 surface 和无法嵌入 flow 两例均已保留 |
| `UI.md:28` | 一次性 route、遵守 routing、不自创顶层、明显 prototype 命名、两个命名位置和相同 URL 模式均已保留 |
| `UI.md:30` | 选 B 前快速检查、是否可嵌入和空 route 隐藏设计问题均已保留 |
| `UI.md:32` | 两子形态共用相同悬浮栏已保留 |
| `UI.md:34` | 流程标题已保留 |
| `UI.md:36` | 第 1 步说明问题和选择 N 已保留 |
| `UI.md:38` | 默认 3、超过 5 变噪声和上限 5 均已保留 |
| `UI.md:40` | 在 prototype 位置或顶部 comment 用一行写计划已保留 |
| `UI.md:42` | settings 三 variant、URL 参数和现有 route 示例已保留 |
| `UI.md:44` | 用户在场与否都适用已保留 |
| `UI.md:46` | 第 2 步生成截然不同 variant 已保留 |
| `UI.md:48` | 起草每个 variant 和约束引导已保留 |
| `UI.md:50` | page 用途和可用 data 已保留 |
| `UI.md:51` | component library 或 styling system 和四个例子均已保留 |
| `UI.md:52` | 清晰 exported component name 和三个例子均已保留 |
| `UI.md:54` | 结构差异、三个差异维度、非仅 colour、轻调 card grid 是 wallpaper 和相似时明确禁止 card grid 重做均已保留 |
| `UI.md:56` | 第 3 步接在一起已保留 |
| `UI.md:58` | route 上单一 switcher component 已保留 |
| `UI.md:60` | TSX 代码块起始已保留 |
| `UI.md:61` | pseudo-code 注释已翻译，适配 framework 已保留 |
| `UI.md:62` | 从 searchParams 取 variant 并默认 A 的代码已保留 |
| `UI.md:63` | return 起始已保留 |
| `UI.md:64` | fragment 起始已保留 |
| `UI.md:65` | A 条件渲染及 data 已保留 |
| `UI.md:66` | B 条件渲染及 data 已保留 |
| `UI.md:67` | C 条件渲染及 data 已保留 |
| `UI.md:68` | PrototypeSwitcher、三 variant 和 current 已保留 |
| `UI.md:69` | fragment 结束已保留 |
| `UI.md:70` | return 结束已保留 |
| `UI.md:71` | TSX 代码块结束已保留 |
| `UI.md:73` | 子形态 A、保留 switcher 上方 fetching 和每 variant 只改 subtree 均已保留 |
| `UI.md:75` | 子形态 B、指定 prototype route 和同 switcher 均已保留 |
| `UI.md:77` | 第 4 步构建悬浮 switcher 已保留 |
| `UI.md:79` | 屏幕底部中央 fixed bar 和三个部分均已保留 |
| `UI.md:81` | 左箭头、前一 variant 和循环已保留 |
| `UI.md:82` | label 显示 key 和可选 export name 均已保留；可见界面示例 `B — Sidebar layout` 已本地化为 `B — 侧边栏布局`，不把普通界面文案误作代码字面量 |
| `UI.md:83` | 右箭头、向前和循环已保留 |
| `UI.md:85` | 行为引导已保留 |
| `UI.md:87` | click 更新 URL、使用 framework router、两个框架例子、可分享和 reload 稳定均已保留 |
| `UI.md:88` | 两个键盘箭头、三类 focus 控件和不拦截均已保留 |
| `UI.md:89` | 视觉区分、两个样式例子和不属于评估设计的目的均已保留 |
| `UI.md:90` | production build 隐藏、环境 gate 示例和防意外 merge 发布均已保留 |
| `UI.md:92` | 单 shared component、两形态复用和放 shared UI 位置均已保留 |
| `UI.md:94` | 第 5 步交给用户已保留 |
| `UI.md:96` | 呈现 URL 与 key、异步切换、B header 加 C sidebar 反馈和真实设计结论均已保留 |
| `UI.md:98` | 第 6 步保存答案并清理已保留 |
| `UI.md:100` | variant 胜出、保存哪个与原因、按主技能存 prototype、winner 进真实代码、其余进一次性 branch 而非 main 均已保留 |
| `UI.md:102` | 子形态 A winner 进现有 page、main 删除落选和 switcher 均已保留 |
| `UI.md:103` | 子形态 B winner 升真实 route、main 删除一次性 route 和 switcher 均已保留 |
| `UI.md:105` | 完整 variant 集是一手来源、一次性 branch 非垃圾桶、main 遗留会腐化并误导后人均已保留 |
| `UI.md:107` | 反模式标题已保留 |
| `UI.md:109` | 仅 colour 或 copy 差异只是 tweak、真实 variant 结构分歧均已保留 |
| `UI.md:110` | 共享过多、Header 可共享、Layout 不可共享和每 variant 可抛弃 layout 均已保留 |
| `UI.md:111` | 禁止真实 mutation、只读可用、需 mutation 指向 stub 和外观而非 backend 问题均已保留 |
| `UI.md:112` | 禁止直接进 production、prototype 约束中的无测试少错误处理和吸收时正确重写均已保留 |
| `agents/openai.yaml:1` | `interface` 字段已保留 |
| `agents/openai.yaml:2` | `display_name: "Prototype"` 已保留 |
| `agents/openai.yaml:3` | prototype 回答设计问题已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。四个上游文件的每个非空行，包括 TSX 示例，都有对应译文和独立检查记录 |
| 增写 | 无。没有加入 MMW prototype 产物目录、issue 子目录、走查审批、验证或下游引用接线 |
| 曲解 | 无。一次性编写约束、持续演进、验证 logic 可移植、完整 prototype 作为一手来源保留四项同时存在 |
| 术语漂移 | 无。prototype、一次性、logic、UI、变体、场景、状态、动作、子形态和切换器使用一致 |
