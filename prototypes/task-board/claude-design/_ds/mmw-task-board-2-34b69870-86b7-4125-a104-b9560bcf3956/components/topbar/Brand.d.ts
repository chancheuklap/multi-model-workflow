/** The top bar's word mark and repository name. Use it once, at the left of the top bar. */
export interface BrandProps {
  repo: string;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function Brand(props: BrandProps): JSX.Element;
