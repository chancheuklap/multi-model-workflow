/** A caption over a band of cards, or the warning over a blocking cycle. */
export interface LaneLabelProps {
  label: {cls: string; pos: object; text: string};
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function LaneLabel(props: LaneLabelProps): JSX.Element;
