# pstack

源目录：`mmw-v2/upstream-pstack/`

上游是 GitHub 仓库 `cursor/plugins` 的 `pstack/` 子目录（MIT），不是整个仓库，所以不能像另外三个 subtree 那样直接 `git subtree pull <url>`。要先在一份临时克隆里把 `pstack/` 切出来，再对切出的分支做 squash。

钉定的上游提交是 `12d587dfb20741cafc376c42c696c5f6e2a64487`（0.15.5，`.cursor-plugin/plugin.json` 的 `version`）。切出的提交是 `dd6ba52b0bf000ee0c8defef96832572944d1e00`（90 个提交），树是 `975600f2f90dc6f755d58cccdccee27f950edcd2`，与 `12d587dfb20741cafc376c42c696c5f6e2a64487:pstack` 的树相同。

## 引入

在仓库之外 `mktemp -d` 的目录里完整克隆。不带 `--filter`：带 `--filter=blob:none` 的克隆在第三步被 `git subtree add` 拉取时报 `fatal: protocol error: bad pack header`（切票会话 2026-10-01 实测）。

```
git clone https://github.com/cursor/plugins <clone>
```

在克隆里检出钉定的提交，再切出 `pstack/`：

```
git checkout 12d587dfb20741cafc376c42c696c5f6e2a64487
git subtree split --prefix=pstack -b pstack-split
```

在本仓库根目录，对切出的分支做 squash：

```
git subtree add --prefix mmw-v2/upstream-pstack <clone> pstack-split --squash
```

`--squash` 这一步生成两个提交。一个标题是 `Squashed 'mmw-v2/upstream-pstack/' content from commit dd6ba52b`，正文有 `git-subtree-dir: mmw-v2/upstream-pstack` 与 `git-subtree-split: dd6ba52b0bf000ee0c8defef96832572944d1e00`。另一个是把这个提交合并进当前分支的合并提交。

## U-13

U-13（能否从 `cursor/plugins` 的 `pstack/` 干净切出 subtree）的结果：能。2026-10-01 在临时克隆里对 `12d587dfb20741cafc376c42c696c5f6e2a64487` 跑 `git subtree split --prefix=pstack`，切出的提交是 `dd6ba52b0bf000ee0c8defef96832572944d1e00`，树是 `975600f2f90dc6f755d58cccdccee27f950edcd2`。

## 与研究快照

研究快照 `docs/research/code-landing-refs/pstack/` 停在 0.15.4（上游提交 `b0b9c7a0`），不随 subtree 更新。R18、R20、R21 与范本引的 pstack 行号出自这份快照。

subtree 与快照相差 16 个文件（43 行增、36 行删）：

- `.cursor-plugin/plugin.json`
- `skills/architect/SKILL.md`
- `skills/arena/SKILL.md`
- `skills/how/SKILL.md`
- `skills/interrogate/SKILL.md`
- `skills/reflect/SKILL.md`
- `skills/setup-pstack/SKILL.md`
- `skills/show-me-your-work/SKILL.md`
- `skills/swarm/SKILL.md`
- `skills/why/SKILL.md`
- `skills/poteto-mode/SKILL.md`（只有第 93 行）
- `skills/poteto-mode/playbooks/autopilot-full.md`
- `skills/poteto-mode/playbooks/babysit.md`
- `skills/poteto-mode/playbooks/multi-phase-plan.md`
- `skills/poteto-mode/playbooks/opening-a-pr.md`
- `skills/poteto-mode/scripts/check-plan.mjs`

subtree 另多快照没有收的 7 个图片：`assets/logo.png`，以及 `docs/guide/images/` 下的 `design.jpg`、`overnight.jpg`、`recipes.jpg`、`router.jpg`、`understanding.jpg`、`verification.jpg`。

本批与 spec #595 取文字的 27 个文件在两边逐字节相同：23 个 `skills/principle-*/SKILL.md`、`skills/reflect/references/synthesizer.md`、`skills/poteto-mode/playbooks/` 下的 `prototype.md`、`authoring-a-skill.md`、`bug-fix.md`。

## 总原则

这个 subtree 里的文字不改。`LICENSE`（MIT）留在 subtree 里，技能的 `disable-model-invocation` 行也留着。

用到的组件由 `mmw-v2/import/import_component.py` 复制进 `mmw-v2/skills/mmw/`，登记在 `mmw-v2/skills/mmw/imports.tsv`。需要判断的改动记在本文件。

## 以后拉更新

在新的上游提交上重做 split，再对切出的分支：

```
git subtree pull --prefix mmw-v2/upstream-pstack <clone> <切出的分支> --squash
```

这一条是照 `git subtree` 的用法推出的，本批没有跑过，没有实测。拉完后改写开头钉定提交那一段，并重新核对「与研究快照」一节的差异与 27 个文件。
