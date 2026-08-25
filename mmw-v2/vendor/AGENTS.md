# mmw-v2/vendor

第三方仓库的技能，逐字副本。和 `upstream/`、`skills/` 里的技能平级，一样经 `skills.txt` 的 `vendor/<名>` 装进宿主。

`draw-diagram` 调用这里的两个：`html-diagram` 定形态，`diagram-design` 出图。

## 关键约定

- 不改这里任何一个字，一个文件都不加。`sync.sh` 每次整目录删掉重写，改动一律丢失。对上游的偏差写进 `mmw-v2/skills/draw-diagram/SKILL.md` 的裁决段。
- 加减 vendor 只改 `sync.sh` 顶部的 `SOURCES`，同时改 `skills.txt`。末段声明这份 vendor 指向本目录之外的哪些技能；校验要求实际断链与声明完全相等，上游新增或去掉一条跨技能引用就会红。
- `html-diagram` 声明的那条断链是 `../design-artifact/SKILL.md`。`effective-html` 的六个技能只取了它一个：`html` 是隐式路由器会抢触发，`html-plan` 的契约是保留原文，`html-wireframe` 和 `html-prototype` 做的是界面不是图，`design-artifact` 的视觉方向与 `diagram-design` 的设计系统打架且带 `tot.page` 外发动作。
- `sync.sh` 走 `gh api` 加 codeload，不走 git 远程：维护者机器上 `github.com:443` 被代理挡着，`git clone` 跑不通。
