/** The shown issue's number and links to its spec and map. */
export interface OriginProps {
  ticket?: boolean;
  num: string;
  links?: {label: string; n: number}[];
  onGoto?: (n: number) => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function Origin(props: OriginProps): JSX.Element;
