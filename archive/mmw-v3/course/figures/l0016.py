"""Figures of lesson 0016: where the task board's settings rows come from; which copy of the board this
machine runs and which one the repository tests as its product."""
from kit import Fig, txt as _t, tbox as _box


def rows():
    f = Fig("m161", 1000)
    SX = 310
    RX, RW = 650, 340

    f.pill(SX, 10, "加一个开会话的角色")
    f.ar([(SX, 44), (SX, 58)])
    _box(f, "config", 10, 60, 600, "dispatch 技能的 roles.json：kind 为 session 的角色",
         ["junior-worker、senior-worker、reviewer、advisor、", "researcher、explainer、synthesizer，现在 7 个"])
    f.ar([(612, 92), (RX - 2, 92)])
    _box(f, "script", RX, 60, RW, "codeversion.py：看板重启",
         ["roles.json 变了，看板进程自己重启；", "不重启，新角色要等下次登录才出现"])
    f.ar([(SX, 124), (SX, 140)])
    _box(f, "script", 10, 142, 600, "models.py：import 时读一次 roles.json",
         ["安装时给 models.json 补上缺的角色，取 hosts.json 的默认值", "保存时只收一个角色一行，多一行少一行都拒绝"])
    f.ar([(SX, 206), (SX, 222)])
    _box(f, "config", 10, 224, 600, "~/.mmw/models.json 的 rows", ["一个角色一行：host、model、effort"])
    f.ar([(SX, 271), (SX, 287)])
    _box(f, "script", 10, 289, 600, "settings_api.py：GET /api/settings 原样交出 rows", [])
    f.ar([(SX, 319), (SX, 335)])
    _box(f, "other", 10, 337, 600, "page/local-config.mjs：行就是 rows 的键",
         ["按文件里的顺序，一个角色一行；每行的中文说明取 ROLE_WHAT", "v2 在这里写死了四个角色"])
    f.ar([(SX, 401), (SX, 417)])
    f.pill(SX, 419, "设置页：7 行，每行可改 host、model、effort")

    _box(f, "other", RX, 224, RW, "brief 会话不上看板",
         ["advisor、researcher、explainer、synthesizer", "由 dispatch.sh brief 开，不挂在票上；",
          "看板的任务列表只读票，所以看不到", "它们在跑。设置页仍有它们的模型行"], dashed=True)
    return f.svg(466, ARIA_ROWS)


ARIA_ROWS = ("第 16 课图 1，任务看板设置页的行从哪来。加一个开会话的角色，先写进 dispatch 技能的 roles.json，kind 为 session 的角色现在 7 个："
             "junior-worker、senior-worker、reviewer、advisor、researcher、explainer、synthesizer。roles.json 变了，codeversion.py 让看板进程自己重启，"
             "不然新角色要等下次登录才出现。models.py 在 import 时读一次 roles.json：安装时给 models.json 补上缺的角色，取 hosts.json 的默认值；"
             "保存时只收一个角色一行，多一行少一行都拒绝。~/.mmw/models.json 的 rows 一个角色一行，记 host、model、effort。"
             "settings_api.py 的 GET /api/settings 原样交出 rows。page/local-config.mjs 把 rows 的键当作行，按文件里的顺序，每行的中文说明取 ROLE_WHAT；"
             "v2 在这里写死了四个角色。结果是设置页 7 行，每行可改 host、model、effort。"
             "旁边一格：brief 会话不上看板。advisor、researcher、explainer、synthesizer 由 dispatch.sh brief 开，不挂在票上，"
             "看板的任务列表只读票，所以看不到它们在跑；设置页仍有它们的模型行。")


def where():
    f = Fig("m162", 1000)

    f.zone(10, 10, 980, 104, "这台机器上常驻的看板：由安装决定")
    _box(f, "other", 24, 40, 250, "com.mmw.board", ["安装器装的常驻任务"])
    f.ar([(276, 63), (318, 63)])
    _box(f, "script", 320, 40, 340, "<installed-root>/board/supervisor.py", ["只有显式安装才换成另一份（第 17 课）"],
         mono_title=True)
    f.ar([(662, 63), (684, 63)])
    _box(f, "config", 686, 40, 290, "~/.mmw/boards.json", ["本仓库 47100，agentflow 47101"], mono_title=True)

    f.zone(10, 128, 980, 200, "本仓库把看板当产品：.mmw/ 和 screen contract")
    _box(f, "script", 24, 158, 330, "harness/target.py、board_server.py", ["在租来的端口上开看板"])
    _box(f, "script", 24, 213, 330, "stories/serve.py", ["给组件故事页交出网页代码"])
    _box(f, "config", 24, 268, 330, "screen-contract.yaml", ["77 处网页代码的路径"])
    for y in (181, 236, 291):
        f.ar([(356, y), (380, y), (380, 236), (406, 236)])
    _box(f, "script", 408, 213, 250, "mmw-v3/board", ["看板的代码和网页"], mono_title=True)
    _box(f, "other", 686, 158, 290, "start 多做的一件事",
         ["私有 models.json 的行不是角色表时，", "按 hosts.json 的默认值重写"], dashed=True)
    return f.svg(340, ARIA_WHERE)


ARIA_WHERE = ("第 16 课图 2，这台机器上常驻的看板和本仓库当产品测的看板各是哪一份。"
              "上面一组：安装器装的常驻任务 com.mmw.board，跑 installed-root 记下的那个 checkout 的 board/supervisor.py，只有显式安装才换成另一份，见第 17 课；"
              "它用 ~/.mmw/boards.json 登记端口，本仓库 47100，agentflow 47101。"
              "下面一组：本仓库把看板当产品的配置。harness/target.py 和 board_server.py 在租来的端口上开看板，stories/serve.py 给组件故事页交出网页代码，"
              "screen-contract.yaml 有 77 处网页代码的路径，三者都直接指向 mmw-v3/board。"
              "旁边一格：start 多做的一件事，私有 models.json 的行不是角色表时，按 hosts.json 的默认值重写。")


FIGS = {"l16-rows": rows, "l16-where": where}
