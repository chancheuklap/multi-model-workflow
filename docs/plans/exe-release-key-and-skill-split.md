# exe-release：把出包拆成钥匙与技能

## 这份文件是什么

一次性把出包能力从产品仓库收拢进 `exe-release` 技能的迁移方案。

写给执行这次迁移的 agent。读完就能开工，不需要再去做调研——调研结论都在下面，带出处。

## 落地状态（2026-08-19）

第 1–5 步与第 8 步已落地，第 6 步的前两层验收已过。下面「迁移步骤」里的形状是动工前的方案，
实现有几处按事实收窄了，以实现为准：

| 计划里写的 | 实际做的 | 为什么 |
| --- | --- | --- |
| 钥匙里有 `lane` 字段 | 没有。声明了 `python_backend` 就编译后端，声明了 `electron` 就打壳 | 车道是从声明推得出来的，再写一遍就是同一件事说两处 |
| `builders/` 下有 `nuitka/pyinstaller/electron/vendored` 四个 | 只有 `nuitka.py` | 四个产品都用 Nuitka；electron 与随包资源在模板里就是几条命令，不值一个模块。用到 PyInstaller 时再加 |
| `doctor.py`、`manifest_check.py`、`gate_core.py`、`protection_rules.py` | 没建 | 引擎已有路径闸与闸门；体检与清单比对是钥匙指向的仓库侧钩子，本来就该在产品那边 |
| builder 在构建机上跑 | builder 在 Mac 上把 argv 渲染成字面 PowerShell，烤进 `release.ps1` | 上构建机的只有 5 个文件，技能的 Python 不在其中。这样零新增运输，引擎一行不动 |
| 三层验收的第一层「新旧 argv 逐字相同」 | 比 flag 多重集合 + 入口在最后 | flag 顺序对 Nuitka 无语义。测试里写明了这一点 |

**未做，且被第三层验收挡着的：**

- **第 6 步第三层：duck 真出一次包。** 唯一预算内的那次构建，没跑。
- **第 7 步：删旧的。** 三层没全过，一样旧东西都没删。v1 与 v2 并存中。
- v2 钥匙叫 `*.release-adapter.v2.json`。`SKILL.md` 第 2 步的 `grep --include='*.release-adapter.json'`
  扫不到它——并存期间就是要这样。要驱一次 v2 出包，把 `<engine> init --manifest` 直接指向
  `.v2.json`。

## 目标

**新加一个 App 要打包时，只写一把钥匙，一行 Python 都不用写。**

写不出来的地方，只有两种合法处理：给钥匙加字段，或给技能加一条车道。**不允许在产品仓库写脚本。**

## 现状：为什么现在做不到

### 钥匙太小

现在 `build_target` 只有 9 个字段：

```
desktop_dir  runtime_lane  entry_module  installer_brand  installer_glob
asset_roots  native_ext_dll  nuitka_include  nuitka_nofollow
```

而产品仓库里 `scripts/release/packaging_manifest.py` 605 行中有 **371 行（61%）是常量声明**：

```python
MIN_PYTHON = (3, 11)
DUCK_ICON = "src/local_agent/assets/xiaohuangya-tray.ico"
PARROT_PYTHON_VERSION = "3.12.10"
PARROT_PYTHON_ABI_TAG = "cp312-win_amd64"
FFMPEG_RUNTIME_FILES = ("ffmpeg.exe", "ffprobe.exe")
```

**这些全是钥匙的内容，被写成了 Python。**

### 两条车道一条做事一条不做事

| 模板 | 行数 | 实际内容 |
| --- | --- | --- |
| `windows_electron_python.ps1.tmpl` | 126 | **七步全在技能里**：pnpm install → 车道准备 → pnpm build → electron-builder dir → 校验 → electron-builder nsis。坑也在里面（NSIS 打完清理临时文件的 ENOENT 竞态） |
| `windows_core_exe.ps1.tmpl` | 73 | **四步全部外包**给产品仓库的 `runtime_prepare` 钩子。模板自己的注释写着「模板不重造 Electron 通用步骤」 |

