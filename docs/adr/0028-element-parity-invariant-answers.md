---
date: 2026-09-20
amends: [0011]
---

# 外观按 data-ui id 做 element parity，App 页纳入 story；boundary test 断言四列；product answers 只写不变要求；judge 不遮不藏；journey 第二遍弄坏一个接口

0011 的「组件级离线判定、整机只跑少量旅程」仍成立。外观改为两侧按 `data-ui` id 配对，比存在、可见、文字、尺寸与位置、样式值（element parity），`App · ` 页与 `Component · ` 页同一标准；像素差异图只作证据。控件是否符合合同，由产品自己的测试在同一条里断言 `calls`、`shows`、`next`、`on_failure` 四列（four-column boundary test），替换产品仓库指名的 outbound call module。`.mmw/` 的 product answers 只写每个回答必须保证什么，不按产品类型给做法。story judge 不再遮罩显示值、不再藏控件；带非空 `volatile_values` 或带 `trigger` 的 `retired_ids` 直接拒绝。带 `--break` 的 journey 第二遍在真实产品上只弄坏 CHECK 点名的一个接口，必须失败。#446 的四项决定记在本份、不另写 ADR：行按 `data-ui` id 识别；组件联动写成 cross-component row；删 `target.kind`；合同不再带让差异消失的键。

证据是 spec #444：工作监控指标 13px 对 26px 只占截图 2.7% 被像素阈值放行；`volatile_values` 与带 trigger 的 `retired_ids` 让差异从比较里消失；boundary 只证明了 `calls`；journey 停掉产品的第二遍让弱断言同样失败因而通过。

## Considered Options

- **继续 0011 的树加像素、保留遮罩与藏控件。** 否决。清单不比字号颜色位置；像素按面积稀释；遮罩和藏控件让没实现的差异通过。
- **product answers 按产品类型写做法。** 否决。合同票会把某一个项目的形状抄成默认，而桌面应用、服务端渲染与 SPA 满足同一保证的路径不同。
- **全部 journey 的第二遍都停掉产品。** 否决。只看标题的脚本在产品停掉时同样失败，负控制不再说明脚本读到了结果。
- **#446 的四项决定另写一份 ADR。** 否决。这四项与本份同一次方案划定，拆开会让「合同怎么指认控件」与「judge 按什么比」分成两份决定。

## Consequences

- 一张界面票的外观判据仍不起产品、不 seed、不走路由；比较单位从树和像素换成带 `data-ui` id 的元素。
- 消费仓库的 story 页必须带 `data-ui` id，且不得渲染 Claude Design 运行时；screen contract 必须有 `locale`，不得再靠 `volatile_values` 或带 trigger 的 `retired_ids` 过关；`.mmw/target.json` 必须声明 `harness_markers`；`.mmw/harness/` 必须实现 break switch。迁移说明在 `mmw-v2/downstream-notes/` 的 449、450、453、454、455、456。
- 半年后再发明「按截图面积判外观」或「按产品类型写验收做法」的人，读这一份。
