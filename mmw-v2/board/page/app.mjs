import {Board, defaultExpanded} from "./board-logic.mjs";
import {render as topbar, fromBoard as topbarFromBoard} from "./topbar.mjs";
import {render as tasks} from "./tasks.mjs";
import {render as canvas} from "./canvas.mjs";
import {find, render as detail, unmount as unmountDetail, fromBoard as detailFromBoard} from "./detail.mjs";
import {render as settings, fromPayload as settingsFromPayload, unmount as unmountSettings} from "./settings.mjs";
import {api} from "./api.mjs";
import {startBoardFeed} from "./board-feed.mjs";

// PROTOTYPE scaffolding — prototypes/board-orchestration/sidebar-events/UI.
// `?variant=A|B|C` hands the detail column to a prototype variant, `?sel=<n>` opens a card
// on load. Nothing runs without the parameter; the import is served only by that
// prototype's own serve.py. It all comes down when a winner is folded in.
const protoQuery = typeof location === "undefined" ? null : new URLSearchParams(location.search);
const protoKey = protoQuery?.get("variant") || null;
const proto = protoKey ? await import("./proto/mount.mjs").catch(() => null) : null;

function nextOrange(tasks, current) {
  const list = [];
  for (const task of tasks) {
    for (const ticket of Board.allTickets(task)) {
      if (Board.lamp(ticket) === "orange") list.push({task: task.n, node: ticket.n});
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

  // PROTOTYPE scaffolding: `?sel=<n>` opens that card as soon as the first payload lands.
  const protoSel = proto ? Number(protoQuery.get("sel")) : NaN;
  let protoSelPending = Number.isFinite(protoSel) && protoSel > 0;

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

  // Each column's render rebuilds it from nothing, which costs the reader whatever they had
  // going in it: the canvas viewport, the detail column's scroll, an edge animation
  // mid-flight. So a column is redrawn only when what it shows differs from what is on
  // screen. A signature is the data that column reads, which includes text derived from the
  // clock (a ticket's elapsed time), so that keeps ticking.
  const shown = {};
  const changed = (column, signature) => {
    if (shown[column] === signature) return false;
    shown[column] = signature;
    return true;
  };

  const paint = () => {
    const list = state.payload.tasks || [];
    if (state.task == null && list[0]) setTask(list[0].n);
    if (protoSelPending && list.length) {
      protoSelPending = false;
      const found = find(list, protoSel);
      if (found) {
        setTask(found.task.n);
        state.sel = protoSel;
      }
    }
    const listSign = JSON.stringify(list);
    const topbarView = topbarFromBoard({...state.payload, settingsOpen: state.settingsOpen});
    if (changed("topbar", JSON.stringify(topbarView))) {
      topbar(slots.topbar, topbarView, api, {
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
    }
    if (changed("tasks", `${state.task}|${listSign}`)) {
      tasks(slots.tasks, {
        tasks: list,
        selectedTask: state.task,
        onSelectTask(n) {
          setTask(n);
          state.sel = null;
          paint();
        },
      });
    }
    if (changed("canvas", `${state.task}|${state.sel}|${(state.expanded || []).join(",")}|${listSign}`)) {
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
    }
    // Nothing picked, nothing to show: the column comes off the page rather than standing
    // there empty, and the canvas takes the width back. The stylesheet follows the slot.
    const detailView = detailFromBoard(state.payload, state.sel);
    const detailHooks = {
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
    };
    // A prototype variant reads the whole payload, not the view the real column reads, so
    // its signature is the payload it is handed.
    const detailSign = proto
      ? `${protoKey}|${state.sel}|${JSON.stringify(state.payload)}`
      : JSON.stringify(detailView);
    if (changed("detail", detailSign)) {
      if (proto) {
        proto.mount(slots.detail, {payload: state.payload, sel: state.sel, variant: protoKey}, api, detailHooks);
      } else if (detailView.empty) {
        unmountDetail(slots.detail);
      } else {
        detail(slots.detail, detailView, api, detailHooks);
      }
    }
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
