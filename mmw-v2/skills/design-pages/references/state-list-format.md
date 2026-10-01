# State list format

Read this when you write a `## State list` or check one: a UI prototype records one for its winning variant, and an existing product gets one in `prototypes/<effort>/README.md` before it is redrawn. The `--state-list` of a pull finds the list by its heading and reports a file without that heading as not checked.

Under the fixed heading `## State list`, list every state of the winning variant: one third-level heading per region (the region name is the later `Component · <region>` page), and one list item per state, starting with the state name. `scene` prop values reuse these names; the pull report and any decision ticket that will change a page's states match against them. A UI has one state list. On a wayfinder map it is written in the design ticket's leaf `README.md`, gathering the winner of every UI prototype ticket on the map, one heading per region; each prototype ticket's own leaf `README.md` keeps its verdict and names the regions it settled.
