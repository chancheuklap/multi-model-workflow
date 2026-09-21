/** What each line and mark on the canvas means. Top right of the canvas. */
export interface LegendProps {
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function Legend(props: LegendProps): JSX.Element;
