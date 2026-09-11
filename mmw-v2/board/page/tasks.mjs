import {Board, LIGHT_WORD} from "./board-logic.mjs";

function markOn(row, selectedTask) {
  const on = row.n === selectedTask;
  return {...row, cls: on ? "task on" : "task", titleCls: on ? "task-title on" : "task-title"};
}

export function taskListView(tasks, selectedTask) {
  return {
    count: tasks.length,
    empty: !tasks.length,
    rows: tasks.map(task => {
      const progress = Board.progress(task);
      const light = Board.aggregate(Board.allTickets(task));
      return markOn({
        n: task.n,
        lightCls: "light " + light,
        lightWord: LIGHT_WORD[light],
        meta: `#${task.n} · ${task.kind}`,
        title: task.title,
        barStyle: {width: (progress.total ? 100 * progress.done / progress.total : 0) + "%"},
        count: `${progress.done}/${progress.total} 落地`,
      }, selectedTask);
    }),
  };
}

function rowsFor(data, selectedTask) {
  if (Array.isArray(data.tasks)) return taskListView(data.tasks, selectedTask);
  if (data.view) {
    return {
      count: data.view.count,
      empty: data.view.empty,
      rows: data.view.rows.map(row => markOn(row, selectedTask)),
    };
  }
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
  fill.style.width = row.barStyle.width;
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
  const root = document.createElement("nav");
  root.dataset.screen = "tasks";
  root.className = "tasks board";
  root.setAttribute("aria-label", "任务");

  const paint = (selectedTask) => {
    const next = rowsFor(data, selectedTask);
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

  paint(data.selectedTask ?? null);
  host.replaceChildren(root);
  return root;
}
