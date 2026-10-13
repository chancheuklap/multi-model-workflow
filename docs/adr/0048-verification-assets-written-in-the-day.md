---
date: 2026-10-13
amends: [0029, 0030, 0041, 0042, 0044]
---

# feature map 放在产品仓库的 `.agents/skills/verify-<product>/features/`，和 e2e test 一起白天写、主人要求时维护复核，夜里只读

主人在 Claude Design 定稿的设计包是界面的标准答案。白天的会话照代码记录已有功能，照设计包为新功能写 e2e test，连同 `verify-<product>` 和 feature map 在开夜前提交。夜里的 worker 只跑票上的 CHECK；测试或设计包本身错了，开 `contract` 子票退回白天。维护复核只在主人点名时做。这份决定采用 spec #984 第 18、19、20 节和 `docs/research/ui-acceptance-v4/plan.md` 的方案。

## 改写的决定

- 0041 的家 `docs/features/<产品>/` 改为 `.agents/skills/verify-<product>/features/`。保持为真的三样，lint、同一提交更新、定期复核，由白天写、主人要求时维护复核、夜里只读取代。
- 0044 第 2、3、4、6 条假定 worker 拥有功能文件，由「白天写、夜里只读」取代；第 1 条的 lint 由维护复核的 doc drift 接替，接受 map 与测试不一致在白天才被发现。第 5 条的 retro 去向不在本次改写范围内。
- 推翻 0042 `## Considered Options` 第 3 条对「照 pstack 给每个仓库生成一个验证 skill」的否决。原决定要避免同一套验收重复维护；现在 e2e test 本身就是仓库资产，`verify-<product>` 只是入口文档，生成后直接提交，维护由主人点名，成本只在主人要求时发生。
- 0029 要求设计包「连同 pull report 一起提交」，本地改动由拉取报告写明。spec #982 删除 pull report；设计仍在 Claude Design 改，由 pull 写入仓库。
- 0030 的示例数据文件约定和 `## Consequences` 中模板带 `ui-ids.md` 的约定由 spec #982 删除。一种情况画一页，设计里的数据只用来画图，数据格式由数据库和代码决定。

## Considered Options

- worker 夜里写或改 e2e test。否决。`docs/research/ui-acceptance-v4/plan.md` `## 规矩（主人定的，方案不越过）`第 3 条把测试放在白天，写产品的人不判自己；夜里只读。
- 新增 verifier。否决。`docs/research/ui-acceptance-v4/plan.md` `## 规矩（主人定的，方案不越过）`第 4 条和 ADR 0026 保留 worker 自己运行 criteria、reviewer 独立审查一次的分工，不再加会话。
- 让 Tests 轴审 e2e test。否决。`docs/research/ui-acceptance-v4/intents.md` `## 已经否决的（不要再提回来）` 已否决让 reviewer 管界面验收；测试在开夜前证明，夜里不重判。

## Consequences

- Isolate 的两层是每次产品运行独占端口和数据目录、每个检出独占后台栈。它不是加回产品槽位，没有登记和租约。
- e2e test 归产品的验证系统，不进 `TESTING.md`、`scripts/check`、spec 的 Testing Decisions 或票的 Seam。
- feature map 每个功能一个文件，没有手写总表或状态字段；文件开头说明功能名、入口和测试文件，未完成的工作只记在票上。
- `verify-ticket.py --closeout` 把 `EVIDENCE: pending` 换成运行记录是现有行为，不增加测试标签或新机制。
