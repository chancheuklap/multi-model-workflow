# exe-release 收尾清单（等小黄鸭这一轮出完包再动）

`scripts/release-flow.sh` **不能在出包过程中改**：bash 是按文件偏移量续读脚本的，改了会让
正在跑的进程读到错位的字节。所以下面这些全部压到那一轮结束之后。

补丁已经写好：`<scratchpad>/engine-patch.py`（对着 `scripts/release-flow.sh` 跑）。

## 1. 引擎（`scripts/release-flow.sh`）

- [ ] 钥匙没声明 `fix_executor` / `derive` 时，`cmd_dispatch_direct` 停成 `needs-context`
      并说清楚原因，不再 `die`——那会把「这把钥匙没配这个」说成引擎坏了。
- [ ] `post_fix_gate` 缺席时记 `skipped` 直接返回。「跑了并通过」和「压根没有这一关」
      在回执里必须分得开。
- [ ] `event_sink` 缺席时不落地，直接返回。
- [ ] 交付目录缺省值不再是 `D:\agentflow-releases`，改成从构建机已经给的事实推
      （远端根目录旁边的 `<root>-delivered`）。
- [ ] 路径硬禁止清单给一份技能自带的底线（`.env`、私钥、证书、锁文件、`.git/`、
      保护规则文件自己、钥匙自己），产品的 `protection_source` 加在它之上而不是取代它。

## 1b. 钥匙不再抄技能已经知道的事

同一条线（每个产品都写同一份东西 ⇒ 该由技能写）还剩两处，都要动引擎：

- [ ] **`diagnose` 给缺省值。** 四把钥匙里这一段一模一样，只有 `--adapter` 后面的路径不同，
      而那条路径引擎手里就有（`manifest_path`）。钥匙不声明时引擎用技能自己的
      `diagnose_core.py`；声明了才用钥匙的。
- [ ] **标准三阶段由引擎提供。** 每把钥匙的 `assemble` 与 `build` 逐字相同，只有钥匙路径不同——
      四十行样板抄四遍。钥匙不声明 `stages` 时引擎用标准流水线，声明了才是「在标准之前/之后
      还要跑什么」（比如某个产品的版本号核对）。

      这不只是省字数：**v2 钥匙指着 v1 钥匙那个 bug，正是抄这段样板抄出来的**，而且它在日志里
      每一步都是绿的。样板由引擎生成，这一类 bug 整个消失。

## 1a. 构建机准备搬进技能

`build_machine_setup.py` 在两个产品仓库各有一份，**239 行一字不差**，只差一张产品名表和
一句注释。一件事被抄了第二遍，就说明它不属于任何一个仓库。

按内容分三堆：

| 内容 | 归谁 | 怎么落 |
| --- | --- | --- |
| `UV_LINK_MODE=copy`、`PYTHONDONTWRITEBYTECODE=1`、TEMP 重定向到仓库内、ccache 探测后设 `NUITKA_CCACHE_BINARY`（Nuitka 不会自己从 PATH 找）、Defender 排除的加与撤 | **技能** | 渲染成 PowerShell 进 `release.ps1`，跟编译命令一样烤成字面量 |
| uv 镜像、electron 镜像、ccache 的具体路径 | **这台构建机** | `remote-build.json` 里加一段可选的 `build_env`，跟 host/root 放一起——它们本来就是同一类事实 |
| duck 那枚 vendored setuptools wheel 的 sha 核对（离线出包用）、按产品排除的 LOCALAPPDATA 缓存目录 | **产品** | 留在 `build_machine.setup` 钩子里 |

Defender 那几条在 PowerShell 里是 `Add-MpPreference` / `Remove-MpPreference`，比现在这份 Python
再 subprocess 回 PowerShell 更直接。

- [ ] 技能侧渲染 setup/teardown。
- [ ] 引擎把 `remote-build.json` 的 `build_env` 放进 `release-context.json`。
- [ ] 两个仓库的 `build_machine_setup.py` 只留产品自己那部分。

## 1c. 删掉编出来的字段

「通用」不等于「万能」。这个技能针对的就是 agentflow 那一种形式的产品：Electron 外壳 +
Nuitka 编译的 Python 后端 + NSIS 安装包 + 远端 Windows 构建机。下面这些字段没有任何一个
真实产品在用，是为假想中的产品留的口子——留着就是在教下一个人「这里有得选」，而那个选项
从来没有人走过、也从来没有被验证过。

- [ ] `python_backend.builder`：只有一个取值的 Literal。
- [ ] `python_backend.output_mode` 与 `folder_per_target`：四个产品全是 onefile。
      改成永远 `--standalone --onefile`。
- [ ] `python_backend.include_data_files`：没人用，`include_data_dirs` 覆盖了真实场景。
- [ ] `electron.package_manager` / `install_args` / `build_script`：五个产品全是 pnpm +
      `install --frozen-lockfile --prefer-offline` + `run build`。改回装配器里的常量。
      （`_required_tools` 跟着改成常量。）
- [ ] `NativeExtDll.dll_source` 的 `"repo"` 取值与 `repo_dir`：没人用。
- [ ] 没有 Electron 外壳的产品那条分支：没有这样的产品。`electron` 与
      `build_target.desktop_dir` 改回必填，`_electron_setup` 的条件分支删掉，
      `tests/test_minimal_key.py` 里那条纯后端测试一并删。

这一批全部要改钥匙（`extra="forbid"`），所以必须和第 4 节同一批做完。

