---
ticket: 46
artifact_refs: []
---

# Plan: 领域文档收口

**Goal:** 领域文档与产物落点及 Wiki 退役合同一致，并补齐工作名取值边界的术语。
**Source spec:** `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md`
**Source ticket:** GitHub issue `#46`

## Constraints

- 本 plan 依赖 01 号 plan 建立 `mmw/cli/artifacts.json`。来源：ticket `#46` 的 `Blocked by` 和 spec 第 20 节。
- 本 plan 依赖 09 号 plan 完成 Wiki 退役。领域文档不得先于实现宣称退役完成。来源：ticket `#46` 的 `Blocked by`。
- 领域文档 leaf 与 Context Map 归本 plan 独占。本 plan 不修改其他 plan、spec、ADR、CLI、技能源或测试。来源：Cross-Plan Contract Anchors。
- `AGENTS.md` 只修改“唯一事实来源”中的产物落点合同。03 号 plan 拥有领域上下文中的 ADR 读取句及其受管种子。09 号 plan 拥有提交检查中的 Wiki 分区。
- 产物落点 leaf 只保留术语定义和一条指向产物落点数据的权威引用。它不再保存类别清单或路径取值。来源：spec 第 20 节和 ADR `0006`。
- 指“两次交付取到同一个工作名”的新术语由 `/mmw-domain-modeling` 定名。本 plan 不预先指定名称。术语归“产物落点” leaf。
- 新术语不得扩大“撞名”的含义。“撞名”继续只指两件产物取到同一个产物引用。来源：spec 第 16、20 节和 ADR `0011`。
- 本 ticket 没有 prototype 资产，也没有 research。来源：ticket `#46`。

## Current State

- `docs/context/artifact-location.md:7-52` 定义路径形状、工作名和撞名等术语。
- 同一 leaf 的 `55-71` 行保存类别根表。`73-85` 行还保存不使用路径形状的类别清单和不落盘判据。
- `docs/context/release-and-closure.md:35-37` 仍把“Wiki 页面”定义为收尾写入的长期页面。
- `CONTEXT-MAP.md:16` 仍把“Wiki 页面”列入“出包与收尾”的所有权。
- `CONTEXT-MAP.md:19` 已登记“产物落点”现有术语。它还没有登记本 ticket 要补的新术语。
- `AGENTS.md:45-50` 还没有点名 `mmw/cli/artifacts.json`。第 50 行仍要求技能直接使用路径字面值。
- `AGENTS.md:107` 的 ADR 读取句归 03 号 plan。`AGENTS.md:113` 已要求长期术语通过 `/mmw-domain-modeling` 更新拥有它的 leaf。
- Serena 定位到 `mmw_domain_check` 位于 `mmw/cli/lib/domain.sh:50-61`。当前源码在 `mmw/cli/mmw:466-478` 把 `domain check` 路由到该函数。
- Graphify 查询被工具取消。Serena 也不能从当前 Bash 语言配置读取 Python 符号。`mmw/cli/lib/context_docs.py:790-820` 已用当前源码验证领域文档检查入口。

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `docs/context/artifact-location.md` | Modify | 收窄为术语层，指向产物落点数据，并增加由领域建模定名的新术语 |
| `docs/context/release-and-closure.md` | Modify | 删除已退役的“Wiki 页面”术语 |
| `CONTEXT-MAP.md` | Modify | 同步“产物落点”与“出包与收尾”两行的术语所有权 |
| `AGENTS.md` | Modify | 只更新“唯一事实来源”中的产物落点合同 |

## Contracts and Seams

- **Test seam:** `mmw/cli/mmw domain check` 验证 Context Map、leaf 和受管领域上下文。`bash mmw/test.sh` 验证完整仓库入口。语义矛盾使用全仓库文本审计和人工判断。
- **Consumes — 01 → 10:** 01 拥有并提供 `mmw/cli/artifacts.json`。10 只把整份文件作为类别数据的权威引用，不修改记录或字段。
- **01 record boundary:** 记录字段是 `term`、`root`、`root_kind`、`has_name`、`allows_scope`、`sub_naming`、`sub_fixed`、`sub_pattern`、`status` 和 `answered_by`。本 plan 不在 leaf 中复制这些字段的取值。
- **Consumes — 09 → 10:** 09 提供 Wiki 归档已退役的实现状态。10 删除领域模型中的旧术语，不修改 09 的 CLI、技能或测试分区。
- **Shared `AGENTS.md`:** 10 只改“唯一事实来源”。03 的 ADR 读取句、领域上下文受管种子和 09 的提交检查分区保持不动。
- **Produces:** 新 canonical 术语只在“产物落点” leaf 定义。Context Map 使用完全相同的字面登记所有权。
- **No migration:** 这是领域文档收口。没有数据迁移、注册表迁移或外部状态变更。

## Implementation

1. **前置合同已经落地**
   - Change: 确认 issue `#37` 与 `#42` 已关闭。确认当前分支已包含两张 ticket 的结果。
   - Change: 确认 `mmw/cli/artifacts.json` 存在。确认 Wiki 退役实现已完成。
   - Files: 只读 `mmw/cli/artifacts.json` 和 09 号 plan 拥有的实现分区。
   - Verify: `gh issue view 37 --json state --jq .state && gh issue view 42 --json state --jq .state` → 两行都是 `CLOSED`。
   - Verify: `test -f mmw/cli/artifacts.json` → 退出码为 0。

