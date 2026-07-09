# codex-skills

**worktree-build / worktree-review 的源在 `plugin/skills/`(随插件发布,宿主中立措辞)**;本目录下两个同名条目是指向 `../plugin/skills/worktree-{build,review}` 的**软链**,只作为 Claude 侧 Codex CLI 的安装入口(Codex 读不到 `plugin/`,但扫 `~/.agents/skills/`,经软链链最终读到 `plugin/skills/` 那份)。单源:改 `plugin/skills/` 一处,两宿主都同步,不会漂移(`plugin/scripts/tests/test_skill_parity.sh` 守护软链完整)。

plugin 派 Codex 时,prompt **只给 stage / worktree / 文档路径 + 指向对应 skill**,方法本体在 skill 里渐进加载(开工前不占 Codex context),**不在 prompt 里重复**。

## 安装(软链进 Codex 自动扫描的 skill hub)

Codex 自动扫描 skill hub `~/.agents/skills/`(与 `/tdd`、`write-design-doc` 等同一套,靠扫描发现、**不需要写 `~/.codex/config.toml`**)。把两份 skill 软链进去即可(指向本目录的软链入口,再跳到 `plugin/skills/` 源):

```bash
ln -s "$(pwd)/codex-skills/worktree-build"  ~/.agents/skills/worktree-build
ln -s "$(pwd)/codex-skills/worktree-review" ~/.agents/skills/worktree-review
```

装好后 Codex 侧 `worktree-build` / `worktree-review` 可用,与已装的 `/tdd`(worktree-build 硬依赖)配合。**装是硬前提**:没装则派发失败可见(Codex 报找不到 skill),不搞"没装也能跑"的降级。

## worktree-build(build 阶段落地)

plugin build 阶段派 Codex 进 worktree 落地一份计划时用。内容在 `plugin/skills/worktree-build/`(本目录软链指过去):

- `SKILL.md` — 落地总纲(5 步循环 + 必读三文档 + 收工回执契约 + 边界)。
- `references/discipline.md` — 防过度设计/兜底、契约类型、登记+迁移(开工读一次)。
- `references/tests.md` — 测试对标仓库治理文档、测公开行为/mock/权威层(写测试前读)。
- `references/when-stuck.md` — 3-strike / 计划冲突 / 缺输入(卡住才读)。

## worktree-review(审闸 review 阶段)

plugin 审闸(design/plan/final/merge-impl)派 Codex 独立审一份产物时用。`review.sh` 打印的协调帮手 brief 里,Codex prompt **只给 stage + 视角 + Source**,指向本 skill;**不给任何 plugin 内路径**。③合同门(plan-impl)是 Claude 机器核、不派 Codex,不在此。内容在 `plugin/skills/worktree-review/`(本目录软链指过去):

- `SKILL.md` — 审查总纲(确认 stage+负责哪路视角 → 读方法 → 读 stage 角度 → 只读边界 → Return Contract)。
- `references/method.md` — 共享审查纪律(只读边界 / 不信自述 / 方向-方法-地基五问 / 防幻觉四件套 / Finding 字段 / 分级 / Return Contract / 禁用红线),开工读一次。
- `references/{design,plan,final,merge}.md` — 各 stage 审查角度,按被派的 stage 读一份。

> `worktree-review` 也是 ④final 双模型审的单源:Claude 无头审者(`claude -p`)与 Codex 读同一份 `~/.agents/skills/worktree-review/`(经软链落到 `plugin/skills/worktree-review/`)。
