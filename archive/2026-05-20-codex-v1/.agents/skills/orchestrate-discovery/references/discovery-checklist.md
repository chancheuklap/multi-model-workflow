# Discovery Checklist

写完 design document 后加载。检查并修正，不进入实现。

## 内容完整性

- [ ] 无 TODO / TBD / placeholder / vague wording。
- [ ] 不和 CONTEXT / PROJECT / SPEC / ADR / GUIDE / 代码事实冲突。
- [ ] 每个目标行为都能转成验收或测试。
- [ ] 对象 / 状态 / 合同有 owner / writer / reader / verifier。
- [ ] 没有混入 implementation plan / Task Pack / worker 指令。
- [ ] 没有把多个独立系统塞进一个 design document。

## 按输入类型检查

- **Bug**：有 current behavior / desired behavior / reproduction / symptom / regression check。
- **Issue**：有 source / acceptance / dependencies / AFK-HITL。
- **Feedback**：有 target state / role / copy / interaction / verification anchor。
- **UI/UX**：有 mockup path / viewport / states / interaction / visual verification。

## 合同与发布

- [ ] 涉及 API / Pydantic / DB / JSON / sync / billing / permission / runtime 时，有 Contract anchors（owner / provider / consumer / model / schema_version / registry / migration / verification）。
- [ ] 涉及 migration / billing / permission / runtime / deploy order / rollback / manual gate 时，有发布风险面和 manual gate owner。

## 结论判定

- 有必须由用户决定的 Open Decision → `NEEDS_USER_DECISION`。
- 全部通过 → `DISCOVERY_READY`。
- 还需补充信息 → 回到 `discovery-input.md` 对应章节。
