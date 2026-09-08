---
date: 2026-09-08
amends: []
---

# 界面等价在组件级离线判定，整机只跑少量旅程

界面是否与设计稿在外观和逐字文案上等价，在组件级离线判定：交接时把每个场景的数据写进 `scenes.json`，产品的展示组件拿同样的数据渲染成 story，story 判官用归一化后的 accessibility tree 和亚格对齐后的像素与设计页的离线渲染比。控件是否发出合同 `calls` 列的请求，在 API client 边界断言，并配一道跳过点击必须变红的机械 negative control。整机只跑 owner 指定的三到五条真实旅程。#115 的决定——视觉验收必须走「真状态加真容器」、由通用驱动器在受控时钟下把整个产品摆进每个设计场景——被这份推翻。

证据是变色龙 S3 上 2026-09-03 到 09-07 的账：七张界面票关了一张；流水线自己的合同、驱动、判官和 harness 占了 25 张子票里的 22 张；#640 的 worker 为了让 class set 判官通过，把 mount 挪到空 wrapper、塞入隐藏节点。缺陷集合是三个开集的乘积（UI 习惯 × 设计状态 × 原型 DOM），每个补丁只关掉其中一个点。组件级离线比对在同一批场景上树全等、像素差 0 到 0.085%，约 3 秒。

像素比较的亚格对齐和 `around:` 按元素框内差异格数排序，是 #215 已落地的部分，这份保留。ADR 0002、0004、0008 不受影响。

像素和树的比较原语留在 `visual-parity.py`，由 `story-parity.py` 导入；该文件不再比较运行中的整机产品。

## 被这份删掉的东西，和谁接管

| 删除 | 接管者 |
| --- | --- |
| `wiring-check.py` 及 `references/wiring-check.md` | `boundary-check.py` 与消费仓库的合同测试 |
| `visual-parity.py` 的 parity、`--addressing`、`--shows-perturbation` 模式 | `story-parity.py`；`shows` 的字段来源由 Spec axis 核对 adapter；寻址由旅程覆盖 |
| `screen_driver.py` 的 `Adapter` 及四个子类、`observe` / `evaluate*`、`perform`、定位钉、`undrivable_lines`、双预算等待 | 旅程脚本用 Playwright 原生 API；story 页面用假定时器；设计侧仍跑 200 ms 虚拟时间 |
| 合同的画面轴、`--pin`、scene 分区 lint | align-screens 第 5 节的合同格式；每页一条 story 判据、每有调用的行一条边界判据 |

## Considered Options

- **继续 #115：真状态加真容器，通用驱动器解释合同。** 否决。变色龙 S3 证明这个形状把流水线自己的缺陷乘开，worker 会被逼改产品迁就判据。
- **把比较原语搬进 `story-parity.py`，删掉 `visual-parity.py`。** 否决。story 判官已经按名导入这些函数；搬一次是重写不是删除，`test_visual_parity.py` 的像素用例与 `render_only` 会无谓分叉。文件留下的是库，命令行退出 2 并点名 `story-parity.py`。

## Consequences

- 一张界面票的外观判据不起产品、不 seed、不走路由。
- 消费仓库里仍写 `wiring-check.py` / 整机 `visual-parity.py`、或 `.mmw/target.json` 仍写 `reach` / `transport_*` 的产物失效；迁移路径在 `mmw-v2/downstream-notes/216-story-judges.md`。
- 半年后再发明「必须把整个产品摆进每个设计场景」的人，读这一份。
