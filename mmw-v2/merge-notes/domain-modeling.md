# domain-modeling

源目录：`mmw-v2/upstream/skills/engineering/domain-modeling/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 开始写文档的那一句 | 追加一句：用 `readable-docs` 技能写，落盘/发布前跑它的 claim-checker。上游改这句的措辞或位置 → 收上游，把我们这一句接回新位置。上游把写文档这一步拆成多句 → 接在真正落笔的那一句后面。其余段落我们没改，全取上游 |

### CONTEXT-FORMAT.md

| 段落 | 我们的意图 |
| --- | --- |
| 「**Keep definitions tight.** One or two sentences max.」 | 文件本身没改，但本仓不守这一条：根 `CONTEXT.md` 兼作 interface record，命令签名、常量表、结构化输出的固定形状都登记在里面，好几条不止一两句。上游把这条写得更硬（例如加机械校验）→ 收上游，本仓仍然不守，在这里记着就够 |

### ADR-FORMAT.md

| 段落 | 我们的意图 |
| --- | --- |
| `Status` frontmatter（`proposed \| accepted \| deprecated \| superseded by ADR-NNNN`） | 文件本身没改，但本仓不用这个键表示改写关系：ADR 用自己的 `amends:` frontmatter，加 `docs/adr/README.md` 的「改写了哪几份」「被哪几份改写」两列。上游改这一行的写法 → 收上游，本仓的两处照旧 |
