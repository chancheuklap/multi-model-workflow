# TESTING.md（本仓库薄层）

> 通用测试方法在 `mmw-tdd/SKILL.md`、`mmw-tdd/tests.md` 和 `mmw-tdd/mocking.md`。本文记录本仓库的目录、分层、外部边界和运行命令。两者冲突时点名具体冲突，不静默覆盖。

## 目录分层

这个仓库不按单元与集成分层，按被测面分层。三层都在 `mmw/` 下。

| 层 | 位置 | 测什么 |
| --- | --- | --- |
| 命令行为 | `mmw/cli/tests/guardrails.sh`、`test_issue.sh`、`test_domain.sh`、`test_artifact.sh`、`test_init.sh`、`mmw/release/tests/test_release_flow.sh`、`test_release_classify.sh`、`test_release_dispatch.sh` | 在一次性 Git 仓库上跑真命令。护栏拒绝了什么、拒绝之后破坏有没有发生、命令写出了什么文件、派发的 argv 长什么样 |
| 纯函数 | `mmw/graph/tests/test_graph.py`、`mmw/release/tests/test_release_contracts.py`、`test_release_script_assembler.py` | 给定输入返回什么。跨语言边解析、配置解析、出包合同、脚本装配 |
| 源与产物一致性 | `mmw/cli/tests/test_materialize_skills.py`、`test_materialize_agents.py`、`test_skill_refs.sh`、`test_skill_paths.sh`、`mmw/mcp/test_graphify_ensure.py` | 技能源与角色源物化成各宿主产物时展开了什么、什么必须当场失败；技能之间的四类引用指不指得到东西；技能源有没有写产物落点字面值 |

不收「版本号五处互相相等」这类断言。它只证明复制粘贴没出错，不证明任何行为，而且改内容忘了改版本号时它照样绿。

## 外部 seam

`mmw-tdd/mocking.md` 说只在系统边界上 mock。本仓库的替代方式是同一种：写一个假可执行文件，放进一次性目录，再把那个目录加到 `PATH` 最前面。下表逐条给出去哪看现成做法——用文件名和标识去 grep，不写行号。

| 边界 | 替身 | 现成做法 |
| --- | --- | --- |
| GitHub Issues | `gh` | `mmw/cli/tests/test_issue.sh` 里 `$WORK/bin/gh` 那个 heredoc。它按整条 argv 匹配预置命令，遇到没预置的写标准错误并以 90 退出，不静默返回空 |
| 外部模型 CLI | `codex` | `mmw/cli/tests/guardrails.sh` 的 `make_fake_codex`。它按环境变量决定这一次返回什么报告、什么 `thread_id`、什么退出码，并把收到的 argv 抄进 `CODEX_STUB_ARGV` 供断言 |
| 系统时间 | `date` | 同一个 `make_fake_codex` 里的 `$fake_bin/date`。它固定输出一个时间戳，让派发进度日志的文件名可断言 |
| 退避等待 | `sleep` | `mmw/cli/tests/test_issue.sh` 里 `$WORK/bin/sleep`。它把参数记进日志就返回，不真的睡 |
| 三个检索服务器进程 | `serena`、`npx`、`python3` | `mmw/cli/tests/test_init.sh` 里 doctor 那一段。每个替身只回它公开合同里的工具集合，探针、合同校验和 doctor 本身照常跑真的 |
| 远端构建主机 | `ssh`、`scp` | `mmw/release/tests/fixtures/fake-remote/`，由 `test_release_flow.sh` 的 `REMOTE_FIX` 挂上 |
| 目标仓库本身 | 无 | 每个用例用 `mktemp -d` 建一次性目录再 `git init`，不碰当前 checkout。做法见 `guardrails.sh` 的 `fresh_repo` |

一次性仓库的 `.gitignore` 要跟 `mmw/cli/lib/init.sh` 的 `mmw_init_gitignore` 写的那份一致。少写一项会让这些仓库跟真实目标仓库行为不同：派发往 `scratch` 写进度日志和句柄文件，那时工作区被判成不干净，下一次派发被护栏拒掉。

网络不在被测路径上：唯一走网络的是 `gh` 和远端构建，两者都已经有替身。

## 权威源指针

测试要对本仓库已持有的值作断言时，从下表的权威源解析，不在测试里复制第二份。

| 值 | 权威源 |
| --- | --- |
| 产物类别、类别根、类别内细分规则 | `mmw/cli/artifacts.json` |
| 各角色的模型、档位与宿主覆盖 | `mmw/cli/mmw.default.json` |
| 工作目录根等各类别根的默认取值 | `mmw/cli/mmw.default.json` 的 `paths` |
| Codex 角色结构 | `mmw/codex/profiles.json` |
| 检索服务器声明 | `mmw/.mcp.json` |
| 目标仓库的标签、CLI 路径与领域文档形态 | 目标仓库根的 `.mmw.json` |

## 怎么跑

```bash
bash mmw/test.sh
```

单独跑一份聚焦测试时直接给它路径，例如 `bash mmw/cli/tests/test_artifact.sh`。

Python 部分是 PEP 723 内联脚本，依赖写在被测文件头部，由 `uv` 装。没装 `uv` 时入口把没跑的那几份列出来并非零退出，不静默跳过。

**别用管道接它的输出。** `bash mmw/test.sh | tail` 交回的是 `tail` 的退出码，全红也看着像通过。要看尾部就先重定向到文件，再单独读那个文件。

改动 `mmw/` 下的 CLI、技能源、出包、图谱或检索之后跑一次完整入口。

## 这个仓库特有的边界

机械校验能覆盖什么、不能覆盖什么，以及扫描技能正文时按文件来源排除哪几处，由 `AGENTS.md` 的「修改规则」一节规定。写测试前读那一节，本文不复述。
