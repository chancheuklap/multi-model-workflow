# 216-story-judges

## 改了什么

界面验收不再把整个跑起来的产品摆进每个设计场景去比。外观与逐字文案由 `story-parity.py` 在组件级离线判定；控件接线由 `boundary-check.py` 跑产品自己的测试两遍（第二遍 `MMW_NEGATIVE=1` 必须红）；整机只跑 `journey.py run <name>` 点名的旅程。`wiring-check.py` 删除。`visual-parity.py` 不再比较运行中的产品。`.mmw/target.json` 不再答 `reach` / `transport_off` / `transport_on`。

## 哪些产物失效

- screen contract：仍写行上 `observe` / `drive` / 定位钉、非 App 页的 `route`、`scenes` 上除 `page` 以外的到达字段、或顶层机制表的，lint 从绿变红。target trees 随合同一起，哈希检查照旧。
- ticket 的 `CHECK:`：`wiring-check.py --contract … --rows …` 和整机 `visual-parity.py --contract … --mount …` 不再是这套工具能驱动的形状。界面票改为 `story-parity.py --pages <mount,…>`（`EXPECT: STORY OK n/n`）和 `boundary-check.py --run …`（`EXPECT: BOUNDARY OK n/n`）；旅程改为 `journey.py run <name>`（`EXPECT: JOURNEY OK <name>`）。
- `.mmw/target.json`：仍写 `reach` / `transport_off` / `transport_on`、或缺 `stories` 的，`target --check` 从绿变红。
- 两条旧守卫：`test_chameleon_handoff_styles.py`（把原型 stylesheet 逐字节当成产品需求）和 `test_chameleon_reach_write_path.py`（为整机到达而写的写路径）。reach 脚本、为判官加的 `/api/dev/` 桩路由、为 class set 判官加的 `data-screen` 空 wrapper，同批作废。

## 怎么迁

消费仓库的接管归第二份 spec（agentflow #700），不在本仓改那些票。形状：

1. 重导交接包，让每个 `scenes.json` 场景带上 `data`。
2. 按 `lint_contract.py` 点名的已删字段改 screen contract；界面票的 `CHECK:` 改成上一节的三条形状。
3. `.mmw/target.json` 填 `stories`，删 `reach` / `transport_*`；产品答案集中到 `.mmw/harness/`、`.mmw/journeys/`、`.mmw/stories/`。
4. 删掉那两条旧守卫、reach 脚本、dev 桩路由，以及只为判官存在的空 wrapper。展示组件从入口可达的模块不含夹具。
