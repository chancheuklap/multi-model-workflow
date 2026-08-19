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
