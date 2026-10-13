# v4 验证系统：最终方案

我和 advisor 讨论一致后定稿。依据：pstack 的 verify 系统（create-/maintain-verification-skill）、e2e（tester-army/e2e@62d5524）、v4 现有技能和脚本，以及主人定下的规矩。每条脚本事实都对照过原文。

## 规矩（主人定的，方案不越过）

1. v4 是技能集合。需要 verify-<产品> 的步骤，文字里明确写「照这个产品的 verify-<产品>」，不靠 agent 自己触发。这条只写在 mmw-mode `## Non-negotiables` 那一行：「Shipping UI / IDE / CLI → 驱动产品用它的 verify-<产品>，没有的产品用 control-cli / control-ui；抓 profile、heap、CDP trace、截图仍用 control-ui / control-cli」。Perf issue、Runtime forensics 原文写的「via the matching control skill」指的就是这一行，不另加字。
2. e2e test 和仓库其他测试分开。e2e test 是判官，归 verify 系统管，事实写在 verify-<产品> 和 feature map；不进 TESTING.md、scripts/check、spec 的 Testing Decisions、票的 Seam。
3. verify-<产品>（含 feature map）和 e2e test 开夜前生成并提交：现有产品、现有功能照代码写；新项目、新功能照 Claude Design 的设计包写。夜里只读：worker 不写不改，reviewer 不判。这条靠文字和审查守：worker 改了不会被拦住，会在 `Outside Owns:` 里被看见。
4. 不新增 verifier。
5. 维护只在主人要求时；验收 e2e test 只用固定步骤；设计包是界面的标准答案；v4 删掉的不加回来。
6. 新方案落地后，项目仓库里旧流水线留下的东西（`.mmw/` 下的 target.json、harness、journeys、stories，旧的 `design/`、feature 文档等）全部删掉，再照新方案 setup。方案不读、不改、不兼容它们；需要的事实写进本方案和新生成的 verify-<产品>。
7. 产出物按产品分目录，按任务分分支：`.agents/skills/verify-<产品>/`、`design/<产品>/`、`tests/e2e/<产品>/`，同一仓库几个产品共用的辅助脚本放 `tests/e2e/helpers/`；任务靠 v4 已有的分支和检出（`fix-<n>`、`issue-<n>`、这一夜的分支）分开。只有 Claude Design 那边没有分支，用 `tasks/<n>.md`（n 是票号）和「一页同一时间只属于一张票」顶替。
8. 测试资源：测试账号、测试许可证、本地测试服务器和数据库、PC 测试机都是测试用的，哪里需要就在哪里用；调用外部收费 API 也是被测的功能之一，照调。唯一的禁区是生产服务器（ssh 登录读文件也算）和主分支代码。本机的数据库、服务器、应用实例每个任务单独一套，互不干扰，用上限控制并发（见第一节 Isolate、agentflow 前提票，第三节 `max_workers`）。

## 零、设计包怎么来：design-pages 技能（第 21 页第 0 节）

v3 的 design-pages 技能带回 v4，三个设计 playbook（Build a design system、Design in Claude Design、Pull a design）并成它的三段 A、B、C。理由：只有带 Claude Design 工具的会话做得了，共用一套知识，v3 每个 playbook 开头都要先读 design-pages、第 1 步都是同一句查工具；v4 规则「只是把事交给一个技能的，不单独成 playbook」。description 逐字用 v4 已有那句 `Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.`逐步的写法和与 v3 的差别在 `design-pages-draft.md`（同目录）（advisor 审过，九处已改）。

- **三段共用（只写一次）**：只有带 Claude Design 工具的会话做，worker 不做；派活写进 `tasks/<n>.md`（n 是叫 design-pages 的那张票；你直接叫、还没有票时先开一张），你只说「开始 <n>」「继续」；写进 project 先列文件你批准一次，带版本号不覆盖你的修改；设计里的示例数据只用来画图；数据格式由数据库和代码定（spec 写明），设计画出来的字段要在 spec 里有，显示的值之后写进 e2e test 的断言。
- **先进哪一段**（技能开头一张表）：产品还没有设计规范 → A→B→C；要画新页面或改页面 → B→C；你说定稿或改了设计 → C；夜里退回白天的 contract 票 → B（`tasks/<n>.md` 写明错在哪）→C。
- **A 建设计规范**（每个产品一次）：定从什么建（生产代码／原型赢家／定稿页面）→ 你在 Claude Design 新建、给链接 → 写它的 `CLAUDE.md`（模板原样，填产品、源代码、示例数据从哪来）→ 你说「开始」，那边整理并记 `Unifications` → 逐张卡片检查 → 产品照表改齐走 spec → 一夜 → 规范改了刷新页面 project 的 `_ds/` 副本，再进 C。
- **B 画页面**（直到你定稿）：每个产品一个长期页面 project → 先查 `tasks/` 里别的没完成的任务有没有列同一页，有就告诉你、等那张票（一页同一时间只属于一张票：Claude Design 没有分支，两张票同时改同一页，后保存的覆盖先保存的）→ 一次批准写好 `CLAUDE.md`（新页面模板）、`_ds/`、`tasks/<n>.md`（这次画哪些页、每页哪几种情况，含出错、加载中）→ 你说「开始 <n>」一起画，当场定的事记进 `设计决策记录.md`（已确认／待确认）→ 处理你的评论 → 读回 `tasks/<n>.md` → 你说定稿。
- **C 拉进仓库**：登记决定（读 `设计决策记录.md` 这个任务那一段，每条待确认、行尾还没票号的开一张票问主人，票号写回那一行；放在拉取之前，拉回仓库的那份就带着票号，下次拉取不会给同一条再开票）→ `git status` 查这次要拉的页有没有本地改动 → 取页面名和临时地址 → `pull_design.py --pages <这个任务的页>`（只下载、去注入代码、React 放本地；只替换列出的页和它们用到的文件，别的页不动，别的任务没定稿的页不会被带进来。现在的脚本是整个目录替换（`pull_design.py` 第 1538-1540 行），要改）→ `git diff` 看改了哪些页 → 直接提交到项目分支（第四个直接提交例外）；从 Feature 的 `fix-<n>` 叫的，再把项目分支合进 `fix-<n>`。`pull_design.py` 把 `设计决策记录.md` 和页面一起拉进 `design/<产品>/`，已确认的决定留在设计包里，跟设计一起作 baseline。待确认的问主人的票：在 map 下开 `wayfinder:grilling` 子票，没有 map 时开一张 `Playbook: Grill with docs` 票、标 `needs-triage`（`wayfinder:` 标签只在 map 和它的子票上）。写 spec、写票的人读到待确认行按未定处理，答案在行尾那张票里。
- **交给下一步**：原型票 → 回 Work through the map 第 4 步（它关票）；Feature、To tickets → 回去照设计包写 e2e test；contract 票 → 改 e2e test（下一夜 open 前提交到那一夜的分支），被退回的票和同源未开始的票回 `ready-for-agent`；你直接叫的（只改了设计）→ e2e test 和 verify-<产品> 都不动，要产品跟着改再走 Feature 或 To spec，写票时照新设计改 e2e test。设计包更新从不需要重跑 setup-mmw。
- **页面 project 的 CLAUDE.md 模板**：只剩两条要求：用语义标记（跳转用 `<a href>`、能折叠写 `aria-expanded`、弹窗菜单写 `role`、图标按钮写 `aria-label`）；页面上的字就是最终的字。外加：一种情况画一页、页名带情况；当场定的事记进 `设计决策记录.md`。不要求 `scene`、每种情况一份 `data/`（那是 v2 的约定，正常的 Claude Design 页面没有），也删 `Component · `/`App · `、`$preview`、`data-ui`/`ui-ids.md`、`state-list.md`。Claude Design 那边照它自己的写法画。
- **为什么夜里不冲突**：设计包只进项目分支，正在跑的一夜拿不到；下一夜 `dispatch.sh open` 把项目分支合进那一夜的分支（冲突就拒绝开夜）。规矩：任何票的 Owns 都不含 `design/`。
- **技能之外要改**：wayfinder.md Prototype 类型、prototype/UI.md 第 6 步（赢家交给 B，不写进产品代码，在这一步拆脚手架）、Feature 第 5 步与 To tickets 第 4 步（设计包里没有要照的页时先点名 design-pages 技能；不写段名，进哪段由技能开头的表定，还没有设计规范的会先进 A）、ticket.md（Owns 不含 `design/`）、owning-a-task.md 直接提交例外（加 `design/<产品>/`）、Work through the map 第 4 步（结论里写设计包的提交）。

