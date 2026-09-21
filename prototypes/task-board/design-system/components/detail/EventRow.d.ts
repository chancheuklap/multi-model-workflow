/** One event: time, name, one line, and, opened, every payload field. */
export interface EventRowProps {
  item: {time: string; name: string; text: string; hasText: boolean; tone: string; detail: {k: string; v: string}[]};
  opened?: boolean;
  onToggle?: () => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function EventRow(props: EventRowProps): JSX.Element;
