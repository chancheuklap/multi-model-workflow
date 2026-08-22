# to-spec

源目录：`mmw-v2/upstream/skills/engineering/to-spec/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 开始写文档的那一句 | 追加一句：用 `readable-docs` 技能写，落盘/发布前跑它的 claim check。上游改这句的措辞或位置 → 收上游，把我们这一句接回新位置。上游把写文档这一步拆成多句 → 接在真正落笔的那一句后面。其余段落我们没改，全取上游 |
| `## Process` 的第 1 步 | 我们加的整步，把上游原来的 1/2/3 顺延为 2/3/4：用户传了引用就先读全，是 wayfinder 地图时按 Decisions so far 逐张读 resolution comment、读到 prototype 与 research 的结论、Out of scope 原样进 spec；然后判一份还是几份 spec（同一个 seam 归一份，能不分就不分），几份时问用户确认并把划分写回地图的 `## Specs`，只写第一份，发布后回填链接再停。上游改了 `## Process` 的编号或在前面插步 → 收上游的顺序，我们这一步永远排第一（它决定这次到底写几份 spec）|
| 开头「Do NOT interview the user」那一句 | 改成「Do NOT interview the user **for facts**」并指向第 1 步那个唯一交还给用户的判断，免得跟分卷确认自相矛盾。上游重写这句 → 收上游措辞，把这个例外重新挂上去 |
| 模板里 `## Further Notes` 之前的 `## Sources` 节 | 我们加的：一手来源（地图、prototype 分支/目录、research 文件）的链接。`implement` 技能靠这个节名往回读，改名要同步改 `implement`。上游自己加了同类的来源节 → 用上游的名字，同步改 `implement` |
