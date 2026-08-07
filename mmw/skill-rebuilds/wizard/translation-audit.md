# `wizard` 1.2.2 翻译审查

## 本技能术语应用

共享术语只由 [上游技能翻译共享术语](../translation-terms.md) 定义。下表记录本技能的术语应用和独有术语，不建立第二份定义。

| 上游原词 | 统一写法 | 理由 |
| --- | --- | --- |
| wizard | `wizard` | 技能和生成脚本的固定名称 |
| stage | 阶段；辅助函数写 `stage` | 普通叙述使用中文，函数名保留 |
| helper | 辅助函数 | 标准中文技术译名；具体函数名保留英文 |
| secret、variable | `secret`、`variable` | GitHub 与 CI 对象名称 |
| cutover | `cutover` | 上游触发词，避免误缩成普通切换 |
| migration | 迁移 | 标准中文技术译名，不额外限定为数据库迁移 |
| upsert | `upsert` | 固定写入语义 |
| idempotent | 幂等 | 标准中文技术译名 |
| confirmation gate | 确认关卡 | 保留继续执行前必须确认的含义 |
| ephemeral | 临时 | 表达默认只供一次运行 |
| library | 库 | 标准中文技术译名；指 `STAGES` 上方固定代码区 |

## 逐行完整性检查

空行只承担 Markdown 或 Shell 分隔，不包含待翻译文字。下表逐一登记其他每一行。

