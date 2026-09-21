import {render as renderProduct, taskListView} from "/product/tasks.mjs";

export function render(host, data, api) {
  const transitions = [];
  window.storyTransitions = () => structuredClone(transitions);

  const selectedTask = data.select?.task ?? null;
  const root = renderProduct(host, {
    view: taskListView(data.payload?.tasks || [], selectedTask),
    selectedTask,
    onSelectTask(task) {
      transitions.push({scene: "Component · 任务列表.morning", data: {task}});
    },
  }, api);
  root.dataset.storyRoot = "";
  root.style.cssText = "width:236px;height:848px";
}
