"""Data of lesson 0018's panorama: every component of MMW v3, read from the skill files where the files
say it, and the Chinese a person reads written here.

Read from the files: the route line of each playbook (mmw-mode `## Playbooks`), each playbook's steps, their
`Done when` lines and every skill, playbook, principle and script a step names; each principle's index
line; each skill's description, scripts and references; each role in dispatch's `roles.json`. Written
here: the columns, a Chinese name and one sentence for each component, the decision points that are
the owner's, the links no step names (who starts which session, what a script reads and writes), and
the typical paths. The page's script draws the network from the JSON this returns."""
import json
import html
import re
from pathlib import Path

from kit import fits, tw

REPO = Path(__file__).resolve().parents[3]
SKILLS = REPO / "mmw-v3" / "skills"
MODE = SKILLS / "mmw-mode"

# ---------------------------------------------------------------- columns, left to right in run order
COLUMNS = [
    ("entry", "入口", "会话怎样开始"),
    ("router", "路由", "mode 把任务分给一份 playbook"),
    ("playbook", "playbook", "一类任务从头到尾怎么做"),
    ("gate", "你的决定点", "停下来等你"),
    ("role", "会话与子代理", "谁在干活"),
    ("skill", "技能", "一件事怎么做"),
    ("machine", "程序与钩子", "真正执行的代码"),
    ("record", "记录与外部系统", "留下什么、连着谁"),
    ("principle", "原则", "做某个决定时读"),
]

PLAYBOOK_GROUPS = [
    ("一夜与一张票", ["run-a-night", "run-one-ticket", "work-a-ticket", "review-a-ticket", "pause-safely"]),
    ("从想法到一批票", ["chart-a-map", "resolve-a-map-ticket", "write-a-spec", "revise-a-spec", "cut-tickets", "triage"]),
    ("界面", ["design-in-claude-design", "build-a-design-system", "pull-a-design", "write-the-screen-contract"]),
    ("单项工程", ["bug-fix", "make-a-small-change", "investigation", "improve-the-architecture", "ship-a-release"]),
    ("维护仓库与技能集", ["set-up-code-checkers", "write-agents-md", "authoring-or-modifying-a-skill", "review-the-skill-set"]),
]

PLAYBOOK_ZH = {
    "run-a-night": ("跑一夜", "作为 orchestrator，从 open 到 finish 跑一个 spec 已发布的票。"),
    "run-one-ticket": ("跑一张票", "夜外由这个会话当 orchestrator 跑一张写好的票，从 open-ticket 到 land。"),
    "work-a-ticket": ("做一张票", "worker 从认领到收尾评论做完一张票，中间开出 reviewer。"),
    "review-a-ticket": ("评审一张票", "reviewer 按轴评审 diff，核实每条发现，贴评审报告。"),
    "pause-safely": ("安全暂停", "干净地停下，留一个新会话能接着做的检查点。"),
    "chart-a-map": ("画地图", "把一个一个会话做不完的模糊想法，画成 tracker 上一张决策票的地图。"),
    "resolve-a-map-ticket": ("解决一张地图票", "一个会话解决地图上的一张决策票，记到地图上，推进前沿。"),
    "write-a-spec": ("写 spec", "把已定下的决定写成 tracker 上的 spec，接着拆票。"),
    "revise-a-spec": ("修订 spec", "原地改已发布 spec 的一节，留下原因，让已拆的票对齐。"),
    "cut-tickets": ("拆票", "把已发布的 spec 拆成一夜要跑、你批准过的一批票。"),
    "triage": ("分诊", "和你一起过分诊队列，把能派给 agent 的 issue 带进 spec。"),
    "design-in-claude-design": ("在 Claude Design 里设计", "建好一个 effort 的 Claude Design 项目，交给里面的 agent，处理评论直到你签收。"),
    "build-a-design-system": ("建设计系统", "判断值不值得建，再让 Claude Design 里的 agent 从代码或签收页建出来并检查。"),
    "pull-a-design": ("拉取设计", "把签收的 Claude Design 页面写进仓库成为设计包，读拉取报告决定下一步。"),
    "write-the-screen-contract": ("写屏幕契约", "把设计包里每个控件绑定到它背后的后端决定。"),
    "bug-fix": ("修 bug", "复现并找到你报的缺陷的原因，写一张票，用 Run one ticket 落地，在同一处证明修好。"),
    "make-a-small-change": ("做小改动", "你在场时做完一个不需要产品决定的小改动，并请第二个读者评审。"),
    "investigation": ("调查", "只读的问题：X 怎么工作、为什么这样建、该选哪个；给出带出处的解释或建议。"),
    "improve-the-architecture": ("改进架构", "找出可以加深的模块做成 HTML 报告，把你选的一个拷问成决定，交给 Write a spec。"),
    "ship-a-release": ("打安装包", "为这次改动碰到的每个产品，从当前分支同一个提交打安装包，交你试装。"),
    "set-up-code-checkers": ("装代码检查器", "给仓库装 linter、formatter、类型检查，一条检查命令和提交钩子。"),
    "write-agents-md": ("写 AGENTS.md", "按固定格式写根目录和子目录的 AGENTS.md 与 CLAUDE.md。"),
    "authoring-or-modifying-a-skill": ("写或改技能", "把给 agent 读的文字放进对的组件、写好、检查，并在真实任务上走一遍。"),
    "review-the-skill-set": ("评审技能集", "按 agent 实际做的任务走查技能文字，写评审报告，再逐条修。"),
}

SKILL_GROUPS = [
    ("夜里的流水线", ["dispatch", "verify-ticket", "code-review", "ui-acceptance", "retro", "setup-mmw"]),
    ("理解与决定", ["how", "why", "research", "advisor", "grilling", "to-questionnaire", "wayfinder", "domain-modeling", "codebase-design"]),
    ("界面与原型", ["design-pages", "write-screen-contract", "prototype", "diagram-design"]),
    ("工程", ["tdd", "diagnosing-bugs", "triage", "exe-release", "manage-agents-md", "wizard", "handoff"]),
    ("写作", ["writing-for-agents", "technical-writing", "unslop"]),
    ("只由你启动", ["teach", "wait-what"]),
]

SKILL_ZH = {
    "dispatch": ("调度", "开会话、叫醒会话、看守会话的脚本，以及角色表；改角色的模型或 runner、开看板、被叫醒时怎么做。"),
    "verify-ticket": ("验票", "跑票的验收标准，通过后收尾；从票里切出子问题；发布一批票前做 lint。"),
    "code-review": ("代码评审", "按 Standards、Spec、Tests、UI 四个轴各派一个子代理评审一个 diff。"),
    "ui-acceptance": ("产品验收", "四个判官、端口租约，以及被测仓库在 .mmw/target.json 里的回答。"),
    "retro": ("夜间复盘", "先证据后结论地复盘一夜，写 Retro Memory 和改进提议。"),
    "setup-mmw": ("接入流水线", "检查并补齐一个仓库接入流水线要的文件、标签、Memory Space 和检查命令。"),
    "how": ("讲清怎么工作", "开 researcher 和 explainer 会话，解释 X 是怎么工作的。"),
    "why": ("讲清为什么", "开 researcher 和 synthesizer 会话，追溯代码为什么这样写。"),
    "research": ("调研", "对照一手来源调查一个仓库外的问题，写成带出处的笔记。"),
    "advisor": ("第二意见", "在更强的模型上另开一个会话，对一个决定给第二意见。"),
    "grilling": ("拷问", "按决定树一轮轮追问，直到双方对一个计划达成共识。"),
    "to-questionnaire": ("问卷", "把卡在第三个人知识上的决定写成给那个人的问卷。"),
    "wayfinder": ("地图", "地图、决策票、迷雾、范围外这些概念和格式。"),
    "domain-modeling": ("领域建模", "边设计边维护 CONTEXT.md 词汇表和 ADR。"),
    "codebase-design": ("深模块设计", "设计模块接口的共同词汇：深度、接缝、删除测试。"),
    "design-pages": ("设计页", "Claude Design 项目和设计包的约定；pull_design.py 拉取设计。"),
    "write-screen-contract": ("屏幕契约", "屏幕契约文件的格式、规则和脚本。"),
    "prototype": ("原型", "用代码回答一个设计问题：逻辑、界面或实现上的试验。"),
    "diagram-design": ("画图", "生成带样式的 HTML 和 SVG 图。"),
    "tdd": ("测试驱动", "红、绿、重构：好测试、接缝和反模式。"),
    "diagnosing-bugs": ("诊断 bug", "难 bug 的诊断流程：先建一个能反复复现的回路。"),
    "triage": ("分诊状态", "把一个 issue 在分诊的几种状态之间移动。"),
    "exe-release": ("打安装包", "Electron 加 Python 产品的发布清单和发布引擎 release-flow.sh。"),
    "manage-agents-md": ("AGENTS.md 格式", "AGENTS.md 和 CLAUDE.md 的固定格式和检查脚本 check.sh。"),
    "wizard": ("人工步骤向导", "生成一个交互式 bash 向导，带人走只有人能做的步骤。"),
    "handoff": ("交接文档", "写一份交接文档，让新会话能接着做。"),
    "writing-for-agents": ("给 agent 写作", "写给 agent 读的文字（技能、AGENTS.md、提示词）的规则。"),
    "technical-writing": ("技术写作", "写给人读的文档的规则。"),
    "unslop": ("去 AI 腔", "删掉文字里的 AI 写作套路。"),
    "teach": ("教学", "在一个教学工作区里分多次课教你一个主题。"),
    "wait-what": ("重讲", "上一条没讲明白，用更简单的话重讲。"),
}

