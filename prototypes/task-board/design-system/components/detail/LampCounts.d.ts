/** How many tickets sit under each lamp. */
export interface LampCountsProps {
  lamps: {lamp: string; word: string; n: number | string}[];
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function LampCounts(props: LampCountsProps): JSX.Element;
