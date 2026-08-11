# 技能之间用产物引用传递产物，不逐跳抄写路径

一份 research 或 prototype 的路径现在从生产它的那一步被手抄到 `worker`，中间经过 decision ticket 结论评论、map 的 `Decisions so far`、spec issue 正文、spec、tracer bullet ticket、plan 和四栏 task，共七跳；任何一跳漏写，下游拿不到，而且没有机械检查会发现。现在改为：每一跳传**产物引用**，也就是类别、工作名、范围段和类别内细分四项，路径由 `mmw artifact path` 解析。理由是路径字面值在散文里既不能被机器解析，也不能在落点形状变化时集中修改，而这四项是安全路径段，写进固定结构之后可以逐条解析验证。

## Considered Options

- **保持逐跳抄写完整路径。** 否决。它把同一条路径复制七份，七份都要靠人保持一致；`mmw/skills-src/mmw-to-tickets/SKILL.md:24` 已经出现过读取方指定节名、生产方没承诺写这一节的情况。
- **照搬 `awslabs/aidlc-workflows` 的引擎解析。** 否决。aidlc 的下游只在 `consumes[]` 声明名字，由 `aidlc-orchestrate` 在发 directive 时解析成路径（`docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/report.md` 第 5、6 节）。MMW 没有这个引擎：每一跳都是 agent 读技能正文写出下一跳，两跳之间没有进程能做解析并注入下游上下文。可搬的是「产物身份是名字不是路径」，承担解析的改为 `mmw artifact path`。
- **在工作名目录下放一份交付产物清单文件，生产方每产出一件追加一行。** 否决。Wayfinder 的每张 decision ticket 各有一条任务分支、共用一个工作名，多条分支同时追加同一个文件，每次合回都冲突。
- **清单文件加产物引用两者都做。** 否决。理由同上一条，而且下游有了产物引用之后不需要再查清单。
- **增加反向机械校验：产物目录里存在、而下游声明写「无」时报错。** 否决。机器判得出产物存在，判不出它与这张 ticket 相关；不是每份 research 都要被每张 ticket 引用。这道校验会用「存在」冒充「相关」，越过 `AGENTS.md` 给机械校验划的线。

## Consequences

- 产物引用写进固定结构，不写进散文。spec 与 plan 写在文件头的元数据块；spec issue 正文与 tracer bullet ticket 正文写在固定标题的那一节；派 `worker` 的四栏 task 的「读」栏写产物引用。生产方一律写出这一节，没有内容写「无」。
- plan 的元数据块增加一个列产物引用的字段。ADR `0001-spec-plan-stay-in-repo.md` 定的是 plan 只有 `ticket` 一个字段，本决定修改它；不加这个字段，plan 这一跳就没有可解析的声明层。
- 点名的粒度到产物索引为止。上游点名一件产物，索引显式列出的文件允许沿着读。`mmw/skills-src/mmw-implement/worker-brief.md:11-12` 现在要求 task 同时点名索引和精确文件，改为只点名产物。禁止的事一条不减：不列目录、不读上级目录、不读索引没列的文件、不读落选变体。判据从「路径是不是 task 抄来的」改为「路径是不是本次点名那件产物的索引列出的」。
- 机械层只有一件事：一条校验命令读 spec 与 plan 元数据块的产物引用，逐条解析，解析不到就非零退出。它与 aidlc 的 `Graph references` 检查是同一条边界——只校声明层，不校某一次运行的文件有没有落到磁盘。
- 行为层规定下游读不到该有的那一节就停下报缺，不猜、不静默继续。aidlc 对上游缺失的规定是同一件事：不许编造缺失产物的内容。
- 上游有产物、下游写「无」这类漏写，机器永远发现不了，由 ① spec 审和 ② plan 审发现。这是本决定接受的代价。
- `mmw artifact path` 的 `--name` 在已绑定任务 worktree 里可以缺省，由命令读 `mmw task state` 的工作名。不在任务 worktree 或读不到工作名时报错退出，不回退默认值。读别的交付的产物必须显式给名字。
- ADR 增加元数据块和一份自动生成的索引 `docs/adr/README.md`。`AGENTS.md` 要求 agent 读取与本次范围相关的 ADR，而 `docs/adr/` 只有文件名可看。research 与 prototype 不补总索引，它们由上游点名；`.out-of-scope/` 不补，`/mmw-triage` 分诊时整个目录读一遍。
- 解析发生在下游：拿到产物引用的那一方自己跑 `mmw artifact path`。aidlc-workflows v2 相反，它由引擎在上游解析好，把实际路径放进 directive 交给执行方，执行方只是传递者。MMW 没有引擎那一层，这是同一条否决理由。后果是拿到产物引用的下游必须能运行这条命令。这一条由 Wayfinder decision ticket #30「九个决定与 aidlc-workflows v2 的对照复核」补记。
- 产物引用在元数据块和 issue 正文里的具体写法、固定标题的字面、校验命令的名字和挂载位置、ADR 元数据块的字段清单都留给 spec 阶段。本决定只定机制。

来源：Wayfinder decision ticket #23「读取产物的技能怎么找到它需要的产物」，map #18「MMW 产物归纳与接线合同」。