PRINCIPLE_ZH = {
    "start-from-what-exists": "从已有的出发", "laziness-protocol": "懒惰协议",
    "migrate-callers-then-delete-legacy-apis": "先迁调用方，再删旧接口",
    "separate-before-serializing-shared-state": "先拆开共享，再谈排队",
    "prove-it-works": "证明它能用", "read-before-you-conclude": "先读再下结论",
    "run-the-smallest-test-set": "跑最小的测试集", "a-check-must-be-able-to-fail": "检查必须能失败",
    "fix-the-product-not-the-check": "修产品，不改检查", "baseline-is-the-contract": "基线就是契约",
    "never-block-on-the-human": "不卡在人身上", "progress-is-what-the-record-says": "进度以记录为准",
    "write-for-where-it-is-read": "为读到它的地方而写", "anchor-every-reference": "每个引用都要锚定",
    "files-describe-the-present": "文件只写现在",
}

# Roles: dispatch's roles.json, with the two worker rows drawn as one node.
ROLE_ZH = {
    "orchestrator": ("orchestrator", "你开的会话跑 Run a night 或 Run one ticket 时的身份：开会话、被叫醒、做每个决定。"),
    "worker": ("worker（junior / senior）", "把一张票做到关闭：写代码、跑验收标准、开 reviewer。票的标签决定用 junior 还是 senior 那一行模型。"),
    "reviewer": ("reviewer", "评审一张票的 diff，派出 code-review 的四个轴。"),
    "advisor": ("advisor", "在更强的模型上对一个决定给第二意见。"),
    "researcher": ("researcher", "读一个来源、代码的一个角度，或回答地图上的一张调研票，交回带出处的发现。"),
    "explainer": ("explainer", "把发现写成一篇「怎么工作」的解释。"),
    "synthesizer": ("synthesizer", "把发现分成已证实、推断、不知道三类，并抽查引用。"),
    "code-review axis": ("审查轴 ×4", "Standards、Spec、Tests、UI 各一个，沿一个轴评审一个 diff。"),
    "grilling fact-finder": ("拷问时查事实", "拷问时去文件或工具里查一个问题需要的事实。"),
    "ambiguity scanner": ("歧义扫描", "读一遍 spec 和草稿票，找出缺失或含糊的决定，最多五个问题。"),
    "architecture explorer": ("架构探索", "走查划定范围的代码，记下难懂、难改、难测的地方，最多十处。"),
    "interface designer": ("接口设计", "在给定约束下设计一个截然不同的模块接口。"),
    "AGENTS.md surveyor": ("AGENTS.md 调查", "读一组仓库内容，报告 AGENTS.md 需要的事实和证据。"),
}

