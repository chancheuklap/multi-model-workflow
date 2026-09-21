/** A quiet paragraph under a block of the sheet. */
export interface SetNoteProps {
  children?: any;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function SetNote(props: SetNoteProps): JSX.Element;
