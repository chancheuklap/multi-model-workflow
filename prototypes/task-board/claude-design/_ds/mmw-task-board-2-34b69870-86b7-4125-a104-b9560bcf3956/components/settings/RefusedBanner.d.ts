/** A save refused because the configuration changed elsewhere. */
export interface RefusedBannerProps {
  text: string;
  onReread?: () => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function RefusedBanner(props: RefusedBannerProps): JSX.Element;
