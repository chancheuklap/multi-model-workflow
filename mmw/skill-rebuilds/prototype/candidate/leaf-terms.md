# delivery-workflow.md terms this round changes

Publish `/mmw-prototype` English candidate, then change these entries in `docs/context/delivery-workflow.md`. Do not patch the live leaf until then.

**prototype** (keep meaning, English skill says throwaway for how it is written):
A running asset that answers a question talk cannot settle, before real code lands. The first cut can be rough. Later rounds edit the same prototype until a walkthrough answers the current question. Throwaway is how it is written. The files stay in the repo.
_Avoid_: MVP, static mock, disposable one-off, promoting the shell to production

**prototype 资产** (update):
The walkthrough-backed running prototype, variants, the README question and walkthrough conclusions, the chosen artifacts, and files kept as long-lived evidence. Path from `mmw artifact path prototype`. Downstream names `README.md` and reads the files it lists.
_Avoid_: process screenshots, DOM, console, recordings, scratch, promoting unfinished work onto production routes, conclusions without the running files

**prototype 索引**:
`README.md` in that directory. It records the question, how to run, walkthrough conclusions, chosen artifacts, rejected constraints, and long-lived evidence. It is not the running prototype.
_Avoid_: 资产索引, capture.md, 五项交接

Leave **走查** as the leaf name until that rename ships with grilling. This skill uses **walkthrough** for the same act: the user operates the prototype and accepts, rejects, or asks for a change.
