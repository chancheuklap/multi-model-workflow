# 验证与测试全流程：按设计意图的审查

日期 2026-10-09。范围：MMW v3 中判断一项改动做对了的整条链，白天定证明、夜里执行审查和收尾、在真实产品上证明、白天的改动和修复，以及改技能本身。标准是 `mmw-v3/skills/writing-for-agents/DESIGN-INTENTS.md` 的 41 条设计意图，下文「意图 N」即其编号。

## 怎样查的

这一轮没有按任务逐个走查并统计读入量，而是逐条意图追踪落地：哪个文件承载它、执行者在哪一步读到、靠脚本还是靠文字、交接形状是否一致、各处说法是否一致。四个只读子任务分段查，每条结论按行号对照原文核过；问题「白天驱动过产品后 journey 被拒」在隔离的 MMW_HOME 里亲手复现过。之后 advisor 对照原文审了一遍，再派两个新 agent 只拿触发语按真实任务走查了改后的技能文字，补上其中三条。没有负载表，因为这一轮没有按任务统计读入的文件和词数。

## 问题

### 一、同一个结论验了不止一次

**1. 修 bug 合并后再证一次**

- 违反：意图 30（只判一次）；意图 33（每个事实由改变它的那一步当场写）
- 证据：bug-fix.md 第 5 步在合并后用 verify-this 再证一次，而 worker 已经用票里的 CHECK 验过。land 在票被退回时仍然退出 0，dispatch.sh 的 land 只在 failed 或 relay 残留时返回 1。第 1 步的复现放在 .scratch 下，git 不跟踪它；功能文件也由白天 agent 先写在本地。
- 影响：可能去证明一段没合进去的代码。证不出来时没有下一步。worker 从 origin 切出，看不到白天的复现。
- 修法：写票时把复现写成票里的 CHECK，要求它先在 base 上变红。第 1 步写了功能文件就当场提交并推送（它是文档，不是产品代码），票的 Owns 再列它，worker 从 origin 切出才看得到。删掉第 5 步，改为读 land 的结果，向主人报告合进去没有。

**2. 收尾时有红票就关不了夜**

- 违反：意图 30（只判一次）；意图 37（退回的票早上由主人分诊）
- 证据：status.py 的 reverify_problems（第 865 行）把"已退回 triage"的票也算进必须为绿。run-a-night 第 8 步又写着"退回 triage 是合法结局"。
- 影响：orchestrator 只能自己修、整批重跑 reverify、再试 summary。这一来既绕过了 triage，又把同一批票验了第二遍。
- 修法：改一个条件。已退回 triage 的票不再要求为绿，照常关夜。夜报的 Handed back 一行现在只取 ticket.returned（status.py 第 578 行），收尾 reverify 退回的票不在里面；同一处把这些票也写进去，否则关得了夜，主人却看不到它们。

**3. worker 在同一个提交上把全部标准跑两遍**

- 违反：意图 30（只判一次）
- 证据：work-a-ticket.md 第 6 步修完审查发现后「run Integrate and run every criterion again」，第 7 步紧接着又跑 verify-ticket.py --reverify --actor worker 全部标准，两步之间没有提交。审查没有发现时，第 3 步那次和第 7 步那次也在同一个提交上。
- 影响：每张票多等一整轮标准，最贵的驱动产品的标准也在内。关票评论里的证据取自第 3 步那次（verify-ticket.py 第 1509 行），关票认的却是第 7 步那次（第 910 行），主人读到的不是关票依据的那次。
- 修法：第 6 步的「run Integrate and run every criterion again」只删后半：修完仍跑 dispatch.sh integrate（审查期间 base 可能前进，重合并要在最后一次运行之前），不再跑全部标准，第 7 步就是修复后唯一的一次。审查没有发现、第 3 步之后也没有新提交时，关票接受第 3 步那次。verify-ticket.py 里「关票认哪次」（第 910 行）和「关票评论的证据取哪次」（第 1509 行）用同一个定义：HEAD 上最新的一次 worker 运行，否则主人读到的和关票依据的仍不是同一次。第 7 步补上退出码 2（槽位占满，什么都没跑）的去路，照第 3 步写，免得被读成失败。这一改动改了 ADR 0026 的「最终证明只有 reverify 一份」，另写一份 ADR。

**4. orchestrator 分派 finding 时再判一次它真不真**

