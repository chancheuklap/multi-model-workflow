/** A square icon button at the right end of the top bar: read GitHub now, or open the settings sheet (`on` while it is open). */
export interface IconButtonProps {
  icon: "refresh" | "settings";
  on?: boolean;
  label: string;
  title?: string;
  onClick?: () => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function IconButton(props: IconButtonProps): JSX.Element;