## 一、产品接入：生成 verify-<产品>（白天，主人点名）

- **setup-mmw 第 1 步 check.py 多一行**：对每个 `design/<x>/` 查 `.agents/skills/verify-<x>/SKILL.md`；缺则报 `missing`，写明「由你点名 create-verification-skill 生成」。setup-mmw 的 SKILL.md 那一步加半句：仓库里有界面、却没有 verify-<产品> 的已有产品，也一起报给你（agent 看仓库判断，只在 setup 时由你点名的会话做）。
- **产品名**：先到者定，后到者读。`<x>` 是仓库里已有的 `verify-<x>` 或 `design/<x>/` 的那个名字；两者都没有时，create-verification-skill 按它已有的 Name 一行定（包名或仓库名，小写），design-pages B1 和你定。各加半句：create-verification-skill 的 Name 行「已有 `design/<x>/` 就用 x」；design-pages B1「已有 `verify-<x>` 就用 x」。名字对不上会以「缺 verify-<x>」被上一条查出来。setup-mmw 不碰 scripts/check 和 TESTING.md。
- **create-verification-skill 换成 e2e 版，并改这几处**：
  - 删 Bug bash 一节和 feature 文件的 Charters；删所有模型步骤：Drive 里 `agent.act` 一条、config 的 `agents` 和模型、`--agent`、replay cache 的句子，写明「config 不配模型」（e2e 自己说没有模型的 config 只跑固定步骤）。frontmatter 去掉 `disable-model-invocation: true`（本仓库 `check_skill_frontmatter.py` 只许 `name`、`description`）。提交信息记上游提交号和删了什么。
  - 生成的 SKILL.md 的 description 逐字用 v4 已有那句：`Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.`（design-pages、create-/maintain-verification-skill 同一句）。
  - 生成器自己开头那段「先读 `.agents/skills/e2e/SKILL.md`」（e2e 版 SKILL.md 第 17-22 行）改成 `npx e2e guide <topic>`，生成的 verify-<产品> 的 Read first 同样。
  - 新增 Rules 一节：不连生产服务器（ssh 也算）、不动主分支代码；测试账号、测试许可证、本地服务器和数据库、PC 测试机哪里要就在哪里用；外部收费 API 照调。
  - 从 pstack 新版带三句进来（e2e 版没有）：Launch 从空数据目录起到可用，含迁移；测试缺前提时报失败、原因写进 Gotchas，不削弱测试；在替身上证明的（Mac 开发模式就是），列出替身做了、真环境不会做的步骤，它们算未验证。
  - 一个产品的 e2e 全在 `tests/e2e/<产品>/`：`e2e.config.ts`、`*.e2e.ts`、`*-snapshots/`、`helpers/`；只有一个产品的仓库也这样放。e2e 以配置文件所在目录为项目根（`config/load.ts` 第 42、55 行），测试路径、`.e2e/` 都落在这个目录下，按产品分开；所以每条命令都带 `--config tests/e2e/<产品>/e2e.config.ts`，不带就是「找不到 config」，不会跑错产品。启动命令的工作目录也默认是这个目录（`run/managed-process.ts` 第 206 行），config 里两个目标都写 `command.cwd` 回到产品根，样例里带上。
  - `e2e.config.ts` 两个运行对象：`product`（真产品）和 `design`（用本机静态服务打开 `design/<产品>/`，端口 0；e2e 不许打开本地文件）。
  - Isolate 分两层写，都是硬要求：被测产品每次运行一套（端口 0、这次运行自己的数据目录；夜里同时跑的是两张票各自的运行，`workers` 只管一次运行里的测试，错不开它们）；产品依赖的后台栈（比如 agentflow 的 Gateway）每个检出一套：Launch 的启动命令先跑一个 ensure 脚本，它先清掉检出已不在的栈，再看本检出的栈通不通，通了直接用，不通才起；同一检出里的多次运行共用它，检出删掉后由下一次任何人的 ensure 收走。产品做不到（端口、数据目录写死，或起栈不能按检出分开），先开前提票改好，落地前这个产品不开界面票。这不是加回 v4 删掉的产品槽位：没有登记和租约，只有每个检出各起各的。
  - Launch 一节给出票上 CHECK 要照抄的整行：先跑仓库自己的依赖安装，再跑 e2e，例如 `pnpm install --frozen-lockfile --silent && npx e2e run <文件> --config tests/e2e/<产品>/e2e.config.ts --target product --trace on --output .e2e/<测试文件名>`。`--trace on` 让每次运行都留 `trace.md`，审计读它，不另跑；`--output` 让每条验收项各留一份，因为 e2e 每次运行先清空上一次的结果（e2e `reference/cli.mdx` 第 386 行）。原因：worker 认领时，v4 在一个什么都没装的临时目录里先跑一遍验收标准。浏览器在生成时装好（`npx @e2e-dev/web install chromium`，一台机器一次；不装的话第一次运行会自己下载，吃掉检查的时间）。`TIMEOUT:` 按生成时实测的冷启动时间写（preflight 在一个新检出里跑，后台栈总是冷的）。preflight 的检出从系统临时目录挪到主检出的 `.worktrees/baseline-<n>`：本机 Docker（Colima）只挂载主目录，临时目录里的检出起不来后台栈；也合本仓库「流水线建的工作树都在 `.worktrees/` 下」的约定。
  - 加一个分支「设计包里有、产品里还没有的功能」：照设计页写 feature 文件和 e2e test；`--target design` 必须通过，`--target product` 必须失败。新项目没有代码就是这个分支的全部功能，并在这里：唯一多的是 Launch 的启动命令取自 spec 的 Implementation Decisions，对真产品的那一半由第一夜第一张票的 smoke test 证明，在 Hand over 里写明。这和 to-tickets.md 第 64 行「spec 逐字给出的文本，CHECK 也要在那段文本的副本上跑一次、必须通过」是同一条规矩在界面上的样子。
  - 同一个 e2e test 跑两个目标，所以分两段：准备一段按目标分（product 用产品自己的入口建数据，design 打开画那种情况的那一页：一种情况画一页，页名带情况，`tests/e2e/<产品>/helpers/design.ts` 把「路由 + 情况」对到页面文件），断言一段两边共用。这个分支给一个样例和 `helpers/design.ts`，写票的人照着写，不各自发明。
  - Launch 让产品从空的临时数据目录起来（pstack 原文要求 Launch 从空数据目录到可用状态，含迁移），product 目标默认连本机真后台。测试要的数据由测试自己建（见二「测试数据」）。
  - **桌面 Electron（进 v4 的只有这一段，通用）**：e2e 原版这里写「桌面应用没有 e2e 引擎，停下」，v4 版换成：product 目标用 e2e 的 browser provider，`scope: 'attempt'`，每个测试开一份新的 Electron（调试端口 0、临时用户数据目录），测完关掉；后台由 Electron 主进程起的产品，`workers: 1`（只管一次运行里的测试），后台的库放这次运行自己的目录、整次运行共用，跨运行的隔离靠上面那条硬要求；靠 docker compose 起后台栈的产品，Doctor 第一项是 Docker 在跑、后台栈可达。2026-10-13 在替身程序上用 e2e 实测通过，凭证和替身代码在同目录 `evidence/electron-stand-in/`。
  - **agentflow 的事实（不进 v4；写进 agentflow 生成的 verify-parrot、verify-hedgehog 和下面那张票）**：
    - `e2e.config.ts` 的 product 目标用 e2e 的 browser provider，`scope: 'attempt'`：每个测试开一份新的 Electron（`electron out/main/index.js --remote-debugging-port=0 --user-data-dir=<临时目录>`），从该目录的 `DevToolsActivePort` 读调试端口；测试结束关掉。传了调试端口参数，parrot 就不再加它写死的 9226（hedgehog 是 9228）。
    - 为什么每个测试一份：实测 Electron 不能新开浏览器上下文，同一份 Electron 交给第二个测试，e2e 会拒绝。
    - `app.command` 起 electron-vite 的界面开发服务，端口用 e2e 给的 `{port}`（`PARROT_RENDERER_DEV_PORT={port}`）；Electron 启动时 `ELECTRON_RENDERER_URL` 设成同一地址。
    - 每个测试的临时目录由 provider 建，测试从这次租到的那份拿。2026-10-13 实测：e2e 的 provider 在各自的 worker 进程里运行，4 个并行 worker 各拿到自己的目录，互不串。
    - parrot 的 Python 后台由 Electron 主进程起（`desktop-parrot/src/main/python-backend.ts`），所以每个测试一份 Electron 也是一份后台。定法：桌面产品 `workers: 1` 写进 Rules；provider 每次运行建一个数据目录，后台的库和激活状态放在这里，整次运行共用（provider 把 `PARROT_DUBBING_DB_PATH` 设成这个目录里的库文件，后台已经读它：`src/parrot_dubbing/state_paths.py` 第 111 行；hedgehog 是 `HEDGEHOG_DB_PATH`）；每个测试只换窗口自己的目录（`PARROT_DUBBING_ELECTRON_USER_DATA_DIR`，开发模式下 `desktop-parrot/src/main/index.ts` 第 505 行读它）；后台端口每次起 Electron 时重新取。所以激活一次运行只做一次，后面的测试看到已激活就跳过。
    - **本机 Gateway**：用 agentflow 自己日常开发、测试、发布都在用的 `local-prod`（`scripts/dev/macos/local_prod_sim.py`；2026-10-13 在这台 Mac 上已连续运行 26 小时，GlitchTip 一起在跑）。不另写启动脚本，不读旧的 `.mmw/harness/`（规矩 6）。它本来就按检出派生独立的 compose 项目、端口、数据卷（`local_prod_instance.py`），gc 也按检出收（`local_prod_sim.py` 第 671、759 行），正好是每个检出一套。每次新起都是新库，`seed_local_accounts` 会种好老板、员工账号和三个产品的许可证，测试就用它们。要先落一张 local-prod 前提票，见下。parrot 的 `PARROT_GATEWAY_BASE_URL` 指本检出那套的地址（hedgehog 用 `HEDGEHOG_*`）。
    - **激活**：由测试自己走产品的激活流程，写在 `tests/e2e/parrot/helpers/activate.ts`：调本机后台的激活开始接口拿授权地址 → 用本检出那套 Gateway 里种好的测试账号登录 → 点「授权当前电脑」→ Gateway 跳回本机后台的 `/auth/callback`，后台自己完成交换。已激活就跳过。2026-10-13 实测通过：后台用 `PARROT_DUBBING_PORT` 起在随机端口、`PARROT_DUBBING_RUNTIME_ROOT` 指临时目录，`PARROT_DUBBING_REDIRECT_URI` 指同一端口，Gateway 接受任意本机端口的回调（`src/gateway/activation.py` 第 229 行），激活后状态 ready（脚本 `evidence/activation/probe.py`）。不在产品代码里加测试开关（agentflow TESTING.md 第 7 条）。
    - `TIMEOUT:` 按生成时实测的冷启动写：起一套 Gateway、种账号，再起 Electron 和后台。Doctor 第一项查：Docker 在跑、共用的 Gateway 镜像在、正在跑的实例数低于上限、本检出那套 `/health` 通。
    - Launch 给的 CHECK 整行对桌面产品：装依赖（pnpm 和 uv sync 两边）→ `electron-vite build` → `npx e2e run …`。
    - macOS 上 Electron 不能无窗口运行，夜里跑测试时屏幕上会弹出窗口：这是给你的信息，写进生成时 Hand over 的回复，不是 agent 的规矩。
    - 夜里证明的是 Mac 开发模式下两半接上；agentflow 自己规定 Mac 证据不算真机证据，Win-PC 安装版真机验收留在白天，照 agentflow-pc-ops 做，由你点名。PR 的 Verification 写明这一点。
  - **前提：agentflow 先落两张票**（都是 Isolate 那条硬要求的前提票，普通代码票，CHECK 用仓库原有测试，夜里可以做；两张都挡在第一张界面票前面）：
    1. local-prod 改五处（Owns `scripts/dev`、`docker`、`src/shared/ports.py`）：(a) `start_local_prod`（`local_prod_sim.py` 第 1144-1150 行）去掉 `pull_ecs_env` 这一步，它 ssh 到生产服务器；派生检出的栈直接只读地用主检出 `~/agentflow/.env.local-prod/` 里的配置和 `github-app/`，不复制（密钥只留一份）；每套自己生成的端口、口令文件仍在本检出；从生产拉配置单独成一个动作，只有你手动跑。(b) 实例名按检出的完整路径算，不按目录名（`resolve_instance` 第 105 行）：位置不同、目录名相同的两个检出会落到同一个 compose 项目、互相 `down -v`（第 623 行）；gc 第 671 行同步改。(c) 端口改成起栈时向系统要空闲端口、记在这个检出的实例里，不再按名字哈希到固定区间：哈希会撞，而且 GlitchTip 用「Gateway 端口加 10」（第 347 行），会撞到别的实例的 Gateway 端口。要到端口和 compose 真正绑上之间有空档，两套同时起可能要到同一个端口：`start_compose` 本来就有「up 失败重来一次」（第 952-974 行），把重来那一次改成重新要一组端口再 up，不加锁。(d) Gateway 镜像用固定名字、缺了才建、所有实例共用（compose 第 57 行现在没写 image 名，每个项目各建一份约 4.7 GB）；清理和 gc 按名字跳过它。(e) 加一个 ensure 动作：先 gc，再查本检出那套 `/health`，通了直接返回，不通才 start；正在跑的实例数到上限（默认 6，可调）就拒绝并说明原因，不排队，拒绝在夜里走现有的 `fault` 子票。
    2. Electron 后台端口改成从环境变量读（下面这条原有的票）：
       后台端口改成从环境变量读（Python 后台已经读 `PARROT_DUBBING_PORT`，没改的是 Electron 主进程；激活回调地址也跟着从端口来；parrot 7 个文件：主进程 BACKEND_URL、python-backend.ts 的 PYTHON_PORT、界面 5 处 BACKEND_URL，加 electron.vite.config.ts 的 PARROT_RENDERER_DEV_PORT；10 月 8 日的实验分支 `exp/894-parrot-driving` 提交 `4b28b5526` 做过，没合；hedgehog 对应位置写死 8795，一并改）。不改的话：parrot 启动时会探 8796，谁在那里答话就按它报的进程号直接杀掉（python-backend.ts `clearStaleBackend`），两张桌面票并行时后起的会杀掉先起的后台；本机还有 agentflow 旅程测试用的 ssh 隧道把 8796、8795 转到 Win-PC 测试机。
