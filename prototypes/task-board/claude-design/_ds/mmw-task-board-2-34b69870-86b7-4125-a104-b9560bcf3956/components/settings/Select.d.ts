/** A dropdown of the sheet; its class says changed or refused. */
export interface SelectProps {
  cls: string;
  value?: string;
  disabled?: boolean;
  label: string;
  opts: {value: string; text: string; disabled?: boolean}[];
  onChange?: (value: string) => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function Select(props: SelectProps): JSX.Element;