- 违反：意图 30（只判一次）
- 证据：run-a-night.md 第 74 行「check the condition its own body states against the current HEAD. If it never held, route … stale invalid」。这条发现 reviewer 已经判过（review-a-ticket.md 第 11 步），worker 也已经筛过（work-a-ticket.md 第 6 步）。
- 影响：同一条发现被第三个 agent 再判一次，夜里多花一轮读代码。
- 修法：删掉「If it never held … stale invalid, and nothing else」这一句，只留「后来的票或本轮修复已经解决」的判断。复盘统计无效发现时也读 worker 的 refuted: 回答（retro/SKILL.md 第 89 行），删掉这句不影响复盘。

**5. 改技能经过一夜后，检查又跑一遍**

- 违反：意图 30（只判一次）；意图 18（改技能的证明是走一遍）
- 证据：authoring-or-modifying-a-skill.md 第 3 步已把 Validate it 里能由命令判的检查写成票的标准，worker 跑过，收尾也跑过。同一步又写这份流程在主人验收、finish 之后「resumes at Validate it」，第 4 步全部检查再跑一次。
- 影响：同一批检查在同一份文字上跑第二遍。
- 修法：改成「resumes at Validate it for its grep alone, then Walk a real task」。grep 那一项需要逐条判断，没写成票的标准，仍在这里做。

### 二、某种结果没人接

**6. 审查失败时，票照样当作审过关掉**

- 违反：意图 12（每种结果都有人接）；意图 35（闸口不沉默）
- 证据：review-a-ticket.md 第 1 步：提交解析不了或 diff 为空时，报告只写一行失败就停。work-a-ticket.md 第 6 步没有这种情况的去路。报告里没有 In-ticket 一节，verify-ticket.py 第 1293 行起把它读成「没有发现」，关票评论写 Review findings: None。
- 影响：一张没审过的票关掉、落地，主人读到的是「没有发现」。
- 修法：先改脚本，因为它机械可判、违反了会悄悄过关：verify-ticket.py 第 1293 行起把「报告里没有 In-ticket 一节」和「写的是 None」分开，前者让关票拒绝并说明原因。work-a-ticket.md 第 6 步再加一句，作为被拒后的去路：开 fault 子票并停下。

**7. 自检排在最后一次运行之后，查出的问题只能写成脚注**

- 违反：意图 1（主人能信任关掉的票）；意图 29（在真实产品上证明）
- 证据：work-a-ticket.md 第 8 步 Audit 在第 7 步最后一次运行之后：「A point that does not hold is said in the closing comment; nothing is committed after the final run.」可这一步点名的 principle-prove-it-works 第 17 行说「A caveat about your own work … is an unmet criterion, not a footnote.」
- 影响：worker 知道有一点没做到，票仍以全部满足关掉、落地。
- 修法：第 8 步挪到第 7 步之前，加一句：不成立的一点现在就修；没有标准覆盖它时，另开 contract 子票。verify-ticket.py 的 RESUME_STEPS 末两项随之对调。改完重跑 check-interfaces.py，因为 RESUME 标题的顺序变了。

**8. 单独跑一张票时，它的子票没人接**

- 违反：意图 12（每种结果都有人接）
- 证据：sub-issues.md 第 11 行：finding 等「the night's closing pass」，decision 和 deferred「reach the user in the morning, in the night summary」。可 Run one ticket 没有夜里的收尾，也没有夜报；run-one-ticket.md 的回复只写「what land did」。relay.py 第 267 行 finding 不叫醒任何人。修 bug 的票也经 Run one ticket 落地。
- 影响：每次修 bug、每张单跑的票，审查留下的发现和交给主人的决定都永远开着，主人不会知道。
- 修法：run-one-ticket.md 第 4 步加一句：落地后按 Run a night 的 Routing a finding 分派每个还开着的 finding，并在回复里点名每个 decision 和 deferred 子票。

**9. 要主人去看的票，夜报里不出现**

- 违反：意图 12（每种结果都有人接）；意图 37（早上几分钟看懂一夜）
- 证据：切票把「要看人反应的」「够不着的」切成 ready-for-human 票，阻塞它的票落地后它就该主人看了。status.py 第 590 行起的夜报只有 Closed、Handed back、Bounced、Not dispatched 和当夜新子票几行，这种票哪一行都不在。run-a-night.md 全文没有 ready-for-human。
- 影响：主人验收这一夜时，没人告诉主人哪张票现在可以去看。
- 修法：夜报加一行：还开着、已没有阻塞的 ready-for-human 票。

**10. 标准小节的标题写错一个字母，白天的 lint 照样通过**

