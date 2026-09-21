/** A sub-issue a ticket opened, with its kind. */
export interface SubIssueRowProps {
  kid: {num: string; title: string; kind: string; lamp: string; hot: boolean};
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function SubIssueRow(props: SubIssueRowProps): JSX.Element;
