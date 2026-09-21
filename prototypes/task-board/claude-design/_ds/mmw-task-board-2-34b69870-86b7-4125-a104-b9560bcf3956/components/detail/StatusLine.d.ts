/** The lamp, its word, the step (tickets) and the elapsed time or landed count. */
export interface StatusLineProps {
  ticket?: boolean;
  lamp: string;
  statusWord: string;
  phase?: string;
  elapsed?: string;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function StatusLine(props: StatusLineProps): JSX.Element;
