# 四栏 task 与角色报告不写文件

派发 subagent 时，四栏 task 原来必须先写成文件再交给 `mmw dispatch --task <文件>`，Codex 路径还会把角色报告额外写一份到 `.dispatch/`。现在两者都不写文件：`mmw dispatch` 改成从标准输入或 `--task-text` 接收正文，`codex exec` 去掉 `-o "$report"`。理由是这两份文件都没有必须落盘的读者——四栏 task 的正文最终被 adapter 用 `jq --rawfile` 读进 params 交给 subagent，subagent 从不打开那个文件；角色报告的内容同时走 stdout，主 agent 从后台 Bash 的输出里已经拿到一份。

## Considered Options

- **保持落盘，把四栏 task 和角色报告一并规定进 scratch。** 否决。它给两份用完即弃的中间物各定一个落点，每个 agent 都要记住这两个目录，`/mmw-closing` 还要为它们写清理规则。
- **只在需要它的那条路径上落盘：Claude Code 的 gpt 族写，其余宿主不写。** 否决。它让落点按宿主名称分叉，技能正文就得写两种路径，违反仓库禁止按宿主分支的规定。这个选项之所以被提出来，是因为现状本来就是这样——Pi 和 Cursor 的主路径直调原生 subagent，四栏 task 从头到尾只是一个字符串，根本不落盘。

## Consequences

- `mmw dispatch` 的 `--task <文件>` 接口变更，调用它的全部技能源派发动作块跟着改。
- `.dispatch/` 目录消失。`mmw init` 写进 `.gitignore` 的六项减为五项，`/mmw-closing` 的 `.dispatch/` 清理规则删掉。
- 派发进度日志仍然落盘，因为进程结束后它是唯一的诊断材料。它的文件名原来取自 task 文件基名，现在没有这个基名了，改成 `<角色>-<时间戳>`；落点补上名字段与范围段，否则 `/mmw-closing` 删名字段目录时会漏掉它。
- 派发出问题时，没有一份文件记录「主 agent 到底派了什么」。这是本决定放弃的东西：四栏 task 原本可以当派发凭据用。
- 去掉 `-o` 的判断建立在「后台 Bash 输出被截断这个顾虑目前没有证据」之上，不是建立在「已确认不会截断」之上。真出现截断，那是宿主输出通道的问题，不用一个常驻落点去兜。

来源：Wayfinder decision ticket #21「每类 MMW 产物的落点与路径形状」，map #18「MMW 产物归纳与接线合同」。
