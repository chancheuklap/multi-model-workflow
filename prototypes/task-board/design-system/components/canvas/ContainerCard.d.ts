/** A map or spec on the canvas trunk, with its landed count, expand chevron and progress bar. */
export interface ContainerCardProps {
  /** One of canvas.mjs canvasView `containers`. */
  item: {n: number; cls: string; pos: object; title: string; num: string; titleCls: string; lampCls: string; lampWord: string; count: string; canExpand: boolean; chev: string; toggleLabel: string; barStyle: {width: string}};
  onPick?: () => void;
  onToggle?: (n: number) => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function ContainerCard(props: ContainerCardProps): JSX.Element;
