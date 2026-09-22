import {render as renderProduct, taskRowView} from "/product/tasks.mjs";

// The scene input is the design page's own example data (`TASK_SCENES.<scene>`):
// one entry per task with the lamp and landed count the page draws, so the
// product's rows are built from the same values the design shows.
function view(tasks) {
  return {
    count: tasks.length,
    empty: !tasks.length,
    rows: tasks.map(taskRowView),
  };
}

export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);

  const selectedTask = data.selected ?? null;
  const root = renderProduct(host, {
    view: view(data.rows || []),
    selectedTask,
    onSelectTask(task) {
      transitions.push({scene: "Component · 任务列表.morning", data: {task}});
    },
  }, api);
  root.dataset.storyRoot = "";
  root.style.cssText = "width:236px;height:848px";
}
