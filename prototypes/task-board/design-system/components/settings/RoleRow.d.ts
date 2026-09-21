/** One agent's host, model and effort dropdowns and their problems. Pass a row of the product's settingsView. */
export interface RoleRowProps {
  row: any;
  onCell?: (agent: string, cell: "host" | "model" | "effort", value: string) => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function RoleRow(props: RoleRowProps): JSX.Element;
