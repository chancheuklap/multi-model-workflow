/** One related issue. A blocker still holding reads "held"; a row the tree cannot read does not link. */
export interface RelationRowProps {
  /** On a ticket: blockers and blocked; otherwise a spec's or map's list row. */
  ticket?: boolean;
  row: {n: number; num: string; title: string; where?: string; lamp: string; state?: string; phase?: string; hold?: boolean; unknown?: boolean};
  onGoto?: (n: number) => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function RelationRow(props: RelationRowProps): JSX.Element;
