"""Figures of lesson 0016: where the task board's settings rows come from; which copy of the board each
thing on this machine runs until v3 replaces v2."""
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


def cutover():
    f = Fig("m162", 1000)

    f.zone(10, 10, 980, 100, "这台机器上正在用的：已安装的 v2，这次不动")
    _box(f, "other", 24, 40, 280, "com.mmw.board", ["v2 的安装器装的常驻任务"])
    f.ar([(306, 63), (348, 63)])
    _box(f, "script", 350, 40, 300, "mmw-v2/board/supervisor.py", ["从 .worktrees/mmw-installed 跑"], mono_title=True)
    f.ar([(652, 63), (684, 63)])
    _box(f, "config", 686, 40, 290, "~/.mmw/boards.json", ["本仓库 47100，agentflow 47101"], mono_title=True)

    f.zone(10, 124, 980, 150, ".mmw/ 的 harness 和 stories：本仓库给看板当产品的配置")
    f.dia(170, 200, 130, 34, ["MMW_TOOLBOX_DIR", "是什么？"])
    f.ar([(300, 200), (340, 200), (340, 177), (378, 177)], "没设", 306, 172)
    f.ar([(340, 200), (340, 235), (378, 235)], "mmw-v3", 290, 252)
    _box(f, "script", 380, 156, 280, "mmw-v2/board", ["v2 的看板测试，关于看板的票"], mono_title=True)
    _box(f, "script", 380, 214, 280, "mmw-v3/board", ["mmw-v3/tests/board/run.sh 设的"], mono_title=True)
    _box(f, "other", 686, 156, 290, "换一份时，start 会",
         ["停掉为另一份记下的看板再开", "按那一份的角色重写 models.json"])

    f.zone(10, 288, 980, 112, "v3 的 dispatch.sh：还没装")
    _box(f, "script", 24, 318, 280, "dispatch.sh board、open", ["和 open-ticket，都会先开看板"])
    f.ar([(306, 341), (348, 341)])
    _box(f, "script", 350, 318, 300, "mmw-v3/board/supervisor.py", ["登记端口的办法和 v2 的相同"], mono_title=True)
    f.ar([(652, 341), (684, 341)])
    _box(f, "config", 686, 318, 290, "同一份 ~/.mmw/boards.json",
         ["两个 supervisor 会争同一张表；", "切换前只在测试的 MMW_HOME 跑"])

    _box(f, "other", 10, 418, 980, "v3 替换 v2 那一步一起改",
         ["screen contract 里 77 处 mmw-v2/board 路径；.mmw/AGENTS.md；MMW_TOOLBOX_DIR 的默认值改成 mmw-v3",
          "根 AGENTS.md；安装入口让 com.mmw.board 跑 mmw-v3/board/supervisor.py"])
    return f.svg(494, ARIA_CUT)


ARIA_CUT = ("第 16 课图 2，在 v3 替换 v2 之前，这台机器上每样东西用哪一份看板。"
            "第一组，正在用的已安装 v2，这次不动：v2 安装器装的常驻任务 com.mmw.board，跑 .worktrees/mmw-installed 里的 mmw-v2/board/supervisor.py，"
            "登记表是 ~/.mmw/boards.json，本仓库 47100，agentflow 47101。"
            "第二组，.mmw/ 的 harness 和 stories，本仓库给看板当产品的配置：看 MMW_TOOLBOX_DIR，没设就用 mmw-v2/board，v2 的看板测试和关于看板的票都走这条；"
            "设成 mmw-v3 就用 mmw-v3/board，mmw-v3/tests/board/run.sh 就是这样设的。换一份时，start 会停掉为另一份记下的看板再开，并按那一份的角色重写 models.json。"
            "第三组，v3 的 dispatch.sh，还没装：board、open 和 open-ticket 都会先开看板，用 mmw-v3/board/supervisor.py，登记端口的办法和 v2 的相同，"
            "也就是同一份 ~/.mmw/boards.json；两个 supervisor 会争同一张表，所以切换前只在测试的 MMW_HOME 里跑。"
            "最下面：v3 替换 v2 那一步一起改的东西，screen contract 里 77 处 mmw-v2/board 路径、.mmw/AGENTS.md、MMW_TOOLBOX_DIR 的默认值改成 mmw-v3、根 AGENTS.md，"
            "以及安装入口让 com.mmw.board 跑 mmw-v3/board/supervisor.py。")


FIGS = {"l16-rows": rows, "l16-cutover": cutover}
