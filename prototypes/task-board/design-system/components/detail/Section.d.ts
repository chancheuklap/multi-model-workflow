/** A ruled block of the detail column with its title and count. */
export interface SectionProps {
  ticket?: boolean;
  title: string;
  note?: string | number | null;
  children?: any;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function Section(props: SectionProps): JSX.Element;