- **e2e 装在哪、装什么**：npm 包（`e2e`、`@e2e-dev/web`）进产品仓库的 devDependencies：测试和 config 都引用它，CHECK 在空检出里先装依赖再跑，版本锁在该仓库的 lockfile，ERP 的合作者不用 MMW 也能跑；包没有安装后自动运行的脚本。不跑 `npx e2e init`：它会把 e2e 技能复制进仓库、写 `.mcp.json`。e2e 技能不进产品仓库、也不复制进 mmw-v4：它的 description 是让模型自己挑的触发词，装进仓库后 worker、reviewer 启动时都会扫到；正文主推 `agent.act`、mcp、bug bash。需要它的内容时，verify-<产品> 点名 `npx e2e guide <topic>`（写测试读 `writing-tests`，跑和读结果读 `running`、`debugging`），打印的是该仓库所装版本的同一段文字。不用 e2e mcp：生成时定位元素跑 smoke test 读 trace 页，白天写测试对 design 目标跑一遍，维护时没测试的功能用 control-ui。create-verification-skill 因此自己写 `tests/e2e/<产品>/e2e.config.ts`、`.gitignore` 的 `.e2e/` 一行（任意深度都管住）、装包、装浏览器。e2e 要求 Node ≥ 24.8 或 22.22.3，Doctor 的 `npx e2e list` 会先报，不另加检查。
- **生成后直接提交并推送，不走 ticket。** 这是 owning-a-task.md `## Playbooks` 里第三个例外，与 release、scripts/check 并列，范围限 `.agents/skills/verify-<产品>/` 和 `tests/e2e/`。截图基线在 `tests/e2e/` 里，Owns 不含它，worker 改了会被看见；白天改了设计后更新基线正要用 `-u`，所以不写「不运行 `-u`」这条禁令。DESIGN-INTENTS 例外表同一提交改。`.e2e/` 不提交，由生成时写进 `.gitignore` 的一行管，不写成规矩。仓库的 `scripts/check` 有一条自检：测试根目录下没进 map 也没列为排除的目录就报错（set-up-code-checkers.md 第 42 行），所以 Set up code checkers 的模板把 `tests/e2e/` 列为排除，这就是「e2e test 不被 scripts/check 跑」的实现；不然第一张界面票落地时 scripts/check 自检先红。

