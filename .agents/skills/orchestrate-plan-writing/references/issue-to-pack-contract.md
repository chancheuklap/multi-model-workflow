# Issue 到 Pack 合同

本文件用于把 `mattpocock-skills:to-issues` 产出的 issue 文档转换成 Orchestrate Workflow Task Pack。

## 1. 映射关系

| source artifact | plan artifact |
| --- | --- |
| source design / SPEC / PRD | plan 的 source of truth 和 coverage checklist |
| 用户明确提供或 Orchestrate parent 明确确认的 `to-issues` vertical large issue | plan 一级章节 |
| parent large issue 文档内已记录的 `to-issues` vertical small issue | 一个 Task Pack |
| issue acceptance criteria | Task Pack acceptance criteria |
| issue blocked-by | Task Pack dependencies |
| issue out of scope | Task Pack out of scope |
| issue AFK / HITL | Task Pack AFK / HITL 和 risk flags |

如果缺少大 issue 或小 issue，返回 `NEEDS_ISSUES`，交回 Orchestrate 运行 `to-issues`。本 skill 可以写出建议拆分提示，但不能把建议拆分直接当成正式 Task Pack。

AgentFlow 使用 GitHub Issues 时，small issue hierarchy 的第一落点是 parent large issue 文档。确认写入 parent issue 后，再由后续流程上传或同步到 GitHub Issue。不要因为要拆 small issue 就创建新的本地 issue 文档；只有用户明确要求，或项目规则指定本地 issue 文件路径时，才创建 standalone issue 文档。

Design、SPEC、ADR 或 PRD 中提到多个相关 issue 时，只处理用户明确提供或 parent 明确确认的 issue。其它 issue 最多作为 read-only context，不进入 plan source、Task Pack inventory 或 coverage map。

如果小 issue 不能独立验证，返回 `NEEDS_ISSUES`，建议用 `to-issues` 继续拆小。不要按文件类型、前后端层、schema / test / implementation 阶段、团队分工来拆。

## 2. Task Pack 必填项

每个 Task Pack 必须包含：

- goal behavior；
- owned files / responsibilities；
- read-first anchors；
- Contract anchors；
- UI / UX 工作的 mockup anchors；
- acceptance criteria；
- verification commands 或 manual gate；
- risk flags；
- AFK / HITL；
- dependencies；
- parallel safety；
- out of scope。

`N/A` 只能用于确实不适用的字段，不能用来绕过上下文缺口。

## 3. 默认串行边界

这些工作默认串行，或放进同一个 pack：

- 同一文件或模板；
- 同一 Pydantic model、shared contract、client contract；
- 同一 DB migration tree、repository、read model；
- 同一 JSON registry 或 validator；
- billing、wallet、chargeable action；
- permission、auth、runtime、browser takeover；
- deployment、rollback、release gate；
- 同一 UI action contract 或 mockup state。

允许并行的 pack 必须能独立验证，并且不会竞争同一 contract surface。

## 4. 不合格 Pack 信号

- worker 必须自行决定 desired behavior、文案、角色、视觉层级、billing meaning、permission meaning、schema shape 或 helper placement。
- pack 只写“实现 mockup”，但没有 states、viewport、interaction 和 visual verification。
- 把未验证路径、fixture、class、command、endpoint 写成现有事实。
- 把真实依赖隐藏成“可以并行”。
- 只产出 schema 或 helper，没有 owner、consumer 和 public behavior verification。
- 需要人工决策、真实账号、生产确认或人工验收，却标成 AFK。

## 5. 上游 route payload

当需要交回 `to-issues` 时，返回这组信息给 Orchestrate：

```text
Upstream route: to-issues
Source design:
Parent large issue:
Issue recording target:
Why current issue boundary is insufficient:
Suggested vertical slices:
  1. Title:
     Type: AFK / HITL
     Blocked by:
     User stories / acceptance:
这些 slices 只是建议；必须等 `to-issues` 运行，并写回 parent large issue 文档后，才能成为正式 issue / Task Pack。GitHub 同步发生在 issue hierarchy 被记录和确认之后。
```