# ---------------------------------------------------------------- nodes written here
# id: (kind, carrier, name, zh, purpose, group, source)
HAND = {
    # entry
    "en:you": ("entry", "human", "你开一个会话", "你", "你在终端或编辑器里开会话、提任务。", "", "AGENTS.md"),
    "en:hook": ("entry", "hook", "mode-hook.py", "会话开始时的钩子", "仓库里有 .mmw/ 时，Claude Code 和 Codex 的会话一开始就被告知：先完整读 mmw-mode 的 SKILL.md。", "", "mmw-v3/skills/mmw-mode/scripts/mode-hook.py"),
    "en:slash": ("entry", "command", "/mmw-mode 或 /技能名", "你点名", "Grok、Cursor，或没有 .mmw/ 的仓库，由你输入 /mmw-mode；只由你启动的技能（teach、wait-what）也这样开。", "", "mmw-v3/skills/mmw-mode/README.md"),
    "en:userprompt": ("entry", "prompt", "shared.md", "用户级提示词", "每个宿主的每个会话都读，带不带 mode 都读：读回复的人是谁，哪些决定只归他。Claude Code、Codex、Grok 经 install.sh 装的软链或生成文件读到；Cursor 的在 app 里手动粘贴。", "", "mmw-v3/prompt/README.md"),
    "en:prompt": ("entry", "prompt", "start prompt", "脚本开会话的第一句", "dispatch.sh 开 worker 或 reviewer 时写的两句话：先完整读 mmw-mode 的 SKILL.md，再在这张票上跑哪份 playbook；后面附上数据。", "", "mmw-v3/skills/dispatch/scripts/dispatch.sh (start_prompt)"),
    # router
    "mode": ("router", "skill", "mmw-mode", "MMW 的工作方式", "每个会话先读它。七节：必守的触发、15 条原则的索引、什么时候直接做什么时候停、子代理、怎么写回复、注释、以及把任务分给 24 份 playbook 的路由行。", "", "mmw-v3/skills/mmw-mode/SKILL.md"),
    # gates
    "g:always": ("gate", "human", "始终停下的事", "产品决定与不可逆的事", "顾客看到什么、钱、范围和顺序、对外发布、删数据这类不可逆的事，只有你能定；agent 先做完不依赖它的部分再问。", "", "mmw-v3/skills/mmw-mode/SKILL.md (## Autonomy)"),
    "g:map-destination": ("gate", "human", "地图的终点", "Chart a map 第 1 步", "你同意一两行话：地图走到底是什么样。", "", "mmw-v3/skills/mmw-mode/playbooks/chart-a-map.md"),
    "g:map-hitl": ("gate", "human", "地图上要你回答的票", "Resolve a map ticket 第 3 步", "grilling 票只能由你自己的回答解决；prototype 票由你对做出来的东西表态。", "", "mmw-v3/skills/mmw-mode/playbooks/resolve-a-map-ticket.md"),
    "g:spec-calls": ("gate", "human", "spec 里的产品决定", "Write a spec 第 1、4 步", "一份还是几份 spec，以及没有来源能定的顾客、钱、范围上的决定，交你定。", "", "mmw-v3/skills/mmw-mode/playbooks/write-a-spec.md"),
    "g:breakdown": ("gate", "human", "批准拆票", "Cut tickets 第 6 步", "你看拆分的粒度、阻塞关系、worker 等级和每个选择，批准后才发布。", "", "mmw-v3/skills/mmw-mode/playbooks/cut-tickets.md"),
    "g:triage": ("gate", "human", "分诊结论", "Triage 第 1、2 步", "你挑要看的 issue，每个定四种结局之一。", "", "mmw-v3/skills/mmw-mode/playbooks/triage.md"),
    "g:start-night": ("gate", "human", "开夜", "Run a night 第 1 步", "你说这一夜开始，orchestrator 才 check、open。", "", "mmw-v3/skills/mmw-mode/playbooks/run-a-night.md"),
    "g:accept-night": ("gate", "human", "验收这一夜", "Run a night 第 10 步", "你早上读 NIGHT SUMMARY 和 NIGHT RETRO，接受之后才 finish，把这一夜合进项目分支。", "", "mmw-v3/skills/mmw-mode/playbooks/run-a-night.md"),
    "g:design-signoff": ("gate", "human", "设计签收", "Design in Claude Design 第 8 步", "你签收页面；之后的改动只能在 Claude Design 里改，再拉取一次。", "", "mmw-v3/skills/mmw-mode/playbooks/design-in-claude-design.md"),
    "g:design-system": ("gate", "human", "设计系统完成", "Build a design system 第 5 步", "你在 Claude Design 里说「开始」，回答统一问题，告诉 agent 完成了。", "", "mmw-v3/skills/mmw-mode/playbooks/build-a-design-system.md"),
    "g:gap-list": ("gate", "human", "缺口清单", "Write the screen contract 第 7 步", "设计有、后端没有，或后端有、设计没有的行，你逐条定。", "", "mmw-v3/skills/mmw-mode/playbooks/write-the-screen-contract.md"),
    "g:arch-pick": ("gate", "human", "选一个架构候选", "Improve the architecture 第 3、4 步", "你从报告里挑一个候选，在拷问里确认或否决。", "", "mmw-v3/skills/mmw-mode/playbooks/improve-the-architecture.md"),
    "g:seams": ("gate", "human", "确认测试接缝", "Make a small change 第 2 步", "没有票时，把要测的接缝写进请求文件，请你确认。", "", "mmw-v3/skills/mmw-mode/playbooks/make-a-small-change.md"),
    "g:agents-md": ("gate", "human", "AGENTS.md 的问题", "Write AGENTS.md 第 5 步", "调查不出的事（项目是什么、哪些规则留下）问你，每题带推荐答案。", "", "mmw-v3/skills/mmw-mode/playbooks/write-agents-md.md"),
    "g:install-test": ("gate", "human", "试装", "Ship a release 第 5 步", "机器判断不了装上能不能用；你装好试过，才算交付。", "", "mmw-v3/skills/mmw-mode/playbooks/ship-a-release.md"),
    "g:install": ("gate", "human", "换本机跑的版本", "只由你授权", "本机跑哪一份，只由一次显式的 install.sh 决定；install.sh 只在你授权时跑。", "", "AGENTS.md (Gotchas)"),
    # machine
    "sc:dispatch": ("machine", "command", "dispatch.sh", "调度主脚本", "开夜、推进、合并、开 worker 和 reviewer、开 brief 会话、reverify、summary、finish、suspend。每一步写成票上的事件。", "调度", "mmw-v3/skills/dispatch/scripts/dispatch.sh"),
    "sc:relay": ("machine", "process", "relay.py", "中继", "常驻：读 tracker 上的新事件，排队叫醒等它的会话；不做判断，不写 GitHub。", "调度", "mmw-v3/skills/dispatch/scripts/relay.py"),
    "sc:watchdog": ("machine", "process", "watchdog.py", "看门狗", "查 relay 是否在跑、在读；问沉默的票的会话还在不在，不在就记 worker.lost 或 reviewer.lost。", "调度", "mmw-v3/skills/dispatch/scripts/watchdog.py"),
    "sc:turn-guard": ("machine", "hook", "turn-guard.py", "回合守卫", "orchestrator 每次要结束回合时运行：看门狗不健康就先重启它，持着票时不让回合在没人看守时结束。", "调度", "mmw-v3/skills/dispatch/scripts/turn-guard.py"),
    "sc:tool-guard": ("machine", "hook", "tool-guard.py", "工具守卫", "在票的工作树里拦下手动关票、结束进程和向屏幕提问。", "调度", "mmw-v3/skills/dispatch/scripts/tool-guard.py"),
    "sc:status": ("machine", "command", "status.py", "批次状态", "从票上的事件算出一批票各在哪一步、下一步推进谁、能不能关夜。", "调度", "mmw-v3/skills/dispatch/scripts/status.py"),
    "sc:models": ("machine", "command", "models.py", "模型与 runner", "读写 models.json：每个角色跑在哪个宿主、模型、effort，选哪个 runner。", "调度", "mmw-v3/skills/dispatch/scripts/models.py"),
    "sc:runners": ("machine", "command", "runner 适配器", "Orca、Herdr、Paseo", "dispatch.sh 通过它在选定的 runner 里开会话、发消息、问会话还在不在。", "调度", "mmw-v3/skills/dispatch/scripts/runners/"),
    "sc:verify": ("machine", "command", "verify-ticket.py", "验票脚本", "认领、跑验收标准、贴决定和评审、切子问题、收尾关票、lint 和发布一批票。", "验票", "mmw-v3/skills/verify-ticket/scripts/verify-ticket.py"),
    "sc:events": ("machine", "command", "events.py", "事件表", "流水线所有事件的词表；写时按表校验，读时把票的评论按顺序折叠成票的状态。", "验票", "mmw-v3/skills/verify-ticket/scripts/events.py"),
    "sc:gate-check": ("machine", "command", "gate-check", "执行验收标准", "逐条执行票上的 CHECK 命令，比对 EXPECT，写回证据。", "验票", "mmw-v3/skills/verify-ticket/scripts/gate-check/gate-check.mjs"),
    "sc:lease": ("machine", "command", "lease.py", "端口租约", "给每个票的工作树一块独占的端口和数据目录；全被占时这次运行报受阻。", "产品验收", "mmw-v3/skills/ui-acceptance/scripts/lease.py"),
    "sc:oracles": ("machine", "command", "四个判官", "story-parity、boundary-check、journey、harness-guard", "对照设计页逐元素比对、跑屏幕契约一行的边界测试、端到端走真实产品、检查验收用的名字没散进产品。", "产品验收", "mmw-v3/skills/ui-acceptance/scripts/"),
    "sc:pull": ("machine", "command", "pull_design.py", "拉设计", "把 Claude Design 页面复制成设计包，写 pull-report.md。", "设计", "mmw-v3/skills/design-pages/scripts/pull_design.py"),
    "sc:contract": ("machine", "command", "extract_skeleton.py 等", "屏幕契约脚本", "从设计包渲染出控件骨架，导出 openapi，lint 屏幕契约到零错误。", "设计", "mmw-v3/skills/write-screen-contract/scripts/"),
    "sc:release": ("machine", "command", "release-flow.sh", "发布引擎", "管每个产品的发布循环：下一阶段、诊断、修复计数、是否成功。", "其他", "mmw-v3/skills/exe-release/scripts/release-flow.sh"),
    "sc:retro": ("machine", "command", "retro.py", "复盘脚本", "收集一夜的证据清单、找前例、写 Retro Memory。", "其他", "mmw-v3/skills/retro/scripts/retro.py"),
    "sc:setup": ("machine", "command", "setup-mmw 的脚本", "check.py、labels.py、space.py", "检查接入状态，建缺的标签，建仓库的 Memory Space。", "其他", "mmw-v3/skills/setup-mmw/scripts/"),
    "sc:agents-check": ("machine", "command", "check.sh", "AGENTS.md 检查", "检查行数、CLAUDE.md 配对、路径引用、子目录那一句。", "其他", "mmw-v3/skills/manage-agents-md/scripts/check.sh"),
    "sc:install": ("machine", "command", "install.sh", "安装入口", "把技能、钩子、用户级提示词、看板、Paseo/Orca/Nowledge 配置装到本机，记下装的是哪一份。", "工具箱", "mmw-v3/install.sh"),
    "sc:checks": ("machine", "command", "check_imports.py 等", "技能集的检查", "check_imports.py 核对拷来的文件都有来源记录；check_wiring.py 核对路由、原则索引和每处点名都存在。", "工具箱", "mmw-v3/check_imports.py, mmw-v3/tests/lib/check_wiring.py"),
    "sc:board": ("machine", "process", "任务看板", "board/", "每个仓库一个本机网页：从 GitHub 读这一批票的状态，改 models.json。", "工具箱", "mmw-v3/board/"),
    # records
    "r:map": ("record", "tracker", "地图与决策票", "GitHub issue", "一个 issue 做索引，子 issue 是一张张决策票。", "GitHub", "mmw-v3/skills/wayfinder/SKILL.md"),
    "r:spec": ("record", "tracker", "spec", "GitHub issue", "一批票的容器：问题、方案、实现决定、测试决定、范围外。", "GitHub", "mmw-v3/skills/mmw-mode/playbooks/write-a-spec.md"),
    "r:ticket": ("record", "tracker", "票", "GitHub sub-issue", "一个工作单元：要做什么、先读什么、能写哪些文件、验收标准。", "GitHub", "mmw-v3/skills/verify-ticket/references/ticket-format.md"),
    "r:child": ("record", "tracker", "子问题", "票下的 sub-issue", "worker 从票里切出的问题：finding、contract、deferred、decision、fault，各自叫醒不同的人。", "GitHub", "mmw-v3/skills/verify-ticket/references/sub-issues.md"),
    "r:events": ("record", "tracker", "票上的事件", "评论尾部的事件块", "票的唯一状态：脚本写，events.py 折叠读。进度以它为准。", "GitHub", "mmw-v3/skills/verify-ticket/scripts/events.py"),
    "r:queue": ("record", "tracker", "分诊队列", "needs-triage 标签", "等人判断的 issue，多数由流水线放进来。", "GitHub", "docs/agents/triage-labels.md"),
    "r:worktree": ("record", "file", "票的工作树和分支", "issue-<n>", "每张票一个工作树和分支，worker 和 reviewer 共用。", "git", "mmw-v3/skills/dispatch/scripts/dispatch.sh"),
    "r:base": ("record", "file", "base branch 与项目分支", "合并去处", "票一张张合进 base branch，仓库检查在合并结果上跑；finish 把一夜合进项目分支。", "git", "docs/contexts/night/how-it-works.md"),
    "r:design": ("record", "file", "设计包", "prototypes/<effort>/", "签收页面写进仓库后的样子，是外观的基线。", "git", "mmw-v3/skills/design-pages/SKILL.md"),
    "r:contract": ("record", "file", "屏幕契约", "screen-contract.yaml", "每个控件调用什么、显示哪个字段、之后进入什么状态。", "git", "mmw-v3/skills/write-screen-contract/references/screen-contract-format.md"),
    "r:models": ("record", "config", "models.json", "本机模型配置", "每个角色跑在哪个宿主、模型、effort，以及选定的 runner。", "本机", "mmw-v3/skills/dispatch/references/editing-models.md"),
    "r:roles": ("record", "config", "roles.json", "角色表", "MMW 开的每种会话和子代理：做什么、交回什么、由谁开。", "本机", "mmw-v3/skills/dispatch/roles.json"),
    "r:target": ("record", "config", ".mmw/target.json", "被测仓库的回答", "产品怎么起停、在哪响应、story 和 journey 在哪、合并时跑哪些检查。", "本机", "mmw-v3/skills/ui-acceptance/references/product-answers.md"),
    "r:state": ("record", "config", "状态目录", "~/.mmw/state/", "relay 的监视、叫醒队列、brief 结果、心跳。", "本机", "mmw-v3/skills/dispatch/scripts/statedir.py"),
    "r:mem": ("record", "external", "Nowledge Mem", "共享记忆", "worker 留给后来者的经验、每夜的 Retro Memory；关夜时逐条决定去留。", "外部", "mmw-v3/skills/mmw-mode/references/memory.md"),
    "r:claude-design": ("record", "external", "Claude Design", "画页面的地方", "你和里面的 agent 画页面；这边经它的工具读写项目。", "外部", "mmw-v3/skills/design-pages/SKILL.md"),
    "r:runner": ("record", "external", "runner 与宿主", "Orca、Herdr、Paseo；Claude Code、Codex、Grok、Cursor", "runner 开出并托管会话，宿主是真正跑模型的命令行程序。", "外部", "mmw-v3/skills/dispatch/hosts.json"),
    "r:decisions": ("record", "tracker", "DECISIONS 评论", "worker 自己定的事", "worker 在开 reviewer 之前贴一次：票和 spec 都没定、它自己定的每件事，以及它改了 Owns 以外哪些文件、为什么。Spec 轴逐条判 reasonable 或 should not。", "GitHub", "mmw-v3/skills/mmw-mode/playbooks/work-a-ticket.md"),
    "r:review": ("record", "tracker", "评审报告", "REVIEW 开头的评论", "reviewer 把四个轴的报告、撤回的发现、票内与票外两张清单贴在票上；它叫醒 worker。", "GitHub", "mmw-v3/skills/mmw-mode/playbooks/review-a-ticket.md"),
    "r:closing": ("record", "tracker", "收尾评论", "--closeout 贴出", "每条标准的结果、每条评审发现怎样处理、worker 自己定的事。后面的 worker 合并冲突时、Spec 轴读已合入的票时都读它；它叫醒 orchestrator。", "GitHub", "mmw-v3/skills/mmw-mode/playbooks/work-a-ticket.md"),
    "r:glossary": ("record", "file", "CONTEXT.md 与 ADR", "领域词汇与架构决定", "仓库里的领域词汇表和架构决定记录。白天写 spec、拆票时用它的词，worker 第 2 步读，Standards 轴拿它判命名；ADR 列进票的 Read first 时就是基线。", "git", "mmw-v3/skills/mmw-mode/playbooks/write-a-spec.md"),
    "r:sources": ("record", "file", "研究与原型", "docs/research、原型目录", "白天调研和原型的结论。写 spec 时全读；被票的 Read first 列出的那几份，worker 读到结论，Spec 轴把记了结论的当基线。", "git", "mmw-v3/skills/verify-ticket/references/ticket-format.md"),
    "r:testing": ("record", "file", "TESTING.md", "仓库的测试事实", "测试放在哪、怎么跑、有哪些层、哪些外部边界替换成假的、测试怎样把系统放进一个状态。写 spec 的会话全读，把用得上的行抄进 spec；票的 Read first 指到其中几行，worker 打开原文读那几行；Tests 轴读全文。", "git", "mmw-v3/skills/setup-mmw/SKILL.md"),
    "r:coding-repo": ("record", "file", "仓库的 CODING_STANDARDS.md", "只在这个仓库成立的规则", "可选，在仓库根目录，和通用那份同样的表格。只有评审读：Standards 轴用 ## Code，Tests 轴用 ## Tests；和通用那份冲突时它赢。", "git", "mmw-v3/skills/manage-agents-md/SKILL.md"),
    "ref:coding-standards": ("skill", "reference", "CODING_STANDARDS.md", "通用的代码与测试规则", "code-review 技能里的规则表。原文写明「The author of a change does not read this file」：写代码的不读，规则在评审时对着 diff 用。它随轴文件写进 Standards 和 Tests 两个轴的 prompt。", "评审独有", "mmw-v3/skills/code-review/CODING_STANDARDS.md"),
    "ref:axis-files": ("skill", "reference", "四份轴文件", "standards / spec / tests / ui-reviewer.md", "每个审查轴的全部指引。reviewer 把它原样写进子代理的 prompt，轴看不到 reviewer 会话里别的东西。", "评审独有", "mmw-v3/skills/code-review/references/"),
    "ref:memory-md": ("skill", "reference", "memory.md", "worker 怎样读写 Memory", "worker 第 2 步打开：怎样读 start prompt 里的两份 Memory 索引，什么时候存一条经验、怎样存。", "worker 独有", "mmw-v3/skills/mmw-mode/references/memory.md"),
    "ref:interface-code": ("skill", "reference", "writing-interface-code.md", "写页面票的规则", "票的 Read first 列了屏幕契约时，worker 第 2 步读。", "worker 独有", "mmw-v3/skills/ui-acceptance/references/writing-interface-code.md"),
    "ref:ticket-format": ("skill", "reference", "ticket-format.md", "票的格式", "一张票每节写什么、每条验收标准怎么写。拆票的白天会话照它写，worker 和 reviewer 读的是照它写出的票。", "白天独有", "mmw-v3/skills/verify-ticket/references/ticket-format.md"),
    "ref:ambiguity-scan": ("skill", "reference", "ambiguity-scan.md", "歧义扫描的指引", "拆票第 6 步派出的歧义扫描子代理读它，扫 spec 和草稿票里没定或含糊的决定。", "白天独有", "mmw-v3/skills/mmw-mode/references/ambiguity-scan.md"),
    "ro:day": ("role", "session", "白天会话", "你开的会话跑白天的 playbook", "和你讨论，把来源读到结论，把定下的东西写成地图、spec 和票。夜里的会话看不到这场对话，只读这些记录。", "会话", "mmw-v3/skills/mmw-mode/SKILL.md (## Playbooks)"),
    "r:build": ("record", "external", "Windows 构建机", "打包的机器", "接收 git archive HEAD，编译并打安装包。", "外部", "mmw-v3/skills/exe-release/references/new-product.md"),
}