- 违反：意图 35（闸口不沉默）；意图 27（完成标准是命令）
- 证据：verify-ticket.py 第 3951 行找不到 ## Acceptance criteria 小节时，就把票当成给人看的票，只查标签。子任务实测：标题写成 Acceptance Criteria（C 大写），--lint 输出 LINT OK；夜里同一张票被 gate-check 以「ledger contains zero live gates」拒绝。
- 影响：白天没拦住，夜里占一个 worker，票退回分诊。
- 修法：这一处加一个条件：标签含 ready-for-agent 而没有这个小节，报 ERROR。

**11. 产品因为本票的代码起不来，worker 却当成流水线故障上报**

- 违反：意图 12（每种结果都有人接）；意图 19（每个分支都有去路）
- 证据：ui-acceptance SKILL.md 第 36 行规则 4「When the product cannot be reached, report the ticket blocked and stop」；sub-issues.md 第 19 行把产品够不着归为 fault。journey.py 的 bail() 在 start 失败时只打印输出、退出 2，不说下一步。
- 影响：本票把启动弄坏时，worker 开 fault 子票停下，夜里把 orchestrator 叫起来修「流水线」，而该修的是本票的代码。
- 修法：规则 4 加半句：start 自己的输出指向本票的代码时，修产品，不开 fault。

**12. Revise a spec 的更正票没写怎么发布、谁来跑**

- 违反：意图 12（每种结果都有人接）
- 证据：revise-a-spec.md 第 4 步只说已落地的票与新文字矛盾时「is followed by a correction ticket, written as … ticket-format.md」，没有发布命令、标签和 lint，也没说谁跑它。全文只有这一处。
- 影响：更正票可能只写在本地，或发布了没人跑。
- 修法：这句后加：用 verify-ticket.py <spec> --publish 发布，并在回复里点名，由主人决定哪一夜跑。

**13. 「请主人跑 setup-mmw」是一条走不通的路**

- 违反：意图 12（每种结果都有人接）；意图 26（每个仓库先配置一次）
- 证据：make-a-small-change 等六份流程（见问题「先读功能文件」那条）都说没有功能地图时「tell the owner to run the setup-mmw skill for this product」。setup-mmw 第 13 步只处理还没有 .mmw/<product>/ 的产品，scripts/check.py 也不报缺 docs/features/<product>/。
- 影响：已接入、只缺功能地图的产品，主人照做后什么都不变，下次流程又让主人跑。
- 修法：第 13 步的条件改成「没有 .mmw/<product>/，或没有 docs/features/<product>/」。

### 三、工程判断交给了主人

**14. 小改动和 tdd 要主人确认测试的 seam**

- 违反：意图 3（工程决定归 agent）
- 证据：小改动第 2 步写着把 seam 写进请求文件，"由主人确认"。write-a-spec 第 3 步却写明 seam 由 agent 决定，不需要主人确认。主人的全局规则也是这样分的。tdd 技能本身也这样写（tdd/SKILL.md 第 22 行「With no ticket in hand, write the seams down and confirm them with the user. No test is written at an unconfirmed seam.」），所以只删小改动那半句，agent 照 tdd 做仍会来问主人。
- 修法：删掉小改动第 2 步的「由主人确认」；tdd 第 22 行改成「写下 seam，没写下的 seam 不写测试」，在 imports.tsv 的 tdd 那一行记一条 J。tdd 第 24 行的「Ask: "What's the public interface, and which seams should we test?"」同样改成 agent 自己回答并写下来，不拿去问主人。

**15. 切票时把工程判断交给主人**

- 违反：意图 3（工程决定归 agent）
- 证据：cut-tickets.md 第 26 行「Ask the owner whether the granularity is right, whether each ticket depends only on tickets that really gate it, whether any should be merged or split, whether each worker grade fits…」；第 24 行把扫描子任务返回的问题不加区分地列进 Choices。
- 影响：主人要逐张判断票切得细不细、依赖对不对、给哪一级 worker，这些是工程判断，问主人占主人的注意力，主人的答案也不会比 agent 的好。
- 修法：第 26 行只问 Choices 里属于产品的选择，以及先交付哪些、按什么顺序；粒度、依赖、worker 等级由切票者定，列给主人看。扫描问题里属于工程的，切票者自己定，写进 What to build。

### 四、小改动的证明走样

**16. "每个入口都要证明"被改写了**