`release_script_assembler.py:170` 的 `_render_lane_block` 对两条车道都只写一句
`Runtime lane is prepared by the repository ...`。

**embedded_python 那条模板就是目标形态的样板。core_exe 是反例。**

### 四个产品里只有一个在反例那条车道上

| 产品 | 车道 |
| --- | --- |
| `duck` | `core_exe` ← **这次要迁的只有它** |
| `parrot` | `embedded_python` |
| `hedgehog` | `embedded_python` |
| `douyin-master-resolve` | `embedded_python` |

另外三个已经在目标形态的车道上，**这次不碰它们的构建路径**。它们的作用是当参照物，
以及在第 8 步验证「只写钥匙」。

### 代码其实是通用的，只是名字带产品名

`src/local_agent/release_builder.py:663` 的 `_build_duck_nuitka_command`：

```python
argv = [
    "-m", "nuitka", "--standalone",
    "--assume-yes-for-downloads",
    f"--jobs={_duck_nuitka_jobs()}",
    "--windows-console-mode=disable",          # 坑
]
for m in DUCK_NUITKA_NOFOLLOW_IMPORTS: ...      # 数据
for p in DUCK_NUITKA_PACKAGES:
    argv.append(f"--include-package={p}")
    argv.append(f"--include-package-data={p}")  # 坑：这两个必须成对
```

函数体是「怎么正确调用 Nuitka 打一个 Windows GUI 程序」，是坑。三个大写常量是数据。**一行 duck 都没有。**

### 常量与代码的比例（`python -m ast` 实测）

| 文件 | 总行 | 常量声明 | 函数/类 |
| --- | --- | --- | --- |
| `scripts/release/packaging_manifest.py` | 605 | 371（61%） | 91 |
| `src/local_agent/release_builder.py` | 905 | 70（7%） | 730 |
| `scripts/release/build_local_assistant_release.py` | 401 | 5（1%） | 324 |
| `scripts/release/release_key.py` | 713 | 8（1%） | 624 |

常量 → 钥匙。函数 → 技能。

### 顺带查出来的两件事

1. **P1 派修现在是死的。** `release_fix_executor.py:93-96` 找
   `$MMW_PLUGIN_DIR/plugin/scripts/worker.sh`，那个文件随旧 mmw 插件一起删了；而且
   `release-flow.sh` 只把 `MMW_PLUGIN_DIR` 传给 `event_sink`（第 622 行），根本不传给
   `fix_executor`。两个产品仓库里这个文件字节相同，所以一起坏。

   它坏正是因为站错了边：它引用 MMW 的东西，却住在产品仓库，MMW 删东西时够不到它。

2. **同一批脚本在两个产品仓库各有一份。** `release_fix_executor.py` 两边字节完全相同；
   `release_event_sink.py` 差 1 行（import 哪个 logger）；`build_machine_setup.py` 差 10 行；
   `post_fix_gate.py` 差 24 行。

## 判据：什么进钥匙，什么进技能

一个文件、一段代码，问一句：

> **换一个 App，这段东西要重写吗？**

| 答 | 归哪 | 形态 |
| --- | --- | --- |
| 不用重写，只是值不同 | **钥匙** | JSON 数据 |
| 不用重写，是同一套动作 | **技能** | 代码 |
| 要重写，是这个 App 独有的业务 | **产品仓库** | 代码，且尽量薄 |

「自愈会改它」**不构成留在产品仓库的理由**——钥匙本来就在产品仓库，路径闸照样管得住。
之前把这一条当成了阻碍，是错的。

## 目标形态

