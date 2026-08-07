# `triage` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| triage | `triage`；作普通动作时写“分诊” | 技能名和方法名保留英文，普通动作使用规范中文 |
| agent brief | `agent brief` | 上游方法中的固定产物名，也是 MMW 现行术语 |
| issue、PR、diff、label | `issue`、`PR`、`diff`、标签 | tracker 对象和代码差异保留行业常用写法；label 使用标准中文 |
| category role、state role | 类别角色、状态角色 | role 是一般概念，不自造中英混合术语 |
| category、state | 类别、状态 | 非模板字段时使用标准中文 |
| comment、triage notes | 评论、分诊记录 | 普通 tracker 内容使用标准中文；模板标题 `Triage Notes` 原样保留 |
| implementation | 实现 | 普通工程概念已有标准中文；代码标识符除外 |
| grilling | `grilling` | 上游技能名和方法名，没有稳定的等价中文术语 |
| Current behavior、Desired behavior、Key interfaces、Acceptance criteria、Out of scope | 原样保留 | Agent Brief 模板的固定字段名 |
| frontmatter、interface、stdout、JSON | 原样保留 | 配置或代码中的标准技术标识 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。下表逐一登记其他每一行，包括 frontmatter、代码块、模板和配置。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | 技能名 `triage` 已保留 |
| `SKILL.md:3` | issue、外部 PR、状态机、分类、验证、按需 grilling 和 agent brief 均已保留 |
| `SKILL.md:4` | 禁止模型隐式调用已保留 |
| `SKILL.md:5` | YAML 结束分隔符已保留 |
| `SKILL.md:7` | Triage 标题已保留 |
| `SKILL.md:9` | 项目 issue tracker 与小型分诊状态机已保留 |
| `SKILL.md:11` | 外部 PR 请求入口、PR 是附带代码的 issue、相同状态机、PR 差异和裸编号解析均已保留 |
| `SKILL.md:13` | triage 期间每条 tracker 评论或 issue 都要免责声明已保留 |
| `SKILL.md:15` | 免责声明代码块起始已保留 |
| `SKILL.md:16` | AI 在 triage 期间生成的免责声明已翻译 |
| `SKILL.md:17` | 免责声明代码块结束已保留 |
| `SKILL.md:19` | Reference 文档标题已保留 |
| `SKILL.md:21` | AGENT-BRIEF 链接和持久 agent brief 写法已保留 |
| `SKILL.md:22` | OUT-OF-SCOPE 链接和知识库作用已保留 |
| `SKILL.md:24` | 角色标题已翻译 |
| `SKILL.md:26` | 两种类别角色已保留 |
| `SKILL.md:28` | `bug` 及内容损坏含义已保留 |
| `SKILL.md:29` | `enhancement` 及新功能或改进含义已保留 |
| `SKILL.md:31` | 五种状态角色已保留 |
| `SKILL.md:33` | `needs-triage` 与维护者评估含义已保留 |
| `SKILL.md:34` | `needs-info` 与等待报告者补充信息已保留 |
| `SKILL.md:35` | `ready-for-agent`、完全明确和 AFK agent 已保留 |
| `SKILL.md:36` | `ready-for-human` 与需要人工实现已保留 |
| `SKILL.md:37` | `wontfix` 与不会执行已保留 |
| `SKILL.md:39` | PR 状态针对附带代码解读、agent brief、继续处理 diff 和人工合并均已保留 |
| `SKILL.md:41` | 每张已分诊 issue 恰有一类一态、冲突先问维护者均已保留 |
| `SKILL.md:43` | 规范角色名、实际标签可不同、映射与 setup 技能均已保留 |
| `SKILL.md:45` | 无标签起点、全部状态转换、报告者回复回流和维护者覆盖状态均已保留 |
| `SKILL.md:47` | 调用方式标题已翻译 |
| `SKILL.md:49` | 维护者调用 `/triage`、自然语言请求、解释并执行均已保留 |
| `SKILL.md:51` | “展示需要我关注的内容”示例已翻译 |
| `SKILL.md:52` | “查看 #42”及 issue 或 PR 两种对象已保留 |
| `SKILL.md:53` | 移到 `ready-for-agent` 示例已保留 |
| `SKILL.md:54` | 可供 agent 认领内容示例已翻译 |
| `SKILL.md:56` | 展示需要关注内容标题已翻译 |
| `SKILL.md:58` | 查询 tracker、三个分组和最旧优先已保留 |
| `SKILL.md:60` | 无标签且从未分诊的第一组已保留 |
| `SKILL.md:61` | `needs-triage` 且正在评估的第二组已保留 |
| `SKILL.md:62` | `needs-info`、报告者在上次记录后活动和重新评估的第三组已保留 |
| `SKILL.md:64` | 外部 PR、逐行对象标记、外部定义、排除协作者进行中 PR、显式 PR 不受筛选均已保留 |
| `SKILL.md:66` | 数量、一行摘要和维护者选择已保留 |
| `SKILL.md:68` | 指定 issue 或 PR 的分诊标题已翻译 |
| `SKILL.md:70` | 完整上下文、旧记录、领域术语、ADR、重复性、领域概念搜索、已有实现和先前否决检查均已保留 |
| `SKILL.md:72` | 类别与状态建议、理由、代码库摘要、已有实现和等待指示均已保留 |
| `SKILL.md:74` | grilling 前验证、bug 复现、PR checkout 与测试、三种结果及验证价值均已保留 |
| `SKILL.md:76` | 按需同时运行 grilling 与 domain-modeling、逐轮提问、术语和就地更新文档均已保留 |
| `SKILL.md:78` | 应用结果步骤标题已保留 |
| `SKILL.md:79` | `ready-for-agent` 发布 agent brief 评论及链接已保留 |
| `SKILL.md:80` | `ready-for-human` 使用相同结构和四类不能委托原因已保留 |
| `SKILL.md:81` | `needs-info` 发布分诊记录和下方模板已保留 |
| `SKILL.md:82` | `wontfix` 关闭且评论取决于原因已保留 |
| `SKILL.md:83` | 已经实现、指出位置、禁止写知识库及其原因已保留 |
| `SKILL.md:84` | 否决 bug、礼貌解释和关闭已保留 |
| `SKILL.md:85` | 否决 enhancement、写知识库、评论链接和关闭已保留 |
| `SKILL.md:86` | `needs-triage` 应用角色和可选进展评论已保留 |
| `SKILL.md:88` | 快速覆盖状态标题已翻译 |
| `SKILL.md:90` | 信任维护者、确认动作、直接改角色、跳过 grilling 和询问是否写 brief 均已保留 |
| `SKILL.md:92` | Needs-info 模板标题已保留 |
| `SKILL.md:94` | Markdown 代码块起始已保留 |
| `SKILL.md:95` | 模板标题 `Triage Notes` 的复数形式已保留 |
| `SKILL.md:97` | 已确定内容字段已翻译 |
| `SKILL.md:99` | 要点 1 占位已翻译 |
| `SKILL.md:100` | 要点 2 占位已翻译 |
| `SKILL.md:102` | 仍需报告者提供内容字段及 mention 已翻译 |
| `SKILL.md:104` | 问题 1 占位已翻译 |
| `SKILL.md:105` | 问题 2 占位已翻译 |
| `SKILL.md:106` | Markdown 代码块结束已保留 |
| `SKILL.md:108` | 保存 grilling 已解决内容、防止丢失以及问题具体可执行均已保留 |
| `SKILL.md:110` | 恢复先前 session 标题已翻译 |
| `SKILL.md:112` | 读取旧记录、检查回复、展示更新情况和不重复提问均已保留 |
| `AGENT-BRIEF.md:1` | 编写 Agent Brief 标题已翻译 |
| `AGENT-BRIEF.md:3` | GitHub 结构化评论、转入状态、权威 spec、AFK agent 和合同地位均已保留 |
| `AGENT-BRIEF.md:5` | issue 从零构建、PR 基于现有 diff、完成缺口和审查意见均已保留 |
| `AGENT-BRIEF.md:7` | 原则标题已翻译 |
| `AGENT-BRIEF.md:9` | 持久性优先于精确定位已翻译 |
| `AGENT-BRIEF.md:11` | 等待数日数周、代码变化和重命名移动重构后仍有用均已保留 |
| `AGENT-BRIEF.md:13` | 应描述接口、类型和行为合同已翻译 |
| `AGENT-BRIEF.md:14` | 应点名具体类型、函数签名和配置结构已翻译 |
| `AGENT-BRIEF.md:15` | 不引用会过期的文件路径已翻译 |
| `AGENT-BRIEF.md:16` | 不引用行号已翻译 |
| `AGENT-BRIEF.md:17` | 不假设当前实现结构不变已翻译 |
| `AGENT-BRIEF.md:19` | 描述行为而非步骤的标题已翻译 |
| `AGENT-BRIEF.md:21` | 说明做什么而非如何实现、agent 重新探索并自行决定均已保留 |
| `AGENT-BRIEF.md:23` | `SkillConfig`、可选 `schedule` 字段和 `CronExpression` 类型好例已保留 |
| `AGENT-BRIEF.md:24` | 文件路径、行号和增加字段的差例已保留 |
| `AGENT-BRIEF.md:25` | 无参数运行 triage 显示待关注 issue 摘要好例已保留 |
| `AGENT-BRIEF.md:26` | 在主 handler 中加 switch 语句的差例已保留 |
| `AGENT-BRIEF.md:28` | 完整验收判据标题已翻译 |
| `AGENT-BRIEF.md:30` | 完成判定、具体可测试和每项独立验证均已保留 |
| `AGENT-BRIEF.md:32` | `gh issue list` 返回已初步分类 issue 的好例已保留 |
| `AGENT-BRIEF.md:33` | “Triage 应正确运行”的差例已翻译 |
| `AGENT-BRIEF.md:35` | 明确范围边界标题已翻译 |
| `AGENT-BRIEF.md:37` | 写明范围外内容、防止过度打磨和相邻功能假设均已保留 |
| `AGENT-BRIEF.md:39` | 模板标题已翻译 |
| `AGENT-BRIEF.md:41` | Markdown 代码块起始已保留 |
| `AGENT-BRIEF.md:42` | `Agent Brief` 模板标题已保留 |
| `AGENT-BRIEF.md:44` | `Category` 字段和两种取值已保留 |
| `AGENT-BRIEF.md:45` | `Summary` 字段与一行说明占位已翻译 |
| `AGENT-BRIEF.md:47` | `Current behavior` 字段已保留 |
| `AGENT-BRIEF.md:48` | 当前发生内容及 bug 含义已翻译 |
| `AGENT-BRIEF.md:49` | enhancement 所依托现状已翻译 |
| `AGENT-BRIEF.md:51` | `Desired behavior` 字段已保留 |
| `AGENT-BRIEF.md:52` | agent 完成后的行为已翻译 |
| `AGENT-BRIEF.md:53` | 边界情况和错误条件已翻译 |
| `AGENT-BRIEF.md:55` | `Key interfaces` 字段已保留 |
| `AGENT-BRIEF.md:56` | `TypeName` 改动及原因占位已翻译 |
| `AGENT-BRIEF.md:57` | 函数返回类型当前与目标差异已翻译 |
| `AGENT-BRIEF.md:58` | 配置结构和新选项已翻译 |
| `AGENT-BRIEF.md:60` | `Acceptance criteria` 字段已保留 |
| `AGENT-BRIEF.md:61` | 具体可测试判据 1 已翻译 |
| `AGENT-BRIEF.md:62` | 具体可测试判据 2 已翻译 |
| `AGENT-BRIEF.md:63` | 具体可测试判据 3 已翻译 |
| `AGENT-BRIEF.md:65` | `Out of scope` 字段已保留 |
| `AGENT-BRIEF.md:66` | 本 issue 不应改动或处理的内容已翻译 |
| `AGENT-BRIEF.md:67` | 看似相关但独立的相邻功能已翻译 |
| `AGENT-BRIEF.md:68` | Markdown 代码块结束已保留 |
| `AGENT-BRIEF.md:70` | 示例标题已翻译 |
| `AGENT-BRIEF.md:72` | 良好 bug agent brief 标题已翻译 |
| `AGENT-BRIEF.md:74` | Markdown 代码块起始已保留 |
| `AGENT-BRIEF.md:75` | `Agent Brief` 标题已保留 |
| `AGENT-BRIEF.md:77` | bug 类别已保留 |
| `AGENT-BRIEF.md:78` | 技能描述在单词中间截断的摘要已翻译 |
| `AGENT-BRIEF.md:80` | `Current behavior` 字段已保留 |
| `AGENT-BRIEF.md:81` | 技能描述超过 1024 字符的条件已翻译 |
| `AGENT-BRIEF.md:82` | 不顾单词边界在 1024 字符处截断已翻译 |
| `AGENT-BRIEF.md:83` | 单词中间结束及原始字符串示例已保留 |
| `AGENT-BRIEF.md:85` | `Desired behavior` 字段已保留 |
| `AGENT-BRIEF.md:86` | 在 1024 前最后一个单词边界截断已翻译 |
| `AGENT-BRIEF.md:87` | 追加省略号表示截断已翻译 |
| `AGENT-BRIEF.md:89` | `Key interfaces` 字段已保留 |
| `AGENT-BRIEF.md:90` | `SkillMetadata.description` 无需改类型已保留 |
| `AGENT-BRIEF.md:91` | 填充字段的验证或处理逻辑已翻译 |
| `AGENT-BRIEF.md:92` | 尊重单词边界已翻译 |
| `AGENT-BRIEF.md:93` | 读取 SKILL.md frontmatter 并提取描述的函数已翻译 |
| `AGENT-BRIEF.md:95` | `Acceptance criteria` 字段已保留 |
| `AGENT-BRIEF.md:96` | 少于 1024 字符不变已翻译 |
| `AGENT-BRIEF.md:97` | 超过 1024 字符时在最后单词边界截断已翻译 |
| `AGENT-BRIEF.md:98` | 单词边界位于 1024 字符之前已翻译 |
| `AGENT-BRIEF.md:99` | 截断描述以省略号结尾已翻译 |
| `AGENT-BRIEF.md:100` | 含省略号总长不超过 1024 已翻译 |
| `AGENT-BRIEF.md:102` | `Out of scope` 字段已保留 |
| `AGENT-BRIEF.md:103` | 不改变 1024 字符限制已翻译 |
| `AGENT-BRIEF.md:104` | 不支持多行描述已翻译 |
| `AGENT-BRIEF.md:105` | Markdown 代码块结束已保留 |
| `AGENT-BRIEF.md:107` | 良好 enhancement agent brief 标题已翻译 |
| `AGENT-BRIEF.md:109` | Markdown 代码块起始已保留 |
| `AGENT-BRIEF.md:110` | `Agent Brief` 标题已保留 |
| `AGENT-BRIEF.md:112` | enhancement 类别已保留 |
| `AGENT-BRIEF.md:113` | 增加目录以跟踪被否决功能请求的摘要已翻译 |
| `AGENT-BRIEF.md:115` | `Current behavior` 字段已保留 |
| `AGENT-BRIEF.md:116` | 功能请求被否决时以 wontfix 关闭已翻译 |
| `AGENT-BRIEF.md:117` | 评论存在但没有持久决定或理由记录已翻译 |
| `AGENT-BRIEF.md:118` | 后续相似请求要求维护者回忆或搜索已翻译 |
| `AGENT-BRIEF.md:119` | 先前讨论已翻译 |
| `AGENT-BRIEF.md:121` | `Desired behavior` 字段已保留 |
| `AGENT-BRIEF.md:122` | 被否决请求记录到按概念命名文件已翻译 |
| `AGENT-BRIEF.md:123` | 文件保存决定、理由和全部 issue 链接已翻译 |
| `AGENT-BRIEF.md:124` | 分诊新 issue 时检查这些文件已翻译 |
| `AGENT-BRIEF.md:125` | 检查是否匹配已翻译 |
| `AGENT-BRIEF.md:127` | `Key interfaces` 字段已保留 |
| `AGENT-BRIEF.md:128` | `.out-of-scope/` 中的 Markdown 格式已翻译 |
| `AGENT-BRIEF.md:129` | Concept、Decision 和 Reason 固定字段已保留 |
| `AGENT-BRIEF.md:130` | Prior requests 清单与 issue 链接已保留 |
| `AGENT-BRIEF.md:131` | triage 工作流应尽早读取全部知识库文件已翻译 |
| `AGENT-BRIEF.md:132` | 按概念相似性匹配传入 issue 已翻译 |
| `AGENT-BRIEF.md:134` | `Acceptance criteria` 字段已保留 |
| `AGENT-BRIEF.md:135` | wontfix 关闭功能会创建或更新文件已翻译 |
| `AGENT-BRIEF.md:136` | 文件含决定、理由和已关闭 issue 链接已翻译 |
| `AGENT-BRIEF.md:137` | 匹配文件已存在的条件已翻译 |
| `AGENT-BRIEF.md:138` | 追加 Prior requests 而非重复创建已保留 |
| `AGENT-BRIEF.md:139` | triage 期间检查并呈现已有文件已翻译 |
| `AGENT-BRIEF.md:140` | 新 issue 匹配先前否决的条件已翻译 |
| `AGENT-BRIEF.md:142` | `Out of scope` 字段已保留 |
| `AGENT-BRIEF.md:143` | 不自动匹配且由人类确认已翻译 |
| `AGENT-BRIEF.md:144` | 不重新开启先前否决功能已翻译 |
| `AGENT-BRIEF.md:145` | bug 报告不写入知识库已翻译 |
| `AGENT-BRIEF.md:146` | Markdown 代码块结束已保留 |
| `AGENT-BRIEF.md:148` | 良好 PR agent brief 标题已翻译 |
| `AGENT-BRIEF.md:150` | PR 当前行为描述 diff 状态且要求完成或修复已保留 |
| `AGENT-BRIEF.md:152` | Markdown 代码块起始已保留 |
| `AGENT-BRIEF.md:153` | `Agent Brief` 标题已保留 |
| `AGENT-BRIEF.md:155` | enhancement 类别已保留 |
| `AGENT-BRIEF.md:156` | 完成贡献者 `--json` 输出标志位的摘要已翻译 |
| `AGENT-BRIEF.md:158` | `Current behavior` 字段已保留 |
| `AGENT-BRIEF.md:159` | PR 增加 JSON 序列化标志位已翻译 |
| `AGENT-BRIEF.md:160` | 正常路径可运行且 diff 符合命令结构已翻译 |
| `AGENT-BRIEF.md:161` | 两个缺口中的人类文本错误输出已翻译 |
| `AGENT-BRIEF.md:162` | 新标志位没有测试覆盖已翻译 |
| `AGENT-BRIEF.md:164` | `Desired behavior` 字段已保留 |
| `AGENT-BRIEF.md:165` | 使用标志位时全部输出为 stdout 上合法 JSON 已翻译 |
| `AGENT-BRIEF.md:166` | 退出码不变且现有人类可读输出已翻译 |
| `AGENT-BRIEF.md:167` | 无标志位时保持不变已翻译 |
| `AGENT-BRIEF.md:169` | `Key interfaces` 字段已保留 |
| `AGENT-BRIEF.md:170` | 命令错误路径发出 error JSON 对象已保留 |
| `AGENT-BRIEF.md:171` | 不再发出纯文本错误已翻译 |
| `AGENT-BRIEF.md:172` | 复用 PR 已有序列化器且不引入第二份已翻译 |
| `AGENT-BRIEF.md:174` | `Acceptance criteria` 字段已保留 |
| `AGENT-BRIEF.md:175` | 成功和错误场景都发出有效 JSON 已翻译 |
| `AGENT-BRIEF.md:176` | 退出码与非 JSON 命令相同已翻译 |
| `AGENT-BRIEF.md:177` | 测试覆盖成功输出和一种错误已翻译 |
| `AGENT-BRIEF.md:178` | 默认输出逐字节不变已翻译 |
| `AGENT-BRIEF.md:180` | `Out of scope` 字段已保留 |
| `AGENT-BRIEF.md:181` | 不给其他命令增加 JSON 标志位已翻译 |
| `AGENT-BRIEF.md:182` | 不改变既定成功载荷 JSON 结构已翻译 |
| `AGENT-BRIEF.md:183` | Markdown 代码块结束已保留 |
| `AGENT-BRIEF.md:185` | 不良 agent brief 标题已翻译 |
| `AGENT-BRIEF.md:187` | Markdown 代码块起始已保留 |
| `AGENT-BRIEF.md:188` | `Agent Brief` 标题已保留 |
| `AGENT-BRIEF.md:190` | 修复 triage bug 的含混摘要已翻译 |
| `AGENT-BRIEF.md:192` | What to do 字段已保留 |
| `AGENT-BRIEF.md:193` | 含混的损坏描述与查看主文件已翻译 |
| `AGENT-BRIEF.md:194` | 第 150 行附近函数有问题已翻译 |
| `AGENT-BRIEF.md:196` | Files to change 字段已保留 |
| `AGENT-BRIEF.md:197` | handler 文件与第 150 行已保留 |
| `AGENT-BRIEF.md:198` | types 文件与第 42 行已保留 |
| `AGENT-BRIEF.md:199` | Markdown 代码块结束已保留 |
| `AGENT-BRIEF.md:201` | 不良原因引导句已翻译 |
| `AGENT-BRIEF.md:202` | 缺少类别已翻译 |
| `AGENT-BRIEF.md:203` | 描述含混及原例已翻译 |
| `AGENT-BRIEF.md:204` | 文件路径和行号会过期已翻译 |
| `AGENT-BRIEF.md:205` | 缺少验收判据已翻译 |
| `AGENT-BRIEF.md:206` | 缺少范围边界已翻译 |
| `AGENT-BRIEF.md:207` | 缺少当前与目标行为说明已翻译 |
| `OUT-OF-SCOPE.md:1` | Out-of-Scope 知识库标题已保留 |
| `OUT-OF-SCOPE.md:3` | 目录保存被否决功能请求的持久记录和两个目的已保留 |
| `OUT-OF-SCOPE.md:5` | 组织记忆、否决原因和 issue 关闭后不丢失推理已保留 |
| `OUT-OF-SCOPE.md:6` | 去重、匹配先前否决和避免重新争论已保留 |
| `OUT-OF-SCOPE.md:8` | 目录结构标题已翻译 |
| `OUT-OF-SCOPE.md:10` | 目录树代码块起始已保留 |
| `OUT-OF-SCOPE.md:11` | `.out-of-scope/` 根目录已保留 |
| `OUT-OF-SCOPE.md:12` | dark-mode 文件示例已保留 |
| `OUT-OF-SCOPE.md:13` | plugin-system 文件示例已保留 |
| `OUT-OF-SCOPE.md:14` | graphql-api 文件示例已保留 |
| `OUT-OF-SCOPE.md:15` | 目录树代码块结束已保留 |
| `OUT-OF-SCOPE.md:17` | 每个概念一份文件、多张相同 issue 合并到一份文件已保留 |
| `OUT-OF-SCOPE.md:19` | 文件格式标题已翻译 |
| `OUT-OF-SCOPE.md:21` | 轻松易读、短设计文档、段落代码样例与示例、首次读者可理解均已保留 |
| `OUT-OF-SCOPE.md:23` | Markdown 代码块起始已保留 |
| `OUT-OF-SCOPE.md:24` | 深色模式示例标题已翻译 |
| `OUT-OF-SCOPE.md:26` | 不支持深色模式或用户可见主题功能已翻译 |
| `OUT-OF-SCOPE.md:28` | 不在范围内的原因标题已翻译 |
| `OUT-OF-SCOPE.md:30` | 渲染管线假设单一调色板已翻译 |
| `OUT-OF-SCOPE.md:31` | 调色板由 ThemeConfig 定义且多主题需要后续项目已保留 |
| `OUT-OF-SCOPE.md:33` | 包裹整个组件树的主题 context provider 已翻译 |
| `OUT-OF-SCOPE.md:34` | 每个组件感知主题的样式解析已翻译 |
| `OUT-OF-SCOPE.md:35` | 用户主题偏好的持久化层已翻译 |
| `OUT-OF-SCOPE.md:37` | 重大架构改动和不符合方向已翻译 |
| `OUT-OF-SCOPE.md:38` | 项目专注内容创作及主题属于下游关注点已翻译 |
| `OUT-OF-SCOPE.md:39` | 嵌入或重新分发输出的使用方已翻译 |
| `OUT-OF-SCOPE.md:41` | TypeScript 代码块起始已保留 |
| `OUT-OF-SCOPE.md:42` | ThemeConfig interface 不支持运行时切换的注释已翻译 |
| `OUT-OF-SCOPE.md:43` | ThemeConfig interface 声明已保留 |
| `OUT-OF-SCOPE.md:44` | ColorPalette 字段及构建时解析单一调色板注释已保留 |
| `OUT-OF-SCOPE.md:45` | fonts 字段与 FontStack 类型已保留 |
| `OUT-OF-SCOPE.md:46` | interface 结束大括号已保留 |
| `OUT-OF-SCOPE.md:47` | TypeScript 代码块结束已保留 |
| `OUT-OF-SCOPE.md:49` | 先前请求标题已翻译 |
| `OUT-OF-SCOPE.md:51` | #42 深色模式支持请求已翻译 |
| `OUT-OF-SCOPE.md:52` | #87 可访问性夜间主题请求已翻译 |
| `OUT-OF-SCOPE.md:53` | #134 深色主题选项请求已翻译 |
| `OUT-OF-SCOPE.md:54` | Markdown 代码块结束已保留 |
| `OUT-OF-SCOPE.md:56` | 文件命名标题已翻译 |
| `OUT-OF-SCOPE.md:58` | 简短描述性 kebab-case、三个示例和无需打开即可识别均已保留 |
| `OUT-OF-SCOPE.md:60` | 编写理由标题已翻译 |
| `OUT-OF-SCOPE.md:62` | 理由要实质充分且说明原因已翻译 |
| `OUT-OF-SCOPE.md:64` | 项目范围或理念及主题属于下游的示例已翻译 |
| `OUT-OF-SCOPE.md:65` | 技术约束与架构冲突示例已翻译 |
| `OUT-OF-SCOPE.md:66` | 战略决定示例已翻译 |
| `OUT-OF-SCOPE.md:68` | 理由要持久、临时忙碌不是否决而是延期均已保留 |
| `OUT-OF-SCOPE.md:70` | 何时检查知识库标题已翻译 |
| `OUT-OF-SCOPE.md:72` | triage 第一步读取全部知识库文件已保留 |
| `OUT-OF-SCOPE.md:74` | 检查请求是否匹配现有范围外概念已翻译 |
| `OUT-OF-SCOPE.md:75` | 按概念相似性而非关键词及 night theme 示例已保留 |
| `OUT-OF-SCOPE.md:76` | 呈现匹配、先前否决理由和询问当前看法的完整话术已翻译 |
| `OUT-OF-SCOPE.md:78` | 维护者可选动作引导已翻译 |
| `OUT-OF-SCOPE.md:80` | 确认后追加先前请求并关闭已翻译 |
| `OUT-OF-SCOPE.md:81` | 重新考虑后删除或更新文件并正常分诊已翻译 |
| `OUT-OF-SCOPE.md:82` | 不同意匹配时按不同请求继续正常分诊已翻译 |
| `OUT-OF-SCOPE.md:84` | 何时写入知识库标题已翻译 |
| `OUT-OF-SCOPE.md:86` | 仅被否决为 wontfix 的 enhancement、排除 bug、PR 同规则和防止代码形式回流均已保留 |
| `OUT-OF-SCOPE.md:88` | 已实现的 wontfix 禁止写入、避免错误否决污染和关闭评论指出实现位置均已保留 |
| `OUT-OF-SCOPE.md:90` | 流程引导已翻译 |
| `OUT-OF-SCOPE.md:92` | 维护者决定功能请求不在范围内已翻译 |
| `OUT-OF-SCOPE.md:93` | 检查匹配文件已翻译 |
| `OUT-OF-SCOPE.md:94` | 已有文件时追加新 issue 到先前请求清单已翻译 |
| `OUT-OF-SCOPE.md:95` | 无文件时以概念、决定、理由和首项请求创建已翻译 |
| `OUT-OF-SCOPE.md:96` | 在 issue 发布解释决定并提到文件的评论已翻译 |
| `OUT-OF-SCOPE.md:97` | 带 wontfix 标签关闭 issue 已翻译 |
| `OUT-OF-SCOPE.md:99` | 更新或移除范围外文件标题已翻译 |
| `OUT-OF-SCOPE.md:101` | 维护者改变先前否决决定的条件已翻译 |
| `OUT-OF-SCOPE.md:103` | 删除知识库文件已翻译 |
| `OUT-OF-SCOPE.md:104` | 不必重新开启旧 issue 及其历史记录性质已翻译 |
| `OUT-OF-SCOPE.md:105` | 触发重新考虑的新 issue 正常分诊已翻译 |
| `agents/openai.yaml:1` | interface 配置键已保留 |
| `agents/openai.yaml:2` | Triage 显示名已保留 |
| `agents/openai.yaml:3` | 让 issue 经过分诊角色的短描述已翻译 |
| `agents/openai.yaml:4` | policy 配置键已保留 |
| `agents/openai.yaml:5` | 禁止隐式调用已保留 |

## 四项检查

| 检查 | 结论 |
| --- | --- |
| 遗漏 | 四份上游文件的 299 个非空行均有独立登记；没有遗漏正文、模板、代码或配置行 |
| 曲解 | 类别与状态机、PR 差异、验证、grilling、agent brief、快速覆盖和拒绝请求知识库的条件与完成动作均未改变 |
| 胡编 | 没有加入上游不存在的 MMW 技能、tracker 动作、审批关卡、文件路径或完成判据 |
| 术语 | 普通工程概念使用规范中文；技能名、状态值、模板字段和代码标识符保留英文；同一原词使用同一写法 |
