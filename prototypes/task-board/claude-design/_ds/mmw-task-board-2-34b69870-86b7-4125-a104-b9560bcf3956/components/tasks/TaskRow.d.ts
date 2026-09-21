/** One task in the left column. Pass a row of the product's taskListView as is. */
export interface TaskRowProps {
  /** A row of tasks.mjs taskListView: cls, lampCls, lampWord, meta, title, titleCls, barStyle, count. */
  row: {cls: string; lampCls: string; lampWord: string; meta: string; title: string; titleCls: string; barStyle: {width: string}; count: string};
  onPick?: () => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function TaskRow(props: TaskRowProps): JSX.Element;
