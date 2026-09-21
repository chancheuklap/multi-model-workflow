/** Zoom out, the level, zoom in and fit, bottom right of the canvas. */
export interface ZoomBarProps {
  level: string;
  onOut?: () => void;
  onIn?: () => void;
  onFit?: () => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function ZoomBar(props: ZoomBarProps): JSX.Element;