## 二、白天：写票时准备验收测试

- **To spec**：第 2 步 Explore the repo 加半句：有 verify-<产品> 的产品，列出 `features/` 并读每个文件的开头几行（功能名、怎么到达、测试文件），再只读改到的那几个功能的全文，把这个 spec 改到的已有功能按 map 里的名字写进 Implementation Decisions，每个注明行为不变或要变；第 5 步给你画的流程图也用这些功能名。To tickets 第 4 步的 pin 与改写两分照抄这份清单。Testing Decisions 只管仓库原有测试。界面票照哪几页设计，写进对应的 Implementation Decisions 小节，作为票上 baseline 的出处。
- **To tickets 第 4 步**（一夜一批）：
  - 照 verify-<产品>，点名 create-verification-skill 的「设计包里有、产品里还没有」分支，为每张界面票写 e2e test 和 feature 文件。元素只用角色、可见名字、标签找；固定步骤；产品那边连本机真后台，测试的前几步用产品自己的入口把要的数据建出来（见下面「测试数据」）；feature 文件 Proof 的存储一半写成测试里的断言：操作之后刷新页面或重开产品，断言数据还在；全走产品自己的入口，不直接查库。`browser.route` 只截三类请求：外部服务、还没做出来的接口（ERP 前后端是两个仓库，前端先做时截住，回的内容照 spec 的接口约定直接写在测试里；后端那个 spec 的 PR 在 Verification 里写「落地后点名维护 verify-erp-frontend」；那就是 maintain-verification-skill 的一次运行：截取已不需要是 harness gap，改了就是 `changed`，直接提交，没有另一条流程。前端的 product 目标连哪个后端检出、哪个提交，是写 verify-erp-frontend 时要答的事实）、靠操作造不出来的出错和加载中。设计包里的数据只用来画图，测试在 product 目标上一个字节都不读它。
  - 对设计页通过、对现在的产品失败，两行结果写进回复。这就是 v4「CHECK 在 base 上先失败」在界面票上的样子。
  - **测试数据**（不新造机制，也是 e2e 自己的思路：测试通过产品自己的入口把状态造出来）：
    - 数据长什么样归 spec：Implementation Decisions 的接口约定和表结构变更，To spec 照数据库表和代码写。
    - 测试自己建：前几步操作界面，或调页面本来就调的那个接口；要断言的值直接写在测试里，从设计页抄。登录、激活这类每个测试都要的步骤写在 `tests/e2e/<产品>/helpers/`，用 Rules 里的测试账号。每次运行一个新的本地后台，测试不靠预先存在的数据。
    - 先红：测试先走已有的入口，再找新东西，所以在 base 上红在「找不到新元素」这类断言上，红的原因正是这张票要做的东西（to-tickets.md 第 64 行），不是导航超时。新项目整个产品还不存在，第一张票是 smoke 票（Launch 起得来、首页可达），它的验收项里写明这张票在 base 上的红是产品起不来；worker 读的是票，work-a-ticket 第 12 行不改。worker 做出接口变绿，并在 Seam 上按 tdd 写后台测试，断言接口返回的字段照 spec。
  - 被这张票碰到的已有功能，分两种：
    - 行为不变：把 feature map 登记的那份 e2e test 写成 pin（在 base 上本来就通过）。还没有测试的，当场照代码写一份、登记进 feature map，和 Refactoring 第 2 步同一规矩。
    - 行为要变：旧测试照新设计改写成验收测试（在 base 上红），feature 文件里那段「产品能做什么」同时改，一起作 baseline。
  - **提交到这一夜的分支**（`open` 之前；还没有这条分支时从项目分支切出来），不提交到项目分支。
  - feature 文件里「产品能做什么」的句子，在第 7 步和票的草稿一起给主人看。
