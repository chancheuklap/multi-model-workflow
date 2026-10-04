# Mission: 把 MMW 迁移到 pstack 的结构，这一次做成

## Why
MMW 向 pstack 结构的迁移已经失败两次，两次都卡在半路、留下一团乱麻，最后整体撤回。原因是没有真正弄懂 pstack 每种组件什么时候被创建、什么时候被使用、文档该怎么写，也没有弄懂 MMW v2 自己的设计理念，于是把 MMW 拆散后硬套成 pstack 的样子。这一次先学懂两边，再动手。

## Success looks like
- 能说出 pstack 每种组件由什么文件组成、文档结构、每一部分写什么，并对着原文核对
- 能说出每种组件在一次任务里什么时候被读、什么时候被创建
- 能说出 MMW v2 每个部分解决什么问题、依赖什么假设
- 能对 MMW v2 的任何一段文字或一个脚本判断：迁过去以后它属于哪种组件，或者为什么不迁
- 每一块迁移在写进源文件之前，先画进课程，由主人看过认可

## Constraints
- 主人不读代码，只看课程页和回复；图优先，文字只说图说不了的
- 依据只用原文：`mmw-v3/upstream-pstack/`（pstack 0.15.9，cursor/plugins `e43c7ee`）、`mmw-v3/upstream-mattpocock/`、现役 MMW v2
- 前两次迁移的成果整体不认；经验教训和工具可以拿来用，但要逐件说明来源

## Out of scope
- 现在就改 MMW v2 或安装版
- pstack 里与 MMW 无关的部分（benny 自动化包、make-bot-ui）的细节
