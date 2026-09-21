/** The settings sheet over a dimmed page; its body is SetBlocks, its foot says what a save would change. */
export interface SheetProps {
  store: string;
  strong: string;
  quiet: string;
  hatch?: boolean;
  closeLabel: string;
  saveOff?: boolean;
  changed?: boolean;
  onClose?: () => void;
  onSave?: () => void;
  children?: any;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function Sheet(props: SheetProps): JSX.Element;
