# ADR 索引

手工维护：新增 ADR 时追加一行，编号取现有最大号 + 1，编号那一格链到文件本身。

## 一份 ADR 长什么样

本目录的 ADR 按这个顺序写：

1. frontmatter：`date`，以及 `amends`（一个编号数组，没有改写任何一份就写 `[]`）。
2. 一行 `# ` 标题。**决定本身就写在这里**，一句话说清定下了什么。
3. 标题下一段散文，说这个决定要覆盖的是什么情形。标题加这一段就是这份 ADR 的决定，别处引用它时引的也是这两样。
4. 零到两节自由标题的节，例如「要修的是什么」。
5. `## Considered Options`：被否决的选项，每条写明否决理由。
6. `## Consequences`：这次改动让什么成立、让什么不再成立。

**本目录不写 `## Decision` 一节。** 找决定就读 `# ` 标题和它下面那一段。

篇幅：0008 至 0022 在 20 到 55 行之间，多数在 26 到 39 行。

| 编号 | 标题 | 日期 | 改写了哪几份 | 被哪几份改写 |
| --- | --- | --- | --- | --- |
| [0001](0001-tracker-repo-authority.md) | tracker 与仓库文件的权威归属 | 2026-08-11 | 无 | 无 |
| [0002](0002-ui-qa-binds-format-not-tool.md) | 界面 QA 绑设计系统的格式规范，不绑生成它的工具 | 2026-08-13 | 无 | 0004（见表下注：pull report，sign-off） |
| [0003](0003-no-plugin-packaging.md) | MMW 不打包成插件，五个宿主由 `install.sh` 统一散装 | 2026-08-18 | 无 | 0006、0015、0032 |
| [0004](0004-design-system-trust-comes-from-lint.md) | 设计系统文件可不可信，由校验结果定，不由来源定 | 2026-08-21 | 0002 | 无（见表下注：pull report，sign-off） |
| [0005](0005-docs-layer-adopted-by-v2.md) | docs 文档层过继到 v2：tracker 配置落地，索引与编号脱离冻结 CLI | 2026-08-25 | 无 | 无 |
| [0006](0006-skills-install-to-neutral-dir.md) | 技能装进一个各家通用的位置，只为 Claude Code 单独再装一份 | 2026-08-26 | 0003 | 0015 |
| [0007](0007-prompt-source-lives-in-repo.md) | 用户级提示词的源放在仓库里，host 目录只放软链或生成物 | 2026-09-05 | 无 | 无 |
| [0008](0008-silence-is-never-a-pass.md) | 流水线里每一道闸口，拒绝要点名事实、给唯一出路，且不许靠什么都不做通过 | 2026-09-06 | 无 | 无 |
| [0009](0009-night-orchestration-on-paseo.md) | 夜间编排从 Herdr 迁到 Paseo：脚本只做工具，判断归 main agent | 2026-09-06 | 无 | 0010、0018、0019 |
| [0010](0010-agents-are-woken-not-polled.md) | agent 之间靠事件互相叫醒，谁都不许轮询另一个 agent | 2026-09-06 | 0009 | 0013、0017、0020 |
| [0011](0011-component-story-not-whole-product.md) | 界面等价在组件级离线判定，整机只跑少量旅程 | 2026-09-08 | 无 | 0028 |
| [0012](0012-review-finding-routing.md) | 一条 review finding 什么时候值一张票：四步判据，默认是 main agent 自己改 | 2026-09-08 | 0008、0009 | 0023 |
| [0013](0013-a-report-and-its-message-are-one-call.md) | reviewer 与 worker 一样，报告落地和报信是同一次脚本调用 | 2026-09-08 | 0010 | 0020（整份作废） |
| [0014](0014-advisor-has-one-door.md) | advisor 只有一扇门：正文是技能，两侧共用 | 2026-09-08 | 无 | 0015 |
| [0015](0015-no-custom-subagents.md) | 工具箱不再交付 subagent：用 host 自带的通用 subagent | 2026-09-09 | 0003、0006、0014 | 0016 |
| [0016](0016-live-session-table.md) | 会话怎么起写在本机活表里 | 2026-09-09 | 0015 | 0018、0024（整份作废） |
| [0017](0017-the-night-has-no-clock.md) | 这一夜没有任何时钟 | 2026-09-10 | 0010 | 0020、0021 |
| [0018](0018-runner-behind-one-boundary.md) | runner 收进一条边界：协议只调三个动词，一个 runner 一个适配器，今晚用哪个是本机一行配置 | 2026-09-10 | 0009、0016 | 0019、0020、0024、0026 |
| [0019](0019-ticket-state-is-a-fold-of-events.md) | 票的状态是它的事件折叠出来的：评论首行不再是协议，谁在跑这张票写在票上 | 2026-09-10 | 0009、0018 | 0026、0034 |
| [0020](0020-wakes-come-from-the-board.md) | 唤醒从 board 上发出：中继读票上的结果事件，经 runner 的送消息动词送到等它的那个会话，任何脚本都不再报信 | 2026-09-10 | 0010、0013、0017、0018 | 0021、0022、0026 |
| [0021](0021-liveness-in-three-layers.md) | 判活分三层，都不是 agent：回合守卫在主 agent 的回合结束时重新武装看门进程，看门进程看中继并问沉默票的 runner，`worker.lost` 只由它写 | 2026-09-10 | 0017、0020 | 0022、0026 |
| [0022](0022-one-relay-many-watches.md) | 唤醒按 watch 分：一个仓库一个中继，同时看多个 watch，每个 watch 叫醒开它的那个主 agent；等槽位的 worker 也由中继叫醒 | 2026-09-11 | 0020、0021 | 0026、0033 |
| [0023](0023-origin-base-branch.md) | base branch 以 GitHub 上那份为准：本机与云端走同一条合并路径，先合、再查、再 fast-forward 推送，合不进去交给 triage | 2026-09-11 | 0012 | 0025、0026、0027、0034 |
| [0024](0024-models-json-and-runner-extension-boundary.md) | 会话配置只存进 `models.json`，runner 的附加操作也只经适配器 | 2026-09-11 | 0016、0018 | 0026 |
| [0025](0025-project-branch-and-finish.md) | 开夜记住并推送 project branch；用户验收后 finish 把 base branch 合回并清理 | 2026-09-11 | 0023 | 无 |
| [0026](0026-no-verifier.md) | 取消 verifier 会话；worker 在 review 后对最终 commit 运行全部 acceptance criteria | 2026-09-14 | 0018、0019、0020、0021、0022、0023、0024 | 0045 |
| [0027](0027-a-bounce-returns-once.md) | 同一夜第一次 landing conflict 把 ticket 交回 worker 队列，第二次才交 triage | 2026-09-14 | 0023 | 无 |
| [0028](0028-element-parity-invariant-answers.md) | 外观按 data-ui id 做 element parity，App 页纳入 story；boundary test 断言四列；product answers 只写不变要求；judge 不遮不藏；journey 第二遍弄坏一个接口 | 2026-09-20 | 0011 | 无 |
| [0029](0029-claude-design-is-the-design-source.md) | 设计的唯一源头是 Claude Design 项目，仓库里的 handoff package 只由 pull 写入 | 2026-09-20 | 无 | 0030 |
| [0030](0030-design-system-built-by-claude-design-agent.md) | design system 由 Claude Design 里的 agent 从产品代码提炼，只装外观；设计页不加载产品代码 | 2026-09-22 | 0029 | 无 |
| [0031](0031-worker-start-memory-is-a-searched-index.md) | worker 开工时拿到两份有上限的 Memory 索引：相关经验用本票 `## Owns` 路径和各级标题的短查询搜出，不用 spec 或 map 正文 | 2026-09-18 | 无 | 无 |
| [0032](0032-v3-is-built-on-pstacks-shape.md) | MMW v3 按 pstack 的形状重建：一份 mode 按任务选 playbook，规则写成原则技能，上游拷进 `skills/` 由 `imports.tsv` 逐行记账 | 2026-10-06 | 0003 | 0036、0040 |
| [0033](0033-a-full-machine-is-a-blocked-ticket.md) | 机器的产品槽位全被占时，worker 这次运行什么都不跑、退 2，票报受阻；不排队，也没有人为槽位叫醒它 | 2026-10-06 | 0022 | 无 |
| [0034](0034-each-night-fact-has-one-record.md) | 夜里每个事实只从记下它的那一条事件读；事件在写时按表校验，读时只拒读不懂的 | 2026-10-06 | 0019、0023 | 无 |
| [0035](0035-a-nights-memory-stays-in-its-repository.md) | 一夜的 Memory 只写进本仓库的 Space：开夜的会话 `NMEM_SPACE` 不对就拒绝开夜；Nowledge Mem 列不全记录时，夜照样关，不做 Memory 收尾 | 2026-10-06 | 无 | 0037 |
| [0036](0036-rollback-to-v2-is-one-install.md) | 从 v3 退回 v2，是在装着的 checkout 里跑一次 `bash mmw-v2/install.sh`；`mmw-v2/` 因此是退路，不只是历史 | 2026-10-07 | 0032 | 无 |
| [0037](0037-the-session-space-is-installed-per-machine.md) | 终端里的 `NMEM_SPACE` 由 `mmw-v3/install.sh` 每台机器装一次；仓库的 Space 仍由 `setup-mmw` 建，它只报告会话的 `NMEM_SPACE` 对不对 | 2026-10-07 | 0035 | 无 |
| [0038](0038-repository-files-are-layered-by-lifetime.md) | MMW 写进产品仓库的文件按时效分处放：通用约定在仓库根，MMW 会执行的产品答案在 `.mmw/`，一次开发的全部文件在 `efforts/<effort>/`，临时文件不进仓库 | 2026-10-07 | 无 | 无 |
| [0039](0039-one-coding-standards-file-per-repository.md) | 每个仓库根目录的 `CODING_STANDARDS.md` 是它审查规则的唯一来源，由 setup-mmw 从模板抄入起头，此后只随本仓库的 retro 提案改；`TESTING.md` 由改变测试做法的改动当场改，retro 补漏 | 2026-10-08 | 无 | 无 |
| [0040](0040-writing-rules-live-in-writing-for-agents.md) | 技能文字的写作规则都在 `writing-for-agents` 技能里；改技能一律从 Authoring or modifying a skill 开始，一个会话做不完的由它交给 Write a spec | 2026-10-08 | 0032 | 无 |
| [0041](0041-feature-map.md) | feature map 是按产品放的常驻文件，放在 `docs/features/<产品>/`，由 lint、同一提交和定期复核保持为真，night 里只有脚本是通过条件 | 2026-10-08 | 无 | 0044 |
| [0042](0042-several-products-in-one-repository.md) | 一个仓库里每个产品占 `.mmw/<产品>/`，一次运行仍只租一个按产品分段的 lease，control-ui 与 control-cli 是 ui-acceptance 的 reference 而不是 skill | 2026-10-08 | 无 | 无 |
| [0043](0043-design-intents-are-the-standard.md) | 改技能以 `writing-for-agents` 的 `DESIGN-INTENTS.md` 为标准：每次改动先说出它服务哪条意图，审查逐条意图追踪落地，一个结论只判一次 | 2026-10-09 | 无 | 无 |
| [0044](0044-feature-map-kept-true-in-the-flow.md) | feature map 靠流程里的环节保持为真：lint、同一提交、Spec 轴读 Owns 里的功能文件、读到不对当场处理、retro 的 `feature-fact`，改「产品能做什么」之前先经主人确认；复核只在主人要求时做 | 2026-10-09 | 0041 | 无 |
| [0045](0045-the-final-proof-is-the-newest-worker-run-at-head.md) | 关票的最终证明是 `HEAD` 上最新的一次 worker 运行：关票接受的和关票评论引用的是同一次；第一次运行之后没有新提交时，就是第一次运行 | 2026-10-09 | 0026 | 无 |