```
mmw-v2/skills/exe-release/
├── SKILL.md                    出哪几个产品
├── driving.md                  怎么跟引擎打交道
└── scripts/
    ├── release-flow.sh                 引擎（不动）
    ├── release_contracts.py            钥匙 schema v2 + 事件合同
    ├── release_script_assembler.py     按钥匙装配 release.ps1
    ├── release_templates/
    │   ├── nuitka_electron.ps1.tmpl        新：core_exe 的七步版
    │   └── embedded_python.ps1.tmpl        现有样板，改名
    ├── builders/
    │   ├── nuitka.py                   Nuitka 命令构造（参数化）
    │   ├── pyinstaller.py              PyInstaller 命令构造
    │   ├── electron.py                 staging、asar、win-unpacked
    │   └── vendored.py                 ffmpeg 等随包资源
    ├── doctor.py                       出包前体检，清单来自钥匙
    ├── manifest_check.py               「必须打进包」的比对
    ├── diagnose_core.py                读日志出 finding，规则表来自钥匙
    ├── gate_core.py                    跑闸门，闸门清单来自钥匙
    ├── fix_dispatch.py                 召来修复 agent（顺手修好 P1）
    ├── protection_rules.py             路径闸规则引擎
    └── tests/

产品仓库
├── <product>.release-adapter.json      钥匙（长大后）
├── remote-build.json                   构建机
├── electron-builder.yml / nsis-*.nsh   electron-builder 自己的配置
├── _build_smoke.py                     import 自己的模块验能不能起来
└── 业务专属证明（凭证代理、包完整性等）
```

## 钥匙 schema v2

字段名以实现为准，这里给形状。来源标注了每个字段今天在哪。

```jsonc
{
  "schema_version": "2",
  "product": "duck",
  "lane": "nuitka_electron",          // 或 embedded_python

  "toolchain": [                       // ← packaging_manifest.TOOLCHAIN
    {"bin": "python", "min": "3.11"},
    {"bin": "pnpm"}, {"bin": "node"}, {"bin": "uv"}, {"bin": "makensis"}
  ],

  "python": {
    "entrypoints": [                   // ← release_builder.duck_nuitka_targets
      {"name": "agentflow-launcher", "exe": "…", "source": "src/local_agent_launcher.py"},
      {"name": "agentflow-core",     "exe": "…", "source": "src/local_agent_core.py"}
    ],
    "include_packages": [],            // ← DUCK_NUITKA_PACKAGES
    "nofollow_imports": [],            // ← DUCK_NUITKA_NOFOLLOW_IMPORTS
    "include_data_dirs": [],           // ← DUCK_NUITKA_DATA_DIRS
    "icon": "src/local_agent/assets/xiaohuangya-tray.ico",
    "jobs": 10,                        // ← DEFAULT_DUCK_NUITKA_JOBS
    "console": false                   // ← --windows-console-mode=disable
  },

  "embedded_runtime": {                // 只有 embedded_python 车道用
    "python_version": "3.12.10",       // ← PARROT_PYTHON_VERSION
    "abi_tag": "cp312-win_amd64",      // ← PARROT_PYTHON_ABI_TAG
    "extra": "parrot-dubbing",
    "packages": []
  },

  "electron": {
    "dir": "desktop",                  // ← build_target.desktop_dir
    "product_exe": "小黄鸭电商助手.exe", // ← ELECTRON_PRODUCT_EXE_NAME
    "unpacked_dir": "win-unpacked",
    "builder_config": "desktop/electron-builder.yml",
    "compression": "small"
  },

  "vendored": {
    "ffmpeg": {"dir": "resources/ffmpeg/bin", "files": ["ffmpeg.exe", "ffprobe.exe"],
               "env": "AGENTFLOW_FFMPEG_DIR", "lock": "resources/ffmpeg/.ffmpeg-version-lock-win64.json"}
  },

  "must_be_in_package": [],            // ← packaging_manifest 的登记簿
  "smoke_modules": [],                 // ← DUCK_BUILT_EXE_SMOKE_MODULES
  "installer_glob": "runtime/assistant-release/*-setup.exe",
  "installer_brand": "小黄鸭电商助手",

  "diagnose_rules": [],                // ← release_diagnose.py 的正则表
  "gates": [],                         // ← post_fix_gate.py 的闸门清单
  "protected_paths": [],               // ← release_protection.json
  "editable_paths": [],
  "build_machine": {"setup": [], "teardown": []},
  "remote_build": {"host": "pc", "root": "D:/agentflow-release-input"},

  "hooks": {                           // 只留真正业务专属的
    "credential_proof": [],
    "package_integrity": []
  }
}
```

