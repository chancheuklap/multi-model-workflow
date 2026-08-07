# `improve-codebase-architecture` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| deepening opportunity | `deepening opportunity` | 上游扫描产物的固定名称 |
| module、interface、implementation | `module`、`interface`、`implementation` | codebase-design 核心词汇 |
| depth、deep、shallow | `depth`、`deep`、`shallow` | codebase-design 核心词汇 |
| seam、adapter、leverage、locality | `seam`、`adapter`、`leverage`、`locality` | codebase-design 核心词汇 |
| deletion test | `deletion test` | codebase-design 的固定检验名称 |
| hot spot | 热点 | 标准中文技术译名 |
| scaffold | `scaffold` | 指完整 HTML 骨架模板，不与一般结构混同 |
| candidate | 候选项 | 报告中待用户选择的对象 |
| mass diagram | `mass diagram` | 没有稳定中文方法名称 |
| cross-section | 剖面图 | 有准确中文译名 |
| sub-agent | `subagent` | 与仓库跨技能术语一致 |

## 逐行完整性检查

空行只承担 Markdown 或 HTML 分隔，不包含待翻译文字。下表逐一登记其他每一行。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | `name: improve-codebase-architecture` 字面量已保留 |
| `SKILL.md:3` | 扫描 deepening opportunity、可视化 HTML 报告和围绕所选项 grilling 均已保留 |
| `SKILL.md:4` | `disable-model-invocation: true` 已保留 |
| `SKILL.md:5` | YAML 结束分隔符已保留 |
| `SKILL.md:7` | 技能标题已保留 |
| `SKILL.md:9` | 呈现架构摩擦、deepening opportunity、shallow 转 deep、可测试性和 AI 可导航性均已保留 |
| `SKILL.md:11` | 领域模型提供信息和共享设计词汇基础均已保留 |
| `SKILL.md:13` | codebase-design、七个词汇、三项原则、每条建议准确用词和四个禁用替代词均已保留 |
| `SKILL.md:14` | CONTEXT 领域语言命名 seam、ADR 记录决定和禁止重新争论均已保留 |
| `SKILL.md:16` | 流程标题已保留 |
| `SKILL.md:18` | 第 1 步探索已保留 |
| `SKILL.md:20` | 扫描前范围、YAGNI、未来改动回报、最近改动加权和先定查看位置均已保留 |
| `SKILL.md:22` | 用户指定 module、subsystem 或痛点时采用并跳过推断均已保留 |
| `SKILL.md:23` | 否则回看足够 commit 历史、命令、热点定义、优先路径和分散时扩大范围均已保留 |
| `SKILL.md:25` | 先读领域术语表和相关 ADR 均已保留 |
| `SKILL.md:27` | Agent 工具、Explore 类型、非僵化启发法、自然探索和记录摩擦均已保留 |
| `SKILL.md:29` | 理解一概念需跨多个小 module 跳转的问题已保留 |
| `SKILL.md:30` | shallow 定义为 interface 近似 implementation 已保留 |
| `SKILL.md:31` | 为测试提取 pure function、真实 bug 藏在调用方式和无 locality 均已保留 |
| `SKILL.md:32` | 紧密耦合 module 跨 seam 泄漏已保留 |
| `SKILL.md:33` | 无测试或难经当前 interface 测试已保留 |
| `SKILL.md:35` | 对 suspected shallow 应用 deletion test、集中或移动复杂性和目标信号均已保留 |
| `SKILL.md:37` | 第 2 步以 HTML 报告呈现候选项已保留 |
| `SKILL.md:39` | 自包含 HTML、OS 临时目录、不落仓库、TMPDIR 与两类 fallback、带 timestamp 新文件、三平台打开命令和绝对路径均已保留 |
| `SKILL.md:41` | Tailwind、Mermaid、两者 CDN、适用图形条件、与 CSS SVG 混合、三类图关系、三类编辑图示、每候选前后图和视觉优先均已保留 |
| `SKILL.md:43` | 每候选一张卡片及内容引导已保留 |
| `SKILL.md:45` | Files 和涉及文件 module 已保留 |
| `SKILL.md:46` | Problem 和架构摩擦原因已保留 |
| `SKILL.md:47` | Solution 和直白英语说明变化已保留 |
| `SKILL.md:48` | Benefits 用 locality leverage 和测试改善说明均已保留 |
| `SKILL.md:49` | Before After 并排自绘、展示 shallow 与 deepening 均已保留 |
| `SKILL.md:50` | 三档 recommendation strength 和 badge 均已保留 |
| `SKILL.md:52` | 报告末尾 Top recommendation、首选候选和原因均已保留 |
| `SKILL.md:54` | 领域用 CONTEXT、架构用 codebase-design、Order intake module 正例和两个反例均已保留 |
| `SKILL.md:56` | ADR 冲突只在真实摩擦值得重开时呈现、明确 warning 示例和不列理论禁止项均已保留 |
| `SKILL.md:58` | HTML-REPORT 链接和三项内容均已保留 |
| `SKILL.md:60` | 此时禁止提出 interface、写完后询问用户选择的原句均已保留 |
| `SKILL.md:62` | 第 3 步 Grilling 循环已保留 |
| `SKILL.md:64` | 用户选择后运行 grilling、决策树和五类讨论内容均已保留 |
| `SKILL.md:66` | 决定结晶时就地副作用、运行 domain-modeling 和保持领域模型更新均已保留 |
| `SKILL.md:68` | 新概念命名 deepened module、加入 CONTEXT 和按需创建已保留 |
| `SKILL.md:69` | 明确含混词时立即更新 CONTEXT 已保留 |
| `SKILL.md:70` | 起关键理由拒绝、提议 ADR 原句、未来避免重复门槛、跳过短暂和不言自明理由均已保留 |
| `SKILL.md:71` | 探索备选 interface、运行 codebase-design 和 design-it-twice 并行 subagent 均已保留 |
| `HTML-REPORT.md:1` | HTML 报告格式标题已保留 |
| `HTML-REPORT.md:3` | 单一自包含 HTML、OS 临时目录、两个 CDN、Mermaid 图结构、手工 div SVG 编辑视觉、两类例子、混用和禁止全 Mermaid 均已保留 |
| `HTML-REPORT.md:5` | Scaffold 标题已保留 |
| `HTML-REPORT.md:7` | HTML 代码块起始已保留 |
| `HTML-REPORT.md:8` | doctype 已保留 |
| `HTML-REPORT.md:9` | html 标签已保留，并把语言声明与译文改为 zh-CN |
| `HTML-REPORT.md:10` | head 起始已保留 |
| `HTML-REPORT.md:11` | utf-8 字符集已保留 |
| `HTML-REPORT.md:12` | title 结构与 repo name 占位符已保留，可见文字已翻译 |
| `HTML-REPORT.md:13` | Tailwind CDN script 已保留 |
| `HTML-REPORT.md:14` | module script 起始已保留 |
| `HTML-REPORT.md:15` | Mermaid ESM import URL 和代码已保留 |
| `HTML-REPORT.md:16` | Mermaid 初始化三项配置已保留 |
| `HTML-REPORT.md:17` | script 结束已保留 |
| `HTML-REPORT.md:18` | style 起始已保留 |
| `HTML-REPORT.md:19` | Tailwind 未覆盖的小型自定义层注释已翻译 |
| `HTML-REPORT.md:20` | seam 虚线和手绘箭头例子注释已翻译 |
| `HTML-REPORT.md:21` | seam CSS 已保留 |
| `HTML-REPORT.md:22` | leak CSS 已保留 |
| `HTML-REPORT.md:23` | deep CSS 已保留 |
| `HTML-REPORT.md:24` | style 结束已保留 |
| `HTML-REPORT.md:25` | head 结束已保留 |
| `HTML-REPORT.md:26` | body class 已保留 |
| `HTML-REPORT.md:27` | main class 已保留 |
| `HTML-REPORT.md:28` | header 占位已保留 |
| `HTML-REPORT.md:29` | candidates section id 与 class 已保留 |
| `HTML-REPORT.md:30` | top-recommendation section id 已保留 |
| `HTML-REPORT.md:31` | main 结束已保留 |
| `HTML-REPORT.md:32` | body 结束已保留 |
| `HTML-REPORT.md:33` | html 结束已保留 |
| `HTML-REPORT.md:34` | HTML 代码块结束已保留 |
| `HTML-REPORT.md:36` | Header 标题译为“页头” |
| `HTML-REPORT.md:38` | repo name、date、四项图例、无介绍段和直接候选均已保留 |
| `HTML-REPORT.md:40` | Candidate card 标题已翻译 |
| `HTML-REPORT.md:42` | 图示承担重量、文字稀少直白和自然使用术语均已保留 |
| `HTML-REPORT.md:44` | 每候选一个 article 已保留 |
| `HTML-REPORT.md:46` | Title、简短、命名 deepening 和 Order 示例均已保留 |
| `HTML-REPORT.md:47` | Badge row、三档颜色和四类依赖 tag 均已保留 |
| `HTML-REPORT.md:48` | Files、等宽清单和 class 已保留 |
| `HTML-REPORT.md:49` | Before After 核心、两列并排和下方模式已保留 |
| `HTML-REPORT.md:50` | Problem 一句和困难点已保留 |
| `HTML-REPORT.md:51` | Solution 一句和变化已保留 |
| `HTML-REPORT.md:52` | Wins、每项至多 6 词和三个例子均已保留 |
| `HTML-REPORT.md:53` | 可选 ADR callout 和 amber 框已保留 |
| `HTML-REPORT.md:55` | 禁止解释段和难懂时重画图均已保留 |
| `HTML-REPORT.md:57` | 图示模式标题已保留 |
| `HTML-REPORT.md:59` | 按候选适配、混用、不全相同和多样性目的均已保留 |
| `HTML-REPORT.md:61` | Mermaid graph 和依赖调用流主力标题已保留 |
| `HTML-REPORT.md:63` | X-Y-Z 条件、flowchart graph、Tailwind card、classDef 两类样式和 sequence 前 6 后 1 例均已保留 |
| `HTML-REPORT.md:65` | Mermaid HTML 代码块起始已保留 |
| `HTML-REPORT.md:66` | Tailwind div 已保留 |
| `HTML-REPORT.md:67` | mermaid pre 已保留 |
| `HTML-REPORT.md:68` | flowchart LR 已保留 |
| `HTML-REPORT.md:69` | OrderHandler 到 OrderValidator 已保留 |
| `HTML-REPORT.md:70` | OrderValidator 到 OrderRepo 已保留 |
| `HTML-REPORT.md:71` | OrderRepo 泄漏到 PricingClient 已保留 |
| `HTML-REPORT.md:72` | leak classDef 已保留 |
| `HTML-REPORT.md:73` | C 与 D leak class 已保留 |
| `HTML-REPORT.md:74` | pre 结束已保留 |
| `HTML-REPORT.md:75` | div 结束已保留 |
| `HTML-REPORT.md:76` | 代码块结束已保留 |
| `HTML-REPORT.md:78` | 手工方框箭头和 Mermaid 布局冲突时使用已保留 |
| `HTML-REPORT.md:80` | div module、border label、内联 SVG line path、绝对定位、适用 deep box 灰内部和 Mermaid 重量不足均已保留 |
| `HTML-REPORT.md:82` | 剖面图和分层 shallow 适用已保留 |
| `HTML-REPORT.md:84` | 水平带 class、调用穿层、前 6 薄层无作用、后 1 粗带归并职责均已保留 |
| `HTML-REPORT.md:86` | mass diagram 和 interface 近 implementation 适用已保留 |
| `HTML-REPORT.md:88` | 每 module 两矩形、各自对象、前近等高 shallow 和后 interface 矮 implementation 高 deep 均已保留 |
| `HTML-REPORT.md:90` | Call-graph collapse 标题已翻译 |
| `HTML-REPORT.md:92` | 前调用树嵌套框、后归并单框和内部调用淡化均已保留 |
| `HTML-REPORT.md:94` | 样式指引标题已保留 |
| `HTML-REPORT.md:96` | 编辑而非企业 dashboard、宽松空白、可选 serif 和 class 配色均已保留 |
| `HTML-REPORT.md:97` | 少用颜色、一 accent、泄漏红和 warning amber 均已保留 |
| `HTML-REPORT.md:98` | 约 320px 和前后并排无需滚动目的均已保留 |
| `HTML-REPORT.md:99` | module label class 和 schematic 非 UI 的视觉目的均已保留 |
| `HTML-REPORT.md:100` | 仅两个 script、其余静态、无 app code 和仅 Mermaid 渲染交互均已保留 |
| `HTML-REPORT.md:102` | Top recommendation section 标题已保留 |
| `HTML-REPORT.md:104` | 大卡片、候选名、一句原因、anchor link 和仅此而已均已保留 |
| `HTML-REPORT.md:106` | Tone 译为“语气” |
| `HTML-REPORT.md:108` | 直白英语、简洁、架构词直接来自技能和禁止以简洁为漂移借口均已保留 |
| `HTML-REPORT.md:110` | 必须准确使用的十个词均已保留 |
| `HTML-REPORT.md:112` | 四组禁止替代词及其目标概念均已保留 |
| `HTML-REPORT.md:114` | 合适措辞引导已保留 |
| `HTML-REPORT.md:116` | Order intake shallow 和 interface 近 implementation 示例已保留 |
| `HTML-REPORT.md:117` | Pricing 跨 seam 泄漏示例已保留 |
| `HTML-REPORT.md:118` | Deepen 为一个 interface 一个测试位置示例已保留 |
| `HTML-REPORT.md:119` | 两 adapter 证明 seam、production HTTP 和 tests in-memory 均已保留 |
| `HTML-REPORT.md:121` | Wins 使用 glossary、三个例子、禁止两个含混收益词和不值得出现的理由均已保留 |
| `HTML-REPORT.md:123` | 无 hedging throat-clearing、禁用开场、句转 bullet、可删则删和先用 glossary 再造词均已保留 |
| `agents/openai.yaml:1` | `interface` 字段已保留 |
| `agents/openai.yaml:2` | display name 已保留 |
| `agents/openai.yaml:3` | 寻找并 grilling 架构改进已保留 |
| `agents/openai.yaml:4` | `policy` 字段已保留 |
| `agents/openai.yaml:5` | `allow_implicit_invocation: false` 已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。三个上游文件的每个非空行，包括完整 HTML scaffold 和 Mermaid 示例，都有对应译文和独立检查记录 |
| 增写 | 无。没有加入 MMW designer、报告保存路径、用户审批、验证或工作流接线 |
| 曲解 | 无。先限定热点范围、再报告候选、用户选择后才进入 grilling 且报告阶段不设计 interface 的顺序保持原样 |
| 术语漂移 | 无。deepening opportunity 和 codebase-design 的十个固定术语使用一致 |
