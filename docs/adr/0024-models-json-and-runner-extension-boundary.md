---
date: 2026-09-11
amends: [0016, 0018]
---

# 会话配置只存进 `models.json`，runner 的附加操作也只经适配器

本机 `MMW_HOME/models.json` 是 runner 与五个派发角色的唯一持久配置；`dispatch.sh start`、task board、`models.py config` 和 `install.sh --check` 共用这一份结构与校验。runner 边界保留起会话、送消息、问死活和结束会话四项协议，并允许具名的附加操作；runner 命令仍只出现在对应适配器，适配器用 `MMW_USES` 声明每个外部命令，让 `install.sh --check` 对实际 CLI 的 help 核对。

## 配置与迁移

`models.json` 含版本号、一个 runner，以及 `junior-worker`、`senior-worker`、`reviewer`、`verifier`、`advisor` 各一行 host、model 与 effort。写入先拿 `models.lock`，核对调用方读到的版本，再以临时文件原子替换整份配置。这样 task board 和命令行同时修改时，一个过期写入会被拒绝，不会静默覆盖另一个人的选择。

`install.sh` 只在 JSON 不存在时创建 version 1：有旧 `models.md` 就导入后删除旧文件，其中没有 runner 行表示 `runner: auto`；没有旧文件就用 `hosts.json` defaults 和 `runner: orca`。已经存在的 JSON 只校验，不被默认值或旧文件覆盖。`MMW_HOME` 改变唯一配置目录；安装测试用的 home 覆盖不成为第二个运行时配置入口。

## runner 附加操作

附加操作不是所有 runner 都必须实现的共同协议。`attach` 在会话成功启动后把已有工作树与 ticket 关联：能显示这种关联的 runner 执行自己的关联命令，失败只在 stderr 报一行，已启动的会话继续；不支持的 runner 明确返回成功但不做事。Paseo 的 provider 状态、模型目录与诊断也由 Paseo 适配器的具名操作提供，`models.py` 和 `dispatch.sh check` 不直接调用 Paseo。

安装器为了安装或核对 runner 本身而执行的配置命令不属于会话运行边界；这些命令仍由 `install.sh` 管理并在那里声明其期望。

## Considered Options

- **继续让 `models.md` 当可编辑权威，再生成 JSON 给 task board。** 否决。两个持久表示需要同步，任何一次中断都可能使页面与 `start` 读到不同选择。
- **task board 直接改 Markdown。** 否决。Markdown 没有版本比较与原子替换合同，两个写入者会互相覆盖。
- **把 `attach` 做成所有 runner 的强制成功条件。** 否决。关联是 runner 界面里的辅助索引，不是会话成立的条件；为了索引失败而终止已启动会话会制造孤立状态。
- **让 `models.py` 和 `dispatch.sh check` 直接调用 Paseo provider 命令。** 否决。命令会散出适配器边界，CLI 改动也无法由一处 `MMW_USES` 声明发现。

## Consequences

- 0016 整份作废；本机选择改由 `models.json` 保存，修改入口是 task board 或 `models.py config set`。
- 0018 的 runner 选择顺序保留，但其中的活表行改为 `models.json` 的 `runner` 字段；边界由固定共同协议加具名附加操作组成。
- 新 runner 若不需要某项附加操作，可以明确 no-op；若执行 runner CLI，命令与 `MMW_USES` 都写在该 runner 的适配器。
