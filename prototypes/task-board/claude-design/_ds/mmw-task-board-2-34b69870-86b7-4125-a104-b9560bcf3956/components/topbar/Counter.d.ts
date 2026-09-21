/** One lamp count in the top bar. The needs-you counter is a button that jumps to the next orange ticket; the others are plain. */
export interface CounterProps {
  lamp: "orange" | "green" | "ink" | "hollow";
  label: string;
  count: number | string;
  sub?: string;
  /** The needs-you counter: a button, enabled while `hot`. */
  button?: boolean;
  hot?: boolean;
  title?: string;
  onClick?: () => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function Counter(props: CounterProps): JSX.Element;
