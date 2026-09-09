# domain-modeling

源目录：`mmw-v2/upstream/skills/engineering/domain-modeling/`

## 逐段意图

### CONTEXT-FORMAT.md

| 段落 | 我们的意图 |
| --- | --- |
| 「**Keep definitions tight.** One or two sentences max.」 | 文件本身没改，但本仓不守这一条：根 `CONTEXT.md` 兼作 interface record，命令签名、常量表、结构化输出的固定形状都登记在里面，好几条不止一两句。上游把这条写得更硬（例如加机械校验）→ 收上游，本仓仍然不守，在这里记着就够 |

### ADR-FORMAT.md

| 段落 | 我们的意图 |
| --- | --- |
| `Status` frontmatter（`proposed \| accepted \| deprecated \| superseded by ADR-NNNN`） | 文件本身没改，但本仓不用这个键表示改写关系：ADR 用自己的 `amends:` frontmatter，加 `docs/adr/README.md` 的「改写了哪几份」「被哪几份改写」两列。上游改这一行的写法 → 收上游，本仓的两处照旧 |
| `## Template` 一节（模板是「标题加一到三句」，并写着 `That's it. An ADR can be a single paragraph.`） | 文件本身没改，但本仓的 ADR 形状是固定的，不是「一句也行」：`docs/adr/` 下 17 份，17/17 第 2 行是 `date:`，16 份带 `amends:` frontmatter，标题行之后那个无标题段落才是决定。上游改这个模板 → 收上游，本仓的形状照旧，以 `docs/adr/` 下现存的 ADR 与 `docs/adr/README.md` 这份索引为准。一处残余，记录，不修：`SKILL.md` 里 `If any of the three is missing, skip the ADR.` 那一句仍把读者指到这个模板上，一个通过这份技能写 ADR、又没先读 `docs/agents/domain.md` 的 agent 会照它写。接受的理由就是本条的处置本身——改上游正文换来一句话，代价是每次 `git subtree pull` 都在这一行冲突 |
| `## Optional sections` 一节（把 `Considered Options` 与 `Consequences` 列为可选，并写着 `Most ADRs won't need them`） | 文件本身没改，但本仓这两节是必需的：17/17 有 `## Considered Options`、17/17 有 `## Consequences`、0 份有 `status:`。上游改这一节 → 收上游，本仓这两节照旧必需。同上一条那处残余：`SKILL.md` 指过来的仍是这份上游模板，本仓不改它 |
