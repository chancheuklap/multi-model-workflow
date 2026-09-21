/** Where a ticket runs, or the line saying it has not run. */
export interface RunBoxProps {
  runtime: {grade: string; model: string; rows: {k: string; v: string}[]} | null;
  noRunText?: string;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function RunBox(props: RunBoxProps): JSX.Element;