- **票的写法**：Read first 写设计页和 feature 文件（baseline）；Seam 只写仓库原有测试的位置；Owns 不列 `tests/e2e/`、verify 目录和 `design/`；CHECK 照抄 Launch 给的整行；EXPECT 抄 e2e 通过时的汇总行；EVIDENCE 照 v4 写 `pending`。
- **One ticket 一票**：Feature 没有 spec，所以第 2 步（`how` over the affected subsystem）加同一半句：有 verify-<产品> 的产品，列出 `features/` 并读每个文件的开头几行，再只读碰到的那几个功能的全文，列出碰到的已有功能和行为变不变；第 5 步照这份清单写 pin 或改写，提交在 `fix-<n>`。Bug fix 第 2 步先对一下这个功能 feature 文件的 Gotchas（写的是「看起来坏了其实没坏」），再照 verify-<产品> 复现，把反馈回路写成失败的 e2e test，提交在 `fix-<n>`，作 AC2（问题出在界面时才有；AC1 是 worker 按 tdd 写的回归测试）；这张 e2e test 写进那个功能在 feature map 登记的测试文件，功能还没登记就当场登记，和提交是同一个动作（To tickets 第 4 步「没有测试就当场写、登记」同一规矩）。Refactoring 第 2 步的 pin 先取 feature map 里已有的 e2e test，没有就当场写好提交在 `fix-<n>`；refactoring.md 第 12 行「Write the pin first and run it green」改为「pin 已在 `fix-<n>`，先把它跑绿再动结构」。one-ticket.md 第 5 步「`fix-<n>` holds only this session's records」那句加上「和这张票的 e2e test、feature 文件」：合项目分支时的冲突现在也可能在它们里面。One ticket 的 worker 开了 contract 子票：回到拥有 `fix-<n>` 的那个白天会话，它改设计（design-pages 的 B→C）、改测试，再派 worker。
- **Perf issue 第 2 步、Runtime forensics 第 1 步**：照 verify-<产品> 把产品带到要测的状态，用 control-ui 抓 profile、heap。
- **Visual parity 退役**：截图基线是 `toHaveScreenshot` 测试（e2e 默认就是零像素差异，不用另写）；两个实现的像素对齐走 Refactoring。playbook 移到 `docs/retired-playbooks/`。