2. **产物落点 leaf 只保留术语层**
   - Change: 调用 `/mmw-domain-modeling`。为“两次交付取到同一个工作名”选择一个 canonical 术语和对应 `_Avoid_`。
   - Change: 在“产物落点” leaf 定义该术语。定义只说明它是什么，不写处置算法。
   - Change: 保持“撞名”只指产物引用相同。若新术语与现有 `_Avoid_` 冲突，同时修正该列表。
   - Change: 删除类别根表和具体类别清单。把仍需保留的“不落盘判据”收进 `## Language`，写成紧凑术语定义。
   - Change: 增加一条指向 `../../mmw/cli/artifacts.json` 的权威引用。不要在旁边复制类别、路径或状态数据。
   - Files: `docs/context/artifact-location.md`。
   - Verify: `rg -n '^## ' docs/context/artifact-location.md` → 术语区之外没有类别数据章节。
   - Verify: `rg -n 'mmw/cli/artifacts.json' docs/context/artifact-location.md` → 只有一条权威引用。

3. **退役术语与 Context Map 同步**
   - Change: 从“出包与收尾” leaf 删除“Wiki 页面”的定义。其他现有术语保持原义。
   - Change: 从 Context Map 的“出包与收尾”行删除“Wiki 页面”。
   - Change: 把第 2 步确定的新术语加入 Context Map 的“产物落点”行。使用 leaf 中的完全相同字面。
   - Files: `docs/context/release-and-closure.md`、`CONTEXT-MAP.md`。
   - Verify: `! rg -n '^\*\*Wiki 页面\*\*：' docs/context/release-and-closure.md` → 没有旧术语定义。
   - Verify: `rg -n '^\| (出包与收尾|产物落点) \|' CONTEXT-MAP.md` → 两行与对应 leaf 一致。

4. **根规则指向新的唯一事实来源**
   - Change: 在“唯一事实来源”第 2 项点名 `mmw/cli/artifacts.json`。
   - Change: 将路径字面值段落改成三项合同。产物落点由 `mmw artifact path` 回答。技能正文不写路径字面值。`.mmw.json` 的 `paths` 只保留四个工作目录根键。
   - Change: 不修改 `MMW-DOMAIN-CONTEXT` 受管区块。保留 03 号 plan 对 ADR 读取句的结果。
   - Files: `AGENTS.md` 的“唯一事实来源”分区。
   - Verify: `git diff -- AGENTS.md` → 差异只位于“唯一事实来源”。

5. **领域合同完成全仓库验证**
   - Change: 全仓库搜索旧术语、旧类别表和旧路径字面值规则。逐条区分现行定义、`_Avoid_` 和历史决定。
   - Change: spec 与 ADR 中说明旧行为已退役的历史文字可以保留。现行 leaf、Context Map、`AGENTS.md` 和技能源不得继续声明旧合同。
   - Files: 本 plan 的四个修改路径；其他命中只读。
   - Verify: `rg -n 'Wiki 页面|技能直接使用已规定的仓库相对产物路径|^## 类别根|^\| 产物 \| 类别根 \|' . --glob '!vendor/**' --glob '!archive/**'` → 每个剩余命中都不是现行领域定义。它只可位于 `_Avoid_`、历史说明或本 ticket 的任务材料。
   - Verify: `mmw/cli/mmw domain check` → 输出 `check\tmap\tCONTEXT-MAP.md\tvalid`。
   - Verify: `bash mmw/test.sh` → 全部测试通过，退出码为 0。
   - Verify: `git diff --check` → 没有空白错误。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| 产物落点 leaf 不再复制类别数据 | 检查 leaf 只有术语区和一条数据权威引用 | `rg -n '^## |mmw/cli/artifacts.json' docs/context/artifact-location.md` → 只有 `## Language` 和一条权威引用 |
| “Wiki 页面”不再是出包与收尾术语 | 检查术语定义已删除 | `! rg -n '^\*\*Wiki 页面\*\*：' docs/context/release-and-closure.md` → 退出码为 0 |
| Context Map 的所有权同步 | 对照两个改动 leaf 与对应 Map 行 | `rg -n '^\| (出包与收尾|产物落点) \|' CONTEXT-MAP.md` → 旧术语消失，新术语字面与 leaf 相同 |
| 两次交付取到同一个工作名有独立术语 | 检查领域建模结果，不把它并入“撞名” | 人工结果：leaf 有独立术语与 `_Avoid_`；Map 登记同一字面；“撞名”定义不变 |
| 全仓库没有与新合同冲突的现行定义 | 审阅全部相关文本命中 | `rg -n 'Wiki 页面|技能直接使用已规定的仓库相对产物路径|^## 类别根|^\| 产物 \| 类别根 \|' . --glob '!vendor/**' --glob '!archive/**'` → 剩余命中只位于 `_Avoid_`、历史说明或本 ticket 的任务材料 |
| 根规则指向产物落点数据与命令 | 检查 `AGENTS.md` 的唯一事实来源分区 | `rg -n 'artifacts.json|mmw artifact path|路径字面值' AGENTS.md` → 三项合同都存在 |
| 领域文档机械合同有效 | 运行现有领域检查 | `mmw/cli/mmw domain check` → `check\tmap\tCONTEXT-MAP.md\tvalid` |
| 完整仓库回归通过 | 运行唯一测试入口 | `bash mmw/test.sh` → 全部测试通过，退出码为 0 |

## Browser Acceptance

不适用。
