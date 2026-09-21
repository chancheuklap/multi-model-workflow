/** What the detail column says when nothing is picked. */
export interface DetailEmptyProps {
  title: string;
  text: string;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function DetailEmpty(props: DetailEmptyProps): JSX.Element;
