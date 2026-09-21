/** One host and what this machine said about it. */
export interface HostChipProps {
  chip: {cls: string; host: string; what: string};
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function HostChip(props: HostChipProps): JSX.Element;
