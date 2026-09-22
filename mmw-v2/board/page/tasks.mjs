import {Board, LAMP_WORD} from "./board-logic.mjs";

function markOn(row, selectedTask) {
  const on = row.n === selectedTask;
  return {...row, cls: on ? "task on" : "task"};
}

export function taskListView(tasks, selectedTask) {
  return {
    count: tasks.length,
    empty: !tasks.length,
    rows: tasks.map(task => {
      const progress = Board.progress(task);
      const lamp = Board.aggregate(Board.allTickets(task));
      return markOn({
        n: task.n,
        lampCls: "lamp " + lamp,
        lampWord: LAMP_WORD[lamp],
        meta: `#${task.n} · ${task.kind}`,
        title: task.title,
        barStyle: {width: (progress.total ? 100 * progress.done / progress.total : 0) + "%"},
        count: `${progress.done}/${progress.total} landed`,
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
  button.dataset.ui = "任务列表.task";
  button.addEventListener("click", () => onPick(row.n));

  const lamp = document.createElement("span");
  lamp.className = row.lampCls;
  lamp.title = row.lampWord;
  lamp.dataset.ui = "任务列表.task.lamp";

  const meta = document.createElement("span");
  meta.className = "task-meta";
  meta.textContent = row.meta;
  meta.dataset.ui = "任务列表.task.meta";

  const title = document.createElement("span");
  title.className = "task-title";
  title.textContent = row.title;
  title.dataset.ui = "任务列表.task.title";

  const fill = document.createElement("span");
  fill.className = "bar-fill";
  fill.style.width = row.barStyle.width;
  fill.dataset.ui = "任务列表.task.bar";
  const bar = document.createElement("span");
  bar.className = "bar";
  bar.append(fill);
  const count = document.createElement("span");
  count.className = "task-count";
  count.textContent = row.count;
  count.dataset.ui = "任务列表.task.count";
  const progress = document.createElement("span");
  progress.className = "task-progress";
  progress.append(bar, count);

  button.append(lamp, meta, title, progress);
  return button;
}

export function render(host, data = {}, api = undefined) {
  const root = document.createElement("nav");
  root.dataset.screen = "tasks";
  root.dataset.ui = "任务列表.root";
  root.className = "tasks board";
  root.setAttribute("aria-label", "The Night");

  const paint = (selectedTask) => {
    const next = rowsFor(data, selectedTask);
    const eyebrow = document.createElement("div");
    eyebrow.className = "eyebrow spread";
    eyebrow.dataset.ui = "任务列表.eyebrow";
    const label = document.createElement("span");
    label.textContent = "The Night";
    label.dataset.ui = "任务列表.eyebrow.label";
    const count = document.createElement("span");
    count.textContent = String(next.count);
    count.dataset.ui = "任务列表.eyebrow.count";
    eyebrow.append(label, count);
    const kids = [eyebrow];
    if (next.empty) {
      const empty = document.createElement("p");
      empty.className = "empty inline empty-text";
      empty.textContent = "没有带 mmw:map label 的 ticket。";
      empty.dataset.ui = "任务列表.empty";
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
