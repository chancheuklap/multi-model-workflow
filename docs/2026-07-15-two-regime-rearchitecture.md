# 两态一门重构方案(2026-07-15)

> 本文是 plugin/ 与 droid-plugin/ 重构的实施依据。负责人可读版(逐阶段行为与选项)见 artifact:
> https://claude.ai/code/artifact/bcdf8e6a-2712-4301-b427-99bf0dd86e12
> 诊断结论:方法论文档是资产,机械层刚性放错位置——在判断处设机器闸(账本/上限/结论词),在事实处用机械默认冒充(afk 默认/取最高版本/旧状态断言)。修法 = 刚性搬家,非统一放松。

## 核心模型

- **两态一门**:讨论态(investigate/propose/design/prototype,螺旋、可中断、可反复)→ 唯一人闸(用户显式确认设计)→ 流水线态(to-issue/plan/build/final/closing,单向、产物明确)。
- **脚本三角色**:讨论态书记员(记书签/落盘/渲染进度)、流水线态工长(建 worktree/派工人/核产物)、任何态不当法官(不否决判断)。
- **机器否决权白名单**(仅此四条,fail-closed 只许出现在这里):
  1. 出站动作(push / gh pr merge / 部署)→ guard-redline 弹权限框人批(现状保留);
  2. 写者≠审者(派发身份 + 审者只读沙箱);
  3. 状态新鲜度(task.json 带 plugin_version + updated_at,超龄/跨版本先 /reassess 对表再续);
  4. 设计确认指纹(过门时盖承重文档,执行与确认不符→请用户重过目)。
- 白名单外一律:记录 + 提醒 + 留痕,不拦。失败可见性不变(自决留痕/警告落盘/超轮汇报)。

## 拆除清单(两 plugin 同步)

| 拆什么 | 替代 |
| --- | --- |
| loop.sh 账本全套(checklist add/cover、finding add、round next、exit-check、空账 fail-closed) | 产物级收口:审查报告落盘且含 verdict 段、Critical 全处置 |
| handoff 拒收(结论词白名单 die、空手 pass die、闸内 exit-check die) | handoff 保留登记产出与指路,缺产出降为警告留痕 |
| caps.max_turnaround=1 锁死 + turnaround_count 永不重置 | 讨论态移动不计数;流水线态回上游从第 2 次起每次向用户汇报,不锁死 |
| needs-redirection 默认回 phases[0] | 默认回上一阶段;回拨时剪掉下游过期 phase_outputs(现状新旧混喂) |
| design 阶段 steps 游标强制推进 | 四动作(讨论/原型/成文/自检)为方法论顺序,agent 按需走 |
| prompt-anchor 每条消息注锚 | 仅 SessionStart 与 compaction 恢复后注入书签回报 |
| source-stability 指纹全阶段勒索重审 | 指纹只在过门处用(白名单第 4 条) |
| droid 逐字 token(确认设计 MMW-APPROVE:<hash>) | /approve-design 显式命令,两宿主同名;hook 可检、LLM 不可自我说服代过 |
| locate-mmw sort -V 取最高版本 | 读 installed_plugins.json 激活 installPath;AGENTS.md 删相对路径教法;清缓存旧版本 |
| Claude 侧 develop 建档 attendance:"afk" | develop 建档 attended,过门自动切 afk(droid flow.sh 已有此逻辑,搬 Claude 侧统一);bug/small-change 动手前一次轻确认(根因+修法等一句话) |
| droid unattended「普通消息不解除」 | 对齐 Claude 语义:用户回来发任意消息即恢复可提问,续无人须再显式进入 |

## 讨论态规则

