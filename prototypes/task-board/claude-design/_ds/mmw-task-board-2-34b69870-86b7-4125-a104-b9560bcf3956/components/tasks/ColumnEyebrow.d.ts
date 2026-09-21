/** The uppercase heading over the task list with its count. */
export interface ColumnEyebrowProps {
  label: string;
  count: number | string;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function ColumnEyebrow(props: ColumnEyebrowProps): JSX.Element;
