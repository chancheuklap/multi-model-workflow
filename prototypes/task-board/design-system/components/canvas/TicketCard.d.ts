/** A ticket on the canvas: lamp, number, step, title and where it runs. */
export interface TicketCardProps {
  /** One of canvas.mjs canvasView `tickets`. */
  item: {n: number; cls: string; pos: object; title: string; num: string; phase: string; pillCls: string; lampCls: string; lampWord: string; run: string; runCls: string};
  onPick?: () => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function TicketCard(props: TicketCardProps): JSX.Element;
