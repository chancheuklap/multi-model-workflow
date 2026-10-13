# design-pages 技能（v4 重组稿）

来源：mmw-v3/skills/design-pages（SKILL.md、两份模板、pull_design.py、check_editable_selectors.py）和 mmw-v3/skills/mmw-mode/playbooks 的 build-a-design-system、design-in-claude-design、pull-a-design；第 20 页（scratchpad/p42/DESIGN.md、p44/pagetext.txt）定下的删改；第 21 页 FINAL.md 的规矩。

## 这个技能做什么、交回什么

你在 Claude Design 里和那边的 agent 一起画产品的界面。这个技能做三件事：给一个产品建设计规范（design system）；管这个产品的页面 project，直到你定稿；把定稿的页面拉进仓库 `design/<产品>/`，也就是设计包。设计包是标准答案：verify-<产品> 的 `design` 运行对象打开它，白天照它写 e2e test。交回：project 链接、设计包的提交、登记好的决定。

description 逐字用 v4 已有那句：`Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.`

## 三段共用（只写一次）

**谁能做。** 只有带 Claude Design 工具的会话；夜里的 worker 永远不做。没有工具：告诉你要换一个有工具的会话，什么都不写，停。

**怎么和那边的 agent 说话。** 那边的 agent 只看得见自己的 project，每次对话先读 project 根目录的 `CLAUDE.md`。长期规矩写在 `CLAUDE.md`；这次要做的事写成一份任务单：页面 project 里是 `tasks/<n>.md`（n 是叫我的那张票；你直接叫、还没有票时先开一张），设计规范 project 里是 `task.md`（每个产品只建一次规范）。一项一个勾选框，写明要画哪几页、每页哪几种情况、参考什么（仓库路径带分支，分支先推送）、做完是什么样。你只说「开始 <n>」或「继续」，不用自己写指令。你说做完了，读回那份任务单，没勾的项问你。

**示例数据。** 设计里的数据只用来画图，只用测试账号、测试租户那样的数据，不用客户数据。数据格式由数据库和代码定，写在 spec 里：设计画出来的字段要在 spec 里有；显示出来的值之后由 To tickets 第 4 步写进 e2e test 的断言，所以设计页和产品上断言的是同一段文字。

**怎么写进 project。** 先 `finalize_plan` 列出要写的文件（你批准一次），再 `write_files` 带 etag；新文件 `if_match: "0"`。这样你刚在编辑器里改的不会被覆盖。

## 先进哪一段

| 情况 | 进哪段 |
| --- | --- |
| 要画页面，产品还没有设计规范 | A，再 B |
| 要画新页面或改页面（原型选出赢家；Feature 要的页设计包里没有；你直接说要设计） | B |
| 你说定稿了，或在 Claude Design 里改了已定稿的设计 | C |
| 夜里退回白天的 contract 票（测试照的设计错了或没画） | B（问题写进 `tasks/<n>.md`），再 C |

A 完了接 B，B 定稿接 C。只拉不画时直接 C。

## A 建设计规范（每个产品一次）

1. **定从什么建。** 已有产品：从生产代码；新产品有原型：从赢家那版的代码；新产品在 Claude Design 里探索：从你定稿的页面。页面 project 已绑定一份和代码一致的规范：不建，告诉你，结束。每个产品都有自己的一份。
   完成：知道从什么建，或知道这次不建。
2. **拿到 project。** 设计规范只能由你在 Claude Design 里新建，把链接给我；id 是链接里的 UUID。
   完成：手里有 id。
3. **写它的 `CLAUDE.md`。** 模板原样，填三处：产品是什么；源代码在哪（仓库、分支、前端目录，分支已推送）；示例数据从哪来。
   完成：`CLAUDE.md` 写好，三处都填了。
4. **交给那边。** 你在那个 project 说「开始」。那边的 agent 读代码，整理出颜色、字体、零件；代码里不一致的统一成一种，每处一行记进 `readme.md` 末尾的 `Unifications` 表，拿不准的当场问你。
   完成：你说做完了。
5. **检查。** 读 `readme.md`；逐张卡片预览：都能打开、没有报错，没有一张是整块页面区域，`readme.md` 以 `Unifications` 表结尾。不过的写进 `task.md`，一项一个，你说「继续」，再查。
   完成：每张卡片都过。
6. **产品照表改齐。** `Unifications` 里每一行都是产品要跟着改的地方：走 To spec → To tickets → 一夜。
   完成：spec 已开，或表是空的。
7. **规范改了以后。** 已绑定的页面 project 里有一份规范副本 `_ds/<folder>/`，不会自己跟着变：删掉规范里已没有的文件，复制新的过去；然后回 C 重拉。
   完成：每个已绑定的页面 project 的副本和规范一致。

## B 画页面（直到你定稿）

