# research：aidlc-workflows v2 的阶段间产物传递机制

## 这次要回答的问题

`awslabs/aidlc-workflows` 的 v2 分支，在它的多阶段工作流里怎么规定产物落点、怎么在阶段之间传递产物？

只取证它的做法与取舍，不评价 MMW 该不该照做。判断留给下游 decision ticket。

来源：Wayfinder decision ticket #20，map 是 #18「MMW 产物归纳与接线合同」。

## 查证范围

- `awslabs/aidlc-workflows` 分支 `v2`，访问日期 2026-08-11。GitHub 当时显示头提交短 SHA `2ce654d`，README 标注版本 `2.5.62`。
- `core/aidlc-common/`：阶段协议、阶段文件、`conductor.md`、`protocols/stage-definition.md`、`protocols/stage-protocol-recovery.md`。
- `core/tools/`：37 个 `aidlc-*.ts` 文件（含分发器），`core/tools/data/`。
- `docs/reference/`：`03-orchestrator.md`、`06-hooks-and-tools.md`、`15-stage-definition.md`、`16-artifact-vocabulary.md`。
- `tests/`、`.github/workflows/ci.yml`、`scripts/package.ts`。

两个取证角度：阶段协议与 conductor、引擎工具与机械校验。主 agent 逐条核对关键断言，核对到的原文在 `report.md` 中标注「主 agent 亲自抓取核对」；只有 `investigator` 抄回、主 agent 未逐字核对的也逐条标注。

## 结论摘要

1. **产物的身份是 canonical name，不是路径。** 短 kebab-case，无扩展名、无斜杠。落点从 `(canonical name) + (producing stage) + (per-unit flag)` 推导得出。
2. **唯一生产者，名称全局唯一。** 一个 canonical name 由恰好一个阶段声明；两个阶段不得声明同名。概念重叠时拆成两个名字（实例：`build-test-results` 与 `load-test-results`，磁盘文件名都可能是 `test-results.md`）。
3. **消费方不拥有路径。** 产物位于**生产它的阶段**目录下。`resolveArtifactPath()` 注释里的短语是 `UNDER THE STAGE THAT OWNS THE FILE`。
4. **传递是三步声明加一次解析**：上游 `produces[]` 声明 name，下游 `consumes[]` 声明同一个 name，引擎发 directive 时把已存在的输入解析成实际路径放进 `directive.consumes`。下游阶段不在正文里抄写上游路径。
5. **阶段正文里的路径不是合同。** YAML frontmatter 才是权威；引擎从不读 `outputs:` 做路径解析，`outputs:` 被标为运行时不承重。阶段文件不硬编码任何工作区根路径；**出现写死的根路径被这份协议定性为文档错误**。
6. **没有中心产物索引。** 只有一个从 `produces[]` 计算出来的 canonical name 注册表，「computed, not written」，由 `aidlc graph artifacts` 输出，不登记实际路径。也**没有独立的公开 `artifact-path` 查询命令**，路径解析是 orchestrate 内部行为。
7. **机械校验校的是声明层。** `/aidlc --doctor` 的 "Graph references" 检查要求每个 `consumes[].artifact` 和 `requires_stage[]` 都解析到注册表里的真实对象，否则报 "broken references"。运行时产物落点没有全局门禁。
8. **上游缺失区分预期与异常。** `required: true` 的含义是「若生产阶段运行，则该消费必须被满足」。被 scope 跳过就是按设计缺失；本应存在却缺失则停下问用户，不允许编造内容。反方向有强制失败：阶段批准时声明的 `produces[]` 文件缺失，引擎拒绝标记完成。

## 本目录的文件

| 文件 | 内容 |
| --- | --- |
| `README.md` | 本文件，research 索引 |
| `report.md` | 完整结论，十二节。英文原文按原样抄写，每条标注主 agent 是否亲自核对 |

## 下游怎么用

- decision ticket #21「每类 MMW 产物的落点与路径形状」：第 1、2、3、4 节给出一种可对照的做法——产物先有 canonical name，路径从 name 加生产者推导。第 2 节的 Collision policy 直接对应 MMW 当前 `docs/evidence/` 由两个技能写入、没有唯一生产者规则的情况。
- decision ticket #23「读取产物的技能怎么找到它需要的产物」：第 4、7 节。aidlc 的下游声明消费的 name 而非路径，这与 MMW 当前七跳抄写精确路径是两条不同路线。
- decision ticket #24「落点合同存放在哪里」：第 5、6、10 节。aidlc 把落点规定拆成三处职责——阶段 frontmatter 声明名字、协议文件规定解析规则、引擎计算实际路径；并明确技能正文里的路径只是给人读的说明。第 6 节那条「写死根路径属于文档错误」的定性，与 MMW 当前技能正文写死 43 处 `<slug>/` 路径形状构成直接对照。
- decision ticket #26「新归纳合同下机械校验能判定什么」：第 11、12 节。aidlc 只机械校验声明层引用完整性，不校验运行时落点。这条边界与 MMW `AGENTS.md` 对机械校验的限制方向一致，可作为判断哪些校验值得加的参照。

## 没查清楚的部分

- **无法固定完整 commit SHA。** `api.github.com/repos/.../commits/v2` 被宿主拒绝为不安全地址，GitHub commits 页面返回 `429`，本机 `git ls-remote` 无法解析 `github.com`。范围快照只有分支名、短 SHA `2ce654d` 和 README 版本 `2.5.62`。要复现这份 research 前先固定 SHA。
- **`resolveArtifactPath()` 的逐字源码未取得。** WebFetch 拒绝复制长段源码。主 agent 取得的逐字内容只有注释短语 `UNDER THE STAGE THAT OWNS THE FILE`；函数行为由两次独立取证的语义一致性支撑，未逐行核对。
- **「没有全局产物落点门禁」是否定断言。** 取证范围见 `report.md` 第 11 节末尾。它是「已查范围内未找到」，不是「不存在」。`investigator` 未阅读全部 37 个文件的完整源码，`aidlc-utility.ts` 因文件过大在主 agent 核对时被截断，该文件的 doctor 校验断言改由 `docs/reference/16-artifact-vocabulary.md` 佐证。
- **`core/tools/data/scaffold/` 的 404 未由主 agent 复核。** 主 agent 只确认 `core/tools/` 下存在 `data` 子目录，`scaffold` 不存在这一点来自 `investigator` 的两次 404 记录。
- **测试覆盖表未逐条核对。** `report.md` 第 12 节的六项测试由 `investigator` 抄回。
