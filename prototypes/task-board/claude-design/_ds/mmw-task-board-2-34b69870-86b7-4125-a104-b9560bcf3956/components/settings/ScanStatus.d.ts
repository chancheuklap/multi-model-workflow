/** When the hosts were last asked, and a rescan; a spinner while asking. */
export interface ScanStatusProps {
  scanning?: boolean;
  scanningText?: string;
  scannedText?: string;
  onRescan?: () => void;
  /** Its id, set on the root; each part carries `<data-ui>.<part>`. */
  "data-ui"?: string;
}
export declare function ScanStatus(props: ScanStatusProps): JSX.Element;
