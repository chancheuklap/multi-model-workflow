import {Board, defaultExpanded} from "./board-logic.mjs";
import {render as topbar, fromBoard as topbarFromBoard} from "./topbar.mjs";
import {render as tasks} from "./tasks.mjs";
import {render as canvas} from "./canvas.mjs";
import {find, render as detail, fromBoard as detailFromBoard} from "./detail.mjs";
import {render as settings, fromPayload as settingsFromPayload, unmount as unmountSettings} from "./settings.mjs";
import {api} from "./api.mjs";
import {startBoardFeed} from "./board-feed.mjs";

function nextOrange(tasks, current) {
  const list = [];
  for (const task of tasks) {
    for (const ticket of Board.allTickets(task)) {
      if (Board.light(ticket) === "orange") list.push({task: task.n, node: ticket.n});
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
    expanded: null,
    settingsOpen: false,
    settingsPayload: null,
  };

  const taskOf = n => (state.payload.tasks || []).find(task => task.n === n) || null;

  const setTask = n => {
    if (state.task === n) return;
    state.task = n;
    const task = taskOf(n);
    state.expanded = task ? [...defaultExpanded(task)] : [];
  };

  const closeSettings = () => {
    if (!state.settingsOpen) return;
    state.settingsOpen = false;
    unmountSettings(slots.settings);
    paint();
  };

  const paint = () => {
    const list = state.payload.tasks || [];
    if (state.task == null && list[0]) setTask(list[0].n);
    topbar(slots.topbar, topbarFromBoard({...state.payload, settingsOpen: state.settingsOpen}), api, {
      onJumpNeedYou() {
        const next = nextOrange(list, state.sel);
        if (next) {
          setTask(next.task);
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
        setTask(n);
        state.sel = null;
        paint();
      },
    });
    canvas(slots.canvas, {
      task: taskOf(state.task),
      sel: state.sel,
      expanded: state.expanded,
      onSelectNode(n) {
        state.sel = n;
        paint();
      },
      onToggle(_n, expanded) {
        state.expanded = expanded;
      },
    });
    detail(slots.detail, detailFromBoard(state.payload, state.sel), api, {
      onGoto(n) {
        const found = find(list, n);
        if (found) {
          setTask(found.task.n);
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
    const open = slots.settings.querySelector('[data-screen="settings"]');
    if (state.settingsOpen && state.settingsPayload && !open) {
      settings(slots.settings, settingsFromPayload(state.settingsPayload), api, {
        onClose: closeSettings,
      });
    } else if (!state.settingsOpen && open) {
      unmountSettings(slots.settings);
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
