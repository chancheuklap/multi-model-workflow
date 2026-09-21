/** What is wrong with a row, one hatched line each. */
export interface ProblemListProps {
  items: {text: string}[];
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function ProblemList(props: ProblemListProps): JSX.Element;
