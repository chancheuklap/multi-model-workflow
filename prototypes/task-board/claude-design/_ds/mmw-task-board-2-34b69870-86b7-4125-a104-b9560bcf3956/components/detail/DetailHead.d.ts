/** The first row of the detail column. */
export interface DetailHeadProps {
  /** A ticket: eyebrow, GitHub and close; otherwise eyebrow and close. */
  ticket?: boolean;
  eyebrow: string;
  onGithub?: () => void;
  onClose?: () => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function DetailHead(props: DetailHeadProps): JSX.Element;
