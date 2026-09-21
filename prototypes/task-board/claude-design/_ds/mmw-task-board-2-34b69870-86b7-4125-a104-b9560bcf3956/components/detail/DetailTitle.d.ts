/** The title of what the detail column shows. */
export interface DetailTitleProps {
  ticket?: boolean;
  title: string;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function DetailTitle(props: DetailTitleProps): JSX.Element;
