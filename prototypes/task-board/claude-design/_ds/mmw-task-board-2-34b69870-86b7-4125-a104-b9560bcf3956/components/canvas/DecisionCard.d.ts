/** A decision ticket of a map, lower than a ticket, with its kind instead of a step. */
export interface DecisionCardProps {
  /** One of canvas.mjs canvasView `decisions`. */
  item: {n: number; cls: string; pos: object; title: string; num: string; kind: string; lampCls: string};
  onPick?: () => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function DecisionCard(props: DecisionCardProps): JSX.Element;
