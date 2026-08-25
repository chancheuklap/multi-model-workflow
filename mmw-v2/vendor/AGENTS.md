# mmw-v2/vendor

上游技能的只读副本。`system-map` 靠自己目录里的 `vendor` 软链读它们。

## 关键约定

- 不改这里任何一个字。`sync.sh` 每次整目录删掉重写，改动一律丢失。对上游的偏差写进 `mmw-v2/skills/system-map/SKILL.md` 的裁决段。
- 加减 vendor 只改 `sync.sh` 顶部的 `SOURCES`。末段声明这份 vendor 指向本目录之外的哪些技能；校验要求实际断链与声明完全相等，上游新增或去掉一条跨技能引用就会红。
- 这些目录不进 `skills.txt`、不软链进宿主。宿主里只出现 `system-map` 一个技能名，模型绕不过它的裁决直接调上游。
- `sync.sh` 走 `gh api` 加 codeload，不走 git 远程：维护者机器上 `github.com:443` 被代理挡着，`git clone` 跑不通。
