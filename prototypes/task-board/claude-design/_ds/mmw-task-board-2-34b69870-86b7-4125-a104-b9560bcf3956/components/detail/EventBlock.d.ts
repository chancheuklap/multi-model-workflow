/** One step of a ticket's history; open, it holds an EventRow per event. */
export interface EventBlockProps {
  /** One of detail.mjs phaseBlocksFrom's blocks. */
  block: {phase: string; tone: string; summary: string; from: string; span: string};
  opened: boolean;
  onToggle?: () => void;
  children?: any;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function EventBlock(props: EventBlockProps): JSX.Element;