MACHINE_GROUPS = ["调度", "验票", "产品验收", "设计", "其他", "工具箱"]
RECORD_GROUPS = ["GitHub", "git", "本机", "外部"]
REF_GROUPS = ["白天独有", "worker 独有", "评审独有"]

# Which scripts a step's text names, by the file name an agent types.
SCRIPT_NAMES = [
    (r"dispatch\.sh", "sc:dispatch"), (r"verify-ticket\.py", "sc:verify"), (r"lease\.py", "sc:lease"),
    (r"status\.py", "sc:status"), (r"pull_design\.py", "sc:pull"),
    (r"extract_skeleton\.py|lint_screen_contract\.py|dump_openapi\.py", "sc:contract"),
    (r"release-flow\.sh", "sc:release"), (r"retro\.py", "sc:retro"), (r"check\.sh", "sc:agents-check"),
    (r"check_imports\.py|check_wiring\.py", "sc:checks"), (r"install\.sh", "sc:install"),
    (r"story-parity\.py|boundary-check\.py|journey\.py|harness-guard\.py", "sc:oracles"),
    (r"models\.py", "sc:models"), (r"watchdog\.py", "sc:watchdog"),
]

# ---------------------------------------------------------------- links no step names
# (from, to, type, Chinese label)
LINKS = [
    # how sessions start and get the mode
    ("en:you", "en:userprompt", "reads", "每个会话"), ("sc:install", "en:userprompt", "writes", "软链、生成"),
    ("en:you", "en:hook", "starts", "Claude Code、Codex"), ("en:you", "en:slash", "starts", "其他宿主"),
    ("en:hook", "mode", "reads", "先读 mode"), ("en:slash", "mode", "reads", "载入 mode"),
    ("en:prompt", "mode", "reads", "先读 mode"),
    ("en:prompt", "pb:work-a-ticket", "route", "点名 playbook"), ("en:prompt", "pb:review-a-ticket", "route", "点名 playbook"),
    ("sc:dispatch", "en:prompt", "writes", "start 写出"),
    # who runs which playbook
    ("ro:orchestrator", "pb:run-a-night", "runs", "照着做"), ("ro:orchestrator", "pb:run-one-ticket", "runs", "照着做"),
    ("ro:worker", "pb:work-a-ticket", "runs", "照着做"), ("ro:reviewer", "pb:review-a-ticket", "runs", "照着做"),
    ("en:you", "ro:orchestrator", "starts", "你开的会话"),
    # who starts which session
    ("pb:run-a-night", "ro:worker", "starts", "advance 开出"), ("pb:run-one-ticket", "ro:worker", "starts", "start 开出"),
    ("pb:work-a-ticket", "ro:reviewer", "starts", "第 5 步 start reviewer"),
    ("sc:dispatch", "sc:runners", "calls", "开会话"), ("sc:runners", "r:runner", "calls", "在 runner 里开"),
    # the night machine
    ("sc:dispatch", "sc:relay", "starts", "open 时开监视"), ("sc:relay", "r:events", "reads", "读新事件"),
    ("sc:relay", "r:state", "writes", "叫醒队列"),
    ("sc:relay", "ro:orchestrator", "wakes", "ticket.passed 等"), ("sc:relay", "ro:worker", "wakes", "reviewer.reported"),
    ("sc:turn-guard", "sc:watchdog", "starts", "不健康就重启"), ("sc:watchdog", "sc:relay", "reads", "在跑在读吗"),
    ("sc:watchdog", "sc:runners", "calls", "会话还在吗"), ("ro:orchestrator", "sc:turn-guard", "runs", "每次回合结束"),
    ("ro:worker", "sc:tool-guard", "runs", "每条命令前"),
    ("sc:dispatch", "r:events", "writes", "worker.started 等"), ("sc:dispatch", "r:worktree", "writes", "开工作树"),
    ("sc:dispatch", "r:base", "writes", "合并、推送"), ("sc:dispatch", "sc:status", "calls", "算下一步"),
    ("sc:status", "r:events", "reads", "折叠事件"), ("sc:dispatch", "sc:models", "calls", "取模型"),
    ("sc:models", "r:models", "reads", ""), ("sc:dispatch", "r:roles", "reads", ""), ("sc:dispatch", "r:target", "reads", "合并时的检查"),
    ("sc:dispatch", "r:mem", "calls", "Memory 收尾"),
    ("sc:verify", "sc:gate-check", "calls", "跑验收标准"), ("sc:verify", "sc:events", "calls", ""),
    ("sc:events", "r:events", "writes", "事件块"), ("sc:verify", "r:ticket", "reads", "验收标准"),
    ("sc:verify", "r:child", "writes", "--sub-issue"), ("sc:verify", "r:spec", "writes", "--publish"),
    ("sc:verify", "r:ticket", "writes", "--publish、--closeout"), ("sc:gate-check", "sc:oracles", "calls", "CHECK 里的判官"),
    ("sc:gate-check", "sc:lease", "calls", "要起产品时"), ("sc:lease", "r:target", "reads", ""),
    ("sc:oracles", "r:design", "reads", ""), ("sc:oracles", "r:contract", "reads", ""),
    ("sc:retro", "r:mem", "writes", "Retro Memory"), ("sc:retro", "r:events", "reads", "证据"),
    ("sc:pull", "r:claude-design", "reads", ""), ("sc:pull", "r:design", "writes", ""),
    ("sc:contract", "r:design", "reads", ""), ("sc:contract", "r:contract", "writes", ""),
    ("sc:release", "r:build", "calls", "远程构建"),
    ("sc:board", "r:events", "reads", ""), ("sc:board", "r:models", "writes", "设置页"),
    ("sc:install", "r:runner", "writes", "装进各宿主"), ("sc:install", "r:models", "writes", "缺时写默认"),
    ("g:install", "sc:install", "human", "只由你授权"),
    # what playbooks leave behind
    ("pb:chart-a-map", "r:map", "writes", ""), ("pb:resolve-a-map-ticket", "r:map", "writes", "记下结论"),
    ("pb:write-a-spec", "r:spec", "writes", ""), ("pb:revise-a-spec", "r:spec", "writes", "原地改"),
    ("pb:cut-tickets", "r:ticket", "writes", "发布一批"), ("pb:triage", "r:queue", "reads", ""),
    ("pb:work-a-ticket", "r:worktree", "writes", "提交"), ("pb:work-a-ticket", "r:child", "writes", "切出子问题"),
    ("pb:design-in-claude-design", "r:claude-design", "writes", ""), ("pb:build-a-design-system", "r:claude-design", "writes", ""),
    ("pb:pull-a-design", "r:design", "writes", ""), ("pb:write-the-screen-contract", "r:contract", "writes", ""),
    ("pb:run-a-night", "r:spec", "reads", "一批票"),
    # sessions a skill or playbook starts
    ("sk:code-review", "ro:code-review axis", "starts", "四个轴"),
    # the day session
    ("en:you", "ro:day", "starts", "你开的会话"),
    *[("ro:day", f"pb:{p}", "runs", "照着做") for p in ("chart-a-map", "resolve-a-map-ticket", "write-a-spec", "revise-a-spec", "cut-tickets", "triage")],
    # each file a skill hands to one role
    ("sk:code-review", "ref:coding-standards", "calls", "它的文件"), ("sk:code-review", "ref:axis-files", "calls", "它的文件"),
    ("mode", "ref:memory-md", "calls", "它的文件"), ("mode", "ref:ambiguity-scan", "calls", "它的文件"),
    ("sk:ui-acceptance", "ref:interface-code", "calls", "它的文件"), ("sk:verify-ticket", "ref:ticket-format", "calls", "它的文件"),
    ("sk:setup-mmw", "r:testing", "writes", "缺时写"), ("pb:write-agents-md", "r:testing", "writes", "移入测试规则"),
    ("pb:write-agents-md", "r:coding-repo", "writes", "移入代码规则"),
    # handoff records
    ("pb:work-a-ticket", "r:decisions", "writes", "第 4 步"), ("pb:work-a-ticket", "r:closing", "writes", "第 11 步"),
    ("pb:review-a-ticket", "r:review", "writes", "第 5 步"), ("r:review", "ro:worker", "wakes", "reviewer.reported"),
    ("r:closing", "ro:orchestrator", "wakes", "ticket.passed"),
    # context: what each session or subagent is given, and at which step
    ("ro:day", "r:map", "gets", "写 spec 第 1 步"), ("ro:day", "r:sources", "gets", "写 spec 第 1 步，全读"),
    ("ro:day", "r:glossary", "gets", "写 spec 第 2 步"), ("ro:day", "r:contract", "gets", "写 spec 第 2 步，全读"),
    ("ro:day", "r:testing", "gets", "写 spec 第 3 步，全读"), ("ro:day", "ref:ticket-format", "gets", "拆票全程"),
    ("ro:day", "r:spec", "writes", "写 spec 第 4 步"), ("ro:day", "r:ticket", "writes", "拆票第 7 步"),
    ("ro:worker", "en:prompt", "gets", "开会话时"), ("ro:worker", "r:ticket", "gets", "第 2 步，全文和评论"),
    ("ro:worker", "r:spec", "gets", "第 2 步，票点名的节"), ("ro:worker", "r:sources", "gets", "第 2 步，Read first"),
    ("ro:worker", "r:glossary", "gets", "第 2 步"), ("ro:worker", "r:design", "gets", "第 2 步，照抄"),
    ("ro:worker", "r:contract", "gets", "第 2 步，拥有的行"), ("ro:worker", "r:mem", "gets", "索引在 prompt，第 2 步打开"),
    ("ro:worker", "sk:tdd", "gets", "第 2 步"), ("ro:worker", "ref:memory-md", "gets", "第 2 步"),
    ("ro:worker", "ref:interface-code", "gets", "页面票第 2 步"), ("ro:worker", "r:review", "gets", "第 6 步"),
    ("ro:worker", "r:closing", "gets", "第 3 步，冲突时读已合入的"),
    ("ro:reviewer", "en:prompt", "gets", "开会话时"), ("ro:reviewer", "r:ticket", "gets", "第 2 步"),
    ("ro:reviewer", "sk:code-review", "gets", "第 2 步"),
    ("ro:code-review axis", "ref:axis-files", "gets", "prompt 里全文"),
    ("ro:code-review axis", "ref:coding-standards", "gets", "Standards、Tests：prompt 里全文"),
    ("ro:code-review axis", "r:coding-repo", "gets", "Standards、Tests：有就读"),
    ("ro:code-review axis", "r:testing", "gets", "Tests 轴，全文"), ("ro:code-review axis", "r:glossary", "gets", "Standards 轴"),
    ("ro:code-review axis", "r:ticket", "gets", "每个轴，全文和评论"), ("ro:code-review axis", "r:decisions", "gets", "Spec 轴逐条判"),
    ("ro:code-review axis", "r:spec", "gets", "Spec 轴，票点名的节"), ("ro:code-review axis", "r:sources", "gets", "Spec 轴，基线"),
    ("ro:code-review axis", "r:contract", "gets", "Spec、Tests、UI 轴"), ("ro:code-review axis", "r:design", "gets", "UI 轴，截图对比"),
    ("ro:code-review axis", "r:closing", "gets", "Spec 轴，已合入的票"),
]

