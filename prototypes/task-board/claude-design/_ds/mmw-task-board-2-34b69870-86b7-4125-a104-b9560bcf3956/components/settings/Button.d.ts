/** A button of the sheet: plain, primary, or a text link. */
export interface ButtonProps {
  kind?: "primary" | "link";
  disabled?: boolean;
  onClick?: () => void;
  children?: any;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function Button(props: ButtonProps): JSX.Element;