## 迁移步骤

**安全性靠一条：全程不动旧路径。** 新车道用新名字，旧车道原样留着。验收过了才删旧的。
任何一步失败，回到旧路径就能照常出货。

**只出一次包。** 出包很贵——三个产品一轮要四小时以上。所以验收不靠「出两个包比一比」，
靠**命令行等价**：新 builder 生成的 Nuitka / electron-builder / PyInstaller 命令行，跟旧代码
生成的逐字相同。旧代码就在仓库里，import 进来直接比，秒级完成。

命令行逐字相同 + 输入相同 ⇒ 产物相同，这是构造保证的，比抽样比对两个包更强。真出包只用来
验编排（步骤顺序、钩子时机），一次就够，而且是在所有代码都已证明等价之后才跑。

验收分三层，只有第三层要出包，见文末「怎么算成功」。

### 第 1 步 钥匙 schema v2

在 `release_contracts.py` 里定义上面那份 schema，`schema_version: "2"`。

**v1 继续支持**，两个版本并存到第 7 步。

来源清单（照着抄，别自己想字段）：

- `packaging_manifest.py` 全部 371 行常量
- `release_builder.py` 第 43–68 行常量
- `build_target` 现有 9 个字段
- `release_diagnose.py` 的规则元组表
- `post_fix_gate.py` 的闸门清单
- `release_protection.json`

### 第 2 步 技能侧的构建器

新建 `scripts/builders/`，把这些函数搬进去并参数化——**函数体照抄，只把大写常量换成钥匙字段**：

| 搬什么 | 从哪 | 搬到 |
| --- | --- | --- |
| `_build_duck_nuitka_command`、`duck_nuitka_targets`、`_duck_standalone_exe_path` | `release_builder.py:630-707` | `builders/nuitka.py` |
| `_build_windows_executables_pyinstaller` | `release_builder.py:565` | `builders/pyinstaller.py` |
| `resolve_staged_electron_asar`、`write_electron_packaged_scan_proof`、`build_windows_release_bundle` | `release_builder.py:138-269` | `builders/electron.py` |
| ffmpeg 随包逻辑 | `release_builder.py` + `packaging_manifest.py` | `builders/vendored.py` |
| `validate_windows_release_bundle`、`run_built_exe_smoke` | `release_builder.py:314,718` | `manifest_check.py` |
| doctor 体检 | `release_key.py` | `doctor.py` |

**不要重写。** 这些代码在三个产品上跑通过，改逻辑就是在制造新的坑。

### 第 3 步 新车道模板 `nuitka_electron.ps1.tmpl`

照 `embedded_python` 那份的结构写。步骤从 `build_local_assistant_release.py` 读出来，
每一步换成调技能侧的 builder。

`_render_lane_block` 从「写一句话」改成真的生成步骤。

**这一步会遇到的硬东西**（core_exe 模板注释已经点名，别绕过去）：

- 手写 NSIS 里的安装包语义：VC++ 运行库携带、AUMID 盖章、卸载保留用户数据。
  这些在 `desktop/scripts/nsis-installer.nsh`，**那是 electron-builder 的配置文件，留在产品仓库**，
  技能只负责在正确的时机调用 electron-builder 并把它指向这个文件。
- Nuitka 长路径问题：远端构建目录用 12 位短 commit 就是为了它（`release-flow.sh` 注释）。

### 第 4 步 自愈三件套骨架

| 新文件 | 从哪来 | 钥匙里留什么 |
| --- | --- | --- |
| `diagnose_core.py` | `release_diagnose.py` 的读日志/匹配/出 finding 骨架 | `diagnose_rules` 正则表 |
| `gate_core.py` | `post_fix_gate.py` 的跑闸门骨架 | `gates` 清单 |
| `protection_rules.py` | `release_protection.py` | `protected_paths` |
| `fix_dispatch.py` | `release_fix_executor.py` 全部 155 行 | 无 |

`fix_dispatch.py` **顺手把 P1 修好**：不再找已经不存在的
`$MMW_PLUGIN_DIR/plugin/scripts/worker.sh`，改成技能自己知道怎么召来一个修复 agent。

