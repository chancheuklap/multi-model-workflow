# delivery-workflow.md terms this round changes

Publish `/mmw-research` English candidate, then change these entries in `docs/context/delivery-workflow.md`. Do not patch the live leaf until then.

**research** (update):
Findings `/mmw-research` saved under one research directory. Each Explore agent writes one findings file. A `wayfinder:research` ticket saves without asking; otherwise the user decides. Saving does not mean downstream must cite it.
_Avoid_: investigation, artifact, 调查资产, 调查结果, 主 agent 综合

**research 索引** (update):
`README.md` in that directory. The main agent writes it. It records the question and lists the files in the directory. Downstream names this file and reads the files it lists. It is not the findings.
_Avoid_: 资产索引, 调查索引, research 报告, 章节指引

**research 目录** (update):
The directory created only after save. It contains the research 索引 and the findings files Explore wrote.
_Avoid_: investigation 目录, artifact 目录, 调查目录

Drop on publish: **research 报告**, **research 配套文件**, **章节指引**. There is no `report.md` and no section map. Each Explore's Markdown file is a findings file, listed by the index.

Leave **research 路径**, **点名**, and **evidence** as they are this round. `research 路径` still uses the topic as the 类别内细分. `点名` already says: read the named index and the files it lists. `evidence` still names `raw/` under a research directory; that belongs to the dropped `EVIDENCE.md` flow and waits for a later round.
