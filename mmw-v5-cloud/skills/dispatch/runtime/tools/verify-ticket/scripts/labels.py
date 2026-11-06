"""Issue labels shared by v5 tools; independent of ticket prose and closeout."""

CLASS_LABELS = {
    "mmw:map": ("5319e7", "MMW kind: the map one discussion opened"),
    "mmw:spec": ("1d76db", "MMW kind: a spec, the container of one batch of tickets"),
    "mmw:ticket": ("0e8a16", "MMW kind: a ticket, one unit of work"),
    "mmw:child": ("c5def5", "MMW kind: a child issue a ticket opened"),
    "mmw:lesson": ("8e44ad", "做法上的问题，等复盘"),
    "mmw:problem": ("f1c40f", "不在任何票里的产品问题，或计划还没批的 issue"),
}

CLASS_SPEC = "mmw:spec"

QUEUE_LABELS = {
    "needs-triage": ("F9D0C4", "等你决定：只有主人能让它离开"),
    "ready-for-agent": ("FEF2C0", "已写清楚，可以直接派工人 AFK 跑"),
    "ready-for-human": ("BFDADC", "HITL 的活，不派工人"),
    "wontfix": ("ffffff", "This will not be worked on"),
}

GRADE_LABELS = {
    "junior-worker": ("C2E0C6", "worker grade: default row in models.json"),
    "senior-worker": ("E99695", "worker grade: silent-failure work"),
}

WAYFINDER_LABELS = {
    "wayfinder:research": ("FEF2C0", "decision ticket，开一个 researcher 查一条事实就能解掉"),
    "wayfinder:prototype": ("BFD4F2", "decision ticket，要先做一个粗糙版本给用户走查"),
    "wayfinder:grilling": ("D93F0B", "decision ticket，靠跟人对谈解掉"),
    "wayfinder:task": ("5319E7", "decision ticket，某个决定做得出来之前必须先完成的手工操作"),
}

LABELS = {**CLASS_LABELS, **QUEUE_LABELS, **GRADE_LABELS, **WAYFINDER_LABELS}
