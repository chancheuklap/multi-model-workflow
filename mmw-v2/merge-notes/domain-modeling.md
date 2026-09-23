# domain-modeling

源目录：`mmw-v2/upstream/skills/engineering/domain-modeling/`

## 逐段意图

### ADR-FORMAT.md

| 段落 | 我们的意图 |
| --- | --- |
| `Status` frontmatter（`proposed \| accepted \| deprecated \| superseded by ADR-NNNN`） | 文件本身没改，但本仓不用这个键表示改写关系：ADR 用自己的 `amends:` frontmatter，加 `docs/adr/README.md` 的「改写了哪几份」「被哪几份改写」两列。上游改这一行的写法 → 收上游，本仓的两处照旧 |
| `## Template` 一节（模板是「标题加一到三句」，并写着 `That's it. An ADR can be a single paragraph.`） | 文件本身没改，但本仓的 ADR 形状是固定的，不是「一句也行」：写在 `docs/adr/README.md` 的 `## 一份 ADR 长什么样`（`date` 与 `amends` frontmatter，`# ` 标题加其下一段就是决定）。上游改这个模板 → 收上游，本仓的形状照旧，以那一节为准。`SKILL.md` 里 `If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md]` 那一句仍把读者指到这个模板上；上游正文不改，连接放在正文之外：`docs/agents/domain.md` 的 `## Flag ADR conflicts` 一节写明本仓的 ADR 照 `docs/adr/README.md` 那一节写，根 `AGENTS.md` 的 `## External References` 也指向同一份。改上游正文换来一句话，代价是每次 `git subtree pull` 都在这一行冲突 |
| `## Optional sections` 一节（把 `Considered Options` 与 `Consequences` 列为可选，并写着 `Most ADRs won't need them`） | 文件本身没改，但本仓这两节是必需的，也不写 `status:`（`docs/adr/README.md` `## 一份 ADR 长什么样`）。上游改这一节 → 收上游，本仓这两节照旧必需。同上一条那处残余：`SKILL.md` 指过来的仍是这份上游模板，本仓不改它 |
