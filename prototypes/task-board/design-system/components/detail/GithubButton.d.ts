/** Open the shown map, spec or decision ticket on GitHub; last in the column. */
export interface GithubButtonProps {
  label: string;
  onClick?: () => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function GithubButton(props: GithubButtonProps): JSX.Element;
