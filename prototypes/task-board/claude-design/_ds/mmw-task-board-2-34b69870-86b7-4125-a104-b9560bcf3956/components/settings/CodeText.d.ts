/** A command or file name inside the sheet's prose. */
export interface CodeTextProps {
  children?: any;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function CodeText(props: CodeTextProps): JSX.Element;