- 违反：意图 29（从功能的每个入口证明）
- 证据：make-a-small-change.md 第 3 步写的是"主人点名的入口证明改动生效，其他每个入口证明自己仍可用"。pstack 原文的意思是：地图列了几个入口，就从每个入口证明这次改动生效，不能拿别的入口顶替。
- 影响："仍可用"没有改前改后的差异可比，按 verify-this 的规则只能判为 NOT VERIFIED。小改动就此结束，不能提交。
- 修法：恢复原意，写成：从每个能到达被改行为的入口证明这次改动生效；到不了的入口写明到不了。删掉「仍可用」这一类证明。只写「每个入口」不行：够不着被改行为的入口同样没有差异可比，会掉进同一个坑。

**17. verify-this 里我们自己加的第 5 步**

- 违反：意图 30（只判一次）；意图 29（从功能的每个入口证明）
- 证据：上游 verify-this 只做改前改后比较。比较之前先跑仓库检查，是 imports.tsv 的 J790、J791 加进来的。小改动第 3 步自己也跑测试。
- 影响：同一批测试在一次小改动里跑好几遍。任何和这次改动无关的红，都会让结论变成 NOT VERIFIED。
- 修法：删掉这一步。测试只在小改动第 3 步跑一次。

### 五、没有票、产品还没接好时

**18. 五条规则只有"报这张票受阻"一条出口**

- 违反：意图 19（每个分支都有去路）
- 证据：ui-acceptance 的 SKILL.md 第 35 到 39 行要求"报这张票受阻、开 fault 子票"。小改动、修 bug 第 1 步、复核、接入产品都受这五条约束，可这些流程都没有票。同一段还写着"start 在 .mmw/target.json"，lease 命令也不带 --product，多产品落地后照着做会被拒一次。person-ticket.md 第 11 行给主人的命令也一样，写的是 lease.py run -- 加 .mmw/target.json 里的 start，不带 --product，lease.py 会拒绝（第 1014 到 1018 行）。
- 修法：改这一段。没有票时就停下，在回复里说受阻和缺什么。路径改成 .mmw/<product>/target.json，lease 命令带上 --product。person-ticket.md 第 11 行同样改。

**19. 复核第 6 步要"完整照做小改动"**

- 违反：意图 15（一事一处）
- 证据：maintain-verification-skill 第 76 行这样写。小改动第 2 步要先写会失败的测试，第 3 步要重证每个入口；复核自己的第 31 行却规定不动产品代码和测试。
- 修法：改成每个功能一次提交，跑一次 code-review，过整仓检查后推送。

**20. 接入一个新产品会卡住**

- 违反：意图 29（每个产品都能被操作）
- 证据：四件事。create-verification-skill 只能从 setup-mmw 第 13 步进入，或者由主人点名。target_config.py 的 --check --product 会把所有产品的问题都报出来（第 270 到 316 行遍历全部产品），新产品永远过不了。没有故事页的产品不知道 stories 怎么填：journey.md 第 73 行允许写 "none"，可写产品答案时读的 product-answers.md 第 78 行没提。migrate_products.py 第 44 行允许名字以连字符开头，于是 --help 会被当成产品名。
- 修法：mmw-mode 加一条触发行，"接入一个产品"直接进 create-verification-skill。--product 只报这一个产品的问题。product-answers.md 的 stories 条目写明没有页面时填 "none"。产品名必须以字母或数字开头。mmw-mode 第 19 行把「没有 .mmw/target.json 的仓库」交给 ui-acceptance 的那半句同时删掉，免得接入有两条路，其中一条跳过主人确认产品名单。

**21. agentflow 的 parrot 写死了后端地址**

- 违反：意图 29（每个产品都能被操作）
- 证据：desktop-parrot/src/renderer 下的 main.ts、settings.ts、job-create.ts、batch-summary.ts 都写死了 http://127.0.0.1:8796。
- 影响：两个 parrot 不能各用自己的端口同时运行，接不进端口租约。
- 修法：在 agentflow 开一张票，地址改为从环境变量读。这是产品代码，不在 MMW 里改。

**22. 白天驱动过一次产品后，同一工作目录里的 journey 一律被拒**

- 违反：意图 29（每个产品都能被启动、操作）；意图 12（每种结果都有人接）
- 证据：lease.py run 每次都把产品记为 started，命令结束后不清，只有 stop_products 清。journey.py 第 316 行看到已 started 就拒绝：「Stop that instance through its owner」。我在隔离目录里复现了：lease.py run --product p -- true 退出 0 后，lease.py list 仍是 "started": ["p"]，接着 journey.py run p/x 被拒。经 lease 跑 start 之后产品真的在跑，这时 started 不清是对的；缺口在经 lease 跑 stop 之后也不清。
- 影响：create-verification-skill 第 4 步、maintain-verification-skill 第 4 步、worker 写 Driving it 前的那次走查之后，再跑带 journey 的标准都会被拒。拒绝信息叫它找「owner」，owner 就是它自己，它只能开 fault 子票。
- 修法：lease.py 的 run 在命令返回后，按这个产品自己的端口段检查，端口都已空闲时把它从 started 里删掉。这一条同时盖住「start 后仍在跑」和「stop 后已停」两种情况。

