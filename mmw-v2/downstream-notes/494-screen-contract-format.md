# 494-screen-contract-format

## 改了什么

screen contract 的 `trigger` 改为控件的 `data-ui` id（字符串），不再记 role 与 accessible name。同一控件的不同状态靠 `precondition` 分行；列表里重复的部件只有一行；会变的数值放进 `shows`。

顶层不再有 `target`（含 `target.kind`）、`volatile_values`、`readme_dispositions`；`pages.<page>` 不再有 `route`。`retired_ids` 条目只留 `id` 与 `note`（日期与裁决），不再有 `page` 与 `trigger`。`locale` 必填，BCP 47 语言标签。新增 `states`：本产品允许出现在 `next` 的领域状态名，lint 只认这份清单。`App · ` 页上「A 区域的操作影响 B 区域」写成 cross-component row，带 `app: "<App · 页名>"`。

lint 对仍出现的已删键报错，并指向本说明。

## 哪些产物失效

screen contract：

- 本仓库 `docs/specs/task-board/screen-contract.yaml`：222 行仍按 role 与 accessible name 识别；有 `target.kind: web-spa`；`App · 任务板.dc.html` 带 `route`；没有 `locale`；仍有 `readme_dispositions` 与空的 `volatile_values`。
- agentflow 工作监控 `docs/specs/work-monitor/screen-contract.yaml`：106 行仍按 role 与 accessible name 识别；有 `target.kind: web-server-rendered`；`App · 小刺猬裂变.dc.html` 带 `route`；没有 `locale`。同仓库桩合同 `prototypes/work-monitor/710/EXP/contract.yaml` 同样带 `target.kind`、没有 `locale`。
- 变色龙的现役合同：同样的旧键（`target.kind`、按 role 与 accessible name 的 `trigger`、可有 `route` / `volatile_values` / `readme_dispositions`、`retired_ids` 带 `page` 与 `trigger`）。本机 checkout 里没有它的 `screen-contract.yaml`；迁移在变色龙重做时另开。

这些合同上，lint 从绿变红。story criterion 在缺 `locale`、或仍带非空遮罩键时也会退出 2（见 `454-story-inputs-and-refusals.md`）。

ticket 的 `CHECK:` 形状不因本票改变。`.mmw/target.json` 的运行时字段不因本票改变。索引行由 #495 加。

## 怎么迁

打开 consuming repository 的 `docs/specs/<effort>/screen-contract.yaml`：

1. 顶层写 `locale:` 一个 BCP 47 标签。删掉 `target`、`volatile_values`、`readme_dispositions`；从每个 `pages.<page>` 删掉 `route`。
2. 每一行的 `trigger` 改成该控件的 `data-ui` id（从新 skeleton 抄）。同一控件的禁用、已添加等状态各写一行（禁用：`calls: [none]`，`next: stay`）；列表重复项合成一行，数值进 `shows`。
3. `retired_ids` 只留 `id` 与 `note`。
4. 领域状态名列入 `states`；`next` 不再自由引用领域文档里的词。
5. 每一处「A 区域影响 B 区域」在对应 `App · ` 页加一条 cross-component row，带 `app:`。
6. 用本仓库的 `lint_screen_contract.py` 对着新 skeleton 跑到零 error。合同文件本身的改写不在本票：任务板在任务板试点 spec；工作监控与变色龙另开。