GATES = {
    "pb:chart-a-map": ["g:map-destination"], "pb:resolve-a-map-ticket": ["g:map-hitl"],
    "pb:write-a-spec": ["g:spec-calls"], "pb:cut-tickets": ["g:breakdown"], "pb:triage": ["g:triage"],
    "pb:run-a-night": ["g:start-night", "g:accept-night"], "pb:design-in-claude-design": ["g:design-signoff"],
    "pb:build-a-design-system": ["g:design-system"], "pb:write-the-screen-contract": ["g:gap-list"],
    "pb:improve-the-architecture": ["g:arch-pick"], "pb:make-a-small-change": ["g:seams"],
    "pb:write-agents-md": ["g:agents-md"], "pb:ship-a-release": ["g:install-test"],
    "mode": ["g:always"],
}

# ---------------------------------------------------------------- typical paths
PRESETS = [
    ("上下文：白天写进 spec 和票的", ["en:you", "ro:day", "pb:write-a-spec", "pb:cut-tickets", "r:map", "r:sources", "r:glossary", "r:contract",
                            "r:design", "r:testing", "ref:ticket-format", "ref:ambiguity-scan", "ro:ambiguity scanner", "r:spec", "r:ticket", "g:spec-calls", "g:breakdown"], [
        "白天你开的会话跑 Write a spec：第 1 步把地图、决策票、研究和原型读到结论，第 2 步读代码、CONTEXT.md、ADR 和屏幕契约，第 3 步读 TESTING.md 定下测试的位置。",
        "读完的东西压成一份 spec：每个决定写明出处；TESTING.md 里用得上的事实抄进 Testing Decisions，因为 worker 读 spec，不读那个文件。",
        "Cut tickets 照 ticket-format.md 把 spec 拆成票：Parent 点名 spec 的哪几节，Read first 只列那几节引用的来源，Seam 写测试放在哪，Owns 写能改哪些文件。歧义扫描子代理找出含糊处，你批准拆法后发布。",
        "夜里的会话看不到这场对话：没写进 spec 和票的，worker 和 reviewer 都拿不到。",
    ]),
    ("上下文：worker 每一步拿到的", ["ro:worker", "en:prompt", "mode", "pb:work-a-ticket", "r:ticket", "r:spec", "r:sources", "r:glossary", "r:design",
                              "r:contract", "r:mem", "sk:tdd", "ref:memory-md", "ref:interface-code", "sc:verify", "r:decisions", "r:review", "r:closing"], [
        "开会话时，start prompt 只给三样：先读 mmw-mode，跑 Work a ticket，以及两份 Memory 索引。规则全在 mode 和 playbook 里。",
        "第 1 步由 verify-ticket.py --preflight 认领，并按票上的事件告诉它从哪一步接着做。",
        "第 2 步一次读入这张票要的全部上下文：票的全文和评论、Read first 列的来源、spec 里票点名的节、CONTEXT.md、和这张票相关的 Memory。写代码的指引也在这一步给：tdd 技能、页面票的 writing-interface-code.md，以及流水线自己的规则（基线、不提问、Owns 的边界、跑哪些测试）和它们点名的五条原则。",
        "worker 不读 CODING_STANDARDS.md，也不读 TESTING.md 全文：前者原文写明作者不读，后者只读票的 Read first 指到的那几行。代码规则只写在 CODING_STANDARDS.md 和它指向的原则里。",
        "第 4 步把自己定的事写成 DECISIONS 评论交给评审；第 6 步读评审报告；第 11 步写收尾评论交给 orchestrator。",
    ]),
    ("上下文：reviewer 与四个轴拿到的", ["ro:reviewer", "en:prompt", "pb:review-a-ticket", "sk:code-review", "ro:code-review axis", "ref:axis-files",
                                "ref:coding-standards", "r:coding-repo", "r:testing", "r:glossary", "r:ticket", "r:decisions", "r:spec", "r:sources",
                                "r:contract", "r:design", "r:closing", "r:review"], [
        "reviewer 的 start prompt 只有路由和 base commit，不给 Memory：Review a ticket 写明 Memory 和 worker 的自我评价都不能作为发现的依据。",
        "第 2 步它跑 code-review，每个轴一个子代理，同时派出、互相看不到。每个轴的 prompt 是它的轴文件全文；Standards 和 Tests 两个轴的 prompt 后面再附通用的 CODING_STANDARDS.md 全文。",
        "各轴自己去读的：Standards 读仓库的 CODING_STANDARDS.md 和 CONTEXT.md；Spec 读 DECISIONS 评论、票点名的 spec 节、基线、屏幕契约的行、已合入的票；Tests 读 TESTING.md 全文和 CHECK 点名的测试；UI 看设计页和产品的截图。",
        "reviewer 第 3 步核实每条发现，第 4 步分成票内和票外，第 5 步贴出评审报告，叫醒 worker。",
    ]),
    ("路由：任务分到哪份 playbook", ["en:you", "en:hook", "en:slash", "mode"] + [f"pb:{p}" for _, ps in PLAYBOOK_GROUPS for p in ps], [
        "你开会话：Claude Code、Codex 在有 .mmw/ 的仓库里由 mode-hook.py 让会话先读 mmw-mode；别的宿主由你输入 /mmw-mode。",
        "mmw-mode 的 ## Playbooks 每份 playbook 一行路由条件。会话按任务挑一行，把那份 playbook 的步骤原样抄进待办清单再动手。",
        "没有一行合适时，说清最接近哪份、哪里不合，再按 mode 的通用规则做；一个会话做不完的想法走 Chart a map。",
        "Work a ticket 和 Review a ticket 不由你的话路由：只有脚本写的 start prompt 会点名它们。点任一 playbook 看它的路由原文和步骤。",
    ]),
    ("一夜：从开夜到验收", ["en:you", "ro:orchestrator", "pb:run-a-night", "g:start-night", "sc:dispatch", "sc:relay", "sc:turn-guard", "sc:watchdog",
                     "en:prompt", "ro:worker", "pb:work-a-ticket", "sc:verify", "sc:gate-check", "ro:reviewer", "pb:review-a-ticket", "sk:code-review",
                     "ro:code-review axis", "r:events", "r:worktree", "r:base", "sk:retro", "g:accept-night"], [
        "你说开夜。你的会话成为 orchestrator，按 Run a night 跑：dispatch.sh check、open 开好监视，relay.py 开始读这一批票的事件。",
        "advance 为每张能开工的票开一个 worker 会话（runner 里），start prompt 让它先读 mode，再跑 Work a ticket。",
        "worker 认领、写代码，用 verify-ticket.py 跑验收标准，再用 dispatch.sh start 开 reviewer；reviewer 跑 Review a ticket，派出 code-review 的四个审查轴，把报告贴在票上。",
        "每一步都写成票上的事件。relay.py 读到 reviewer.reported 叫醒 worker，读到 ticket.passed 叫醒 orchestrator；orchestrator 每次回合结束 turn-guard.py 确认看门狗还健康。",
        "orchestrator 把通过的票合进 base branch（仓库检查在合并结果上跑），处理子问题，所有票走完后 reverify、summary，再跑 retro。",
        "你早上读 NIGHT SUMMARY 和 NIGHT RETRO，接受之后 finish 把这一夜合进项目分支。",
    ]),
    ("修一个 bug", ["en:you", "mode", "pb:bug-fix", "sk:diagnosing-bugs", "sk:how", "sk:why", "r:ticket", "pb:run-one-ticket", "ro:worker", "pb:work-a-ticket", "ro:reviewer"], [
        "你报一个缺陷，mode 路由到 Bug fix。",
        "按 diagnosing-bugs 先建一个能反复复现的回路，在你看到 bug 的地方亲自复现；需要时用 how、why 查清机制和来由。",
        "写一张票，交给 Run one ticket：这个会话当 orchestrator，开一个 worker 按 Work a ticket 做，worker 再开 reviewer。",
        "票关闭后，回到你看到 bug 的地方证明修好了。",
    ]),
    ("从想法到一批票", ["en:you", "pb:chart-a-map", "g:map-destination", "sk:wayfinder", "r:map", "pb:resolve-a-map-ticket", "ro:researcher", "g:map-hitl",
                   "pb:write-a-spec", "g:spec-calls", "r:spec", "pb:cut-tickets", "ro:ambiguity scanner", "g:breakdown", "sc:verify", "r:ticket"], [
        "想法太大时走 Chart a map：你同意终点，地图和决策票写到 GitHub。",
        "Resolve a map ticket 一次解决一张：调研票交 researcher 会话，拷问票要你亲自回答。",
        "决定都有了，Write a spec 写成 spec；没有来源能定的产品决定交你定。",
        "Cut tickets 拆成一批票，歧义扫描子代理找出含糊处，你批准拆法后用 verify-ticket.py 发布。之后就是一夜。",
    ]),
    ("从设计到屏幕契约", ["pb:design-in-claude-design", "r:claude-design", "g:design-signoff", "pb:pull-a-design", "sc:pull", "r:design",
                    "pb:write-the-screen-contract", "sc:contract", "g:gap-list", "r:contract", "pb:write-a-spec"], [
        "Design in Claude Design 建项目、交给里面的 agent，你和它画页面，直到你签收。",
        "Pull a design 用 pull_design.py 把签收页写进仓库成为设计包，读拉取报告。",
        "Write the screen contract 把每个控件绑到后端决定，缺口清单交你逐条定。",
        "屏幕契约和设计包成为 Write a spec 和拆票的基线，夜里的判官按它们验收。",
    ]),
    ("改技能集", ["pb:authoring-or-modifying-a-skill", "sk:writing-for-agents", "sc:checks", "pb:review-the-skill-set"], [
        "Authoring or modifying a skill：先决定这段文字属于哪种组件，再写，用 check_imports.py 和 check_wiring.py 检查，最后在一个真实任务上走一遍。",
        "Review the skill set：按 agent 实际做的任务走查，写评审报告，逐条修。",
    ]),
    ("打安装包", ["pb:ship-a-release", "sk:exe-release", "sc:release", "r:build", "g:install-test"], [
        "Ship a release 先确认工作树干净，再为每个碰到的产品跑一轮 release-flow.sh，在构建机上打包。",
        "核对整组安装包来自同一个提交，交你试装；你装好试过才算交付。",
    ]),
]