**23. 照文档写的 doctor 在 lease 下拿不到它要比对的提交**

- 违反：意图 29（每个产品都能被体检）；意图 12（交接同名同形）
- 证据：product-answers.md 第 60 到 61 行说 doctor 比对的版本是 MMW_WORKTREE_COMMIT。全仓库只有 journey.py 第 249 行设置它；接入和复核都用 lease.py run 跑 doctor。本仓库任务板的 doctor 自己补了 or worktree_commit()，说明缺口是真的。
- 影响：新产品照文档写的 doctor 拿空值比对、退出 1，接入第 4 步达不到完成判据。
- 修法：lease.py 给产品的环境变量里加上 MMW_WORKTREE_COMMIT，与 journey.py 第 249 行同源。

**24. 产品答案的说明里没有 discover**

- 违反：意图 12（交接同名同形）
- 证据：product-answers.md 的 What the repository answers 没有 discover 一条。读的一方却依赖它打印的键：control-ui.md 第 17、18 行读 origin、cdp，journey.md 第 21 行也读。命令行产品要的 tmux 会话名由谁打印，也没写。
- 影响：接入新产品的 agent 不知道 discover 要打印什么，写出来的接不上。
- 修法：product-answers.md 加一条 discover：打印一个 JSON，网页给 origin，Electron 给 cdp，命令行给会话名，外加 instance。

**25. 白天直接探测产品时不体检，可能在旧进程上取证（推断）**

- 违反：意图 29（每个产品都能被体检）
- 证据：control-ui.md 第 15 行的启动步骤没有 doctor；product-answers.md 第 39 行规定 start「leaves its own current product alone」，产品已在跑就不重启。
- 影响：小改动改完代码再 start 一次，产品没重启，改后的那次证明拍的是旧代码。推断，没有实测。
- 修法：control-ui.md 第 1 步加一句：随后跑 doctor；改过产品代码后先 stop 再 start。

**26. create-verification-skill 单独运行时不跑 lint、不提交**

- 违反：意图 36（机器能判的交给脚本）；意图 12（交接同名同形）
- 证据：它第 3 步的完成判据是「each feature file matches that reference」，机器能判，却没点名 feature_map.py lint。第 1 到 5 步都不提交，提交只写在 setup-mmw 第 13 步。
- 影响：主人直接点名这个技能时（问题 20 要加的就是这个入口），写下的文件只留在本机，夜里从 origin 切出的工作目录看不到。
- 修法：第 3 步完成判据改成 lint 退出 0；第 5 步加「提交并推送」；setup-mmw 第 13 步里那句重复的提交删掉。

### 六、常驻文件在流程里保持为真

**27. 缺两个当场更新的环节**

- 违反：意图 33（常驻文件在流程里更新）
- 证据：拿 TESTING.md 的四个环节对照。前两个功能文件有：切票时由票认领，改的人在同一提交里改。后两个没有：code-review 的四个轴和 review-a-ticket 都不读功能文件；retro 的去向里只有 testing-fact。此外没有任何文字让读到功能文件不对的 agent 去改它。
- 影响：功能文件只在写下的那一刻被人看过一次。
- 修法：照 TESTING.md 补齐。Spec 轴读票 Owns 里那几个功能文件被审那次提交的版本；feature-map.md 加一句，读到不对就在本次提交里改；retro 加一个补功能事实的去向。审查轮次不变。

**28. 任务板功能文件已知的六处不符**

- 违反：意图 33（常驻文件在流程里更新）
- 证据：举两处。settings.md 第 91 行写"未改动时点 X 关闭"，可 settings.mjs 里的 close 不看状态，有改动也直接关掉。read-detail.md 第 124 行写标签读作 TICKET，可 detail.mjs 第 111 行写的是 Ticket，大写是 CSS 做的。
- 修法：用一次小改动把六处一起改正。

**29. ADR 0041 还把定期复核算作保持 feature map 为真的办法**