1. **找到或建页面 project。** 一个产品一直用同一个。产品名：仓库里已有 `verify-<x>` 或 `design/<x>/` 就用 x，都没有就和你定。已有：从你给的链接取 id，确认它的 `CLAUDE.md` 是页面模板原样。没有：新建，绑定这个产品的设计规范。
   完成：手里有 id。
2. **写 project 的文件，一次批准。** 先查 `tasks/` 里别的没勾完的任务单有没有列这次要画的页：有就告诉你，等那张票做完（一页同一时间只属于一张票：Claude Design 没有分支，两张票同时改同一页，后保存的覆盖先保存的）。然后写 `CLAUDE.md`（页面模板原样）；规范副本 `_ds/<folder>/`；`tasks/<n>.md`：这次画哪些页、每页哪几种情况（含出错、加载中）、照什么画（原型赢家所在的目录、现有产品的代码路径）、先画一页给你看。已有产品：只画这次要改的页，照现有代码画，不把整个产品重画（已有功能的 e2e test 照代码写，用不到设计包）；产品已有 verify-<产品> 时，要改哪些页照它的 feature map 找：改到的功能和它的路由（How to get to it）写进 `tasks/<n>.md`。contract 票退回时：`task.md` 写明哪一页、错在哪。
   完成：文件都写好，`CLAUDE.md` 和模板一字不差。
3. **交给你。** 给你页面 project 的链接，你在那里说「开始 <n>」。你和那边的 agent 一起画；当场定的事，那边记进 `设计决策记录.md`，每条标「已确认」或「待确认」。
   完成：你拿到链接。
4. **处理发给我的评论**，直到你说画好了。评论是你对页面的要求：照改，改完 ack。别人写的评论（不是你写的）先给你看，你同意再改。你要求时我才自己改页面。
   完成：每条排队的评论都处理并 ack，或已给你看；我改过的页能打开、没有报错。
5. **读回 `tasks/<n>.md`。** 没勾的项问你。
   完成：每项都勾了，或你说了为什么留着。
6. **你说定稿。** 从这一刻起，设计只在 Claude Design 里改，进仓库只靠 C。
   完成：你说了定稿，进 C。

## C 拉进仓库（每次定稿或改了设计）

1. **先看这次要拉的页本地有没有改过。** 对 `tasks/<n>.md` 列的页跑 `git status`：有没提交的改动就告诉你。
   完成：没有本地改动，或你已知道。
2. **拿到页面名和临时地址。** 列出 project 根目录的页面；取预览地址放进环境变量（约一小时有效，不打印、不写文件）。
   完成：手里有页面名，变量已设。
3. **跑 `pull_design.py design/<产品>/ --pages <页面>…`。** 它下载每一页和它用到的文件，外加 `设计决策记录.md` → 去掉网站自己加进去的代码 → 把 React 放到本地 → 只替换列出的页和它们用到的文件，别的页不动（别的任务还没定稿的页不会被带进来；两个任务共用的文件，比如样式，以后拉的为准，它们在 Claude Design 里本来就只有一份）。缺文件、有页面在本机打不开：退出 2，设计包保持原样，照它说的修了再跑。
   完成：退出 0。
4. **看改了哪些页。** `git diff --stat design/<产品>/` 列出来，写进回复。
   完成：知道改了哪些页。
5. **直接提交到项目分支。** 设计包只由这个脚本写，不走 ticket（直接提交的第四个例外）。正在跑的一夜拿不到它：下一夜 `dispatch.sh open` 会把项目分支合进那一夜的分支（能快进就快进，否则合并；有冲突就拒绝开夜）。不冲突靠一条规矩：任何票的 Owns 都不含 `design/`，worker 不碰设计包。从 Feature 的 `fix-<n>` 里叫的：提交后把项目分支合进 `fix-<n>`，第 5 步写的 e2e test 才打得开新设计页。
   完成：一个提交，只含 `design/<产品>/`；从 `fix-<n>` 叫的，`fix-<n>` 已带上它。
6. **登记决定。** `设计决策记录.md` 已随页面拉进 `design/<产品>/`：「已确认」的留在那里，跟设计一起作 baseline；「待确认」的每条开一张 `wayfinder:grilling` 票问你。写 spec、写票的人读到待确认行按未定处理，答案在那张票里。
   完成：每条待确认都有一张票。
7. **交给下一步，看谁叫的我：**
   - map 上的 `wayfinder:prototype` 票：回到 Work through the map 第 4 步，由它发结论、关票、给 map 加指针；结论里写设计包的提交。
   - Feature 第 5 步、To tickets 第 4 步：回到那一步，照设计包写 e2e test。
   - 夜里退回白天的 contract 票：照新设计改 e2e test（和其他票一样，在下一夜 `open` 之前提交到那一夜的分支）；被退回的页面票和同源未开始的票移回 `ready-for-agent`；contract 子票按 verify-ticket 的子票规矩收口。
   - 你直接叫的（只改了设计）：告诉你设计包已更新，e2e test 和 verify-<产品> 这时都不动，它们照的是现在的产品。要产品跟着改，走 Feature（一张票）或 To spec（一批）：写票那一步照新设计写或改 e2e test。
   完成：下一步已开始，或已告诉你没做的部分。

