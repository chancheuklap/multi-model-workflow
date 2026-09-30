---
date: 2026-10-01
amends: [0006]
---

# pstack 以 squash subtree 进入 mmw-v2/upstream-pstack/，原文不改，钉在切票时上游最新的提交，研究快照停在 0.15.4

pstack 进入仓库，是因为以后按需导入一个组件只是复制一个文件、加一行登记，前提是原文在仓库里。这份 ADR 覆盖它怎样进来、一个组件按八种类型落在哪里、调用开关在哪里去掉。子树钉的是切票时上游 `main` 上最后一个改动 `pstack/` 的提交 `12d587dfb20741cafc376c42c696c5f6e2a64487`（`.cursor-plugin/plugin.json` 的 `version` 是 0.15.5，树 `975600f2f90dc6f755d58cccdccee27f950edcd2`）。研究快照 `docs/research/code-landing-refs/pstack/` 停在 0.15.4（上游 `b0b9c7a0`），R18、R20、R21 与范本引的行号出自它。ADR 0006 定的是两处宿主位置都直接指向仓库源目录，并否决了经另一个目录中转的软链。带 `+model-invoked` 的技能改为指向 `~/.mmw/skill-copies/<name>/`，这一条对它们不再成立。0006 的正文不改。

## 八种导入类型

每个外来文件登记在 `mmw-v2/skills/mmw/imports.tsv`。`mmw-v2/import/import_component.py` 只做下面的机械改写。需要判断的改动另记：`imports.tsv` 的「判断改动」列，以及 `mmw-v2/merge-notes/pstack.md`。

| 类型 | 落位 | 机械改写 |
| --- | --- | --- |
| `playbook` | `mmw-v2/skills/mmw/playbooks/<file>` | `../references/X` 改为 `../references/pstack/X`；`scripts/X` 改为 `scripts/pstack/X` |
| `principle` | `mmw-v2/skills/mmw/principles/principle-<slug>.md` | 删掉 `disable-model-invocation` 那一行；`../principle-x/SKILL.md` 改为 `principle-x.md`；索引行由 description 生成 |
| `skill` | 不复制。`skills.txt` 一行 `pstack/<name>`，解析到 `mmw-v2/upstream-pstack/skills/<name>` | 被 mode 或 playbook 点名时，那一行加 `+model-invoked`。开关不在子树里改 |
| `mode-trigger` | mode `## Non-negotiables` 的 `### Imported triggers`，原文一行 | 无 |
| `mode-section` | mode 里一个同名小节，原文复制。目前只有 `## Comments` | 无 |
| `mode-reference` | `mmw-v2/skills/mmw/references/pstack/<file>` | 无 |
| `mode-script` | `mmw-v2/skills/mmw/scripts/pstack/<path>`，连同它导入的同目录文件 | 无 |
| `agent` | `mmw-v2/skills/mmw/references/pstack/agents/<name>.md`，作为宿主通用子代理的简报 | 删 frontmatter 里 `is_background` 等宿主字段 |

外来的 reference 与脚本放 `references/pstack/`、`scripts/pstack/`，`skills.txt` 的前缀是 `pstack/`。playbook 与原则不分这个命名空间：同名就是同一任务类型或同一条规则。

## 调用开关与按需

被 mode 或 playbook 点名、上游带 `disable-model-invocation` 的技能，子树原文不改。只在 `skills.txt` 那一行加 `+model-invoked`。`install.sh` 在 `~/.mmw/skill-copies/<name>/` 生成副本：`SKILL.md` 是源文件去掉这一行之后的拷贝，`agents/openai.yaml` 按同一标记生成、不写 `policy`，其余文件软链回源目录。宿主的技能软链指向副本。`install.sh --check` 比对副本与源文件，源文件变了就报副本过期。

导入按需。本批只导入被 MMW 自写组件点名的 14 条原则：`prove-it-works`、`fix-root-causes`、`attack-the-premise`、`redesign-from-first-principles`、`laziness-protocol`、`subtract-before-you-add`、`migrate-callers-then-delete-legacy-apis`、`test-behavior-not-implementation`、`separate-before-serializing-shared-state`、`make-operations-idempotent`、`encode-lessons-in-structure`、`build-the-lever`、`guard-the-context-window`、`never-block-on-the-human`。不导入任何 pstack playbook 或能力技能。扩展工具箱（`reflect`、`eval`、`figure-it-out`、`automate-me`、`show-me-your-work`、`create-verification-skill`、`maintain-verification-skill`）与多模型面板（`dispatch.sh panel`、`panel-wait`、`models.json` 里的面板角色）同样按需。PR 交付那一组不引入：`delivery: pr`、`opening-a-pr`、`babysit`、`shipping`、`bugbot-triage.md`、`watch-pr/` 与 bun。

## Considered Options

- **其余类型用软链指子树。** 否决。pstack 文件里的相对链接按读者打开的路径解析，软链会让它们指错。能力技能不复制，走 `skills.txt` 与安装副本；其余类型复制进 `mmw-v2/skills/mmw/`。
- **外来 reference、脚本与 MMW 自有文件放在同一目录。** 否决。`mmw-v2/skills/mmw/scripts/` 是流水线的状态脚本，不混入 bun 的 `package.json` 与 `bun.lock`。
- **在子树里去掉 `disable-model-invocation`。** 否决。拉上游会在开关行冲突。开关只在安装副本里去掉，子树保持原文。
- **钉在研究快照的提交 `b0b9c7a0`。** 否决。那一版让子树与每一处引文同版。主人定的是用切票时上游最新的提交。代价由取文字的 27 个文件两边逐字节相同来承担。

## Consequences

- `mmw-v2/upstream-pstack/` 是 pstack 原文，一个字不改。`LICENSE`（MIT）留在子树里。命令、切出的提交与两个版本号记在 `mmw-v2/merge-notes/pstack.md`。
- 带 `+model-invoked` 的技能，宿主软链指向 `~/.mmw/skill-copies/<name>/`，不再直接指向仓库源目录。ADR 0006 的那一条对它们不再成立，正文仍是 2026-08-26 写下的那一版。
- 本批落进仓库的 pstack 文字，在引入子树这一步只有这棵子树。14 条原则的复制，以及任何 playbook 或能力技能，发生在各自的导入。
- 研究快照与子树不是同一版。本批与 spec #595 取文字的 27 个文件两边逐字节相同，导入脚本从子树复制出的文字与快照相同。
- 编号 0033 空着，留给 B2 的唤醒带步骤指针。本份取 0034，因为 R18 与本批的 spec 已经按这个号引用它。