- 违反：意图 33（常驻文件在流程里更新，不靠定期复核）
- 证据：docs/adr/0041-feature-map.md 第 6 行的标题写"由 lint、同一提交和定期复核保持为真"，正文还说定期复核由本组第 5 份 spec 执行。mmw-mode 的触发行已经是主人要求时才复核（SKILL.md 第 21 行）。
- 影响：以后读 ADR 的 agent 会照它去安排定期复核，和主人的规则相反。
- 修法：ADR 写完不改（ADR 0038），所以写一份新 ADR 修订 0041 这一句：保持为真靠 lint、同一提交，加上问题 27 补的两个当场更新的环节；复核只在主人要求时做。

**30. 屏幕契约退役一行，base 上的 feature map lint 就变红**

- 违反：意图 33（事实由改变它的那一步当场写）
- 证据：write-screen-contract SKILL.md 第 16 行把退役的行 id 移进 retired_ids；feature_map.py 第 464 行只读 rows，功能文件里引用那一行的 row:<id> 被报成问题。write-the-screen-contract.md 第 8 步提交时没提 docs/features。这条 lint 在 checks 里，checks 红就把票退回。
- 影响：之后当夜每张票合并都被退回，而那个功能文件不在任何一张票的 Owns 里，worker 改不了。
- 修法：write-the-screen-contract.md 第 8 步加一句：退役的行，同一提交里改掉 docs/features/<product>/ 中引用它的那一行，并跑 feature_map.py lint。

**31. 「测试事实和改动同一提交写进 TESTING.md」这条规则，worker 读不到**

- 违反：意图 11（规则写在执行者读的地方）；意图 33（常驻文件在流程里更新）
- 证据：这条只写在 setup-mmw/SKILL.md 第 32 行，同一处还写着「a worker gets what it needs from the spec and the ticket」。work-a-ticket.md 和 ticket-format.md 都没让票认领 TESTING.md。本仓库 TESTING.md 只有 20 行，没写任务板的假 gh、journey、故事服务。
- 影响：审查的 Tests 轴拿过时的 TESTING.md 判，下一份 spec 以为某个造状态的机制不存在。
- 修法：ticket-format.md 写 Owns 的那段加一句：新增测试层、桩或造状态机制的票，把 TESTING.md 列进 Owns。

**32. 功能文件写的是产品有什么功能，各处写进它之前是否问主人不一致**

- 违反：意图 3（产品决定归主人）；意图 22（白天定下主人的决定）
- 证据：feature-map.md 第 33 行：功能的划分在产品接入时、在 spec 的 Feature map changes 里由主人确认；create-verification-skill 第 3 步同样要主人确认。make-a-small-change.md 第 1 步、bug-fix.md 第 1 步、runtime-forensics.md 第 1 步在没有功能文件时直接写一份，小改动第 4 步改了行为就直接改功能文件，maintain-verification-skill 第 3 步补登遗漏的界面，都不问主人。
- 影响：主人对产品有什么功能的理解，会被 agent 自己写下的版本替换，主人不知道。
- 修法：主人 2026-10-09 定：功能文件写的是产品有什么功能，来自白天讨论；写进或改动其中「产品能做什么」的部分（开头一段、Sub-features、How to get to it、README 的 Features 索引行）之前，先在对话里列出，请主人确认对功能的理解和设计没问题，再写。夜里只写 spec 的 Feature map changes 已列出、已确认的。Driving it、Gotchas、check、source 是工程事实，agent 自己写。规则只写在 feature-map.md 一处（替换第 33 行），写功能文件的各处只留指针；和问题「先读功能文件那段抄了六份」一起收口。

### 七、规则写错地方、写反或写了多份

**33. 「需要判断的」规则被送到不审它的轴**

- 违反：意图 11（规则写在执行者读的地方）；意图 12（交接同名同形）
- 证据：ticket-format.md 第 66 行把「接口深不深」「标准背后的测试能不能失败」这类判断写进 spec 的 Implementation Decisions，由 Spec 轴读。可 spec-reviewer.md 第 62 行说测试可不可信「belong to the other axes. Leave their questions alone」，而 Standards 轴、Tests 轴本来每次都问这两类。Parent 写 None 的票（修 bug）根本没有 spec 小节可写。
- 影响：切票者多跑一轮 Revise a spec，写进去的话没人用；修 bug 的票不知道写哪。
- 修法：第 2 问末句改成：每次审查都会问的不写；只属于这张票的判断写进那一节；没有 spec 的票写进 What to build。

**34. worker 等级规则前后两句相反**

- 违反：意图 19（没有让 agent 自己猜的选择）
- 证据：ticket-format.md 第 97 行先说出错会悄悄发生（钱、崩溃恢复、已装用户读的契约、安全默认）的票给 senior-worker，接着说「A ticket whose Seam names a test layer that has a precedent to copy … stays on junior-worker」。spec 要求每层都写先例，几乎每张票都满足后一句。
- 影响：涉及钱和崩溃恢复的票会按后一句交给 junior。
- 修法：后一句开头加「Short of those,」。

