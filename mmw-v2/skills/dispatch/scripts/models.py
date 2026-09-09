"""读 models.md，把它的行变成 Paseo 认的两样东西：Agent profile 与 create_agent 的 settings。

一个库，没有命令行入口。两个 caller 各取一部分，都用 importlib 按路径载入：

  install.sh    profile_rows() 写 ~/.paseo/config.json 的 daemon.agentProfiles，
                apply_permissions() 把权限档写进每条 profile
  dispatch.sh   create_agent_settings() 拼 create_agent 的 settings

每一个被派出去的 agent 的 model 只有 models.md 那一处，user 只开那一个文件；这里只做
格式转换，一种 host 只有一种拼法。
"""

from pathlib import Path
from typing import NamedTuple

MODELS = Path(__file__).resolve().parent.parent / "models.md"


def parse_model_rows() -> list[tuple[str, str, str, str, str]]:
    """models.md 表的每一行：(agent, host, model, effort, permissions)。

    install.sh 与 dispatch.sh 共用这一份解析。表头、分隔行、非五列的行丢掉。
    """
    if not MODELS.is_file():
        raise ValueError(f"缺 models.md：{MODELS}")
    rows: list[tuple[str, str, str, str, str]] = []
    for line in MODELS.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            continue
        agent, host, model, effort, permissions = cells
        if agent == "agent" or set(agent) <= set("- "):
            continue
        rows.append((agent, host, model, effort, permissions))
    if not rows:
        raise ValueError(f"{MODELS} 里一行 agent 都没有")
    return rows


def profile_id(agent: str, host: str, *, primary: bool) -> str:
    """id 与 name 写入 ~/.paseo/config.json 的 daemon.agentProfiles。

    一个 agent 的第一条 bypass 行沿用 agent 名，已有的 profile 和 mmw.profile 标签
    都不动。同一 agent 的后一条 bypass 行是备用 host，id 为 `{agent}@{host}`，
    两条才不会抢同一个 id。
    """
    return agent if primary else f"{agent}@{host}"


class ProfileRow(NamedTuple):
    profile_id: str
    agent: str
    host: str
    model: str
    effort: str
    permissions: str


def profile_rows() -> list[ProfileRow]:
    """生成 Agent profile 的行：permissions 是 bypass 的那些。

    一个 agent 至多两条 bypass：第一条是首选，profile_id 等于 agent；第二条是
    备用 host，profile_id 为 `{agent}@{host}`。两条 bypass 不能落在同一 host 上。
    """
    primary_host: dict[str, str] = {}
    have_fallback: set[str] = set()
    out: list[ProfileRow] = []
    for agent, host, model, effort, permissions in parse_model_rows():
        if permissions != "bypass":
            continue
        if agent not in primary_host:
            primary_host[agent] = host
            out.append(ProfileRow(
                profile_id(agent, host, primary=True),
                agent, host, model, effort, permissions))
            continue
        if host == primary_host[agent]:
            raise ValueError(f"{MODELS}: {agent} has two bypass rows on {host}")
        if agent in have_fallback:
            raise ValueError(
                f"{MODELS}: {agent} has more than one fallback bypass row")
        have_fallback.add(agent)
        out.append(ProfileRow(
            profile_id(agent, host, primary=False),
            agent, host, model, effort, permissions))
    # The loop above already keeps two rows of one agent apart. What it cannot see
    # is an agent literally named `<other>@<host>`, which would collide with the
    # fallback id generated for `<other>` on that host.
    ids = [row.profile_id for row in out]
    if len(ids) != len(set(ids)):
        clash = sorted({i for i in ids if ids.count(i) > 1})
        raise ValueError(
            f"{MODELS}: an agent name collides with a generated fallback id: "
            + ", ".join(clash))
    return out


def create_agent_settings(host: str, permissions: str) -> dict:
    """permissions 单元格写成 create_agent 的 settings。

    install 的 profile 与 dispatch 的 create_agent JSON 都从这里取，所以一种 host 只有
    一种拼法。两个键管两件事，一个 host 可以两个都要：`modeId` 是 host 自己的权限档，
    `features.auto_accept` 是自动批准 ACP 的权限提示——无人值守的夜里没人去点。

    档位是 host 自己的东西，Paseo 只负责把名字传过去。有档位的 host 必须显式收到一个：
    Paseo 不让新会话从起它的那个会话继承档位（`cannot inherit mode … Pass an explicit
    mode`），所以缺了这个键的 host 起不来会话。grok 与 pi 没有档位，只有开关。
    """
    if permissions != "bypass":
        raise ValueError(f"permissions 只能是 bypass，得到 {permissions!r}")
    if host == "claude":
        return {"modeId": "bypassPermissions"}
    if host == "codex":
        return {"modeId": "full-access"}
    if host == "cursor":
        return {"modeId": "agent", "features": {"auto_accept": True}}
    return {"features": {"auto_accept": True}}


def apply_permissions(profile: dict, host: str, permissions: str) -> dict:
    """按 host 把 permissions 单元格写成 profile 的 modeId / featureValues。

    一份，install 与 --check 共用。settings 的 `features` 在 profile 里叫 featureValues。
    两个键各自写入或摘除，因为一个 host 可以两个都要。
    """
    settings = create_agent_settings(host, permissions)
    for key, name in (("features", "featureValues"), ("modeId", "modeId")):
        if key in settings:
            profile[name] = settings[key]
        else:
            profile.pop(name, None)
    return profile