- 状态 = 书签(task.json 瘦身):任务身份 + 版本戳/时效戳 + 一句话现场注记。开场回报三源自动派生:①最近 commit 标题流水(=上次做了什么;「固化一个结论 commit 一次」的既有习惯是数据源)、②设计文档 Open Decisions 节(=待拍板)、③书签注记。不要求 agent 维护第四本进展账。
- **取证战役**为一等公民(源自 agentflow 案例:9 天 260 commit,evidence/prototype 目录全是实测产物):缺口→取证计划落盘→真实测(脚本/浏览器/真 API,产物保真落 docs/design/<slug>/prototype/)→证据台账(docs/design/<slug>/evidence/,按证据等级标注,否决候选留否决理由)→回填设计。量小主线程打,成规模派并行调查工人;涉凭证/真机/生产先问一句。
- 自由往返:调查↔方案↔设计↔原型移动不计数不留案底;同一来回超 3 次 agent 主动摆「卡在哪、要不要换切法」(提醒不拦)。
- 设计预审:成文+自检后自动跑一次跨模型审(写者≠审者),findings 给用户和 agent 参考,不冻结阶段。
- 跨宿主接力:状态 host-neutral,今天 Claude Code 明天 droid 同 worktree 续,同一份书签。

## 门:/approve-design

- 唯一硬 HITL。用户显式命令放行(自然语言同意不解锁,agent 请用户敲命令)。
- 记录:确认人、时间、承重文档指纹。**指纹只盖主设计文档 + 被引用合同文档**——设计目录形态(主文档+evidence/+prototype/+子文档)下,往 evidence 追加取证不作废确认。
- 过门自动:attendance→afk、进度板刷新、进 to-issue。

## 流水线态规则

- 阶段推进/接力单(reads 声明拼 prev_outputs)/worker 派发/审者派发脚本全保留(纯代劳,资产)。
- record-step hook 保留(commit 即进度,真值链取 HEAD,机器记账替代人工销账——这是「记录不否决」的样板)。
- 审查:review start 定编制(按 diff/Complexity 分档 1/2/4 审者,现状保留)→ 审者读 worktree-review skill → findings 原样落盘 → 主线程亲验标处置 → 收口核产物(报告存在+verdict 段+Critical 全处置)。
- ④final 缺陷回路:代码缺陷派全新工人定点修;撞破上游→汇报后回上游;同层返修第 3 轮起每轮向用户汇报。

## 外部 skill 协作(三接法)

| 接法 | 实例 | 规则 |
| --- | --- | --- |
| 委托型 | to-tickets(切片含自带用户确认闸)、domain-modeling(领域文档)、tdd(红绿循环) | 严格遵循其输入输出与自带质量闸,plugin 只定落点,不叠闸 |
| 场景型 | diagnosing-bugs、codebase-design、triage、prototype、playwright-cli、impeccable | 情境触发用完即回 |
| 作业本型 | worktree-build / worktree-plan / worktree-review(plugin 自有) | 软链 ~/.codex/skills 发布给 Codex,即时生效;工人唯一读物 |

两纪律:派发 prompt 只点名 skill、永不内联方法论、永不给 plugin 内路径;外部 skill 自带质量闸直接采用。

## 多模型通信(Claude 侧 Codex)

装备(skill 预装,工人不读 plugin 目录)→ 派发(脚本代劳:子 worktree、按 plan Complexity 自动选模型档、纯路由 prompt)→ 执行(工人 worktree 内逐 Pack 提交)→ 回执(Return Contract 结构化落盘固定路径,主线程亲验不吃自述)→ 续接(worker resume 回原会话,脚本重钉模型/沙箱/workdir,session 从 run.log 捞)。
新增硬化(机器可核验,白名单延伸):**派发前自检**——三文档存在、点名 skill 已装且指向当前版本、仓库测试治理文档定位一次并把路径写进 prompt;缺装备当场报错。
droid 侧:Custom Droid 定义即模型分配,派发走原生 subagent;作业本/回执/验收契约与 Claude 侧同源。

## 测试质量层(治 Codex 垃圾测试)

**方法论随 plugin 走(随身携带,任何仓库生效);仓库只留一张薄层事实表。** 分工:plugin 管「测试该怎么写」,仓库薄层只管「本仓库的事实」,两者不重叠、无覆盖关系。

