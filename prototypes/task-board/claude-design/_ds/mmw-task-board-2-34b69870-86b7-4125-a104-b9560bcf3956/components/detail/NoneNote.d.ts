/** The line an empty list shows. */
export interface NoneNoteProps {
  ticket?: boolean;
  text: string;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function NoneNote(props: NoneNoteProps): JSX.Element;
