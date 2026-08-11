---
date: 2026-08-11
amends: []
---

# tracker 与仓库文件的权威归属

MMW 的同一份内容常常同时存在于 issue tracker 和仓库文件两处。权威副本在生产这份内容的那一侧，另一侧是 tracker 索引。agent 从 tracker 进入取得关系，再沿精确路径打开权威副本；两侧都不单独作为行动依据。理由是父子关系、阻塞关系、frontier 和认领状态只存在于 tracker，而细节只存在于权威副本那一侧。

## Considered Options

- **仓库文件一律权威，tracker 一律是 tracker 索引。** 否决。agent brief 只存在于 tracker，仓库里没有对应文件，这条判据对它不成立。
- **长期留存的那一份权威。** 否决。issue 和仓库里的产物都长期保留，这条判据在两侧都长期留存时给不出答案。agent brief 与 spec 就是这种情况：agent brief 留在 tracker 上，spec 留在仓库里，两侧都不消失。
- **tracker 索引必须跟随权威副本更新。** 否决。它要求技能反向找出全部引用者，而 MMW 当前没有可靠的反向引用能力。改为：tracker 索引是写下那一刻的快照；引用只在消费窗口内必须有效，执行删除或移动的技能在受影响的位置就地留记录。

## Consequences

- decision ticket 的结论评论是长期产物。`wayfinder:grilling` 与 `wayfinder:task` 两种 ticket 在仓库里没有对应文件，它们的决定只存在于结论评论。
- tracker 正文中被下游按位置读取的节必须固定标题。生产方规定标题字面，读取方引用同一字面。
- spec 发布后，带 agent brief 的原 issue 关闭并挂到 spec issue 底下。这需要 CLI 新增一个动作：给已存在的 issue 设置父 issue。
