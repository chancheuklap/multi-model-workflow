# Retrieval Doctrine · 结构候选与亲验

结构性问题包括：谁调用或引用某符号、什么与什么连接、依赖路径，以及改动影响面。

1. **先拿候选。** Serena 可用时，用语言服务器的引用查询找符号候选；当前仓库存在新鲜 `graphify-out/graph.json` 时，用 graphify `query` / `affected` / `path` / `explain` 找结构候选。按问题选择一个合适入口，不为形式把两个工具都跑一遍。外部依赖、动态图或工具未覆盖面不得冒充完整。
2. **再亲验。** 图/LSP 是派生候选，不是证据。任何写进 finding、plan、investigating report、handoff 或交付物的承重结论，都必须回到目标 checkout 用 `rg`/Read 核对，并给 `file:line` 与原始行；验不过就删除或明确标为未验证。
3. **无损退化。** Serena 不可用、图缺失或过期、查询歧义、或没有适用工具时，直接使用现行 `rg`/Read，不报错、不阻塞。若当前仓库存在 `scripts/dev/knowledge_graph/rebuild.sh`，可选择运行它重建；`graphify-out/graph.json` 的 mtime 早于 `git show -s --format=%ct HEAD` 时视为过期。

这份 doctrine 不授权安装 graphify、启用它的 hook/strict，也不降低各角色原有的证据与引用门。

审查收口方（主线程）收到缺少“结构候选”行的回执，按不合格打回，效力与缺少 `file:line` 验证同级。
