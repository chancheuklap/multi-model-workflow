import {render as renderProduct, canvasView} from "/product/canvas.mjs";
import {LAMP_WORD} from "/product/board-logic.mjs";

// The scene input is CANVAS_SCENES.<scene>: selected node, open containers, and a
// tree whose tickets already carry lamp, phase, run, done, released and running,
// and whose decisions carry closed. The component draws a view. This adapter is
// what turns that scene into the view, including on expand and collapse.

// Board.layout calls these facts blocker_hold, decision state and a live session.
// The words on the cards stay the scene's own lamp, phase and run.
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

export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);
  const move = (scene, value) => transitions.push({scene, data: value});
  const scene = data.task ?? null;
  const root = renderProduct(host, {
    project(sel, expanded, reduced) {
      if (!scene) return canvasView(null, sel, expanded, reduced);
      return withSceneText(canvasView(layoutTask(scene), sel, expanded, reduced), scene);
    },
    sel: data.selected ?? null,
    expanded: data.expanded ?? [],
    onSelectNode(node) {
      move("Component · 画布.morning", {node});
    },
    onToggle(node, expanded) {
      move(expanded.includes(node) ? "container-expanded" : "container-collapsed",
        {node, expanded});
    },
    onViewport(sceneName, view) {
      move(sceneName, view);
    },
  }, api);
  root.dataset.storyRoot = "";
  root.style.cssText = "width:864px;height:848px";
}
