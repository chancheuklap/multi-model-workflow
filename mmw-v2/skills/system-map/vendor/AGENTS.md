# system-map/vendor

`system-map` 调用的两份上游技能，只读副本。

技能是交付物，要能整个目录拷走或分发出去照样能用，所以这两份副本和同步它们的 `sync.sh` 都住在技能里，不放仓库别处再软链过来。

## 关键约定

- 不改这里任何一个字。`sync.sh` 每次整目录删掉重写，改动一律丢失。对上游的偏差写进上一层的 `SKILL.md` 裁决段。
- 这里的两个 `SKILL.md` 嵌在技能目录第三层。Claude Code 不递归扫技能目录，只认最外层那一个；另外四个宿主没有验证过，宿主技能列表里冒出 `diagram-design` 或 `html-diagram` 就是它递归扫了。
- 加减 vendor 只改 `sync.sh` 顶部的 `SOURCES`。末段声明这份 vendor 指向本目录之外的哪些技能；校验要求实际断链与声明完全相等，上游新增或去掉一条跨技能引用就会红。
- `diagram-design/scripts/verify-geometry.py` 是 `SOURCES` 的附加文件，上游装成技能时不带它，只有 repo checkout 有。它检查标签遮罩被后画的节点盖住，是出图质量唯一的机械检查，所以补进来。同一个 `scripts/` 下缺的是 `verify-motion.py`：它的 `ROOT = parent.parent` 假设自己在 repo 根的 `scripts/` 下，放进技能目录会指错 asset 路径，所以 `system-map` 钉死静态图，用不到它。
- 这些目录不进 `skills.txt`、不软链进宿主。宿主里只出现 `system-map` 一个技能名，模型绕不过它的裁决直接调上游。
- `sync.sh` 走 `gh api` 加 codeload，不走 git 远程：维护者机器上 `github.com:443` 被代理挡着，`git clone` 跑不通。
