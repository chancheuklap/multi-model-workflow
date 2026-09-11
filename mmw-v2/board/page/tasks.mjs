import {Board, LIGHT_WORD} from "./board-logic.mjs";

function css(value) {
  if (value == null || value === "") return "";
  if (typeof value === "string") return value;
  return Object.entries(value)
    .map(([key, val]) => `${key.replace(/[A-Z]/g, ch => `-${ch.toLowerCase()}`)}: ${val}`)
    .join("; ");
}

export function taskListView(tasks, taskN) {
  return {
    count: tasks.length,
    empty: !tasks.length,
    rows: tasks.map(task => {
      const progress = Board.progress(task);
      const light = Board.aggregate(Board.allTickets(task));
      const on = task.n === taskN;
      return {
        n: task.n,
        cls: on ? "task on" : "task",
        titleCls: on ? "task-title on" : "task-title",
        lightCls: "light " + light,
        lightWord: LIGHT_WORD[light],
        meta: `#${task.n} · ${task.kind}`,
        title: task.title,
        barStyle: {width: (progress.total ? 100 * progress.done / progress.total : 0) + "%"},
        count: `${progress.done}/${progress.total} 落地`,
      };
    }),
  };
}

function viewFrom(data) {
  if (data?.vals?.v) return data.vals.v;
  if (data?.view) return data.view;
  if (Array.isArray(data?.tasks)) return taskListView(data.tasks, data.task ?? data.state?.task);
  return {count: 0, empty: true, rows: []};
}

function rowButton(row, onPick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = row.cls;
  button.addEventListener("click", () => onPick(row.n));

  const light = document.createElement("span");
  light.className = row.lightCls;
  light.title = row.lightWord;

  const meta = document.createElement("span");
  meta.className = "task-meta";
  meta.textContent = row.meta;

  const title = document.createElement("span");
  title.className = row.titleCls;
  title.textContent = row.title;

  const fill = document.createElement("span");
  fill.className = "bar-fill";
  fill.style.cssText = css(row.barStyle);
  const bar = document.createElement("span");
  bar.className = "bar";
  bar.append(fill);
  const count = document.createElement("span");
  count.className = "task-count";
  count.textContent = row.count;
  const progress = document.createElement("span");
  progress.className = "task-progress";
  progress.append(bar, count);

  button.append(light, meta, title, progress);
  return button;
}

export function render(host, data = {}, api = undefined) {
  const selected = data.state?.task ?? data.task ?? null;
  const view = viewFrom(data);
  const root = document.createElement("nav");
  root.dataset.screen = "tasks";
  root.className = "tasks board";
  root.setAttribute("aria-label", "任务");

  const paint = (taskN) => {
    const next = data.vals?.v || data.view
      ? {
          ...view,
          rows: view.rows.map(row => ({
            ...row,
            cls: row.n === taskN ? "task on" : "task",
            titleCls: row.n === taskN ? "task-title on" : "task-title",
          })),
        }
      : viewFrom({...data, task: taskN, state: {...data.state, task: taskN}});
    const eyebrow = document.createElement("div");
    eyebrow.className = "col-eyebrow";
    const label = document.createElement("span");
    label.textContent = "任务";
    const count = document.createElement("span");
    count.textContent = String(next.count);
    eyebrow.append(label, count);
    const kids = [eyebrow];
    if (next.empty) {
      const empty = document.createElement("p");
      empty.className = "tasks-empty";
      empty.textContent = "没有带 mmw:map label 的票。";
      kids.push(empty);
    }
    for (const row of next.rows) {
      kids.push(rowButton(row, n => {
        paint(n);
        data.onSelectTask?.(n);
      }));
    }
    root.replaceChildren(...kids);
  };

  paint(selected);
  host.replaceChildren(root);
  return root;
}