**35. Run one ticket 在流程运行时修补流水线脚本**

- 违反：意图 40（正在跑的版本冻结）
- 证据：run-one-ticket.md 第 15 行：「a fault stopped the worker; fix what the child names, then dispatch.sh resume」。run-a-night.md 第 39 行区分了两种：环境的 fault 修，「A fault in the pipeline's own scripts you do not patch while they run the night」。根 AGENTS.md 规定单票运行同样冻结。
- 影响：修 bug 时的 orchestrator 会在运行中直接改正在跑的脚本。
- 修法：第 15 行的 fault 一句改成照 Run a night 表里 fault 那一行做。

**36. MISS 的提示叫人去改测试**

- 违反：意图 27（修产品，不改检查）
- 证据：boundary-check.py 第 115 行打印「Fix the product's test; the negative control was not reached.」ui-acceptance SKILL.md 第 10 行是「change the product … never the check」。SKILL.md 第 21 行说 boundary-check.md 讲怎样读 MISS，那份文件里没有这一节。
- 影响：worker 按提示去改测试让它通过。
- 修法：提示改成：第一次运行就红，先让产品满足这一行；只有测试断言了这一行没说的东西时才改测试。SKILL.md 第 21 行承诺的「怎样读 MISS」也要落地：在 boundary-check.md 补一个小节，或者改掉第 21 行，不然指针仍是空的。

**37. 「先读功能文件」那一段抄了六份**

- 违反：意图 15（一事一处）
- 证据：同一段（读 docs/features/<product>/ 的功能文件，取入口、Driving it、Gotchas；「A product with no such directory has no feature map」）分别写在 make-a-small-change、bug-fix、runtime-forensics、chart-a-map、write-a-spec、resolve-a-map-ticket 六份流程里。各份写下新功能文件后怎样提交不同，这一点是各自情形决定的，没问题。
- 影响：改一处要改六处，漏一处就两种说法。
- 修法：这段写进 mmw-mode 的 references/feature-map.md 的一个小节，连同「写下的功能文件当场提交并推送，夜里的票才看得到」这一句，六份流程各留一句指针。问题 1 的提交缺口同此。

**38. downstream-notes 与 ADR 0032 矛盾，也没人读**

- 违反：意图 15（一事一处）；意图 33（每个事实只有一处记录）
- 证据：ADR 0032 第 28 行写 v3 不再有 downstream-notes。这个分支又新建了 mmw-v3/downstream-notes/，v3 的技能和脚本没有一处读它。
- 修法：删掉这个目录。迁移该跑的命令，lease 的拒绝信息里已经写着。

**39. 分诊技能的步骤指针指错**

- 违反：意图 12（交接同名同形）
- 证据：triage/SKILL.md 第 64 行说 pipeline-issues.md「replaces step 1's reproduction」，复现在第 70 行的第 3 步，第 1 步是收集上下文。从 v2 原样搬来。
- 影响：分诊夜里退回的票时，agent 可能照第 3 步去拉起产品复现，白花时间。
- 修法：改成「replaces step 3's reproduction」。

**40. 修 bug 流程复述了 diagnosing-bugs 的一条规则**

- 违反：意图 15（一事一处）；意图 10（按名字交给另一个技能，不复述它的规则）
- 证据：bug-fix.md 第 7 行「Show the ranked list to the owner and carry on without waiting.」；diagnosing-bugs/SKILL.md 第 98 行「Show the ranked list to the user before testing. … Don't block on it; proceed with your ranking if the user is AFK.」
- 影响：两份说法迟早改得不一样。
- 修法：删掉 bug-fix.md 第 7 行那一句，第 2 步已经让 agent 按 diagnosing-bugs 的 Phase 3、4 做。

### 八、改技能这件事本身

**41. 新 agent 走一遍时，读到的可能是安装目录里的旧文字（推断）**

- 违反：意图 18（改技能的证明是走一遍）
- 证据：WALKING-A-SKILL-SET.md 第 21 行列出给新 agent 的说明要带什么，没有「改后的文字在哪个目录」。根 AGENTS.md 的 Gotchas 写着宿主的技能链接都指向安装目录，主工作区的改动发布前到不了宿主。
- 影响：新 agent 只拿触发语时，宿主给它的是旧版，这次走的证明证错了对象。推断，没有实测。
- 修法：第 21 行的清单加一项：改后的文字从哪个目录读。

