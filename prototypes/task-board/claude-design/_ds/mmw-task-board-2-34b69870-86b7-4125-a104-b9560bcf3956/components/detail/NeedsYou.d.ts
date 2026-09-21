/** Why the lamp is orange, one line per reason. Show it only when there is one. */
export interface NeedsYouProps {
  why: {head: string; body: string}[];
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function NeedsYou(props: NeedsYouProps): JSX.Element;
