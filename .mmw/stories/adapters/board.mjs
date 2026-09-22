import {Board, LAMP_WORD, defaultExpanded} from "/product/board-logic.mjs";
import {applyShell, boardShell} from "/product/app.mjs";
import {canvasView, render as renderCanvas} from "/product/canvas.mjs";
import {find, fromBoard as detailFromBoard, render as renderDetail, unmount as unmountDetail} from "/product/detail.mjs";
import {LocalConfig} from "/product/local-config.mjs";
import {fromPayload, render as renderSettings, unmount as unmountSettings} from "/product/settings.mjs";
import {render as renderTasks, taskRowView} from "/product/tasks.mjs";
import {fromBoard as topbarFromBoard, render as renderTopbar} from "/product/topbar.mjs";

// Scene input is APP_SCENES.<scene>: which board, which task, which card, and
// which settings scene. The trees and the detail views sit beside that value in
// the same file. Each column's own scene input supplies the fields that scene
// already drew (the top bar, the task list, the settings answer).

async function readJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const reason = (await response.text()).trim();
    throw new Error(reason || `${url} returned ${response.status}`);
  }
  return response.json();
}

function sceneInput(name) {
  return readJson(`/scene-input.json?scene=${encodeURIComponent(name)}`);
}

function windowKeys(file, keys) {
  const query = new URLSearchParams({file});
  for (const key of keys) query.append("key", key);
  return readJson(`/window-keys.json?${query}`);
}

// Board.layout reads blocker_hold, decision state and a live session. The words
// on the cards stay the tree's own lamp, phase and run.
function layoutTask(task) {
  const ticket = item => ({
    ...item,
    events: [],
    children: [],
    blocker_hold: item.released ? "" : "held",
    state: "open",
    fold: {
      sessions: item.running ? [{live: true, kind: "worker"}] : [],
      children: {},
    },
  });
  const decision = item => ({
    ...item,
    state: item.closed ? "closed" : "open",
    blocked: item.blocked || [],
  });
  return {
    ...task,
    decisions: (task.decisions || []).map(decision),
    specs: (task.specs || []).map(spec => ({
      ...spec,
      tickets: (spec.tickets || []).map(ticket),
    })),
  };
}

function lampOf(tickets) {
  const lamps = tickets.map(ticket => ticket.lamp);
  if (lamps.includes("orange")) return "orange";
  if (lamps.includes("green")) return "green";
  if (lamps.length && lamps.every(lamp => lamp === "ink")) return "ink";
  return "hollow";
}

function face(lamp) {
  return {lampCls: "lamp " + lamp, lampWord: LAMP_WORD[lamp]};
}

function withSceneText(view, task) {
  const tickets = new Map();
  for (const spec of task.specs || []) {
    for (const ticket of spec.tickets || []) tickets.set(ticket.n, ticket);
  }
  const specs = new Map((task.specs || []).map(spec => [spec.n, spec.tickets || []]));
  const all = [...tickets.values()];
  return {
    ...view,
    tickets: view.tickets.map(item => {
      const ticket = tickets.get(item.n);
      if (!ticket) return item;
      return {
        ...item,
        ...face(ticket.lamp),
        phase: ticket.phase,
        pillCls: "pill " + ticket.phase,
        run: ticket.run,
        runCls: ticket.runFlag ? "card-run flag" : "card-run",
      };
    }),
    containers: view.containers.map(item => {
      const list = item.n === task.n ? all : specs.get(item.n);
      if (!list) return item;
      const done = list.filter(ticket => ticket.done).length;
      const lamp = lampOf(list);
      return {
        ...item,
        ...face(lamp),
        count: `${done}/${list.length}`,
        barStyle: {width: (list.length ? 100 * done / list.length : 0) + "%"},
      };
    }),
  };
}

function designExpanded(task) {
  if (!task) return [];
  const out = [task.n];
  for (const spec of task.specs || []) {
    const lamps = (spec.tickets || []).map(ticket => ticket.lamp);
    if (lamps.includes("orange") || lamps.includes("green")) out.push(spec.n);
  }
  return out;
}

function taskHolding(trees, n) {
  for (const [taskN, tree] of Object.entries(trees)) {
    if (Number(taskN) === n) return Number(taskN);
    if ((tree.decisions || []).some(item => item.n === n)) return Number(taskN);
    for (const spec of tree.specs || []) {
      if (spec.n === n) return Number(taskN);
      if ((spec.tickets || []).some(ticket => ticket.n === n)) return Number(taskN);
    }
  }
  return null;
}

