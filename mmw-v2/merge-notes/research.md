# research

源目录：`mmw-v2/upstream/skills/engineering/research/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 正文开头两行（全文没有小标题）：上游的「Spin up a **background agent** to do the research, so you keep working while it reads.」与「Its job:」 | 能力改动：删去派 agent 的那一句，「Its job:」改成不指代 agent 的引导语「To research a question:」；三步正文与 `description` 不动。理由：能力技能不写由谁来执行，要不要另开一个上下文由调用方决定（`mmw` 技能的 `## Subagents`；playbook **Research a question** 的 **Run the research** 在本会话里读来源）。照原句，一个已经被派出来做调研的会话还会再派一层 agent，这是上游 mattpocock/skills #530 记下的嵌套派发；`dispatch.sh research <n>` 起的 `researcher` 会话本身就是那个被派出的会话。上游改这两行的其余措辞 → 收上游，派 agent 的那一句仍不收；上游自己去掉派 agent 的写法（例如改成由调用方决定，或修掉 #530）→ 取上游，删掉这一行。`description` 末尾「or reading legwork delegated to a background agent」不改：它说的是用户想要什么时用这个技能，不让技能自己派 agent，改它只会多一处与上游的冲突 |
