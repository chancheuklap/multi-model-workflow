# `resolving-merge-conflicts` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| Git、merge、rebase | `Git`、`merge`、`rebase` | 版本控制操作字面词 |
| conflict hunk | 冲突区块 | Git 差异片段的准确中文表达 |
| primary source | 一手来源 | 有稳定中文译名 |
| intent | 意图 | 有稳定中文译名 |
| stated goal | 已声明目标 | 保留目标必须已经存在的限制 |
| trade-off | 取舍 | 有稳定中文译名 |
| automated checks | 自动检查 | 有稳定中文译名 |
| stage | 暂存 | Git 操作的标准中文译名 |
| `--abort` | 保留原文 | Git 参数字面量 |

## 逐段完整性检查

| 上游位置 | 结论 |
| --- | --- |
| `SKILL.md:1-4` | 正在进行的 merge 或 rebase 冲突这一 invocation 条件已完整保留 |
| `SKILL.md:6` | 当前状态、Git 历史和冲突文件三项检查均已保留 |
| `SKILL.md:8` | 双方一手来源、改动原因和原始意图，以及 commit、PR、issue、ticket 四类证据均已保留 |
| `SKILL.md:10` | 同时保留双方意图、按已声明目标取舍、记录取舍、不发明行为和绝不 `--abort` 均已保留 |
| `SKILL.md:12` | 自动发现检查、典型顺序和修复 merge 破坏内容均已保留 |
| `SKILL.md:14` | 暂存、提交和持续 rebase 直到全部提交完成均已保留 |
| `agents/openai.yaml:1-3` | 展示名称和短描述均已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入 MMW 的结果分支、集成记录或安全停止边界 |
| 曲解 | 无。`where incompatible` 仍只在双方意图不兼容时按既定目标取舍；没有放宽为自由设计 |
| 术语漂移 | 无。merge、rebase、意图、一手来源和 `--abort` 始终使用同一写法 |
