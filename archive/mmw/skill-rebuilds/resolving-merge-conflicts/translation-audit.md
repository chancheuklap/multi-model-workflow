# `resolving-merge-conflicts` 1.2.2 翻译审查

## 本技能术语应用

共享术语只由 [上游技能翻译共享术语](../translation-terms.md) 定义。下表记录本技能的术语应用和独有术语，不建立第二份定义。

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

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名已保留 |
| `SKILL.md:3` | 正在进行的 Git merge 或 rebase 冲突使用条件已保留 |
| `SKILL.md:4` | YAML 结束分隔符已保留 |
| `SKILL.md:6` | 当前状态、Git 历史和冲突文件检查已保留 |
| `SKILL.md:8` | 一手来源、改动原因、原始意图、提交信息、PR、issue 和 ticket 均已保留 |
| `SKILL.md:10` | 逐区块解决、尽量兼顾、冲突时按既定目标取舍、不发明行为和绝不 abort 均已保留 |
| `SKILL.md:12` | 发现自动检查、典型顺序及修复 merge 破坏均已保留 |
| `SKILL.md:14` | 暂存提交和继续 rebase 至全部完成均已保留 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | 显示名已保留 |
| `agents/openai.yaml:3` | 解决 merge 与 rebase 冲突的短描述已翻译 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。两个上游文件的全部有效内容均有对应翻译 |
| 增写 | 无。没有加入 MMW 的结果分支、集成记录或安全停止边界 |
| 曲解 | 无。`where incompatible` 仍只在双方意图不兼容时按既定目标取舍；没有放宽为自由设计 |
| 术语漂移 | 无。merge、rebase、意图、一手来源和 `--abort` 始终使用同一写法 |
