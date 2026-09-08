# 298-scene-data-from-the-page

## 改了什么

场景数据导出的输入从交接包的 `src/*.py` 换成包里的 `.dc.html`。一页的构建源不是它的数据源：app page 按 porting 规程就是手写的、没有 `src/*.py`，在 Claude Design 里直接写的页更是结构上不可能有源，而源与下载下来的页可以各自漂移。现在 `export_scene_data.py` 解析包里的页——`data-props` 的默认值垫底、场景的 props 覆盖，页里 `<script src>` 声明的脚本按序喂给 Node——再照 `support.js` 自己的 `evalDcLogic` 跑那页的类体（构造 → `componentDidMount` → `renderVals`）。`DC_FX`、`DC_FX_FILE`、`DC_FRAME` 三个环境变量从这条路上消失。

porting 侧另一件：CSS 压平那一步（原第 6 步）整步删除，换成写组件时就按 Claude Design 编辑器能解析的形状写，`selector_check.py` 在第 4 步守着。`flatten.py`、`collect_dom_classes.js`、`mkallharness.py` 删除。

## 哪些产物失效

- **target trees**：本次改动本身不动 `scenes.json`，但重导是必要的——旧导出给没有 `componentDidMount` 的页凭空塞了 `state.fx`，那是真页在浏览器里没有的字段。重导后 `scenes.json` 变，`docs/specs/<effort>/targets/<page>.aria` 与 `.classes` 头部的 `# scenes.json sha256=` 失配，`lint_contract.py` 从绿变红。screen contract 本身不变：`scenes` 只写 `page`，`data` 不进合同。
- **ticket 的 `CHECK:`**：不变。判官读的是 `scenes.json` 的 `data`，形状（`{state, vals}`）没动。
- **`.mmw/target.json`**：不变。
- **只为导出而写的 shim `src/*.py`**：为一个没有源的页补写的、只带 `PROPS` 与 `LOGIC` 的源文件，现在什么也不喂，删掉。agentflow 的 `prototypes/hedgehog-boss-console/518/claude-design/src/App · 小刺猬裂变.py` 是这一类。

## 怎么迁

1. 重导：拿着 claude-design-blocks 技能的 agent 从它的 `scripts/` 就地跑 `export_scene_data.py <交接包>`。包里 `.dc.html` 齐全就够，`src/` 不参与。
2. 目标树按 align-screens 第 6 步重生成（`extract_skeleton.py --targets`），哈希跟上。
3. 删掉只为导出而写的 shim `src/*.py`。
4. 已有项目的 CSS 不受影响：压平步删除只管下一次 port。既有包里编辑器点不中的选择器是另一件事，清单见 agentflow #713。