## 三、开夜前

不加步骤。`dispatch.sh check` 照旧只跑 scripts/check 默认档。

**同时在跑的票数上限**：`~/.mmw/models.json` 顶层加 `max_workers`（默认 3），经 `models.py config set` 改（`models.py` 第 137 行的校验加三行，`editing-models.md` 加一行）。`status.py --advance-plan`（第 615-678 行）把派出的票截到「上限减这一夜已认领、还没结束的票数」；`dispatch.sh` 一行不改。这是每一夜的上限：v4 没有跨仓库的「谁在跑」登记，整机的保护由产品那一侧的实例上限做（agentflow 是 local-prod 的 ensure）。白天的会话由你自己开，不受它管。

## 四、夜里（对 e2e test 只读）

- **Work a ticket 第 1 步 `--preflight`**：脚本在 base 上跑全部 CHECK；验收测试红，pin 绿。
- **第 2 步不加字**：「先跑它、读它为什么红」和「设计包是 baseline、照抄」原文已有（work-a-ticket.md 第 12、13 行）。
- **第 3 步只加一句**：「e2e test 失败照这个产品的 verify-<产品> 排查；测试或设计包本身错了，开 `contract` 子票，夜里不改它们。」怎么排查由 verify-<产品>（Doctor、Gotchas）说；产品起不来是现有的 `fault` 子票，不另写。
- **contract 子票**（测试或设计错）：run-a-night.md 第 98 行的 authority 段允许 orchestrator 有书面依据时自己改 baseline，设计包也在那张次序里，所以要加一句「e2e test 和 `design/` 夜里不改，这种 contract 走无依据那一支」。那一支（第 100 行）把同源未开始的票移到 needs-triage；正在做的票原文是「stays held」，把这句换掉（两句互斥），换成：orchestrator 用 `resume` 让持票的 worker 以 `stuck` 放弃那条 AC（指向子票）并收口，它才会 `ticket.returned` 进 needs-triage，白天才有东西可改：在 Claude Design 改、重新拉、改测试，再 ready。换的是这一支的末句，所以对每种没有依据的 contract 都生效；主人指南 `07-overnight.md` 第 56 行跟着改。
- **第 2 步 worker 碰到 Owns 之外的文件**：work-a-ticket.md 第 17 行「A file outside Owns」后加一句：`tests/e2e/`、verify 目录、`design/` 除外，改不了就开 contract 子票。这是 worker 那一侧唯一要写的地方（规矩放在动手的 agent 读的那一行）；worker 若还是改了，不会被拦住，它会进 verify-ticket 的 `Outside Owns:`，由审查的 Spec 轴看见，不另写审查规矩，也不加拦截（只为真出过事的地方加防）。
- **第 5、6 步 reviewer**：tests-reviewer.md 加一句：CHECK 点名、但本次 diff 没碰的 e2e test 不在范围内，它在票之前写好、对产品证明过红（Tests 轴按 CHECK 点名的测试文件定范围，`code-review/references/tests-reviewer.md` 第 1 节，不加这句它会去审 e2e test）。
- **第 7 步审计**：读本票每条 CHECK 留下的 `tests/e2e/<产品>/.e2e/<测试文件名>/results/…/trace.md`，不另跑（CHECK 行自带 `--trace on` 和各自的 `--output`）。这半句写在 work-a-ticket 第 7 步。
- **第 11 步 `--closeout`**：脚本把 `EVIDENCE: pending` 换成运行记录、打勾。这就是「去掉 pending」的那一步，测试文件本身没有任何标签。
- **land**：scripts/check 只跑仓库原有测试。
- **夜里只跑 `--target product`**：CHECK 行和 Run a night 第 5 步都是。`design` 目标只在白天写测试时和维护时跑，不然你改了设计没重拉，夜里会红在设计而不是产品。

## 五、收尾与之后

- **Run a night 第 5 步**：`reverify` 重跑每张已落地票的 CHECK（含 pin），之后在这一夜分支的检出上，对这一夜碰到的每个产品各整体跑一遍 `npx e2e run --config tests/e2e/<产品>/e2e.config.ts --target product`；碰到哪些产品，就看这一夜各票 CHECK 行里的 `--config` 路径，不另登记。红的若是开着的票（被退回的、还没做的）自己的测试，是预期，写进 PR 那张票名下：退回票的测试会跟着一夜合进项目分支，项目分支上一个红的界面测试就等于一张开着的票，不另设机制摘掉；其余是回归，按收尾环节现有规矩处理（一个文件自己修，否则开票），修完再跑。汇总行写进 PR。
- **One ticket 第 4 步验证段**（保留，不退役）：界面这一项对这张票碰到的产品整体跑一遍 `npx e2e run --config tests/e2e/<产品>/e2e.config.ts --target product`，和 Run a night 第 5 步同一件事（一张票就是只有一张票的一批）。查数据存进去已在票上的 e2e test 里；Doctor 只在失败排查时跑。任何红：不 land，告诉你；全绿就 land。你亲眼看界面不设成 land 前的关卡：合并本来就等你点头（Opening a PR 第 4 步），PR 的回复里给你起产品的那一行命令（verify-<产品> Launch，在 `fix-<n>` 的检出上），你想看就看，看完说合并。开夜的 PR 也一样，所以单票和开夜没有差别。
- **Opening a PR**：Verification 本来就有 `scripts/check --all` 的汇总行（Run a night 第 6 步），只多一行 product 目标 e2e 的汇总行（已含存储断言）和你自己起产品看的那一行命令；桌面产品注明是 Mac 开发模式，真机验收另做。不录像（你定的）：e2e 的结果和每一步的文字记录 `trace.md` 就是证据。给你看的那一页（The owner's page）：界面上的部分用 feature map 里的功能名；改了界面时要的前后两张截图，由写 PR 的会话照 verify-<产品> 的 Launch 起产品、用 control-ui 拍：改动前在项目分支的检出上，改动后在 `fix-<n>` 或这一夜的分支上。不另跑 e2e（验收测试在改动前是红的，e2e 只在失败那一步截图）。
- **feature map 没有手写总表，也没有「状态」字段**：每个功能一个文件，开头几行写功能名、怎么到达（路由）、覆盖它的测试文件（没有就写「无」）。「有没有测试」看这一行就知道，「还没做出来」只记在票上。两个分支各加一个功能是两个新文件，合并不冲突，也不会出现表和文件对不上。偏离 e2e、pstack 原来的 README 总表格式，提交信息写明。