# ---------------------------------------------------------------- reading the files
STEP = re.compile(r"^(\d+)\. (?:\*\*(.+?)\*\*|(.+?)(?<=[.:])(?=\s))", re.M)
SKILL_REFS = [
    re.compile(r"the `([a-z0-9-]+)` skill"), re.compile(r"the \*\*([a-z0-9-]+)\*\* skill"),
    re.compile(r"`([a-z0-9-]+)` skill's"), re.compile(r"\bskill `([a-z0-9-]+)`"),
]
PRINCIPLE_REF = re.compile(r"[`*]+principle-([a-z0-9-]+)[`*]")


def clean(text):
    return re.sub(r"\s+", " ", re.sub(r"<!--.*?-->", "", text, flags=re.S)).strip()


def names_in(text, titles, skills):
    """The components a passage names, as node ids, in the order they first appear."""
    found = []
    def add(i):
        if i not in found:
            found.append(i)
    for rx in SKILL_REFS:
        for m in rx.finditer(text):
            if m.group(1) in skills:
                add(f"sk:{m.group(1)}")
    for m in PRINCIPLE_REF.finditer(text):
        add(f"pr:{m.group(1)}")
    for title, pid in titles.items():
        if f"**{title}**" in text:
            add(pid)
    for rx, sid in SCRIPT_NAMES:
        if re.search(rx, text):
            add(sid)
    return found


def frontmatter(text, key):
    m = re.search(rf"^{key}:\s*(.*)$", text, re.M)
    return m.group(1).strip().strip('"') if m else ""


