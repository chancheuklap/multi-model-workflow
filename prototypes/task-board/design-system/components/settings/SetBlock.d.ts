/** One block of the sheet's body. */
export interface SetBlockProps {
  ruled?: boolean;
  title?: string;
  aside?: any;
  children?: any;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function SetBlock(props: SetBlockProps): JSX.Element;