## 六、维护（主人要求时）

maintain-verification-skill：路径改 `.agents/skills/verify-*/`；Live pass 照 verify-<产品>：有测试的功能，跑测试就是 Live pass；没有测试的功能用 control-ui 走一遍；Triage 三分类：doc drift 改 map 和测试（map 和测试文件对不上，靠这里在白天发现，没有 lint），harness gap 修环境，product gap 开一张只有 `## Problem` 的票、标 needs-triage；结论 `changed` 直接提交推送，不开票。

## 七、技能之外

- DESIGN-INTENTS 同一提交改：第 25 条 Home 改成「`design/<产品>/`，由 design-pages 写」；第 29 条 Home 不改（verify-<产品> 是产品仓库的生成物，模板在 create-verification-skill，已在那一条里）；Departures 表 P21 行只记「直接提交例外加两条」，清单只在 owning-a-task.md 一处（`.agents/skills/verify-<产品>/` 和 `tests/e2e/`、`design/<产品>/`）；加一条新意图「设计包是界面的标准答案；e2e test 白天写、夜里只读」，Home 列 to-tickets 第 4 步、work-a-ticket 第 17 行那句、ticket.md。
- 一份新 ADR：amends 0041、0044，推翻 0042 里否决「每仓库生成验证技能」的一条；feature map 的家改到 `.agents/skills/verify-<产品>/features/`；保持为真的环节是白天写、维护复核，夜里只读；0044 第 2、3、4、6 条由规矩 3 取代（它们假定 worker 拥有功能文件；现在功能文件白天写、夜里只读）；0044 第 1 条（lint 保持 feature map 为真）由维护的 doc drift 接替，接受白天才发现。推翻 0042 那一条要写理由：0042 否决它是因为维护成本；现在 e2e test 本身就是仓库资产，verify-<产品> 只是入口文档，生成后直接提交、维护由你点名，成本只在你要时发生。
- v4 自己对旧 `.mmw/target.json` 的兼容走一张票删掉，共五处：setup-mmw 的 SKILL.md 第 5 步和 `check.py` 报旧 `checks` 键；set-up-code-checkers.md 第 43 行删那个键；`verify-ticket.py` 第 2301-2322 行的提示；`dispatch/scripts/tool-guard.py` 第 233 行的拒绝提示还叫 agent 用 target.json 里的 `stop` 命令停产品，v4 没有这个命令，改成照 verify-<产品> 停。`events.py` 第 96 行的 `repo-checks` 留着：它读的是本仓库 tracker 上 v2 关掉的票的历史，不是项目仓库里的东西。
- 本仓库任务板的旧材料（`docs/features/task-board/`、scripts/check 的 feature-map 一步、`.mmw/task-board/` 的 stories、journeys、harness）走一张票清理，同时处理板测试对 v3 ui-acceptance 两个脚本的依赖，并改本仓库 `AGENTS.md` 第 2 段「root `.mmw/target.json` lists `task-board`」那句。
- `docs/contexts/ui-acceptance/CONTEXT.md` 整篇重写：现在全文是 v3 的词（screen contract、data-ui、lease），没有一段能留。

## 已定的默认（可改）

- 单张票落地前不设「你亲眼看」的关卡：绿就 land，PR 里给你起产品的命令，看完说合并（和开夜一样）。
- 设计页一种情况画一页、页名带情况，不用 v2 的 `scene` 和每种情况一份数据。
- 被退回票的红测试跟着一夜合进项目分支，当成「一张开着的票」，不另设机制摘掉。
- 桌面产品的界面票照常排进夜里，前提是上面两张 agentflow 前提票已经落地。
- 夜里发现测试或设计写错，票退回白天，这一夜少落地几张。

## 八、放到哪里（放置表）

每条新规矩进哪个组件、哪个文件，谁在什么时候读，怎么登记。「登记」写「无」的，没有自动检查，只靠这张表。和 advisor 一起定。

