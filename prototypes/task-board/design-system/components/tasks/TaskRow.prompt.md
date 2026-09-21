One task in the left column. Pass a row of the product's taskListView as is.

```jsx
<TaskRow row={row} onPick={() => pick(row.n)} data-ui="任务列表.task" />
```

It renders the product's own markup and classes; pass the product's view data as is.
