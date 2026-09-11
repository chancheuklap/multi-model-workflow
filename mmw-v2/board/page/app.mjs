import {Board} from "./board-logic.mjs";
import {render as topbar, fromBoard as topbarFromBoard} from "./topbar.mjs";
import {render as tasks} from "./tasks.mjs";
import {render as canvas} from "./canvas.mjs";
import {render as detail, fromBoard as detailFromBoard} from "./detail.mjs";
import {render as settings, fromPayload as settingsFromPayload} from "./settings.mjs";
import {api} from "./api.mjs";
import {startBoardFeed} from "./board-feed.mjs";

function find(tasks, n) {
  if (n == null) return null;
  for (const task of tasks) {
    if (task.n === n) return {type: "map", ref: task, task};
    for (const decision of task.decisions || []) {
      if (decision.n === n) return {type: "decision", ref: decision, task};
    }
    for (const spec of task.specs || []) {
      if (spec.n === n) return {type: "spec", ref: spec, task};
      for (const ticket of spec.tickets || []) {
        if (ticket.n === n) return {type: "ticket", ref: ticket, task, spec};
      }
    }
  }
  return null;
}

function nextOrange(tasks, current) {
  const list = [];
  for (const task of tasks) {
    for (const spec of task.specs || []) {
      for (const ticket of spec.tickets || []) {
        if (Board.light(ticket) === "orange") list.push({task: task.n, node: ticket.n});
      }
    }
  }
  if (!list.length) return null;
  const index = list.findIndex(item => item.node === current);
  return list[(index + 1) % list.length];
}

export function mountPage(doc = document) {
  const slots = {
    topbar: doc.querySelector('[data-mount="topbar"]'),
    tasks: doc.querySelector('[data-mount="tasks"]'),
    canvas: doc.querySelector('[data-mount="canvas"]'),
    detail: doc.querySelector('[data-mount="detail"]'),
    settings: doc.querySelector('[data-mount="settings"]'),
  };
  const state = {
    payload: {tasks: []},
    task: null,
    sel: null,
    settingsOpen: false,
    settingsPayload: null,
  };

  const taskOf = n => (state.payload.tasks || []).find(task => task.n === n) || null;

  const paint = () => {
    const list = state.payload.tasks || [];
    if (state.task == null && list[0]) state.task = list[0].n;
    topbar(slots.topbar, topbarFromBoard({...state.payload, settingsOpen: state.settingsOpen}), api, {
      onJumpNeedYou() {
        const next = nextOrange(list, state.sel);
        if (next) {
          state.task = next.task;
          state.sel = next.node;
          paint();
        }
      },
      onRefresh(data) {
        state.payload = data;
        paint();
      },
      onOpenSettings(data) {
        state.settingsPayload = data;
        state.settingsOpen = true;
        paint();
      },
    });
    tasks(slots.tasks, {
      tasks: list,
      selectedTask: state.task,
      onSelectTask(n) {
        state.task = n;
        state.sel = null;
        paint();
      },
    });
    canvas(slots.canvas, {
      task: taskOf(state.task),
      sel: state.sel,
      onSelectNode(n) {
        state.sel = n;
        paint();
      },
    });
    detail(slots.detail, detailFromBoard(state.payload, state.sel), api, {
      onGoto(n) {
        const found = find(list, n);
        if (found) {
          state.task = found.task.n;
          state.sel = n;
          paint();
        }
      },
      onClose() {
        state.sel = null;
        paint();
      },
    });
    if (!slots.settings) return;
    slots.settings.style.pointerEvents = state.settingsOpen ? "auto" : "none";
    if (state.settingsOpen && state.settingsPayload) {
      settings(slots.settings, settingsFromPayload(state.settingsPayload), api, {
        onClose() {
          state.settingsOpen = false;
          paint();
        },
      });
    } else {
      slots.settings.replaceChildren();
    }
  };

  startBoardFeed({
    read: async () => {
      try {
        const response = await api.board();
        if (response.ok) return await response.json();
      } catch {}
      return state.payload;
    },
    isVisible: () => doc.visibilityState !== "hidden",
    onData(data) {
      state.payload = data;
      paint();
    },
  });
}

if (typeof document !== "undefined") mountPage(document);
