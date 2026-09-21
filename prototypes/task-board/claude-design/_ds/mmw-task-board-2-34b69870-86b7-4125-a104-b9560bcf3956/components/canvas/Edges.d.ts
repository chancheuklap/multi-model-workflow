/** Every line on the canvas, drawn from the product's layout. */
export interface EdgesProps {
  /** canvas.mjs canvasView `svg`. */
  svg: string;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function Edges(props: EdgesProps): JSX.Element;