def data():
    mode_text = (MODE / "SKILL.md").read_text()
    skills = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md")
                    if not p.parent.name.startswith("principle-") and p.parent.name != "mmw-mode")
    nodes, edges = {}, []

    def edge(a, b, t, label=""):
        if a != b and not any(e[0] == a and e[1] == b and e[2] == t for e in edges):
            edges.append([a, b, t, label])

    for nid, (col, car, name, zh, purpose, group, source) in HAND.items():
        nodes[nid] = {"col": col, "car": car, "name": name, "zh": zh, "purpose": purpose, "group": group, "source": source}
    nodes["mode"]["sections"] = re.findall(r"^## (.+)$", mode_text, re.M)
    nodes["mode"]["refs"] = sorted(p.name for p in (MODE / "references").glob("*.md") if p.name != "README.md")

    # playbooks: route line, steps, reply
    routes = {}
    body = mode_text.split("## Playbooks", 1)[1]
    for m in re.finditer(r"^- \*\*(.+?)\.\*\* (.*)`playbooks/([a-z0-9-]+)\.md`", body, re.M):
        routes[m.group(3)] = (m.group(1), clean(m.group(2)).rstrip(" .") .removesuffix("Full steps:").strip())
    titles = {routes[s][0]: f"pb:{s}" for s in routes}
    unplaced = set(routes) - {p for _, ps in PLAYBOOK_GROUPS for p in ps}
    if unplaced:
        raise SystemExit(f"playbooks with no group on the panorama: {sorted(unplaced)}")
    for group, stems in PLAYBOOK_GROUPS:
        for stem in stems:
            path = MODE / "playbooks" / f"{stem}.md"
            text = path.read_text()
            title, route = routes[stem]
            zh, purpose = PLAYBOOK_ZH[stem]
            steps, last = [], 0
            matches = list(STEP.finditer(text))
            for i, m in enumerate(matches):
                n = int(m.group(1))
                if n != last + 1:
                    break
                last = n
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                chunk = text[m.end():end].split("**Reply:**")[0]
                done = re.search(r"Done when (.+?)(?:\n|$)", chunk)
                names = [x for x in names_in(chunk, titles, skills) if x != f"pb:{stem}"]
                steps.append({"n": n, "t": clean(m.group(2) or m.group(3)).rstrip(".,:"),
                              "done": clean(done.group(1)) if done else "", "names": names})
            reply = re.search(r"\*\*Reply:\*\*(.+?)(?:\n\n|\Z)", text, re.S)
            own = re.search(r"\*\*You own (.+?)\*\*", text)
            nodes[f"pb:{stem}"] = {"col": "playbook", "car": "playbook", "name": title, "zh": zh, "purpose": purpose,
                                   "group": group, "route": route, "steps": steps,
                                   "own": clean("You own " + own.group(1)) if own else "",
                                   "gates": [int(x) for g in GATES.get(f"pb:{stem}", []) for x in re.findall(r"\d+", HAND[g][3])],
                                   "reply": clean(reply.group(1)) if reply else "",
                                   "source": f"mmw-v3/skills/mmw-mode/playbooks/{stem}.md"}
            edge("mode", f"pb:{stem}", "route", "")
            for s in steps:
                for x in s["names"]:
                    t = {"pb": "handoff", "pr": "applies"}.get(x.split(":")[0], "calls")
                    edge(f"pb:{stem}", x, t, f"第 {s['n']} 步")
            for g in GATES.get(f"pb:{stem}", []):
                edge(f"pb:{stem}", g, "human", re.sub(r"^.*?(第 .+ 步)$", r"\1", nodes[g]["zh"]))
    for g in GATES["mode"]:
        edge("mode", g, "human", "")

    # principles
    pbody = mode_text.split("## Principles", 1)[1].split("## Autonomy", 1)[0]
    group = ""
    for line in pbody.splitlines():
        g = re.match(r"^\*\*(\w+)\*\*$", line)
        if g:
            group = g.group(1)
        m = re.match(r"^- \*\*(.+?)\*\* \(\*\*principle-([a-z0-9-]+)\*\*\)\. (.*)$", line)
        if m:
            nodes[f"pr:{m.group(2)}"] = {"col": "principle", "car": "skill", "name": m.group(1),
                                         "zh": PRINCIPLE_ZH[m.group(2)], "purpose": "", "group": group,
                                         "index": clean(m.group(3)),
                                         "source": f"mmw-v3/skills/principle-{m.group(2)}/SKILL.md"}
            edge("mode", f"pr:{m.group(2)}", "applies", "原则索引")

    # skills
    for group, names in SKILL_GROUPS:
        for name in names:
            path = SKILLS / name / "SKILL.md"
            text = path.read_text()
            zh, purpose = SKILL_ZH[name]
            scripts = sorted(p.name for p in (SKILLS / name / "scripts").glob("*")
                             if p.is_file() and p.suffix in (".py", ".sh", ".mjs")) if (SKILLS / name / "scripts").is_dir() else []
            refs = sorted(p.name for p in (SKILLS / name / "references").glob("*.md")) if (SKILLS / name / "references").is_dir() else []
            nodes[f"sk:{name}"] = {"col": "skill", "car": "skill", "name": name, "zh": zh, "purpose": purpose, "group": group,
                                   "desc": frontmatter(text, "description"), "scripts": scripts, "refs": refs,
                                   "by_name": "disable-model-invocation: true" in text,
                                   "source": f"mmw-v3/skills/{name}/SKILL.md"}
            for x in names_in(text, titles, skills):
                if x != f"sk:{name}":
                    edge(f"sk:{name}", x, {"pb": "handoff", "pr": "applies"}.get(x.split(":")[0], "calls"), "")
    missing = set(skills) - {n for _, ns in SKILL_GROUPS for n in ns}
    if missing:
        raise SystemExit(f"skills with no group on the panorama: {sorted(missing)}")
    for nid in [n for n in nodes if n.startswith("sk:")]:
        for sid, owner in (("sc:dispatch", "dispatch"), ("sc:relay", "dispatch"), ("sc:watchdog", "dispatch"),
                           ("sc:verify", "verify-ticket"), ("sc:lease", "ui-acceptance"), ("sc:oracles", "ui-acceptance"),
                           ("sc:pull", "design-pages"), ("sc:contract", "write-screen-contract"), ("sc:release", "exe-release"),
                           ("sc:retro", "retro"), ("sc:setup", "setup-mmw"), ("sc:agents-check", "manage-agents-md")):
            if nid == f"sk:{owner}":
                edge(nid, sid, "calls", "它的脚本")

    # roles
    roles = json.loads((SKILLS / "dispatch" / "roles.json").read_text())["roles"]
    nodes["ro:orchestrator"] = {"col": "role", "car": "session", "name": "orchestrator", "zh": ROLE_ZH["orchestrator"][0],
                                "purpose": ROLE_ZH["orchestrator"][1], "group": "会话", "source": "mmw-v3/skills/mmw-mode/playbooks/run-a-night.md"}
    for r in roles:
        rid = "worker" if r["name"].endswith("-worker") else r["name"]
        key = f"ro:{rid}"
        if key in nodes:
            nodes[key]["what"] += f" / {r['name']}: {r['what']}"
            continue
        zh, purpose = ROLE_ZH[rid]
        sub = r["kind"] == "subagent"
        nodes[key] = {"col": "role", "car": "subagent" if sub else "session", "name": rid, "zh": zh, "purpose": purpose,
                      "group": "子代理" if sub else "会话", "what": f"{r['name']}: {r['what']}", "returns": r["returns"],
                      "how": "宿主自带的通用子代理，同一回合里交回" if sub else f"dispatch.sh {r['command']}",
                      "source": "mmw-v3/skills/dispatch/roles.json"}
        for s in r.get("sent_by", []):
            src = f"sk:{s}" if "/" not in s else "pb:" + Path(s).stem
            if src in nodes or src.startswith("pb:"):
                edge(src, key, "starts", "brief" if r.get("command") == "brief" else "")

    for a, b, t, label in LINKS:
        edge(a, b, t, label)
    ids = set(nodes)
    bad = [e for e in edges if e[0] not in ids or e[1] not in ids]
    if bad:
        raise SystemExit(f"links to unknown components: {bad}")

    groups = {}
    for c, _, _ in COLUMNS:
        if c == "playbook":
            groups[c] = [[g, [f"pb:{s}" for s in ss]] for g, ss in PLAYBOOK_GROUPS]
        elif c == "skill":
            groups[c] = [[g, [f"sk:{s}" for s in ss]] for g, ss in SKILL_GROUPS] + \
                [[g, [i for i, n in nodes.items() if n["car"] == "reference" and n["group"] == g]] for g in REF_GROUPS]
        elif c == "principle":
            order = []
            for nid, n in nodes.items():
                if n["col"] == "principle" and n["group"] not in order:
                    order.append(n["group"])
            groups[c] = [[g, [i for i, n in nodes.items() if n["col"] == c and n["group"] == g]] for g in order]
        elif c == "role":
            groups[c] = [[g, [i for i, n in nodes.items() if n["col"] == c and n["group"] == g]] for g in ("会话", "子代理")]
        elif c == "machine":
            groups[c] = [[g, [i for i, n in nodes.items() if n["col"] == c and n["group"] == g]] for g in MACHINE_GROUPS]
        elif c == "record":
            groups[c] = [[g, [i for i, n in nodes.items() if n["col"] == c and n["group"] == g]] for g in RECORD_GROUPS]
        else:
            groups[c] = [["", [i for i, n in nodes.items() if n["col"] == c]]]
    placed = {i for gs in groups.values() for _, ids_ in gs for i in ids_}
    if placed != ids:
        raise SystemExit(f"components with no place: {sorted(ids - placed)}")
    for name, path, steps in PRESETS:
        unknown = [p for p in path if p not in ids]
        if unknown:
            raise SystemExit(f"path {name} names unknown components: {unknown}")
    return {"columns": [{"key": k, "name": n, "sub": s, "groups": groups[k]} for k, n, s in COLUMNS],
            "nodes": nodes, "edges": edges,
            "presets": [{"name": n, "path": p, "steps": s} for n, p, s in PRESETS]}


def panorama_data():
    text = json.dumps(data(), ensure_ascii=False, separators=(",", ":"))
    return '<script id="pano-data" type="application/json">' + text.replace("</", "<\\/") + "</script>"


# ---------------------------------------------------------------- figure: who is given which context, and when
# One row per piece of context, one column per session or subagent in the order they work. A cell names
# the step and how: F reads it whole, P gets a part or a restatement, W writes it, N is told not to read
# it or is not given it, ? not checked. In the last group a cell
# is work a script does for that role.
CTX_COLS = [("白天会话", "你开的"), ("worker", "脚本开的"), ("reviewer", "worker 开的"),
            ("Standards", ""), ("Spec", ""), ("Tests", ""), ("UI", "")]
