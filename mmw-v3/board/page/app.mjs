import {Board, defaultExpanded} from "./board-logic.mjs";
import {render as topbar, fromBoard as topbarFromBoard} from "./topbar.mjs";
import {render as tasks} from "./tasks.mjs";
import {render as canvas} from "./canvas.mjs";
import {find, render as detail, unmount as unmountDetail, fromBoard as detailFromBoard} from "./detail.mjs";
import {render as settings, fromPayload as settingsFromPayload, unmount as unmountSettings} from "./settings.mjs";
import {api} from "./api.mjs";
import {startBoardFeed} from "./board-feed.mjs";

function nextOrange(tasks, current) {
  const list = [];
  for (const task of tasks) {
    const nodes = Board.layout(task, defaultExpanded(task)).nodes
      .filter(node => node.type === "ticket" && Board.lamp(node.ref) === "orange")
      .sort((left, right) => left.y - right.y || left.x - right.x);
    for (const node of nodes) {
      list.push({task: task.n, node: node.id});
    }
  }
  if (!list.length) return null;
  const index = list.findIndex(item => item.node === current);
  return list[(index + 1) % list.length];
}

export function boardShell(doc) {
  const root = doc.createElement("main");
  root.className = "app-shell board";
  root.dataset.screen = "board";
  root.dataset.boardRoot = "";
  root.dataset.ui = "任务板.root";
  const slot = (className, mount) => {
    const node = doc.createElement("div");
    node.className = className;
    if (mount) node.dataset.mount = mount;
    return node;
  };
  const row = slot("app-row");
  row.append(slot("app-slot", "tasks"), slot("app-slot", "canvas"), slot("app-slot", "detail"));
  root.append(slot("app-top", "topbar"), row, slot("app-sheet", "settings"));
  return root;
}

function pageRoot(target) {
  const existing = target.matches?.("[data-board-root]")
    ? target
    : target.querySelector?.("[data-board-root]");
  if (existing) return existing;
  const doc = target.ownerDocument || target;
  const root = boardShell(doc);
  (target.body || target).append(root);
  return root;
}

// The design page is a column: the top bar, then a row of the task list, the
// canvas and (only while a card is open) the detail. The detail slot leaves the
// row when it is empty, and the canvas takes that width.
export function applyShell(root, slots, hasDetail) {
  Object.assign(root.style, {
    position: "relative",
    width: "100%",
    height: "100%",
    display: "flex",
    flexDirection: "column",
    background: "var(--panel)",
    overflow: "hidden",
  });
  Object.assign(slots.topbar.style, {flex: "none", minWidth: "0"});
  const row = root.querySelector(".app-row");
  if (row) {
    Object.assign(row.style, {
      flex: "1", minHeight: "0", display: "flex", alignItems: "stretch",
    });
  }
  Object.assign(slots.tasks.style, {
    flex: "none", width: "236px", minWidth: "0", minHeight: "0", overflow: "hidden",
  });
  Object.assign(slots.canvas.style, {
    flex: "1", minWidth: "0", minHeight: "0", overflow: "hidden",
  });
  Object.assign(slots.detail.style, {
    flex: "none", width: "340px", minWidth: "0", minHeight: "0", overflow: "hidden",
    display: hasDetail ? "" : "none",
  });
  Object.assign(slots.settings.style, {
    position: "absolute", inset: "0", zIndex: "30",
    pointerEvents: root.querySelector('[data-screen="settings"]') ? "auto" : "none",
  });
}

export function mountPage(target = document, options = {}) {
  const root = pageRoot(target);
  const slots = {
    topbar: root.querySelector('[data-mount="topbar"]'),
    tasks: root.querySelector('[data-mount="tasks"]'),
    canvas: root.querySelector('[data-mount="canvas"]'),
    detail: root.querySelector('[data-mount="detail"]'),
    settings: root.querySelector('[data-mount="settings"]'),
  };
  const input = options.data || {};
  const apiClient = options.api || api;
  const fixedNow = input.now ? new Date(input.now) : null;
  const state = {
    payload: input.payload || {tasks: []},
    task: input.select?.task ?? null,
    sel: input.select?.node ?? null,
    expanded: null,
    settingsOpen: Boolean(input.settingsOpen),
    settingsPayload: input.settings || null,
    hasSuccessfulPayload: Boolean(input.payload && !input.payload.read_failed),
  };

  const taskOf = n => (state.payload.tasks || []).find(task => task.n === n) || null;

  const setTask = n => {
    if (state.task === n) return;
    state.task = n;
    const task = taskOf(n);
    state.expanded = task ? [...defaultExpanded(task)] : [];
  };

  const revealNode = n => {
    const found = find(state.payload.tasks || [], n);
    if (!found) return false;
    setTask(found.task.n);
    const expanded = new Set(state.expanded || []);
    if (found.type === "ticket") expanded.add(found.spec.n);
    if (found.type === "decision") expanded.add(found.task.n);
    state.expanded = [...expanded];
    state.sel = n;
    return true;
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
    const listSign = JSON.stringify(list);
    const topbarView = topbarFromBoard(
      {...state.payload, settingsOpen: state.settingsOpen},
      fixedNow || new Date(),
    );
    if (changed("topbar", JSON.stringify(topbarView))) {
      topbar(slots.topbar, topbarView, apiClient, {
        onJumpNeedYou() {
          const next = nextOrange(list, state.sel);
          if (next && revealNode(next.node)) paint();
        },
        onRefresh(data) {
          if (data.read_failed && state.hasSuccessfulPayload) {
            state.payload = {
              ...state.payload,
              read_at: data.read_at,
              read_failed: data.read_failed,
            };
          } else {
            state.payload = data;
            if (!data.read_failed) state.hasSuccessfulPayload = true;
          }
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
    const detailView = detailFromBoard(state.payload, state.sel, fixedNow || new Date());
    const detailHooks = {
      onGoto(n) {
        if (revealNode(n)) paint();
      },
      onClose() {
        state.sel = null;
        paint();
      },
    };
    if (changed("detail", JSON.stringify(detailView))) {
      if (detailView.empty) {
        unmountDetail(slots.detail);
      } else {
        detail(slots.detail, detailView, apiClient, detailHooks);
      }
    }
    if (!slots.settings) return;
    const open = slots.settings.querySelector('[data-screen="settings"]');
    if (state.settingsOpen && state.settingsPayload && !open) {
      settings(slots.settings, settingsFromPayload(state.settingsPayload), apiClient, {
        onClose: closeSettings,
      });
    } else if (!state.settingsOpen && open) {
      unmountSettings(slots.settings);
    }
    applyShell(root, slots, !detailView.empty);
  };

  paint();
  if (options.live !== false) {
    const doc = root.ownerDocument;
    startBoardFeed({
      read: async () => {
        try {
          const response = await apiClient.board();
          if (response.ok) return await response.json();
        } catch {}
        return state.payload;
      },
      isVisible: () => doc.visibilityState !== "hidden",
      onData(data) {
        state.payload = data;
        if (!data.read_failed) state.hasSuccessfulPayload = true;
        paint();
      },
    });
  }
  return root;
}

if (typeof document !== "undefined" && document.querySelector("[data-board-root]")) {
  mountPage(document);
}