1. **plugin 测试写作权威**(完整方法论,内化自 agentflow TESTING.md 的通用部分,落 worktree-build/references/test-quality.md 替换现 tests.md):
   - 测试名 = 业务行为陈述;每测试一个逻辑断言;
   - 断言对象 = 外部可观察事实(系统读接口 > HTTP 响应 > 文件产物 > 账本行),禁内部调用序列/私有函数/源码文本;
   - mock 只在外部供应商接缝,自家模块间禁 mock;每行为在权威层测一次,禁跨层重复;
   - 测试数据走真实 producer 路径/共享 builder,禁手搓第二份形状拷贝;
   - 回归测试进业务域文件,禁 fix_xxx 新文件;价格/文案/枚举不硬编码,从权威源读后比对;
   - 行为退役测试同删,skip 超一迭代=删;生产代码禁为测试留 seam,可测试性靠 DI;
   - **禁止形态清单**:grep 源码断言、逐字锁文案、字段全集/默认值/枚举镜像、文档计数断言、墓碑路径清单、「测试测测试」meta-gate、per-file allowlist、mock 自家服务;
   - **准入问题**:守哪个用户旅程/哪笔钱/哪份数据,坏了哪个用户当天受伤——答不出=无资格进仓。
2. **仓库薄层**(各仓库 TESTING.md 只写仓库专属事实,不写方法论):分层目录表(哪层测试放哪、各层职责)、本仓库外部供应商接缝清单(哪些边界算外部可 mock)、权威源指针(价格/文案/枚举从哪读)、套件入口与门控(env 门控、定时 vs 每 commit)、仓库特有禁形态补充(如有,只增不减)。派发 preflight 定位薄层并把路径写进工人 prompt;仓库没有薄层 → 按 plugin 方法论写、测试落点跟随仓库既有目录惯例、回执注明 `no-repo-test-sheet`。
3. **外部 tdd skill**:管红绿循环(先写失败测试/一次一片/tautological 与 implementation-coupled 反模式)。工人语境下 seam 由计划 Task Pack 钉死,tdd 的「与用户确认 seam」= 计划即确认,不再另行商定。

单源机制:方法论用 build/fragments/test-quality 片段注入三处读者——worktree-build(工人写测试前读)、build-b.md B3(主线程验收对表)、worktree-review final(独立审计视角复扫);build.sh --check 防漂移。三道检查同一把尺。存量仓库(如 agentflow)的 TESTING.md 后续瘦身成薄层,方法论部分退给 plugin,由该仓库自己的任务处理,不在本重构范围。

**本仓库自查(已坐实,清洗列入 P1)**:plugin/build/tests/test_build.sh 存在禁形态实例——逐字锁文档 prose 当合同(如 `grep -q "建 worktree(进去之后才开干)"` 锁 scenario 文案、`grep -q '^# Small-change · 需独立任务边界的小改$'` 锁标题),文档润色即假红。合法意图(片段注入传播、锚点存在性)改用结构化断言(fragment 文件内容与注入块程序化比对、锚点标记存在性),不锁具体句子;纯锁文案的删。本仓库同时补一张薄层 TESTING.md(shell 测试放哪、断什么、门控入口)。

## 实施顺序

1. P1 减仪式:拆账本 + handoff 不拒收 + prompt-anchor 降频 + **测试质量基线落地**(同批,同属工人作业本改造);
2. P2 运行时卫生:激活路径定位 / 版本戳时效戳 / 删相对路径 / 清缓存;
3. P3 HITL:attendance 翻转 + /approve-design(替代 droid token)+ droid unattended 退出语义对齐 + bug/small-change 轻确认;
4. P4 回退:上限转汇报 / 默认回上一阶段 / 回拨剪过期产物 / steering 命令写明引擎动作;
5. P5 讨论态书签化(SessionStart 三源回报、取证战役 reference、设计预审服务化);
6. 后置:双 plugin 合流单源+宿主适配层(等行为稳定,短期靠 build fragments + diff 守卫)。

每步在 worktree 分支做、带测试、`--no-ff` 合回 main;改 fragments 后跑 build.sh --apply + --check;版本号 plugin.json 与 marketplace.json 双处同步。
