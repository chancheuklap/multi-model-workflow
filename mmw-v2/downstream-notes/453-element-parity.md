# 453-element-parity

## 改了什么

`story-parity.py` 现在按 `data-ui` id 逐元素比较存在、可见、文字、尺寸、位置、父元素和五项计算样式。成功行是 `STORY OK <passed>/<total>`；像素差异图仍写入 `--out`，但不决定通过或失败。`Component · ` 与 `App · ` 页使用同一套判定。

产品 story 的组件根元素同时带 `[data-story-root]`、`data-screen="<mount>"` 和 design page 根元素使用的同一个 `data-ui` id；组件内其它被比较的元素也使用 design page 上相同的 `data-ui` id。

## 哪些产物失效

- ticket 的 story `CHECK:` 如果传入 `--max-pct`，命令会拒绝这个参数；`EXPECT:` 如果要求成功行带像素百分比，也不会再匹配。
- handoff package 的 design page 没有 `data-ui` 时，element parity 的字号扰动 negative control 无法证明 judge 能判失败，运行会退出 2。
- consuming repository 的 story 页如果把 `[data-story-root]` 放在组件外的 wrapper，或没有复制 design page 的 `data-ui` id，story criterion 会报 `missing` / `extra`，不能代表该组件。
- screen contract 与 `.mmw/target.json` 的字段没有改变；依赖上述旧命令或旧 story 页面形状的 ticket 与产物失效。

## 怎么迁

1. 在 design page 的每个需要比较的元素上写稳定的 `data-ui` id；重复组件实例可复用 id，judge 按文档顺序配对。
2. 在产品组件的对应元素上复制同一个 id。把 `[data-story-root]` 放到组件自己的根元素上，并让该元素同时带 `data-screen="<mount>"` 与 design page 根元素的 `data-ui` id。
3. 从 story `CHECK:` 删除 `--max-pct`，把成功 `EXPECT:` 改为 `STORY OK <scene × viewport 总数>/<同一总数>`。
4. 运行该 ticket 的 story criterion；逐行修正 `DIFF <mount> <scene> <viewport> <id> <property> …` 点名的元素与属性。`--out` 中的像素差异图只用于人工查看。
