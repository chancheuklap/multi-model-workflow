# Investigating · wayfind 前缀阶段 + 颗粒化取证接入(2026-07-22-wayfind-phase)

> 现状取证,不判定方案。范围:阶段引擎、prepare/pin 机制、路由层、design discussion 现状,三镜像同构性。

## 1. 阶段引擎:wayfind 作为 develop 前缀,reads/prev_outputs 零改动

- `pi-plugin/state-schema/routes.json` `presets` 是阶段序列单源;`prepare.sh cmd_new` 从中解析(prepare.sh:80-82 `phases_json=$(jq -c --arg s "$scenario" '.presets[$s]')`)。加 wayfind 的最小面:`cmd_new` 加 `--with-wayfind` flag,置位时 `phases_json='["wayfind"]+.presets.develop'`,非 develop 拒。
- `phase_bindings` 每条 `{load, do, produced, reads?}`。investigate 当前**无 reads 键**。
- prev_outputs 组装(flow.sh:497-505):当前阶段无 reads 时**默认取上一阶段产出**(`phase_outputs[phases[i-1]]`)。wayfind 前缀进 phases 后,investigate 自动拿到 wayfind 产出;无 wayfind 的任务 investigate 是 index 0 → 空。**无需给 investigate 加 reads 键**。
- needs-redirection 的 `--to-phase` 校验目标在 manifest.phases 内(flow.sh cmd_handoff 段),wayfind 入列后自由往返天然可用。

## 2. prepare/pin:scaffold 与提交白名单、布局门全部零改动

- prepare.sh:62 scaffold 只建顶层目录(`docs/design` `docs/issues` `docs/plans` `docs/context` `docs/reviews`);design 子目录由写文档时自建(investigating.md 惯例「目录不存在就建」)。wayfind/ 同此,无 scaffold 改动。
- 提交白名单 = `docs/.gitignore` 只排除 `reviews/`、`*-final-review.md`、`.gitignore`(prepare.sh:66-70)。`docs/design/<slug>/wayfind/` 自动进 git,零改动。
- pin(flow.sh:380-417):produced 通用存在性检查,目录可钉(`[ -e "$top/$pp" ]`);布局门**仅 design 阶段**(要求单文件夹+同名主文档)。wayfind 产出 `docs/design/<slug>/wayfind/` 走通用检查即过,零改动。
- escalate(prepare.sh cmd_escalate):`.presets[develop]` 无 wayfind,bug/small-change 升级路径天然不带,符合预期。

## 3. 路由层落点

- `orchestrate/SKILL.md` 纯路由:Step 1 路由表 + `${SKILL_DIR}/references/scenario/develop.md`。wayfind 触发判据(双条件:终点大致明确 + 决策空间在雾里、单会话装不下)是语义判断,SKILL.md:82 明确「路由是 LLM 语义判断,不要脚本化」——判据写进路由层文档,不写进脚本。
- 值守档:develop 起步 attended(prepare.sh:86-87),wayfind 作为 develop 前缀天然讨论态,零改动。

## 4. design discussion 现状(5b 改写面)

- `references/design/discussion.md`「按需补充上下文」节:当前只有「小缺口四步(锚点区)+ 大缺口读 evidence-campaign.md」两分流,无「在途取证冻结面」概念。
- 该节内嵌 `<!-- BEGIN: gather-context-steps -->` 锚点区(discussion.md:56-61),由 `build/fragments/gather-context-steps.md` 注入,**锚点区内不可手改**;5b 的分流表插在锚点区之前,锚点区原样保留。
- `references/design/evidence-campaign.md` 纪律节:现有「每固化一个结论 commit 一次」「结论必须可追溯」「旁路 spinoff」三条;5b 在此加一条「开打前登记冻结面、打完解锁回灌」纪律。

## 5. 三镜像同构性

- `plugin/`、`droid-plugin/` 的 routes.json / prepare.sh / flow.sh 与 pi-plugin 同构,差异仅在宿主词(工人=Codex/droid exec、状态目录、技能加载路径)与个别行号。wayfind reference 三镜像同文,仅 investigate 调用方式段按宿主各写(pi:`/investigate-internal`;plugin:`Workflow({scriptPath})`;droid:`mmw investigate start`)。
- 版本号:plugin 8.1.3 / pi 9.4.3 / droid 8.0.4(本次落地后再 bump)。

## 6. 测试落点

- `pi-plugin/scripts/tests/test_flow.sh:402-412` 已有冷启动断言(where 首行 RESUMABLE/UNMANAGED 合同);新测试仿其结构:`task new --with-wayfind` 建任务 → 断言 phases 首元素 wayfind、where load=references/wayfind.md → handoff pass 后 advance 到 investigate 且 prev_outputs 含 wayfind 目录;另测非 develop 加 --with-wayfind 报错。
- build/test_build.sh 与 test_shared_refs_sync.sh 不涉及(reference 新增不触发片段注入;三镜像各自独立文本)。

## 7. 已确认的设计输入(用户拍板,2026-07-22)

- 接入 wayfinder 决策地图机制(借机制不直接引用:外部 tracker 权威冲突)。
- 接入颗粒化取证(granular fact-finding):在途取证只冻结依赖分支。
- 明确不做:外部知识问卷(to-questionnaire)。
- 上游参考:mattpocock/skills@ed37663 `skills/engineering/wayfinder/SKILL.md`(map 是索引不是仓库 / decision tickets 与 Not yet specified 分离 / frontier / 每会话一决策 / Plan,don't do / 先建 ticket 再连边 / 指名不指号)。
