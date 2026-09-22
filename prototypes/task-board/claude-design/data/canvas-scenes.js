/* 画布的场景数据：每个 scene 是选中任务的那棵树。
   每张 ticket 上的 lamp / phase / run / done / released / running 是照
   board-logic.mjs 的 Board.* 从真实数据算出来的；位置与连线由
   data/board-layout.js 按同样的几何算出来。 */
window.CANVAS_SCENES = {
 "morning": {
  "selected": 133,
  "expanded": [
   98,
   131
  ],
  "task": {
   "n": 98,
   "kind": "map",
   "title": "落地流水线改造",
   "decisions": [
    {
     "n": 99,
     "kind": "grilling",
     "title": "事件格式怎么定",
     "closed": true,
     "blocked": []
    },
    {
     "n": 100,
     "kind": "research",
     "title": "读票用什么",
     "closed": true,
     "blocked": [
      99
     ]
    },
    {
     "n": 104,
     "kind": "prototype",
     "title": "唤醒要不要队列",
     "closed": true,
     "blocked": [
      99
     ]
    },
    {
     "n": 105,
     "kind": "grilling",
     "title": "槽位推到哪一步",
     "closed": true,
     "blocked": [
      100,
      104
     ]
    },
    {
     "n": 106,
     "kind": "task",
     "title": "判活放哪一层",
     "closed": true,
     "blocked": [
      105
     ]
    },
    {
     "n": 107,
     "kind": "grilling",
     "title": "团队版什么时候做",
     "closed": false,
     "blocked": [
      105
     ]
    }
   ],
   "specs": [
    {
     "n": 123,
     "title": "事件评论格式",
     "tickets": [
      {
       "n": 124,
       "title": "事件表与校验",
       "lamp": "ink",
       "phase": "landed",
       "run": "cursor · grok 4.6 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": []
      },
      {
       "n": 125,
       "title": "折叠重放",
       "lamp": "ink",
       "phase": "landed",
       "run": "grok · grok 4.6 · xhigh",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        124
       ]
      },
      {
       "n": 127,
       "title": "一次 GraphQL 读四层",
       "lamp": "ink",
       "phase": "landed",
       "run": "claude · opus 5 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        124
       ]
      },
      {
       "n": 126,
       "title": "status.py 改读折叠",
       "lamp": "ink",
       "phase": "landed",
       "run": "codex · gpt-5.5 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        125
       ]
      }
     ]
    },
    {
     "n": 131,
     "title": "唤醒回路",
     "tickets": [
      {
       "n": 132,
       "title": "中继进程骨架",
       "lamp": "ink",
       "phase": "landed",
       "run": "claude · opus 5 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": []
      },
      {
       "n": 133,
       "title": "折叠接入中继",
       "lamp": "orange",
       "phase": "working",
       "run": "grok · grok 4.6 · xhigh",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 134,
       "title": "唤醒队列持久化",
       "lamp": "green",
       "phase": "review",
       "run": "codex · gpt-5.5 · medium",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 142,
       "title": "唤醒日志落盘",
       "lamp": "ink",
       "phase": "landed",
       "run": "codex · gpt 5.6 sol · medium",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 139,
       "title": "槽位交还后叫醒",
       "lamp": "orange",
       "phase": "verify",
       "run": "claude · opus 5 · high",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 138,
       "title": "离线时唤醒去向",
       "lamp": "orange",
       "phase": "verify",
       "run": "grok · grok 4.6 · high",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 141,
       "title": "中继日志轮转",
       "lamp": "green",
       "phase": "working",
       "run": "cursor · composer 2.5 · —",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": true,
       "blocked": [
        132
       ]
      },
      {
       "n": 136,
       "title": "重试与退避",
       "lamp": "green",
       "phase": "waiting",
       "run": "waiting for a slot · since 07:32",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 135,
       "title": "投递回执",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        133,
        134
       ]
      },
      {
       "n": 137,
       "title": "中继自检命令",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        135
       ]
      }
     ]
    },
    {
     "n": 140,
     "title": "判活三层",
     "tickets": [
      {
       "n": 143,
       "title": "心跳读取",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": []
      },
      {
       "n": 144,
       "title": "回合守卫",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        143
       ]
      },
      {
       "n": 145,
       "title": "worker.lost 写入",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        144
       ]
      },
      {
       "n": 146,
       "title": "判活扫描",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        143
       ]
      }
     ]
    }
   ]
  }
 },
 "twenty-tickets": {
  "selected": 220,
  "expanded": [
   210,
   211
  ],
  "task": {
   "n": 210,
   "kind": "map",
   "title": "判活三层落地",
   "decisions": [
    {
     "n": 208,
     "kind": "grilling",
     "title": "三层各看什么",
     "closed": true,
     "blocked": []
    },
    {
     "n": 209,
     "kind": "research",
     "title": "runner 能不能证明它停了",
     "closed": true,
     "blocked": [
      208
     ]
    }
   ],
   "specs": [
    {
     "n": 211,
     "title": "判活：心跳、回合、扫描",
     "tickets": [
      {
       "n": 212,
       "title": "心跳文件格式",
       "lamp": "ink",
       "phase": "landed",
       "run": "claude · opus 5 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": []
      },
      {
       "n": 213,
       "title": "心跳写入钩子",
       "lamp": "ink",
       "phase": "landed",
       "run": "codex · gpt-5.5 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        212
       ]
      },
      {
       "n": 214,
       "title": "回合守卫骨架",
       "lamp": "ink",
       "phase": "landed",
       "run": "grok · grok 4.6 · xhigh",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        212
       ]
      },
      {
       "n": 216,
       "title": "Paseo 回合字段读取",
       "lamp": "ink",
       "phase": "landed",
       "run": "cursor · grok 4.6 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        212
       ]
      },
      {
       "n": 217,
       "title": "Herdr 状态读取",
       "lamp": "ink",
       "phase": "landed",
       "run": "codex · gpt-5.5 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        212
       ]
      },
      {
       "n": 218,
       "title": "Orca tui-idle 等待",
       "lamp": "green",
       "phase": "working",
       "run": "cursor · composer 2.5 · —",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        212
       ]
      },
      {
       "n": 219,
       "title": "tmux pane 探活",
       "lamp": "green",
       "phase": "working",
       "run": "grok · grok 4.6 · high",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        212
       ]
      },
      {
       "n": 229,
       "title": "远程 --on 探活",
       "lamp": "orange",
       "phase": "verify",
       "run": "grok · grok 4.6 · xhigh",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        212
       ]
      },
      {
       "n": 215,
       "title": "Stop hook 叠挂",
       "lamp": "ink",
       "phase": "landed",
       "run": "claude · opus 5 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        214
       ]
      },
      {
       "n": 220,
       "title": "判活扫描循环",
       "lamp": "orange",
       "phase": "working",
       "run": "claude · opus 5 · high",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        213,
        214
       ]
      },
      {
       "n": 223,
       "title": "扫描间隔配置",
       "lamp": "green",
       "phase": "review",
       "run": "codex · gpt-5.5 · medium",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        214
       ]
      },
      {
       "n": 225,
       "title": "陈旧绑定检测",
       "lamp": "green",
       "phase": "waiting",
       "run": "waiting for a slot · since 07:26",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        217
       ]
      },
      {
       "n": 228,
       "title": "install --check 覆盖叠挂",
       "lamp": "ink",
       "phase": "landed",
       "run": "grok · grok 4.6 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": true,
       "blocked": [
        215
       ]
      },
      {
       "n": 221,
       "title": "worker.lost 写入",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        220
       ]
      },
      {
       "n": 222,
       "title": "「不知道」与「死了」分开",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        216,
        217,
        218,
        219
       ]
      },
      {
       "n": 224,
       "title": "误判回放测试",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        221,
        222
       ]
      },
      {
       "n": 226,
       "title": "retract 联动",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        221
       ]
      },
      {
       "n": 227,
       "title": "夜间摘要一行",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        221
       ]
      },
      {
       "n": 230,
       "title": "判活文档",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        222,
        223
       ]
      },
      {
       "n": 231,
       "title": "端到端夜跑",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        224,
        226,
        227,
        230
       ]
      }
     ]
    }
   ]
  }
 },
 "bad-data": {
  "selected": 306,
  "expanded": [
   300,
   301
  ],
  "task": {
   "n": 300,
   "kind": "map",
   "title": "端口租约回收",
   "decisions": [],
   "specs": [
    {
     "n": 301,
     "title": "租约回收",
     "tickets": [
      {
       "n": 302,
       "title": "租约登记表",
       "lamp": "ink",
       "phase": "landed",
       "run": "claude · opus 5 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": []
      },
      {
       "n": 303,
       "title": "回收脚本",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        302,
        304
       ]
      },
      {
       "n": 304,
       "title": "占用探测",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        303
       ]
      },
      {
       "n": 305,
       "title": "回收日志",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        399
       ]
      },
      {
       "n": 307,
       "title": "回收冲突告警",
       "lamp": "orange",
       "phase": "working",
       "run": "stopped · grok · grok 4.6",
       "runFlag": true,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        302
       ]
      },
      {
       "n": 306,
       "title": "lease --check",
       "lamp": "green",
       "phase": "working",
       "run": "codex · gpt-5.5 · high",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        302
       ]
      }
     ]
    }
   ]
  }
 },
 "empty": {
  "selected": null,
  "expanded": [],
  "task": null
 },
 "nothing-selected": {
  "selected": null,
  "expanded": [
   98,
   131
  ],
  "task": {
   "n": 98,
   "kind": "map",
   "title": "落地流水线改造",
   "decisions": [
    {
     "n": 99,
     "kind": "grilling",
     "title": "事件格式怎么定",
     "closed": true,
     "blocked": []
    },
    {
     "n": 100,
     "kind": "research",
     "title": "读票用什么",
     "closed": true,
     "blocked": [
      99
     ]
    },
    {
     "n": 104,
     "kind": "prototype",
     "title": "唤醒要不要队列",
     "closed": true,
     "blocked": [
      99
     ]
    },
    {
     "n": 105,
     "kind": "grilling",
     "title": "槽位推到哪一步",
     "closed": true,
     "blocked": [
      100,
      104
     ]
    },
    {
     "n": 106,
     "kind": "task",
     "title": "判活放哪一层",
     "closed": true,
     "blocked": [
      105
     ]
    },
    {
     "n": 107,
     "kind": "grilling",
     "title": "团队版什么时候做",
     "closed": false,
     "blocked": [
      105
     ]
    }
   ],
   "specs": [
    {
     "n": 123,
     "title": "事件评论格式",
     "tickets": [
      {
       "n": 124,
       "title": "事件表与校验",
       "lamp": "ink",
       "phase": "landed",
       "run": "cursor · grok 4.6 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": []
      },
      {
       "n": 125,
       "title": "折叠重放",
       "lamp": "ink",
       "phase": "landed",
       "run": "grok · grok 4.6 · xhigh",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        124
       ]
      },
      {
       "n": 127,
       "title": "一次 GraphQL 读四层",
       "lamp": "ink",
       "phase": "landed",
       "run": "claude · opus 5 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        124
       ]
      },
      {
       "n": 126,
       "title": "status.py 改读折叠",
       "lamp": "ink",
       "phase": "landed",
       "run": "codex · gpt-5.5 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        125
       ]
      }
     ]
    },
    {
     "n": 131,
     "title": "唤醒回路",
     "tickets": [
      {
       "n": 132,
       "title": "中继进程骨架",
       "lamp": "ink",
       "phase": "landed",
       "run": "claude · opus 5 · high",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": []
      },
      {
       "n": 133,
       "title": "折叠接入中继",
       "lamp": "orange",
       "phase": "working",
       "run": "grok · grok 4.6 · xhigh",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 134,
       "title": "唤醒队列持久化",
       "lamp": "green",
       "phase": "review",
       "run": "codex · gpt-5.5 · medium",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 142,
       "title": "唤醒日志落盘",
       "lamp": "ink",
       "phase": "landed",
       "run": "codex · gpt 5.6 sol · medium",
       "runFlag": false,
       "done": true,
       "released": true,
       "running": false,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 139,
       "title": "槽位交还后叫醒",
       "lamp": "orange",
       "phase": "verify",
       "run": "claude · opus 5 · high",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 138,
       "title": "离线时唤醒去向",
       "lamp": "orange",
       "phase": "verify",
       "run": "grok · grok 4.6 · high",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 141,
       "title": "中继日志轮转",
       "lamp": "green",
       "phase": "working",
       "run": "cursor · composer 2.5 · —",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": true,
       "blocked": [
        132
       ]
      },
      {
       "n": 136,
       "title": "重试与退避",
       "lamp": "green",
       "phase": "waiting",
       "run": "waiting for a slot · since 07:32",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": true,
       "closeout": false,
       "blocked": [
        132
       ]
      },
      {
       "n": 135,
       "title": "投递回执",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        133,
        134
       ]
      },
      {
       "n": 137,
       "title": "中继自检命令",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        135
       ]
      }
     ]
    },
    {
     "n": 140,
     "title": "判活三层",
     "tickets": [
      {
       "n": 143,
       "title": "心跳读取",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": []
      },
      {
       "n": 144,
       "title": "回合守卫",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        143
       ]
      },
      {
       "n": 145,
       "title": "worker.lost 写入",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        144
       ]
      },
      {
       "n": 146,
       "title": "判活扫描",
       "lamp": "hollow",
       "phase": "queued",
       "run": "not dispatched",
       "runFlag": false,
       "done": false,
       "released": false,
       "running": false,
       "closeout": false,
       "blocked": [
        143
       ]
      }
     ]
    }
   ]
  }
 }
};
