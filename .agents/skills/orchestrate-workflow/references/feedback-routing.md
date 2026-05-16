# Feedback 路由

反馈、截图、测试失败或人工验收结果进入代码前先分类。

## 分类

| 信号 | route |
| --- | --- |
| 实现偏离已批准 design / mockup / acceptance | Phase A repair |
| target state、role、copy、interaction、permission、billing、lifecycle 不清 | `grill-with-docs` |
| state machine、interface shape 或 UI 方向需要比较 | `prototype` |
| bad seam、repeated repair、single-adapter interface、caller leaks implementation | `improve-codebase-architecture` |
| 需要跨会话跟踪或暂时不能关闭 | `triage` / `to-prd` / `to-issues` |

## 门禁

- 没有 target state，不派 worker。
- 没有 verification anchor，不派 worker。
- 主观反馈必须先转成可验证行为、UI state、copy、interaction 或 acceptance。
- 反馈暴露 source design 缺口时，先修 design，再回到 Phase 0a / Phase 0b。

## 流程图

```mermaid
flowchart TD
    A["反馈 / 截图 / 测试失败 / 人工验收结果"] --> B{"目标状态和验证方式清楚?"}
    B -->|否| C["grill-with-docs 澄清 target state / role / copy / interaction"]
    C --> D["回写 design / plan / issue brief"]
    D --> B
    B -->|是| E{"实现偏离已批准 design / mockup / acceptance?"}
    E -->|是| F["Phase A repair"]
    E -->|否| G{"需要方案比较?"}
    G -->|是| H["prototype"]
    G -->|否| I{"暴露 architecture friction?"}
    I -->|是| J["improve-codebase-architecture"]
    I -->|否| K["triage / to-prd / to-issues 或 user decision"]
```