## 文件

- `references/template-design-system-claude-md.md`：v3 原样；示例数据只用测试数据。
- `references/template-page-project-claude-md.md`（原 template-project-claude-md.md，改写）：
  - 留：只加载 project 自己的文件，不加载产品代码；有任务单时你说开始就照做。
  - 改：一种情况画一页，页名带情况（e2e test 的 design 目标靠页名打开那种情况）。删掉 v3 的 `scene` 参数和每种情况一份 `data/`：那是 v2 的约定，正常的 Claude Design 页面没有；设计包也不承担数据格式。
  - 加：语义标记（跳转用 `<a href>`、能折叠写 `aria-expanded`、弹窗菜单写 `role`、图标按钮写 `aria-label`）；页面上的字就是最终的字；当场定的事记进 `设计决策记录.md`，标已确认、待确认。
  - 删：`Component · ` / `App · ` 页名、`$preview`、`data-ui` 与 `ui-ids.md`、`state-list.md`。它们只为旧的逐元素比对服务；e2e 按角色和可见名字找元素。
- 结构：`SKILL.md` 只留「三段共用」和「先进哪一段」；A、B、C 各一份 `references/`（一次运行只走一段，SKILL-SET-RULES：只有一个分支读的一节放进那个分支的参考文件）。
- `scripts/pull_design.py`：只留下载（外加 `设计决策记录.md`）、去掉注入代码、React 放本地、只替换 `--pages` 列出的页和它们用到的文件（现在第 1538-1540 行是整个目录替换，要改）；删掉场景渲染比对、`pull-report.md`、改动分类、`--state-list`、`--contract`。
- 删：`scripts/check_editable_selectors.py`（只为拉取报告服务）。

## 和 v3 比，改了什么、为什么

1. 三个 playbook 并成技能里的三段：它们只有带 Claude Design 工具的会话做得了，共用一套知识；v3 每个 playbook 开头都要先读 design-pages、第 1 步都是同一句查工具。v4 规则：只是把事交给一个技能的，不单独成 playbook。
2. 入口由一张「先进哪一段」表决定，代替 mmw-mode 里三条路由。
3. 页面 project 从「每个 effort 一个」改成「每个产品一个、长期用」；设计包从 `efforts/<effort>/claude-design/` 改到 `design/<产品>/`，跟产品一样久。
4. 拉取报告删掉：改了哪些页由 git 列出；本地改动在拉之前用 `git status` 查。
5. 拉完的下一步：v3 交给 screen contract（已删）；现在按谁叫的分四路。contract 票在白天处理、不在夜里 resume worker，因为规矩 3：夜里对 e2e test 和设计只读，改它们只在白天。v3「worker 跑票时不换设计包」由 C5 代替：设计包只进项目分支，正在跑的一夜拿不到，下一夜 open 时才合进来。
6. 原型脚手架的拆除从 Pull 挪到 prototype 技能 UI.md 第 6 步：赢家交给 Claude Design 画正式页面，不直接写进产品代码。
7. 新增 `设计决策记录.md` 和「登记决定」一步（第 20 页定的）：已确认的随设计包进仓库，待确认的开 grilling 票；v3 写进原型票 leaf README 那一路删掉。
8. 示例数据只用测试账号、测试租户的数据（商业产品，客户数据不进 Claude Design）。
9. 「只改一页可以不建设计规范」删掉：第 20 页已定每个产品各一个。
10. 示例数据不再放在设计这边（v3 的 `efforts/<effort>/example-data/` 删掉）：数据格式归 spec，设计包不承担。

## v4 里点名它的地方（技能之外要改）

- `mmw-mode/references/wayfinder.md` Prototype 类型：界面问题的原型选出赢家后，点名 design-pages 的 B。
- `prototype/UI.md` 第 6 步：赢家交给 design-pages 的 B，不写进产品代码；在这一步拆脚手架。
- Feature 第 5 步、To tickets 第 4 步：设计包里没有要照的页，先点名 design-pages 的 B、C。
- Run a night 第 3 步退回白天的 contract 票：点名 design-pages 的 C。
- owning-a-task.md `## Playbooks` 的直接提交例外：加上 `design/<产品>/`。
- `mmw-mode/references/ticket.md` 票的写法：Owns 不含 `design/`（和不含 verify 目录、e2e test 并列）。
- Work through the map 第 4 步：原型票的结论里写设计包的提交。
- create-verification-skill 的 Name 一行：已有 `design/<x>/` 就用 x。