| 组件 | 文件 | 加什么 | 谁、何时读 | 登记 |
| --- | --- | --- | --- | --- |
| mode | `mmw-mode/SKILL.md` `## Non-negotiables` 第 18 行 | 「Shipping UI」改成：驱动产品用它的 verify-<产品>，没有的产品用 control-cli / control-ui；抓 profile、heap、trace、截图仍用 control-* | 任何会话，碰到界面时 | 无 |
| mode | `mmw-mode/references/owning-a-task.md` `## Playbooks` | 直接提交例外加两条：`.agents/skills/verify-<产品>/` 和 `tests/e2e/`、`design/<产品>/`（清单只在这里）；删 Visual parity 路由行 | 拥有任务的会话，开始时 | DESIGN-INTENTS P21 行；check_wiring |
| skill | `design-pages/`：`SKILL.md`（共用四段、入口表），`references/` 里 A、B、C 各一份，两份模板，`pull_design.py` | 三段；页面模板只剩语义标记、最终文字、一种情况一页；pull 带上 `设计决策记录.md`；B1 产品名规则；B2 先查 `tasks/` 一页一票、已有 verify-<产品> 的产品照 feature map 找要改的功能和路由；派活写进 `tasks/<n>.md`；`pull_design.py` 改成只替换 `--pages` 列出的页 | 被点名的白天会话 | 点名处：wayfinder.md Prototype、prototype/UI.md 第 6 步、feature.md 第 5 步、to-tickets.md 第 4 步、run-a-night.md 第 3 步、work-through-the-map.md 第 4 步；DESIGN-INTENTS 第 25 条；提交信息写 v3 来源 |
| skill | `create-verification-skill/` | 换 e2e 版：删 Bug bash、Charters、全部模型步骤，去掉 `disable-model-invocation`；不跑 `npx e2e init`，自己写 config、`.gitignore` 一行、装包、装浏览器；全放 `tests/e2e/<产品>/`，config 写 `command.cwd`，CHECK 带 `--config`、`--output`；Isolate 两件硬要求，做不到先开前提票；Read first 点名 `npx e2e guide <topic>`；Rules；pstack 新版三句；两个目标；设计包分支（含新项目、`helpers/design.ts` 样例）；通用 Electron 段；feature 文件开头写功能名、路由、测试文件，没有手写总表；Name 行「已有 `design/<x>/` 就用 x」 | 你点名的白天会话 | setup-mmw 的 missing 文案点名它；to-tickets 第 4 步点名其分支；提交信息写两个来源：tester-army/e2e 的提交号（底）和 pstack 新版的提交号（三句），以及删了什么 |
| skill | `maintain-verification-skill/` | Live pass：有测试的跑测试，没测试的用 control-ui；Triage 三分类，doc drift 接替 feature map 的 lint；changed 直接提交（ERP 去截取也走这里）；Gateway 这类镜像缺了由它建 | 你点名时 | 无 |
| 产品仓库生成物 | `.agents/skills/verify-<产品>/`、`tests/e2e/<产品>/`、`tests/e2e/helpers/`、devDependencies 里的 e2e 包 | Launch、Doctor、Isolate、Rules、features/；agentflow 的事实全在这里 | 见上面「谁、什么时候、用什么」 | 无（模板在 create-verification-skill）；做不到 Isolate 的产品，它的前提票就是登记 |
| script | `setup-mmw/scripts/check.py` | 每个 `design/<x>/` 查 `verify-<x>`，缺了报 missing | 你跑 setup-mmw 时 | setup-mmw 测试加一例 |
| skill | `setup-mmw/SKILL.md` 那一步 | 半句：有界面却没有 verify-<产品> 的已有产品也报给你 | 你点名的 setup 会话 | 无 |
| playbook | `to-tickets.md` 第 4 步 | 界面票写 e2e test 和 feature 文件；pin 与改写两种；没有这一夜的分支就切出来，提交到它；设计页绿、产品红两行进回复；没有设计页先点名 design-pages 技能 | 写票的白天会话 | 新意图的 Home |
| playbook | `to-spec.md` 第 2 步 | 半句：列出 `features/`、读开头几行，再只读改到的功能，把改到的已有功能和变不变写进 Implementation Decisions；第 5 步的图用功能名 | 写 spec 的白天会话 | 无 |
| playbook | `feature.md` 2、5，`bug-fix.md` 2，`refactoring.md` 2 | Feature 2 读 feature map 列出碰到的功能；Bug fix 2 先对 Gotchas，e2e test 写进登记的测试文件、没登记就登记；各一句「照 verify-<产品>」和测试的去处 `fix-<n>` | 白天会话 | 无 |
| playbook | `refactoring.md` 第 12 行 | 「Write the pin first」改成「pin 已在 `fix-<n>`，先跑绿再动结构」 | worker | 无 |
| playbook | `work-a-ticket.md` 第 3、7 步和第 17 行 | 第 3 步一句（失败照 verify-<产品>，测试或设计错开 contract）；第 7 步半句（读 trace 页）；第 17 行例外句（`tests/e2e/`、verify、`design/`） | worker，夜里 | 新意图的 Home |
| playbook | `run-a-night.md` 第 98-101 行、第 5 步 | authority 段加「e2e test 和 `design/` 夜里不改」；无依据那一支加「resume 让 worker 以 stuck 收口」；第 5 步对碰到的每个产品整体跑 `--target product`（清单就是各票 CHECK 的 `--config`），红的对照开着的票 | orchestrator | 无 |
| playbook | `one-ticket.md` 第 4、5 步 | 第 4 步对碰到的产品整体跑 `--target product`，绿就 land；第 5 步 `fix-<n>` 那句加「和这张票的 e2e test、feature 文件」；contract 子票回拥有 `fix-<n>` 的会话 | 白天会话 | 无 |
| playbook | `opening-a-pr.md` | Verification 多一行 e2e 汇总、一行你自己起产品看的命令；桌面注明 Mac 开发模式；The owner's page 的界面部分用 feature map 的功能名，前后截图照 Launch 起产品、control-ui 拍 | 白天会话、orchestrator | 无 |
| script | `dispatch/scripts/status.py --advance-plan`、`models.py`、`references/editing-models.md` | `max_workers`：派出的票截到上限减已认领未结束的数 | orchestrator 每次 advance | dispatch 测试加一例；ADR 写一句「不是加回槽位」 |
| playbook | `set-up-code-checkers.md` 的 scripts/check 模板 | 把 `tests/e2e/` 列为排除 | Set up code checkers | 无 |
| playbook | `visual-parity.md` | 移到 `docs/retired-playbooks/` | — | 删路由行；check_wiring |
| 脚本 | `verify-ticket/scripts/verify-ticket.py` `run_baseline` | preflight 的检出建在主检出的 `.worktrees/baseline-<n>`，不建在系统临时目录 | Work a ticket 第 1 步的 `--preflight` | 根 `AGENTS.md` 流水线工作树名单加 `baseline-<n>` |
| reference | `mmw-mode/references/ticket.md` | 写 Owns 时不列 `tests/e2e/`、verify 目录、`design/`（写票者的动作；规矩本体在 work-a-ticket 第 17 行）；CHECK 照抄 Launch 整行 | 写票的会话、worker | 新意图的 Home |
| reference | `code-review/references/tests-reviewer.md` | 一句：CHECK 点名、diff 没碰的 e2e test 不在范围 | Tests 轴 reviewer | 无 |
| 文档 | 新 ADR（amends 0041、0044 第 1、2、3、4、6 条，推翻 0042 一条并写理由）；`ui-acceptance/CONTEXT.md` 整篇重写；DESIGN-INTENTS 第 25 条、P21 行、新意图 | 见第七节 | 人读 | ADR 索引 |
| 票 | agentflow 两张前提票（local-prod 每检出一套且不连生产；Electron 端口从环境变量读）；本仓库：任务板清理一张，v4 对旧 target.json 的兼容清理一张 | — | — | — |

`verify-ticket.py --closeout` 换掉 `EVIDENCE: pending` 是 v4 现有行为（`verify-ticket.py` 第 628-671 行），不是改动，不列。