- [ ] `key.md` 里对应的段落同一批删掉：`output_mode` 那一行、`electron` 段的前三个字段与
      「Every field has a default」那句、`dll_source` 的 `repo` 取值、「Omit `electron`
      entirely」那一句。**schema 和这份文档必须一起改**——文档还写着一个已经不存在的字段，
      比没写更糟：照着写出来的钥匙过不了合同，而写的人以为自己照文档做了。

## 1d. 出包不再堆垃圾

实测：构建机上 48 个构建目录，最老的来自 07-16，抽一个量是 **6.11 GB**；Mac 侧一个 worktree
的 `.release` 是 **1.1 GB**。而每一次尝试真正值得留下的东西加起来 **约 80 KB**。

判据一句话：**能从更小的东西一字不差地重生出来，就不是记录。**

| 东西 | 大小 | 判 | 为什么 |
| --- | --- | --- | --- |
| `.release/delivered/<产品>.json` | ~100 B | **记录** | 产品 + 出货 commit。跨会话唯一的事实，SKILL.md 第 4 步靠它 |
| `build-run.log` | ~34 KB | **记录** | 失败只存在于这里 |
| `build.findings.json` | ~18 KB | **记录** | 当时是怎么分级的 |
| `release.ps1` + `release-context.json` | ~21 KB | **记录** | 真正跑的是它 |
| `SOURCE_COMMIT.txt` | 41 B | **记录** | 正是它让 source.zip 变成多余 |
| `source.zip` | **372 MB × 每次** | 垃圾 | 就是 `git archive $(cat SOURCE_COMMIT.txt)`，git 里本来就有 |
| 远端解开的 `source/` | **数 GB** | 垃圾 | 仓库 + node_modules + Nuitka 的 .build/.dist/.onefile-build + dist |
| 远端历史构建目录 | 48 个 | 垃圾 | 早已被后面的轮次取代 |
| `D:\agentflow-releases\<产品>\` 里的安装包 | ~100 MB | **产品** | 那是要发的东西 |
| ccache | ≤5 GB 自封顶 | **留** | 下一轮快不快全靠它 |

- [ ] 构建阶段一返回就删两端的 `source.zip`。`SOURCE_COMMIT.txt` 留着，源码随时从 git 取回。
- [ ] 构建**成功**且安装包已收拢到交付目录后，删掉远端整个构建目录。**失败的留着**——
      现场只存在于那里。
- [ ] 失败目录也只留最近几轮，再老的一并删。
- [ ] `init` 不能继承上一轮的 attempt 目录。

最后一条不是省空间，是**正确性**：放弃小黄鸭那轮之后，它的 `a4-verify_key` 跟小刺猬的
`a3-verify_key` 并排躺着，编号还撞了——我自己就读错了一次，把小黄鸭的结果当成小刺猬的。
一次出包的现场里混着上一次出包的现场，是会让人得出错误结论的。

## 2. 删掉 v1

- [ ] `release_contracts.py`：`SchemaVersion` 只剩 `"2"`，删 v1 的分支与
      `_version_matches_content` 里的 v1 段。
- [ ] `release_script_assembler.py`：删 `_render_bootstrap` 的 v1 分支、`_hook_calls`、
      `_render_hook_calls`、`_render_hook_functions`（v1 那份）、`_check_v1`。
- [ ] 删 `release_templates/windows_core_exe.ps1.tmpl` 与
      `release_templates/windows_electron_python.ps1.tmpl`。
- [ ] 删 `build_target` 里 v2 不再用的字段：`runtime_lane`、`entry_module`、
      `nuitka_include`、`nuitka_nofollow`、`deps_extra`，以及 `RuntimeLane`。
      （`extra="forbid"`，所以删字段和改钥匙必须同一批做完。）
- [ ] `tests/test_release_script_assembler.py`（v1 那份）随之删掉或改写。

## 3. 自检入口由钥匙说了算

- [ ] `BuiltExeSmoke.run_module` 换成 `args: list[str]`：模板现在把 `--run-module <模块>`
      写死了，那是我们三个产品的约定，不是通用事实。换成钥匙给整串参数。
- [ ] 模板 `Invoke-BuiltExeSmoke` 的 `-Module` 改成 `-Arguments`。
- [ ] 四把钥匙跟着改。

## 4. 钥匙改回正名

- [ ] `agentflow`：`{duck,parrot,hedgehog}.release-adapter.v2.json` → 覆盖同名的 v1 文件。
- [ ] `douyin-master-resolve`：`douyin-master-resolve.release-adapter.v2.json` → 同上。
- [ ] 两个仓库里指向 `.v2.json` 的地方一起改：钥匙自己的 `stages`/`diagnose`、
      两份测试、`tests/support/release_contracts_plugin.py`。
- [ ] 改完 `SKILL.md` 第 2 步那条 grep 才扫得到它们（`*.release-adapter.json` 不匹配
      `.v2.json`，并存期间就是要这样）。

**覆盖现有发布入口要用户点头**——这一条动的是产品仓库里现役的钥匙文件。

## 5. 删产品仓库里已经搬空的出包代码

三层验收全过之后才做，而且要单独确认：这批文件是现役发布入口。

`agentflow`：`packaging_manifest.py`、`build_local_assistant_release.py`、
`release_builder.py` 的 Nuitka 部分、`release_key.py`、`release_diagnose.py`、
`release_fix_executor.py`。

## 6. 收尾

- [ ] 三个仓库的分支用 `git merge --no-ff` 合回主分支。
- [ ] 根 `AGENTS.md` 的出包段跟着最终形态再核一遍。
