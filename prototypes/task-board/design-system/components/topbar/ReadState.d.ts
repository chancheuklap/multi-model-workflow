/** When the page last read GitHub, or, hatched, that the last read failed and which data is shown. */
export interface ReadStateProps {
  failed?: boolean;
  text: string;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function ReadState(props: ReadStateProps): JSX.Element;
