---
date: 2026-09-22
amends: [0029]
---

# design system 由 Claude Design 里的 agent 从产品代码提炼，只装外观；设计页不加载产品代码

一个产品要在 Claude Design 里设计时，它的 design system 由 Claude Design 自己的 agent 在 design system 项目里建。MMW 只做三件事：把说明写进那个项目的 `CLAUDE.md`、指明源代码和示例数据在哪、事后检查结果。design system 只装外观：变量（颜色、字号档位、间距档位、圆角、阴影）、字体与图标、可复用零件（一个类名加它的变体，一张卡片展示全部状态）。它不装页面区块、示例数据和产品逻辑。代码里不一致的数值和写法全部统一，每处统一记进它 `readme.md` 末尾的 `Unifications` 表，产品代码照这张表跟上。设计页只用 design system 和自己的标记画，不加载任何产品代码；每页的示例数据放在设计项目自己的数据文件里。

## 要修的是什么

任务板试点里，MMW 的本地 agent 自己建 design system：先把产品每块标记改写成 46 个 React 组件、连同产品逻辑和示例数据上传；返工一次后又把产品样式表按页面区块切开上传。两次的结果都是产品前端的副本。设计页挂这些组件、调用产品逻辑，于是 element parity 拿产品和产品自己比，44 个场景全过；用户在编辑器里改不动页面，想改外观得先改代码。一致性本该由验收在产品一侧对照设计去查，却被做成了在设计一侧照着产品去复制。

## Considered Options

- **本地 agent 按规则提炼 design system，再上传。** 否决。归并档位、合并零件是设计判断，用户要在过程中拍板；在 Claude Design 里由它的 agent 做，用户当场看到、当场定。本地两次都做成了产品副本。
- **design system 装 React 组件，设计页挂组件。** 否决。组件里的标记编辑器进不去；Claude Design 内置的 Classical 没有一个 React 组件。React 组件只适合本身就是 React 组件库的产品，由 Claude Code 的 `/design-sync` 同步。
- **照原样记下代码里的不一致，不统一。** 否决。design system 的意义就是一套统一的外观；照抄不一致只是把产品的现状换个地方存一份。
- **仓库里保留一份 design system 源目录。** 否决。那是第二个源头，与 0029 的“设计的唯一源头是 Claude Design 项目”冲突。

## Consequences

- design-pages 的 `references/design-system.md` 改为：何时、从什么建（已有产品的生产代码、原型胜出方案、定稿的设计页；新产品在第一步没有来源），由谁建，怎么交给 Claude Design 的 agent，怎么检查。`check_design_system.py` 与 `build_ds_bundle.py` 删除。
- 已有产品迁入 Claude Design：先建 design system，再由 Claude Design 的 agent 用它把每个区域重画成设计页；第一次 pull 后，element parity 逐个点名统一带来的差异，由票把产品改到设计。
- 设计项目 `CLAUDE.md` 模板增加示例数据文件与 `ui-ids.md` 两条约定；story adapter 从设计页自己的数据文件取场景输入。