`release_event_sink.py` **不搬**——它的全部作用就是接进产品自己的日志系统。

### 第 5 步 三个产品各写一把 v2 钥匙

`duck`、`parrot`、`hedgehog`。值全部从第 1 步列的来源抄，**不要重新决定任何值**。

### 第 6 步 验收

**第一层 命令行等价（零构建，秒级）**

写一份对拍测试：旧代码 import 进来生成 argv，新 builder 读 v2 钥匙生成 argv，逐字比对。

三把钥匙都要过：`duck`（Nuitka + electron-builder）、`parrot`、`hedgehog`。后两个虽然不迁
车道，但它们的 builder 调用也走新代码，必须一起证明没变。

**这一层覆盖风险最高的部分**——Nuitka 的那堆 flag、electron-builder 的那堆参数。任何一个字
不同，当场就能看见是哪个。

**第二层 装配产物等价（零构建，秒级）**

同一把钥匙，新装配器生成的 `release.ps1` 跟旧的比：步骤序列、每一步调用的命令、钩子插入的
位置必须一致。差异只允许出现在「原本外包给仓库脚本、现在由技能自己做」的那几步。

**第三层 duck 真出一次包（一次）**

只出 duck，因为只有它换了车道。验的是编排能不能跑通、包能不能装能不能起：

- 安装包产出，落在 `installer_glob` 指的位置
- 装上之后跑 `smoke_modules`，模块 import 得起来
- 安装包大小跟历史同量级（差异超过 5% 要查清楚再往下走）

**这一层不过，不删任何旧东西。**

### 第 7 步 删旧的

三层验收全过之后：

- 产品仓库删掉：`packaging_manifest.py`、`build_local_assistant_release.py`、
  `release_builder.py`、`release_key.py`、`release_diagnose.py`、`post_fix_gate.py`、
  `release_protection.py`、`release_fix_executor.py`、`prepare_*_runtime.py`
- 技能删掉 v1 schema 支持与 `windows_core_exe.ps1.tmpl`

### 第 8 步 用第二个产品仓库验证

`douyin-master-resolve` 也走远端构建（它的钥匙 `stages[2]` 就是那个哨兵）。给它写一把 v2 钥匙。

**判据：这一步只写钥匙，不写 Python。** 写不出来的地方，就是钥匙还缺字段或技能还缺车道——
补钥匙、补车道，**不许回到产品仓库写脚本**。

**这一步不用出包。** `douyin-master-resolve` 走的是 `embedded_python`，车道没变。验两件事：
一把不需要配套 Python 脚本的钥匙写得出来，以及它生成的 `release.ps1` 跟现在那份等价。

这一步过了，这次迁移才算成功。

## 不做什么

- **不改 CI。** 不走 GitHub Actions 是有理由的：出新 App 的包中间会产生大量错误，
  本地 Mac→PC 管道能立刻读日志、立刻改。CI 那条路每错一次要推一次、等一轮。
- **不动引擎。** `release-flow.sh` 的状态机、运输、分级、刹车全部原样。
- **不改哨兵。** `mmw-release-remote-build` 是钥匙里写的字符串，跨仓库合同，两个产品仓库都在用。
- **不动 `electron-builder.yml` 与 `nsis-installer.nsh`。** 那是 electron-builder 自己的配置，
  跟应用住在一起是对的。

## 怎么算成功

| | 判据 | 代价 |
| --- | --- | --- |
| 命令没变 | 三把钥匙生成的构建命令行，新旧逐字相同 | 零构建 |
| 编排没变 | 生成的 `release.ps1` 步骤序列与旧的等价 | 零构建 |
| 包能用 | duck 出一次包，装得上、`smoke_modules` 起得来 | **一次出包** |
| 形态对 | `douyin-master-resolve` 只写钥匙，不写 Python | 零构建 |
| 体量降 | 产品仓库的出包代码从约 5200 行降到 900 行以内，且大部分是 JSON | — |
| 顺手 | P1 派修恢复可用 | — |
