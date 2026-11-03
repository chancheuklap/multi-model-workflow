# Language

Names for the files that hold this repo's vocabulary. "Context" here is a glossary area. The agent's context window is a different word, from principle-guard-the-context-window, and is not this term.

Do not invent a Chinese name for a term in this file, or for any MMW skill. Use the English name.

## Language

**context**:
One area of this repo with its own `GLOSSARY.md`. The glossary map at the root lists the contexts.
_Avoid_: any invented Chinese name.

**glossary**:
The `GLOSSARY.md` for one context. An entry says what a term is. The file is not a spec, a scratch pad, or a store of implementation decisions.
_Avoid_: any invented Chinese name.

**glossary map**:
The root file `GLOSSARY-MAP.md`. It names each context, where that context's glossary lives, and how the contexts relate.
_Avoid_: any invented Chinese name.

**ADR**:
A record of one decision: what was decided, and why. This repo has none current. A new one is written only when the decision is hard to reverse, surprising without the record, and the result of a real trade-off.
_Avoid_: architectural decision record, and any invented Chinese name.

**skill**:
A named instruction file. Call it by the English `name` in its frontmatter. The cloud edition's names are listed in the skills glossary.
_Avoid_: any invented Chinese name.