| 上游行 | 本行翻译检查 |
| --- | --- |
| `SKILL.md:1` | YAML 起始分隔符已保留 |
| `SKILL.md:2` | `name: wizard` 字面量已保留 |
| `SKILL.md:3` | 交互 Bash、人类专属步骤、基础设施、凭证、CI secret、第三方仪表板、一次性迁移、cutover 和 agent 能做则不用均已保留 |
| `SKILL.md:4` | YAML 结束分隔符已保留 |
| `SKILL.md:6` | Wizard 标题已保留 |
| `SKILL.md:8` | Bash 脚本、人类逐步手动流程、两种繁琐、开 URL、点击复制、捕获写入、两类落点、逐阶段确认、剩余量和三类用途均已保留 |
| `SKILL.md:10` | 模板已解决 UX、七项能力、职责仅限定流程与编写阶段、STAGES 上方库相同、一致性目的和禁止手改均已保留 |
| `SKILL.md:12` | 默认临时、一次运行、scratch 或 scripts、完工删除和用户要可重复路径才 commit 均已保留 |
| `SKILL.md:14` | 流程标题已保留 |
| `SKILL.md:16` | 第 1 步限定流程已保留 |
| `SKILL.md:18` | 找全人工步骤和值、先读仓库和不冷问均已保留 |
| `SKILL.md:20` | 设置流程的七类文件、workflow glob 和每个 secrets vars 引用必须产值均已保留 |
| `SKILL.md:21` | 迁移过渡的当前状态、目标状态和不可逆动作均已保留 |
| `SKILL.md:23` | 展示有序 stage 与产值、用户确认和可增删排序均已保留 |
| `SKILL.md:25` | 完成判据中的阶段顺序、值来源、四类落点、纯动作例外、secret 隐藏与公开均已保留 |
| `SKILL.md:27` | 第 2 步描绘每阶段 journey 已保留 |
| `SKILL.md:29` | URL、动作、值位置、变量、完整示例、不知 UI 命令时说明询问查文档和禁止编造均已保留 |
| `SKILL.md:31` | 每阶段具体到陌生人可遵循的完成判据已保留 |
| `SKILL.md:33` | 第 3 步编写 wizard 已保留 |
| `SKILL.md:35` | 复制模板、每步一 stage、依赖顺序、全部辅助函数、两个总量诚实估计和剩余时间用途均已保留 |
| `SKILL.md:37` | 先开 URL、secret 辅助函数、所有持久值、仅 CI 值、不可逆确认、每 stage 清屏、聚焦单任务、防滚屏和禁止改库均已保留 |
| `SKILL.md:39` | 第 4 步验证与 hand off 已保留 |
| `SKILL.md:41` | bash -n 和可用时 shellcheck 已保留 |
| `SKILL.md:42` | chmod +x 已保留 |
| `SKILL.md:43` | 禁止端到端运行、浏览器与人工阻塞理由、静态追踪所有值和 set_secret 精确匹配 CI 均已保留 |
| `SKILL.md:44` | 告知运行方式、可重复时 commit 并 README 链接和下一人不问 AI 均已保留 |
| `template.sh:1` | Bash shebang 已保留 |
| `template.sh:2` | 注释分隔行已保留 |
| `template.sh:3` | wizard 逐步人工流程注释已翻译 |
| `template.sh:4` | 由 wizard 技能生成已翻译 |
| `template.sh:5` | 注释分隔行已保留 |
| `template.sh:6` | STAGES 上方是库且禁止手改已翻译 |
| `template.sh:7` | 标记下方编写阶段已翻译 |
| `template.sh:9` | `set -euo pipefail` 已保留 |
| `template.sh:11` | 库上方分隔线已保留 |
| `template.sh:12` | wizard 库的愉悦一致 UX 和全 wizard 相同已翻译 |
| `template.sh:13` | 库下方分隔线已保留 |
| `template.sh:15` | terminal、tput、colors 条件已保留 |
| `template.sh:16` | BOLD DIM RESET 赋值已保留 |
| `template.sh:17` | 四个颜色变量赋值已保留 |
| `template.sh:18` | else 已保留 |
| `template.sh:19` | 无颜色 fallback 赋值已保留 |
| `template.sh:20` | if 结束已保留 |
| `template.sh:22` | 编写者设置两个总量的注释已翻译 |
| `template.sh:23` | TOTAL_STAGES 初值已保留 |
| `template.sh:24` | TOTAL_MINUTES 初值已保留 |
| `template.sh:26` | stage index 初值已保留 |
| `template.sh:27` | elapsed minutes 初值已保留 |
| `template.sh:28` | ENV_FILE 默认 `.env` 已保留 |
| `template.sh:29` | WRITTEN_ENV 数组与本次写入 KEY 注释已保留 |
| `template.sh:30` | WRITTEN_SECRET 数组与 secret NAME 注释已保留 |
| `template.sh:31` | SKIPPED 数组与 gh 例子注释已保留 |
| `template.sh:33` | _clear 清 terminal 与当前步骤目的注释已翻译 |
| `template.sh:34` | 非 terminal no-op 和管道日志可读已翻译 |
| `template.sh:35` | _clear 函数起始已保留 |
| `template.sh:36` | 非 terminal return 已保留 |
| `template.sh:37` | tput clear 与 ANSI fallback 已保留 |
| `template.sh:38` | _clear 结束已保留 |
| `template.sh:40` | banner 参数、开场作用与时间注释已翻译 |
| `template.sh:41` | banner 函数起始已保留 |
| `template.sh:42` | _clear 调用已保留 |
| `template.sh:43` | 标题 printf 已保留 |
| `template.sh:44` | 阶段数与分钟可见格式已翻译 |
| `template.sh:45` | 四个格式参数已保留 |
| `template.sh:46` | 用户操作浏览器和 wizard 指示开句已翻译 |
| `template.sh:47` | 捕获值、Ctrl-C 停止和稍后重跑已翻译 |
| `template.sh:48` | 记住已保存值已翻译 |
| `template.sh:49` | 准备开始 pause 已翻译 |
| `template.sh:50` | banner 结束已保留 |
| `template.sh:52` | stage 参数、清屏、宣布阶段注释已翻译 |
| `template.sh:53` | 进度、剩余时间和只留当前步骤已翻译 |
| `template.sh:54` | stage 函数起始已保留 |
| `template.sh:55` | _clear 已保留 |
| `template.sh:56` | stage index 加一已保留 |
| `template.sh:57` | remaining 计算已保留 |
| `template.sh:58` | remaining 下限为零已保留 |
| `template.sh:59` | elapsed 增加 stage 分钟已保留 |
| `template.sh:60` | 阶段进度和剩余分钟文字已翻译，printf 结构已保留 |
| `template.sh:61` | 九个格式参数已保留 |
| `template.sh:62` | stage 结束已保留 |
| `template.sh:64` | say 普通指令注释已翻译 |
| `template.sh:65` | say 函数已保留 |
| `template.sh:66` | step 浏览器动作注释已翻译 |
| `template.sh:67` | step 函数已保留 |
| `template.sh:68` | note 函数已保留 |
| `template.sh:69` | warn 函数已保留 |
| `template.sh:71` | open_url 跨平台含 WSL 注释已翻译 |
| `template.sh:72` | open_url 起始已保留 |
| `template.sh:73` | local url 已保留 |
| `template.sh:74` | 正在打开可见文字已翻译 |
| `template.sh:75` | wslview 分支已保留 |
| `template.sh:76` | explorer.exe 分支已保留 |
| `template.sh:77` | xdg-open 分支已保留 |
| `template.sh:78` | open 分支已保留 |
| `template.sh:79` | 无浏览器命令 warning 已翻译 |
| `template.sh:80` | 打开失败 warning 已翻译，重定向已保留 |
| `template.sh:81` | open_url 结束已保留 |
| `template.sh:83` | pause 参数和人工确认注释已翻译 |
| `template.sh:84` | pause 起始已保留 |
| `template.sh:85` | 默认按 Enter 提示已翻译 |
| `template.sh:86` | read 已保留 |
| `template.sh:87` | pause 结束已保留 |
| `template.sh:89` | confirm 参数、y/N gate 和 yes 成功已翻译 |
| `template.sh:90` | confirm 起始已保留 |
| `template.sh:91` | reply 初值已保留 |
| `template.sh:92` | question 与 y/N 输出已保留 |
| `template.sh:93` | read reply 已保留 |
| `template.sh:94` | Y 或 y 正则成功判据已保留 |
| `template.sh:95` | confirm 结束已保留 |
| `template.sh:97` | _existing 取 ENV_FILE 当前 KEY 注释已翻译 |
| `template.sh:98` | _existing 起始已保留 |
| `template.sh:99` | 文件存在判据已保留 |
| `template.sh:100` | grep 最后一项 KEY 值已保留 |
| `template.sh:101` | 去掉等号前缀输出已保留 |
| `template.sh:102` | _existing 结束已保留 |
| `template.sh:104` | ask 参数、读入 KEY、现有 env 默认注释已翻译 |
| `template.sh:105` | 重跑 Enter 保留与可见非 secret 已翻译 |
| `template.sh:106` | ask 起始已保留 |
| `template.sh:107` | 五个 local 变量已保留 |
| `template.sh:108` | current 读取已保留 |
| `template.sh:109` | current 非空条件已保留 |
| `template.sh:110` | Enter 保留当前值提示已翻译 |
| `template.sh:111` | else 已保留 |
| `template.sh:112` | 无 current 的 prompt 输出已保留 |
| `template.sh:113` | if 结束已保留 |
| `template.sh:114` | read input 已保留 |
| `template.sh:115` | 空 input 使用 current 已保留 |
| `template.sh:116` | printf 写入动态 key 已保留 |
| `template.sh:117` | ask 结束已保留 |
| `template.sh:119` | ask_secret 如 ask 但隐藏输入注释已翻译 |
| `template.sh:120` | ask_secret 起始已保留 |
| `template.sh:121` | 五个 local 变量已保留 |
| `template.sh:122` | current 读取已保留 |
| `template.sh:123` | current 非空条件已保留 |
| `template.sh:124` | Enter 保留当前值提示已翻译 |
| `template.sh:125` | else 已保留 |
| `template.sh:126` | 无 current 的 prompt 输出已保留 |
| `template.sh:127` | if 结束已保留 |
| `template.sh:128` | read -s 隐藏输入已保留 |
| `template.sh:129` | 换行输出已保留 |
| `template.sh:130` | 空 input 使用 current 已保留 |
| `template.sh:131` | printf 写入动态 key 已保留 |
| `template.sh:132` | ask_secret 结束已保留 |
| `template.sh:134` | write_env upsert、创建与替换注释已翻译 |
| `template.sh:135` | 幂等注释已翻译 |
| `template.sh:136` | write_env 起始已保留 |
| `template.sh:137` | key value tmp 已保留 |
| `template.sh:138` | touch ENV_FILE 已保留 |
| `template.sh:139` | mktemp 已保留 |
| `template.sh:140` | 过滤旧 key 行已保留 |
| `template.sh:141` | 追加新 KEY=VALUE 已保留 |
| `template.sh:142` | 临时文件覆盖 ENV_FILE 已保留 |
| `template.sh:143` | 记录 WRITTEN_ENV 已保留 |
| `template.sh:144` | 已写入提示已翻译 |
| `template.sh:145` | write_env 结束已保留 |
| `template.sh:147` | set_secret 经 gh 写 GitHub Actions repo secret 注释已翻译 |
| `template.sh:148` | gh 不可用未认证时 warning 与记录已翻译 |
| `template.sh:149` | set_secret 起始已保留 |
| `template.sh:150` | name value 已保留 |
| `template.sh:151` | gh 存在且认证条件已保留 |
| `template.sh:152` | pipe value 到 gh secret set 已保留 |
| `template.sh:153` | 记录 WRITTEN_SECRET 已保留 |
| `template.sh:154` | 已设置 secret 提示已翻译 |
| `template.sh:155` | return 已保留 |
| `template.sh:156` | 内层 if 结束已保留 |
| `template.sh:157` | 外层 if 结束已保留 |
| `template.sh:158` | SKIPPED 手动命令已翻译并保留命令 |
| `template.sh:159` | 跳过 secret warning 已翻译 |
| `template.sh:160` | set_secret 结束已保留 |
| `template.sh:162` | set_var GitHub Actions repo variable 非 secret 注释已翻译 |
| `template.sh:163` | set_var 起始已保留 |
| `template.sh:164` | name value 已保留 |
| `template.sh:165` | gh 存在且认证条件已保留 |
| `template.sh:166` | gh variable set 命令已保留 |
| `template.sh:167` | 已设置 variable 提示已翻译 |
| `template.sh:168` | return 已保留 |
| `template.sh:169` | 内层 if 结束已保留 |
| `template.sh:170` | 外层 if 结束已保留 |
| `template.sh:171` | SKIPPED variable 已保留 |
| `template.sh:172` | 跳过 variable warning 已翻译 |
| `template.sh:173` | set_var 结束已保留 |
| `template.sh:175` | finish 清屏与结束总结注释已翻译 |
| `template.sh:176` | finish 起始已保留 |
| `template.sh:177` | _clear 已保留 |
| `template.sh:178` | 设置完成提示已翻译 |
| `template.sh:179` | 写入 env 数量、路径和 key 总结已翻译 |
| `template.sh:180` | secret 数量和名称总结已翻译 |
| `template.sh:181` | SKIPPED 非空条件已保留 |
| `template.sh:182` | 仍需手工完成提示已翻译 |
| `template.sh:183` | 遍历 skipped 并列项已保留 |
| `template.sh:184` | if 结束已保留 |
| `template.sh:185` | 末尾换行已保留 |
| `template.sh:186` | finish 结束已保留 |
| `template.sh:188` | STAGES 上分隔线已保留 |
| `template.sh:189` | 编写章节和每人工步骤一个 stage 注释已翻译 |
| `template.sh:190` | 替换示例和总量匹配注释已翻译 |
| `template.sh:191` | STAGES 下分隔线已保留 |
| `template.sh:193` | 示例总阶段 1 已保留 |
| `template.sh:194` | 示例总分钟 5 已保留 |
| `template.sh:196` | Stripe 设置 banner 已翻译 |
| `template.sh:198` | 示例阶段替换提示已翻译 |
| `template.sh:199` | Stripe API key stage 和 5 分钟已翻译 |
| `template.sh:200` | 取得测试 key 并供本地和 CI 使用已翻译 |
| `template.sh:201` | Stripe URL 已保留 |
| `template.sh:202` | Publishable key 页面、前缀和复制动作已翻译 |
| `template.sh:203` | STRIPE_PUBLISHABLE_KEY 和粘贴提示已保留并翻译 |
| `template.sh:204` | Reveal test key、Secret key 行和复制动作已保留并翻译 |
| `template.sh:205` | STRIPE_SECRET_KEY 隐藏询问已保留并翻译 |
| `template.sh:206` | publishable key 写 env 已保留 |
| `template.sh:207` | secret key 写 env 已保留 |
| `template.sh:208` | secret key 写 CI 和 CI 需要注释已保留 |
| `template.sh:209` | 示例阶段下分隔线已保留 |
| `template.sh:211` | finish 调用已保留 |
| `agents/openai.yaml:1` | `interface` 字段已保留 |
| `agents/openai.yaml:2` | `display_name: "Wizard"` 已保留 |
| `agents/openai.yaml:3` | 生成交互式设置 wizard 已保留 |

## 四类检查

| 检查 | 结果 |
| --- | --- |
| 遗漏 | 无。三个上游文件的每个非空行，包括 211 行 Bash 模板，都有对应译文和独立检查记录 |
| 增写 | 无。没有加入 `mmw path scratch`、任务 slug、Wayfinder 产物目录或其他 MMW 接线 |
| 曲解 | 无。先与用户确认阶段和值落点、再生成，固定库不手改，只静态验证不代替用户运行三项保持原样 |
| 术语漂移 | 无。wizard、阶段、辅助函数、secret、variable、迁移、cutover、upsert、幂等和库使用一致 |
