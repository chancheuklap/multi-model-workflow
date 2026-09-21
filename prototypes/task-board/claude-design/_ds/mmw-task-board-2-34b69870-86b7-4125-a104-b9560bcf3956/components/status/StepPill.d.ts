/** The step a ticket is at, named in a coloured capsule. Use it on ticket cards, relation rows, event blocks and step counts. */
export interface StepPillProps {
  phase: "queued" | "working" | "waiting" | "review" | "verify" | "landed";
  big?: boolean;
  /** Replaces the step name, e.g. "working · 2". */
  children?: string;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function StepPill(props: StepPillProps): JSX.Element;
