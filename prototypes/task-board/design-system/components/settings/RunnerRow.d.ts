/** Which runner starts sessions. */
export interface RunnerRowProps {
  cls: string;
  value: string;
  disabled?: boolean;
  opts: {value: string; text: string; disabled?: boolean}[];
  bads?: {text: string}[];
  onChange?: (value: string) => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function RunnerRow(props: RunnerRowProps): JSX.Element;