0002 与 0004 讲的界面 QA 已挂起：技能在 `deprecated/ui-qa`。设计系统是否被遵守、页面是否画对，由 pull report（`mmw-v3/skills/mmw-mode/playbooks/pull-a-design.md` 的 **Design problems in the report**）与用户的 sign-off（`mmw-v3/skills/mmw-mode/playbooks/design-in-claude-design.md` 第 8 步 **Take the sign-off, then pull**）承担，由 0029 定。0011 推翻的是 #115「真状态加真容器」，不是 0002 / 0004。

## 编号在本仓库以外仍会出现

issue tracker、commit message，以及 `docs/` 下的历史材料仍写着旧编号，而**同一个号在不同时期指的不是同一份**。这套编号重排过两轮，所以历史文本里可能是两代中的任意一代。遇到本目录以外的 ADR 编号，先按这张表翻译：

| 2026-08-26 之前写的 | 2026-08-26 那一轮写的 | 现在 |
| --- | --- | --- |
| 0002 | 0002 | 0001 |
| 0015 | 0012 | 0002 |
| 0018 | 0015 | 0003 |
| 0019 | 0016 | 0004 |
| 0023 | 0017 | 0005 |
| 0024 | 0018 | 0006 |
| 其余任何编号 | 其余任何编号 | 已删除，没有对应 |

两列旧编号互不重叠地共存：同一个 `0015`，写在 8 月 26 日之前指的是现在的 0003，写在那之后指的是现在的 0002。分不清是哪一代时，看写下它的那条 commit 或 issue 的日期。

2026-10-08 两条分支各自写了 0039 和 0040。spec #893、#894 和它们的票里写的 `0039` 是现在的 0041（feature map），`0040` 是现在的 0042（一个仓库多个产品）。同一天其他地方写的 0039、0040 指的就是现在的 0039、0040。

## 删过哪几批

- **2026-08-26，12 份。** 主题依附上一代 `mmw` CLI（`mmw artifact path`、`mmw task`、`mmw domain`）与 `mmw/skills-src/`，两者都已进 `archive/`，活层零调用；产物落点合同、产物引用、索引由命令算出、机械校验的两条正则、界面 QA 依赖装进 runtime 这几条，在 v2 里都没有承接对象。同批删掉 `docs/specs/` 与 `docs/assets/`，随后删掉 `docs/plans/`。
- **更早，两批。** 一批是上一轮重编号时并掉的三份，一批是落地后被整批撤回的三份。两批都没有对应文件。