**42. 两处小缺口**

- 违反：意图 7（每一步都写完成的判据）；意图 39（发布由主人决定）
- 证据：trace-forensics.md 第 6 步没有 Done when。authoring-or-modifying-a-skill.md 第 6 步告诉主人改了 description「takes effect in a new session」，没说要等安装目录移到这次提交之后才生效。
- 影响：后一处会让主人以为开个新会话就生效了。
- 修法：第 6 步补 Done when；「in a new session」后加「once the installed checkout is moved to it」。

**43. 技能文字有错时怎么办，只写在一处读不到的地方，而且那一句让人直接改正在用的技能**

- 违反：意图 40（正在跑的版本冻结）；意图 38（教训进机制、改规则经主人）
- 证据：上游 pstack poteto-mode 的 Non-negotiables：「Broken skill mid-task → fix it in its own PR. Don't block. Don't silently work around it.」imports.tsv 第 47 行的 J90 没带进来。MMW 只有 ticket-format.md 第 26 行 Owns 一段「the toolbox is improved in use, and the change is made there at once」。
- 影响：白天的会话读不到这句，遇到写错的技能会悄悄绕过；夜里照这句做，会直接改本机正在用的那一版技能，不经提交和发布。
- 修法：删掉 ticket-format.md 那一句；mmw-mode 的 Non-negotiables 加一行：技能或流程文字有错，不绕过，也不夹进手上的改动；白天按 Authoring or modifying a skill 单独修、单独提交，夜里不改，留给复盘。设计意图表把 P28 从「还没有家」移到对应意图下。

### 九、文档和产品

**44. ADR 指向不存在的文件**

- 违反：意图 24（ADR 指向的东西必须存在）
- 证据：docs/adr/README.md 第 65 行指向 design-pages 的 references/pull.md，可那个目录里只有两个模板。ADR 0042 第 15 行指向的 mmw-mode/references/skill-set-rules.md 也已不在，现在的文件是 writing-for-agents 的 SKILL-SET-RULES.md。
- 修法：两处都改成现在实际讲这件事的文件。ADR 写完不改正文，但指针错了属于勘误，只改路径。

**45. 任务板保存按钮的禁用逻辑写了两份**

- 违反：意图 27（检查要能因为它守的缺陷而失败）
- 证据：按钮用的是 local-config.mjs 第 244 行那份；测试 local-config.test.mjs 第 164 到 173 行测的是第 110 行那份，而产品代码里没有地方用第 110 行。
- 影响：第 244 行的条件哪天写错了，测试也不会变红。
- 修法：按钮改用第 110 行那份，删掉第 244 行的重复。开一个 issue 记下。

## 查到但不采纳的


删掉收尾时的 reverify。它把这一夜所有票合在一起之后，再跑每张票的标准。子任务认为这是第二遍验证。不采纳：它验的是合在一起之后的状态，这件事在它之前没有人验过，不是同一个结论的第二遍。切票流程里「功能文件进 Owns」和 lint 重复。不改：切票者在第 3 步起草时就要知道这条，lint 要到发布时才报，删了就是先写错再返工。审查者核实自己的每条发现，worker 可以回答 refuted:。这两处不算第二次验证：前者是审查内部的过滤，后者是修复这一步的输出。按主人的规则，这是验一次、修一次。
另有一件。本仓库有 docs/features/，.mmw/target.json 却没有 checks，所以 feature map lint 在合并时不跑（setup-mmw 的 check.py 会报这一项）。照 ADR 0041 把它加进 checks；根 AGENTS.md 里「这个仓库的 target.json 没有 checks」那条说明也随之删掉。


## 主人的决定

- 2026-10-09：第 6 节的修法全部照做。
- 2026-10-09：功能文件写进或改动「产品能做什么」的部分之前，先在对话里列出请主人确认；全 MMW 统一（问题 32）。
- 2026-10-09：任务板设置表单点 X 时直接丢掉未保存的修改，不算大事，不修。
- 2026-10-09：spec #892 至 #895 的票都已关闭、代码已在分支上，直接关闭这四份 spec。

## 没做的

- 没有统计每个任务的读入量。
- 走查只走了「改一个流程」和「审查 Bug fix」两个任务；其余任务没有用新 agent 走。
- agentflow 的 parrot 写死端口（问题 21）是 agentflow 仓库的产品代码，不在本仓库改，已在 agentflow-hq/agentflow 开 issue #1152。
- 走查顺带发现的旧文字含糊处，另开了 issue #969 至 #977。
