# `setup-matt-pocock-skills` 1.2.2 翻译审查

## 固定术语

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| issue tracker、issue、ticket | `issue tracker`、`issue`、`ticket` | 三种不同 tracker 对象不混称 |
| triage role、triage label | `triage role`、`triage label` | role 与实际 label 字符串保持区分 |
| request surface | 请求入口 | 表达 PR 或 MR 是否进入 triage 队列 |
| single-context、multi-context | 单 context、多 context | context 不擅自补成 bounded context |
| canonical | 规范 | 表达上游选定的固定 role 集合 |
| flag | 标志位 | 配置中的可切换状态 |
| child ticket、blocking、frontier | `child ticket`、`blocking`、`frontier` | Wayfinding 方法和 tracker 对象 |
| claim、resolve | `Claim`、`Resolve` | tracker 操作标题与状态动作 |
| context pointer | `context pointer` | 上游 map 中的引用对象 |
| filter | 筛选条件 | 标准中文技术译名 |

## 逐行完整性检查

空行只承担 Markdown 分隔，不包含待翻译文字。下表逐一登记其他每一行，包括目录树、命令和模板。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | setup 技能名已保留 |
| `SKILL.md:3` | 配置仓库、tracker、label、领域布局和首次使用前运行均已保留 |
| `SKILL.md:4` | 禁止隐式调用已保留 |
| `SKILL.md:5` | YAML 结束分隔符已保留 |
| `SKILL.md:7` | 技能标题已保留 |
| `SKILL.md:9` | 建立仓库级假定配置已保留 |
| `SKILL.md:11` | issue tracker 定义、GitHub 默认和本地 Markdown 支持已保留 |
| `SKILL.md:12` | 五种规范 triage role 的 label 字符串已保留 |
| `SKILL.md:13` | CONTEXT、ADR 位置和消费规则已保留 |
| `SKILL.md:15` | 提示驱动、非确定脚本、探索展示确认再写入均已保留 |
| `SKILL.md:17` | 流程标题已保留 |
| `SKILL.md:19` | 第 1 步探索已保留 |
| `SKILL.md:21` | 理解起始状态、读实际内容和不假设均已保留 |
| `SKILL.md:23` | remote 与 git config、GitHub 判定和仓库身份均已保留 |
| `SKILL.md:24` | 两个 agent 文档、存在性和 Agent skills 章节检查均已保留 |
| `SKILL.md:25` | 根 CONTEXT 与 CONTEXT-MAP 已保留 |
| `SKILL.md:26` | 系统和各 src ADR 目录已保留 |
| `SKILL.md:27` | docs/agents 与先前输出检查已保留 |
| `SKILL.md:28` | scratch 代表本地 Markdown tracker 约定已保留 |
| `SKILL.md:29` | triage 安装的两种判据和决定 B 节运行已保留 |
| `SKILL.md:30` | 三类 monorepo 信号、真正大型多 package 条件和无信号默认单 context 均已保留 |
| `SKILL.md:32` | 第 2 步展示与询问已保留 |
| `SKILL.md:34` | 总结已有缺失、按节顺序和一节一答均已保留 |
| `SKILL.md:36` | 推荐答案先行、一词接受、仅真分支解释、已定则跳节和两个跳过例均已保留 |
| `SKILL.md:38` | A 节 issue tracker 已保留 |
| `SKILL.md:40` | tracker 定义、三个技能读写、三类实现路径和选实际工作位置均已保留 |
| `SKILL.md:42` | GitHub 默认、remote 推断 GitHub GitLab、self-hosted 和其他偏好均已保留 |
| `SKILL.md:44` | GitHub Issues 与 gh CLI 已保留 |
| `SKILL.md:45` | GitLab Issues 与 glab 链接已保留 |
| `SKILL.md:46` | 本地 Markdown 路径和两类适用仓库已保留 |
| `SKILL.md:47` | 其他 tracker、两个例子、用户一段说明和自由文本记录均已保留 |
| `SKILL.md:49` | 记录文件、PR request flag、默认 off、不主动提和用户日后打开均已保留 |
| `SKILL.md:51` | B 节、无 triage 完全跳过和无技能无需 label 均已保留 |
| `SKILL.md:53` | 已安装时只问一问已保留 |
| `SKILL.md:55` | 保留默认 label 的原问句和推荐 yes 已保留 |
| `SKILL.md:57` | 五种 role 字面量、yes 原样写、no 才收 override、bug:triage 例和避免重复均已保留 |
| `SKILL.md:59` | C 节默认单 context、根两类文件、几乎全仓库和不询问直接写均已保留 |
| `SKILL.md:61` | 只有 monorepo 信号才提供多 context、map 指向和确认布局均已保留 |
| `SKILL.md:63` | 第 3 步确认并编辑已保留 |
| `SKILL.md:65` | 展示草稿引导已保留 |
| `SKILL.md:67` | Agent skills block、两文件选择和第 4 步规则均已保留 |
| `SKILL.md:68` | 三份 docs 内容和 triage 条件已保留 |
| `SKILL.md:70` | 写入前允许用户编辑已保留 |
| `SKILL.md:72` | 第 4 步写入已保留 |
| `SKILL.md:74` | 选编辑文件引导已保留 |
| `SKILL.md:76` | CLAUDE 存在则编辑已保留 |
| `SKILL.md:77` | 否则 AGENTS 存在则编辑已保留 |
| `SKILL.md:78` | 二者皆无询问用户且不代选已保留 |
| `SKILL.md:80` | 已存在一方绝不创建另一方已保留 |
| `SKILL.md:82` | 既有 block 原地更新、不重复和不覆盖周边用户改动均已保留 |
| `SKILL.md:84` | block 引导已保留 |
| `SKILL.md:86` | Markdown 代码块起始已保留 |
| `SKILL.md:87` | Agent skills 标题已保留 |
| `SKILL.md:89` | Issue tracker 子标题已保留 |
| `SKILL.md:91` | 一行 tracker 总结占位与链接已翻译 |
| `SKILL.md:93` | Triage labels 子标题已保留 |
| `SKILL.md:95` | 一行 label 总结占位与链接已翻译 |
| `SKILL.md:97` | Domain docs 子标题已保留 |
| `SKILL.md:99` | 一行布局总结、两个字面形态和链接已翻译 |
| `SKILL.md:100` | 代码块结束已保留 |
| `SKILL.md:102` | 仅 triage 安装且 B 运行才写子 block 与文件，否则均省略已保留 |
| `SKILL.md:104` | seed template 起点引导已保留 |
| `SKILL.md:106` | GitHub template 链接已保留 |
| `SKILL.md:107` | GitLab template 链接已保留 |
| `SKILL.md:108` | local template 链接已保留 |
| `SKILL.md:109` | label template 与安装条件已保留 |
| `SKILL.md:110` | domain template 与消费规则布局已保留 |
| `SKILL.md:112` | 其他 tracker 从用户说明重新编写已保留 |
| `SKILL.md:114` | 第 5 步完成已保留 |
| `SKILL.md:116` | 告知完成、哪些技能读取、可直接编辑和仅换 tracker 或重启才重跑均已保留 |
| `domain.md:1` | 领域文档标题已保留 |
| `domain.md:3` | 工程技能探索时消费领域文档的目的已保留 |
| `domain.md:5` | 探索前读取标题已保留 |
| `domain.md:7` | 根 CONTEXT 已保留 |
| `domain.md:8` | 可选根 CONTEXT-MAP、每 context 指针和读取相关项均已保留 |
| `domain.md:9` | 系统 ADR、相关区域和多 context 专属 ADR 均已保留 |
| `domain.md:11` | 缺失静默继续、不指出不预建、domain-modeling 按需创建和两个到达路径均已保留 |
| `domain.md:13` | 文件结构标题已保留 |
| `domain.md:15` | 多数仓库单 context 已保留 |
| `domain.md:17` | 单 context 目录树起始已保留 |
| `domain.md:18` | 根目录已保留 |
| `domain.md:19` | CONTEXT 已保留 |
| `domain.md:20` | docs/adr 已保留 |
| `domain.md:21` | 第一 ADR 示例已保留 |
| `domain.md:22` | 第二 ADR 示例已保留 |
| `domain.md:23` | src 已保留 |
| `domain.md:24` | 目录树结束已保留 |
| `domain.md:26` | 多 context 与根 map 判据已保留 |
| `domain.md:28` | 多 context 目录树起始已保留 |
| `domain.md:29` | 根目录已保留 |
| `domain.md:30` | 根 map 已保留 |
| `domain.md:31` | 系统级 ADR 及注释已保留 |
| `domain.md:32` | src 已保留 |
| `domain.md:33` | ordering 已保留 |
| `domain.md:34` | ordering CONTEXT 已保留 |
| `domain.md:35` | context 专属 ADR 及注释已保留 |
| `domain.md:36` | billing 已保留 |
| `domain.md:37` | billing CONTEXT 已保留 |
| `domain.md:38` | billing ADR 已保留 |
| `domain.md:39` | 目录树结束已保留 |
| `domain.md:41` | 使用术语表词汇标题已保留 |
| `domain.md:43` | 四类输出位置、CONTEXT 定义词和禁止 Avoid 同义词均已保留 |
| `domain.md:45` | 缺词信号、发明项目未用语言需重想或真实缺口记 domain-modeling 均已保留 |
| `domain.md:47` | 标记 ADR 冲突标题已保留 |
| `domain.md:49` | 冲突显式呈现而非静默覆盖已保留 |
| `domain.md:51` | ADR-0007 event-sourced orders 示例已翻译 |
| `issue-tracker-github.md:1` | GitHub tracker 标题已保留 |
| `issue-tracker-github.md:3` | issue spec 存 GitHub issue 和全操作用 gh 已保留 |
| `issue-tracker-github.md:5` | 约定标题已保留 |
| `issue-tracker-github.md:7` | 创建命令和多行 heredoc 已保留 |
| `issue-tracker-github.md:8` | 读取含 comments、jq filter 和 labels 均已保留 |
| `issue-tracker-github.md:9` | 列表完整命令和 label state filter 均已保留 |
| `issue-tracker-github.md:10` | comment 命令已保留 |
| `issue-tracker-github.md:11` | label 增删命令已保留 |
| `issue-tracker-github.md:12` | close 命令与 comment 已保留 |
| `issue-tracker-github.md:14` | remote 推断和 clone 内 gh 自动判定已保留 |
| `issue-tracker-github.md:16` | PR 作为 triage 入口标题已保留 |
| `issue-tracker-github.md:18` | request surface no、改 yes 条件和 triage 读 flag 均已保留 |
| `issue-tracker-github.md:20` | yes 后 PR 同 labels states 和 gh pr 等价命令均已保留 |
| `issue-tracker-github.md:22` | PR 读取与 diff 两命令已保留 |
| `issue-tracker-github.md:23` | 外部 PR 列表命令、保留三 association 和删除三 association 均已保留 |
| `issue-tracker-github.md:24` | comment label close 三类命令已保留 |
| `issue-tracker-github.md:26` | GitHub 共用编号、裸 42 二义和先 PR 后 issue fallback 均已保留 |
| `issue-tracker-github.md:28` | publish to tracker 标题已保留 |
| `issue-tracker-github.md:30` | 创建 GitHub issue 已保留 |
| `issue-tracker-github.md:32` | fetch ticket 标题已保留 |
| `issue-tracker-github.md:34` | 读取 issue 命令已保留 |
| `issue-tracker-github.md:36` | Wayfinding 操作标题已保留 |
| `issue-tracker-github.md:38` | wayfinder 使用、单 map issue 和 child issue ticket 均已保留 |
| `issue-tracker-github.md:40` | map label、三段正文和创建命令均已保留 |
| `issue-tracker-github.md:41` | child sub-issue、endpoint、fallback task list 与 Part of、四 type label 和认领分配均已保留 |
| `issue-tracker-github.md:42` | 原生 dependency、完整 add edge 命令、database id 获取与两个非 id、summary gate、fallback 行和全 closed 解阻塞均已保留 |
| `issue-tracker-github.md:43` | frontier 开 child、scope、两类 open blocker、assignee 和 map 顺序首项均已保留 |
| `issue-tracker-github.md:44` | claim 命令和 session 首次写已保留 |
| `issue-tracker-github.md:45` | comment close、context pointer 与 map Decisions 追加均已保留 |
| `issue-tracker-gitlab.md:1` | GitLab tracker 标题已保留 |
| `issue-tracker-gitlab.md:3` | issue spec 存 GitLab issue、glab 链接和全操作已保留 |
| `issue-tracker-gitlab.md:5` | 约定标题已保留 |
| `issue-tracker-gitlab.md:7` | 创建、description、heredoc 和 editor flag 均已保留 |
| `issue-tracker-gitlab.md:8` | 读取与 JSON 输出已保留 |
| `issue-tracker-gitlab.md:9` | 列表和 label filter 已保留 |
| `issue-tracker-gitlab.md:10` | comment note 命令和 GitLab 命名已保留 |
| `issue-tracker-gitlab.md:11` | label 增删、逗号或重复 flag 均已保留 |
| `issue-tracker-gitlab.md:12` | close 无 comment、先 note 后 close 均已保留 |
| `issue-tracker-gitlab.md:13` | MR 命名、三命令和 gh pr 到 glab mr note message 映射均已保留 |
| `issue-tracker-gitlab.md:15` | remote 推断与 clone 内 glab 自动判定已保留 |
| `issue-tracker-gitlab.md:17` | MR 作为 triage 入口标题已保留 |
| `issue-tracker-gitlab.md:19` | request surface no、改 yes 条件和 triage 读 flag 均已保留 |
| `issue-tracker-gitlab.md:21` | yes 后 MR 同 label state 和 glab mr 等价命令均已保留 |
| `issue-tracker-gitlab.md:23` | MR 读取与 diff 已保留 |
| `issue-tracker-gitlab.md:24` | 外部 MR 列表、作者非 member owner 和 contributor 非 maintainer 条件均已保留 |
| `issue-tracker-gitlab.md:25` | comment label close 命令已保留 |
| `issue-tracker-gitlab.md:27` | GitLab 分开编号和知道 surface 后无歧义均已保留 |
| `issue-tracker-gitlab.md:29` | publish 标题已保留 |
| `issue-tracker-gitlab.md:31` | 创建 GitLab issue 已保留 |
| `issue-tracker-gitlab.md:33` | fetch ticket 标题已保留 |
| `issue-tracker-gitlab.md:35` | 读取命令已保留 |
| `issue-tracker-gitlab.md:37` | Wayfinding 操作标题已保留 |
| `issue-tracker-gitlab.md:39` | 单 map issue 和 child issue ticket 已保留 |
| `issue-tracker-gitlab.md:41` | map label、三段正文、创建命令、native epic tier 例外和 issue 通用均已保留 |
| `issue-tracker-gitlab.md:42` | child Part of、四 type label 和认领分配均已保留 |
| `issue-tracker-gitlab.md:43` | 原生 blocking link、quick action note 命令、付费 tier、免费 fallback 和全 closed 解阻塞均已保留 |
| `issue-tracker-gitlab.md:44` | frontier 命令、map child scope、两类 open blocker、API、assignee 和 map 顺序首项均已保留 |
| `issue-tracker-gitlab.md:45` | claim 命令和 session 首次写已保留 |
| `issue-tracker-gitlab.md:46` | note close、context pointer 与 map Decisions 追加均已保留 |
| `issue-tracker-local.md:1` | 本地 Markdown tracker 标题已保留 |
| `issue-tracker-local.md:3` | issue spec 存 scratch Markdown 已保留 |
| `issue-tracker-local.md:5` | 约定标题已保留 |
| `issue-tracker-local.md:7` | 每 feature 一目录路径已保留 |
| `issue-tracker-local.md:8` | spec 路径已保留 |
| `issue-tracker-local.md:9` | 每 ticket 一 implementation 文件、路径、01 编号和禁止合并文件均已保留 |
| `issue-tracker-local.md:10` | Status 行和 role 字符串 reference 已保留 |
| `issue-tracker-local.md:11` | Comments 标题下追加历史已保留 |
| `issue-tracker-local.md:13` | publish 标题已保留 |
| `issue-tracker-local.md:15` | scratch 路径新文件和按需建目录已保留 |
| `issue-tracker-local.md:17` | fetch 标题已保留 |
| `issue-tracker-local.md:19` | 读引用路径和用户通常传路径或编号已保留 |
| `issue-tracker-local.md:21` | Wayfinding 操作标题已保留 |
| `issue-tracker-local.md:23` | map 文件与每 ticket child 文件已保留 |
| `issue-tracker-local.md:25` | map 路径和三段正文已保留 |
| `issue-tracker-local.md:26` | child 路径、01 编号、问题、Type 四值和 Status 两值均已保留 |
| `issue-tracker-local.md:27` | Blocked by 行和全 resolved 解阻塞均已保留 |
| `issue-tracker-local.md:28` | frontier 扫描、open unblocked unclaimed 和编号首项均已保留 |
| `issue-tracker-local.md:29` | 工作前 claim 并保存已保留 |
| `issue-tracker-local.md:30` | Answer、resolved 和 context pointer 追加 map Decisions 均已保留 |
| `triage-labels.md:1` | Triage Labels 标题已保留 |
| `triage-labels.md:3` | 五种规范 role 和映射实际 label 字符串均已保留 |
| `triage-labels.md:5` | 三列表头已翻译 |
| `triage-labels.md:6` | 表格分隔行已保留 |
| `triage-labels.md:7` | needs-triage 两侧字面量和 maintainer 评估含义已保留 |
| `triage-labels.md:8` | needs-info 两侧字面量和等待 reporter 含义已保留 |
| `triage-labels.md:9` | ready-for-agent 两侧字面量、完全明确和 AFK agent 含义已保留 |
| `triage-labels.md:10` | ready-for-human 两侧字面量和人类 implementation 含义已保留 |
| `triage-labels.md:11` | wontfix 两侧字面量和不执行含义已保留 |
| `triage-labels.md:13` | 技能提 role、AFK-ready 例和使用对应 label 字符串均已保留 |
| `triage-labels.md:15` | 编辑右列匹配实际词汇已保留 |
| `agents/openai.yaml:1` | interface 字段已保留 |
| `agents/openai.yaml:2` | display name 已保留 |
| `agents/openai.yaml:3` | 配置仓库技能已保留 |
| `agents/openai.yaml:4` | policy 字段已保留 |
| `agents/openai.yaml:5` | 禁止隐式调用已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。七个上游文件的每个非空行，包括三种 tracker 的完整 Wayfinding 操作，都有对应译文和独立检查记录 |
| 增写 | 无。没有加入 `.mmw.json`、MMW CLI、宿主物化、当前 tracker 合同或其他 MMW 接线 |
| 曲解 | 无。探索后逐节询问、用户审阅草稿后才写入、已有 agent 文档二选一和 tracker 模板完整保留 |
| 术语漂移 | 无。issue tracker、triage role、triage label、context、request surface、child ticket、blocking 和 frontier 使用一致 |
