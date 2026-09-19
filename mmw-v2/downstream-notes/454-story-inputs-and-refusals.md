# 454-story-inputs-and-refusals

## 改了什么

`story-parity.py` 两侧浏览器窗口都是合同 `viewports` 的一项；design side 外框是 design page 在该窗口里渲染出的尺寸，不再钉成产品 `[data-story-root]` 的宽高。两侧 locale 都从合同顶层 `locale` 读，缺这个键就退出 2，不回退 `zh-CN`。合同里 `volatile_values` 非空，或 `retired_ids` 任一条带 `trigger`，退出 2。产品 story 页出现 `sc-interp`、`data-dc-tpl`、`data-dc-script` 或 `dc-root` 也退出 2。`--render-only` 执行同样的 `viewports`、`locale` 与旧键拒绝。

## 哪些产物失效

- screen contract 没有 `locale` 时，story criterion 与 `--render-only` 都会退出 2。
- screen contract 仍带非空 `volatile_values`，或 `retired_ids` 里仍有 `trigger` 时，story criterion 退出 2，不再按这些键遮罩或藏控件。
- 产品 story 页如果仍渲染 Claude Design 运行时（`sc-interp`、`data-dc-tpl`、`data-dc-script`、`dc-root`），story criterion 退出 2。
- ticket 的 `CHECK:` 形状没有变；`.mmw/target.json` 的字段没有变。依赖上述旧合同键或旧 story 页捷径的产物失效。

## 怎么迁

1. 在 screen contract 顶层写 `locale:` 一个 BCP 47 标签（例如 `zh-CN`）。
2. 删掉 `volatile_values`；从 `retired_ids` 去掉 `trigger`（只留 id 与 note）。若产品还缺那个控件，把控件改回 Claude Design，而不是靠 judge 藏掉。
3. 产品 story 页只渲染产品组件：不要出现 `span.sc-interp`、`data-dc-tpl`、`data-dc-script` 或 `id="dc-root"`。
4. 重新跑该 ticket 的 story criterion。