function nextDesignOrange(trees, current) {
  const list = [];
  for (const [taskN, tree] of Object.entries(trees)) {
    for (const ticket of (tree.specs || []).flatMap(spec => spec.tickets || [])) {
      if (ticket.lamp === "orange") list.push({task: Number(taskN), n: ticket.n});
    }
  }
  if (!list.length) return null;
  const at = list.findIndex(item => item.n === current);
  return list[(at + 1) % list.length];
}

function nextPayloadOrange(tasks, current) {
  const list = [];
  for (const task of tasks) {
    const nodes = Board.layout(task, defaultExpanded(task)).nodes
      .filter(node => node.type === "ticket" && Board.lamp(node.ref) === "orange")
      .sort((left, right) => left.y - right.y || left.x - right.x);
    for (const node of nodes) list.push({task: task.n, n: node.id});
  }
  if (!list.length) return null;
  const at = list.findIndex(item => item.n === current);
  return list[(at + 1) % list.length];
}

function applyPage(model, page) {
  for (const [agent, cell, value] of page.edit || []) {
    LocalConfig.setCell(model.scan, model.st.draft, agent, cell, value);
  }
  if (page.scanning) model.st.scanning = true;
  if (page.refused) model.st.refused = page.refused;
  if (page.modifiedAt) model.st.modifiedAt = page.modifiedAt;
  if (page.saveAt) {
    model.st.saved = structuredClone(model.st.draft);
    model.st.savedAt = page.saveAt;
  }
  if (page.serverFlags) {
    model.st.serverFlags = page.serverFlags.map(error => {
      const [key, cell] = String(error.cell).split(".");
      return {key, cell: cell || key, text: error.reason};
    });
  }
  return model;
}

function failureRead(data) {
  return topbarFromBoard({
    read_at: data.read_at,
    read_failed: data.read_failed,
    tasks: [],
  });
}

