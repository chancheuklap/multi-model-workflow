<!-- MMW-CONTEXT-MAP-RULES-START -->
## 使用规则

1. 根据 `Contexts` 和 `Relationships` 选择本次涉及的全部 leaf。答复用户或写入文件前读完这些 leaf。
2. 术语归属不明确时，运行 `mmw domain dirs` 取得 `context` 路径并搜索该术语。仍无法判断时询问用户。
3. 使用 leaf 定义的 canonical 术语，避开 `_Avoid_`。共享术语以标有 `authoritative` 路径的主 leaf 为准。
4. 读取 `mmw domain dirs` 返回的 `adr` 路径下与本次范围相关的 ADR。
5. 用户说法、多个 leaf、ADR 或代码现状互相冲突时，明确列出冲突，不得静默覆盖。
6. 长期术语、关系和歧义只写入拥有它们的 leaf。只有上下文集合、所有权或跨上下文关系改变时才修改本 Map。
7. 操作步骤、实施计划、发布状态和一次性调查不进入领域文档。
<!-- MMW-CONTEXT-MAP-RULES-END -->