CTX_ROWS = [
    ("每个会话一开始就有，用到结束", [
        ("用户级提示词 shared.md", "other", ["F:全程", "F:全程", "F:全程", "?:未查证", "?:未查证", "?:未查证", "?:未查证"]),
        ("mmw-mode 的 SKILL.md", "mode", ["F:开头读完", "F:第一句点名", "F:第一句点名", "N:prompt 不含", "N:prompt 不含", "N:prompt 不含", "N:prompt 不含"]),
        ("自己那份 playbook 的步骤", "playbook", ["F:抄进待办", "F:抄进待办", "F:抄进待办", "", "", "", ""]),
    ]),
    ("白天产生、几方共享的记录", [
        ("决策票、研究、原型的结论", "reference", ["F:写 spec 全读", "P:Read first", "P:按票的指针", "", "P:当作基线", "", ""]),
        ("CONTEXT.md 与 ADR", "reference", ["F:第 2 步", "F:第 2 步", "", "F:词汇表", "P:ADR 基线", "", ""]),
        ("spec", "other", ["W:写出 第 4 步", "P:点名的节", "P:按票的指针", "", "P:点名的节", "", ""]),
        ("票：全文和评论", "other", ["W:拆票时写出", "F:第 2 步", "F:第 2 步", "F:全文", "F:全文", "F:全文", "F:全文"]),
        ("设计包", "reference", ["P:列进来源", "F:第 2 步照抄", "", "", "N:明文不看", "", "P:截图对比"]),
        ("屏幕契约 screen-contract.yaml", "reference", ["F:第 2 步全读", "P:拥有的行", "", "", "P:拥有的行", "P:四列断言", "P:页面与场景"]),
        ("TESTING.md", "reference", ["F:第 3 步全读", "P:指到的行", "", "", "", "F:全文", ""]),
        ("Memory 里的共享经验", "other", ["", "F:索引与第 2 步", "N:不作依据", "", "", "", ""]),
        ("已合入的其他票和它们的收尾评论", "other", ["", "P:冲突时读", "", "", "F:逐张读", "", ""]),
    ]),
    ("会话之间交接的记录", [
        ("start prompt", "agent", ["", "F:路由与索引", "F:路由与 base", "", "", "", ""]),
        ("DECISIONS 评论（worker 自己定的事）", "other", ["", "W:写出 第 4 步", "", "P:看理由", "F:逐条判", "", ""]),
        ("轴报告", "agent", ["", "", "F:第 3 步核实", "W:写出", "W:写出", "W:写出", "W:写出"]),
        ("评审报告", "other", ["", "F:第 6 步", "W:写出 第 5 步", "", "", "", ""]),
        ("收尾评论（交给 orchestrator）", "other", ["", "W:写出 第 11 步", "", "", "", "", ""]),
    ]),
    ("只交给一个角色的工作指引", [
        ("tdd，和它的 tests.md、mocking.md", "skill", ["", "F:第 2 步", "", "", "", "P:规则出处", ""]),
        ("Work a ticket 第 2 步点名的五条原则", "principle", ["", "F:第 2 步", "", "", "", "", ""]),
        ("memory.md（怎样读写 Memory）", "reference", ["", "F:第 2 步", "", "", "", "", ""]),
        ("writing-interface-code.md", "reference", ["", "P:页面票才读", "", "", "", "", ""]),
        ("code-review 技能", "skill", ["", "", "F:第 2 步", "", "", "", ""]),
        ("各轴自己的轴文件", "reference", ["", "", "", "F:prompt 全文", "F:prompt 全文", "F:prompt 全文", "F:prompt 全文"]),
        ("CODING_STANDARDS.md（通用）", "reference", ["", "N:明文不读", "", "F:Code 节", "", "F:Tests 节", ""]),
        ("仓库根目录的 CODING_STANDARDS.md", "reference", ["", "N:只给评审", "", "P:有就读", "", "P:有就读", ""]),
        ("spec 模板、ticket-format.md", "reference", ["F:写 spec、拆票", "", "", "", "", "", ""]),
        ("ambiguity-scan.md", "reference", ["P:给子代理", "", "", "", "", "", ""]),
    ]),
    ("交给脚本做，不占 agent 的注意力", [
        ("认领、找续做的位置（--preflight）", "script", ["", "F:第 1 步", "", "", "", "", ""]),
        ("跑验收标准、记证据（verify-ticket.py）", "script", ["", "F:第 3、7 步", "", "", "", "", ""]),
        ("收尾评论草稿（--draft）", "script", ["", "F:第 10 步", "", "", "", "", ""]),
        ("拼 start prompt 和 Memory 索引（dispatch.sh）", "script", ["", "F:开会话时", "F:开会话时", "", "", "", ""]),
        ("列出已合入的票（dispatch.sh integrated）", "script", ["", "", "", "", "F:读票之前", "", ""]),
        ("发布前 lint 一批票（--lint）", "script", ["F:拆票第 7 步", "", "", "", "", "", ""]),
    ]),
]
CTX_LEGEND = [("F", "读入全文"), ("P", "只读一部分，或读别人转述的"), ("W", "写出它"), ("N", "明文不给或不读"),
              ("?", "没查证")]


def _cell(f, mark, kind, x, y, w, text):
    import html as _h
    h = 20
    if mark == "F":
        f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="3"/></g>')
    elif mark == "P":
        f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="3" style="fill:var(--surface);stroke-dasharray:3 2"/></g>')
    elif mark == "W":
        f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="3" style="fill:var(--surface);stroke-width:2.4"/></g>')
    elif mark == "N":
        f.e(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" style="fill:none;stroke:var(--rule2);stroke-dasharray:2 3"/>')
    else:
        f.e(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" style="fill:none;stroke:var(--rule2);stroke-dasharray:1 3"/>')
    colour = {"N": "var(--muted)", "?": "var(--muted)"}.get(mark, "var(--ink)")
    if text:
        fits(text, "s", w - 4)
        f.e(f'<text x="{x + w / 2:.1f}" y="{y + 14}" text-anchor="middle" class="s" style="fill:{colour}">{_h.escape(text)}</text>')


def context_figure():
    from kit import Fig
    f = Fig("m181", 1000)
    X0, CW, LABEL = 330, 95, 316
    cx = [X0 + i * CW for i in range(len(CTX_COLS))]
    # headers: three sessions, then the four axes under one band
    for i, (name, sub) in enumerate(CTX_COLS[:3]):
        f.box("agent", cx[i] + 3, 8, CW - 6, 46, name, [sub] if sub else [], head=True)
    f.e(f'<g class="k-agent"><rect class="box" x="{cx[3] + 3}" y="8" width="{4 * CW - 6}" height="22" rx="4"/></g>', False)
    f.e(f'<text x="{cx[3] + 2 * CW:.1f}" y="23.5" text-anchor="middle" class="h" style="font-size:12.5px">四个审查轴：reviewer 同时派出的子代理</text>')
    for i in range(3, 7):
        f.e(f'<text x="{cx[i] + CW / 2:.1f}" y="48" text-anchor="middle" class="m">{CTX_COLS[i][0]}</text>')
    f.e(f'<text x="10" y="24" class="h">谁在哪一步拿到什么</text>')
    f.e(f'<text x="10" y="44" class="s">从左到右是干活的先后</text>')
    y = 66
    for title, rows in CTX_ROWS:
        f.e(f'<rect x="4" y="{y}" width="992" height="24" rx="3" style="fill:var(--sunk)"/>', False)
        f.e(f'<text x="12" y="{y + 16.5}" class="h" style="font-size:13px">{title}</text>')
        y += 30
        for label, kind, cells in rows:
            f.e(f'<g class="k-{kind}"><rect class="box" x="8" y="{y + 3}" width="5" height="14" rx="1"/></g>')
            fits(label, "s", LABEL - 24)
            f.e(f'<text x="20" y="{y + 14.5}" class="s" style="fill:var(--ink);font-size:12px">{html.escape(label)}</text>')
            for i, c in enumerate(cells):
                if not c:
                    continue
                mark, text = c.split(":", 1)
                _cell(f, mark, kind, cx[i] + 4, y, CW - 8, text)
            f.e(f'<line class="rule" x1="8" y1="{y + 23}" x2="992" y2="{y + 23}"/>', False)
            y += 26
        y += 6
    for x in cx + [X0 + 7 * CW]:
        f.e(f'<line class="rule" x1="{x}" y1="60" x2="{x}" y2="{y - 6}"/>', False)
    f.e(f'<line x1="{cx[3]}" y1="8" x2="{cx[3]}" y2="{y - 6}" style="stroke:var(--rule2);stroke-width:1.5"/>', False)
    # legend
    y += 8
    lx = 10
    for mark, text in CTX_LEGEND:
        _cell(f, mark, "reference", lx, y, 40, "")
        f.e(f'<text x="{lx + 48}" y="{y + 14.5}" class="s" style="fill:var(--ink2)">{text}</text>')
        lx += 48 + tw(text, 11.5) + 22
    y += 30
    f.e(f'<text x="10" y="{y + 4}" class="s">最后一组的实心格，是脚本替这个角色做掉的事。格子的颜色是那一行组件的种类。</text>')
    return f.svg(y + 14, CTX_ARIA)


CTX_ARIA = ("第 18 课图 1，谁在哪一步拿到什么上下文。列从左到右：白天会话、worker、reviewer，以及 reviewer 同时派出的四个审查轴 "
            "Standards、Spec、Tests、UI。worker 第 2 步读票、spec 里票点名的节、Read first 的来源、CONTEXT.md、Memory，并拿到 tdd、五条原则、memory.md；"
            "它明文不读 CODING_STANDARDS.md，TESTING.md 只读票的 Read first 指到的那几行。CODING_STANDARDS.md 写进 Standards 和 Tests 两个轴的 prompt，"
            "仓库自己那份它们有就读；Tests 轴读 TESTING.md 全文。白天会话写 spec 时全读来源、CONTEXT.md、屏幕契约和 TESTING.md，写出 spec 和票。"
            "reviewer 第 4 步按票里指向 spec 节和基线的指针给发现分类。认领、跑验收标准、收尾草稿、拼 start prompt、lint 由脚本做。")


FIGS = {"l18-data": panorama_data, "l18-context": context_figure}