export async function render(host, data, api) {
  host.style.cssText = "width:1440px;height:900px";
  const board = data.board;
  const [pack, topbarScene, taskScene, settingsScene] = await Promise.all([
    windowKeys("data/app-scenes.js", ["APP_TREES", "APP_DETAILS"]),
    sceneInput(`Component · 顶栏.${board}`),
    sceneInput(`Component · 任务列表.${board}`),
    data.settings ? sceneInput(`Component · 本机配置.${data.settings}`) : null,
  ]);
  const trees = pack.APP_TREES[board] || {};
  const details = pack.APP_DETAILS[board] || {};
  const state = {
    source: "design",
    payload: null,
    topbar: topbarScene,
    taskRows: taskScene.rows || [],
    task: data.task ?? null,
    sel: data.sel ?? null,
    expanded: null,
    settingsOpen: Boolean(data.settings),
    settingsModel: settingsScene ? applyPage(fromPayload(settingsScene.payload), settingsScene.page || {}) : null,
    good: !topbarScene.readFailed,
  };

  const root = boardShell(host.ownerDocument);
  host.replaceChildren(root);
  root.dataset.storyRoot = "";
  const slots = {
    topbar: root.querySelector('[data-mount="topbar"]'),
    tasks: root.querySelector('[data-mount="tasks"]'),
    canvas: root.querySelector('[data-mount="canvas"]'),
    detail: root.querySelector('[data-mount="detail"]'),
    settings: root.querySelector('[data-mount="settings"]'),
  };

  const designTree = n => (n == null ? null : trees[String(n)] || null);
  const payloadTask = n => (state.payload?.tasks || []).find(task => task.n === n) || null;
  const currentTree = () => (state.source === "payload" ? payloadTask(state.task) : designTree(state.task));

  const setTask = n => {
    if (state.task === n) return;
    state.task = n;
    const task = currentTree();
    state.expanded = task
      ? (state.source === "payload" ? [...defaultExpanded(task)] : designExpanded(task))
      : [];
  };

  const reveal = n => {
    const holder = state.source === "payload"
      ? (find(state.payload?.tasks || [], n)?.task.n ?? null)
      : taskHolding(trees, n);
    if (holder == null) return false;
    setTask(holder);
    const expanded = new Set(state.expanded || []);
    if (state.source === "payload") {
      const found = find(state.payload.tasks, n);
      if (found?.type === "ticket") expanded.add(found.spec.n);
      if (found?.type === "decision") expanded.add(found.task.n);
    } else {
      const tree = designTree(holder);
      const spec = (tree?.specs || []).find(item =>
        (item.tickets || []).some(ticket => ticket.n === n));
      if (spec) expanded.add(spec.n);
      if ((tree?.decisions || []).some(item => item.n === n)) expanded.add(tree.n);
    }
    state.expanded = [...expanded];
    state.sel = n;
    return true;
  };

  const detailView = () => {
    if (state.sel == null) return null;
    if (state.source === "payload") {
      const view = detailFromBoard(state.payload, state.sel, new Date());
      return view.empty ? null : view;
    }
    return details[String(state.sel)] || null;
  };

  const paintTopbar = () => {
    const view = state.source === "payload"
      ? topbarFromBoard({...state.payload, settingsOpen: state.settingsOpen})
      : {...state.topbar, settingsOpen: state.settingsOpen};
    renderTopbar(slots.topbar, view, api, {
      onJumpNeedYou() {
        const next = state.source === "payload"
          ? nextPayloadOrange(state.payload?.tasks || [], state.sel)
          : nextDesignOrange(trees, state.sel);
        if (next && reveal(next.n)) paint();
      },
      onRefresh(body) {
        if (body.read_failed && state.good) {
          const failed = failureRead(body);
          if (state.source === "payload") {
            state.payload = {
              ...state.payload,
              read_at: body.read_at,
              read_failed: body.read_failed,
            };
          } else {
            state.topbar = {...state.topbar, readFailed: failed.readFailed, readText: failed.readText};
          }
          paintTopbar();
          return;
        }
        state.source = "payload";
        state.payload = body;
        state.good = !body.read_failed;
        const task = payloadTask(state.task);
        state.expanded = task ? [...defaultExpanded(task)] : [];
        paint();
      },
      onOpenSettings(body) {
        state.settingsModel = fromPayload(body);
        state.settingsOpen = true;
        paint();
      },
    });
  };

  const paintTasks = () => {
    const selectedTask = state.task;
    if (state.source === "payload") {
      renderTasks(slots.tasks, {
        tasks: state.payload?.tasks || [],
        selectedTask,
        onSelectTask(n) {
          setTask(n);
          state.sel = null;
          paint();
        },
      });
      return;
    }
    renderTasks(slots.tasks, {
      view: {
        count: state.taskRows.length,
        empty: !state.taskRows.length,
        rows: state.taskRows.map(taskRowView),
      },
      selectedTask,
      onSelectTask(n) {
        setTask(n);
        state.sel = null;
        paint();
      },
    });
  };

  const paintCanvas = () => {
    const task = currentTree();
    if (state.expanded == null) {
      state.expanded = task
        ? (state.source === "payload" ? [...defaultExpanded(task)] : designExpanded(task))
        : [];
    }
    const shared = {
      sel: state.sel,
      expanded: state.expanded,
      onSelectNode(n) {
        state.sel = n;
        paint();
      },
      onToggle(_n, expanded) {
        state.expanded = expanded;
      },
    };
    if (state.source === "payload") {
      renderCanvas(slots.canvas, {...shared, task});
      return;
    }
    // `task` is what the canvas uses to decide that the tree changed. `project`
    // is what it draws: the design tree's own lamp, phase and run.
    renderCanvas(slots.canvas, {
      ...shared,
      task,
      project(sel, expanded, reduced) {
        if (!task) return canvasView(null, sel, expanded, reduced);
        return withSceneText(canvasView(layoutTask(task), sel, expanded, reduced), task);
      },
    });
  };

  const paintDetail = () => {
    const view = detailView();
    if (!view) {
      unmountDetail(slots.detail);
      return;
    }
    renderDetail(slots.detail, view, api, {
      onGoto(n) {
        if (reveal(n)) paint();
      },
      onClose() {
        state.sel = null;
        paint();
      },
    });
  };

  const paintSettings = () => {
    const open = slots.settings.querySelector('[data-screen="settings"]');
    if (state.settingsOpen && state.settingsModel && !open) {
      const sheet = renderSettings(slots.settings, state.settingsModel, api, {
        onClose() {
          state.settingsOpen = false;
          unmountSettings(slots.settings);
          paintTopbar();
          applyShell(root, slots, Boolean(detailView()));
        },
      });
      sheet.classList.remove("transparent");
    } else if (!state.settingsOpen && open) {
      unmountSettings(slots.settings);
    }
  };

  function paint() {
    applyShell(root, slots, Boolean(detailView()));
    paintTopbar();
    paintTasks();
    paintCanvas();
    paintDetail();
    paintSettings();
    // Sets the column roots to the viewport height before the canvas fits.
    applyShell(root, slots, Boolean(detailView()));
  }

  paint();
  return root;
}
