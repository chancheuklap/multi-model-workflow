# docs

交付产物的长期落点：`adr/` 是决策记录；`specs/`、`plans/`、`research/` 和 prototypes 按交付永久保留。不放过程材料（scratch、reviews、out-of-scope）。

- 每个路径的名字段是这次交付的任务分支 slug（最后一个 `/` 之后）；Wayfinder 工作用地图分支的 slug。
- 路径段一律小写的单个安全段（macOS 不分大小写，Linux 分）。
- spec 和 plan 的 frontmatter 必须带 `artifact_refs`，空也写 `artifact_refs: []`。
- frontmatter 只认一个受限 YAML 子集：不要折叠/字面字符串、嵌套映射、锚点、制表符、多行引号；`artifact_refs` 的两级映射列表是唯一允许的嵌套。
- 新建 research 主题或 prototype 变体前先列父目录，已存在就换名；后写的会静默覆盖先写的。
- `adr/README.md`、`specs/README.md` 是生成副本，生成器在冻结的 `mmw/cli/`；权威是命令输出。
