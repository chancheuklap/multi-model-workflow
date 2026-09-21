/** The status lamp: orange needs the owner, green is running, ink is done, hollow waits to be dispatched. Use it wherever a ticket, task, map or row is listed. */
export interface LampProps {
  tone?: "orange" | "green" | "ink" | "hollow" | "none";
  size?: "big" | "small";
  title?: string;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function Lamp(props: LampProps): JSX.Element;
