# project-context.md 本轮要改的术语

发布 `/mmw-retrieval` 英文候选时，替换 `docs/context/project-context.md` 里检索相关条目的英文名。领域模型条目的含义不动。

**structure graph**（现用名 `结构图谱`）：
由 `mmw graph build` 构建的本机派生物。
_Avoid_: Context Map、Wayfinding 的 map

**structure candidate**（现用名 `结构候选`）：
Serena 或 Graphify 返回、尚未回到当前源码验证的关系。
_Avoid_: 代码事实、已验证关系

**`mmw graph status`**：
报告结构图谱是 `FRESH`、`STALE` 还是 `MISSING` 的命令。
_Avoid_: 查询成功、文件修改时间
