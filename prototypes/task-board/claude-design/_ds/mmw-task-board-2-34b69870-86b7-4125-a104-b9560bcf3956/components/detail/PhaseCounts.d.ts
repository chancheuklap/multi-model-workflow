/** How many tickets sit at each step. */
export interface PhaseCountsProps {
  phases: {phase: string; label: string}[];
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function PhaseCounts(props: PhaseCountsProps): JSX.Element;
