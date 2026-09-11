# Task board

The local browser surface over a night: one small HTTP server per registered consuming repository, reading that repository's ticket state from GitHub and reading or writing this machine's agent configuration. It exists so a person can watch a night and change which host, model and effort each role runs on without a command line, and it fixes only the words the server and its registry invent — the command that opens it, `dispatch.sh board`, is defined in the dispatch-and-the-night context.

How to read an entry: the bold line is the term's only name; a term whose name is a literal string that appears in a file, a command, or a comment is named by that string exactly (case, colon, and all). The definition says what the thing is and what sets it apart from its neighbours. `_Admitted_` lists the one other wording that may appear in prose. `_Avoid_` lists dead words: a sentence in this repository that uses one is wrong; an item followed by a note in parentheses says in which sense the word is dead. `_Home_` is the file whose text or code the definition is taken from; when this file and that one disagree, that one is right and this file is rewritten. An attribute that can be had by reading that file — a field list, an exit code, a command's switches, the branches of a behaviour — is not repeated here: an entry says what the term is and how it differs from its neighbours, and points at `_Home_` for the rest.

## Language

### The board and what keeps it running

**task board**:
The local browser interface for reading a spec's ticket state and editing this machine's dispatch configuration. `server.py` serves it on `127.0.0.1` at the port `boards.json` assigned, with the repository as its working directory; one server runs per registered consuming repository, and `supervisor.py` keeps them running. It reads ticket state from GitHub through the `gh` list reader and reads or writes `MMW_HOME/models.json`; it does not become a second store for either. A model change uses the same validation and write operation as `models.py config`, version and all, so a configuration changed from a command line while the page was open is refused rather than overwritten.
_Avoid_: board (for an agent), dashboard
_Home_: `mmw-v2/board/server.py`

**`boards.json`**:
The machine-level task board registry at `MMW_HOME/boards.json`, defaulting to `~/.mmw/boards.json` and written `0600`. It is a JSON object from each consuming repository's absolute main-checkout path to that repository's fixed local port; it owns no ticket or model state. A repository registering for the first time takes the lowest port from 47100 upward that is neither already in the registry nor already answering, under a lock on `boards.json.lock`; a repository already in the registry keeps the port it has.
_Home_: `~/.mmw/boards.json`

**`supervisor.py`**:
`mmw-v2/board/supervisor.py`, the process kept alive by the `com.mmw.board` LaunchAgent. It reads `boards.json`, starts `server.py` in every registered main checkout on the assigned port, restarts an exited server, and reports a missing checkout once — `skipping missing repository <path>` — without preventing the other registered servers from running and without repeating itself until that directory comes back. Run against one checkout instead of as the loop, it registers that repository's port, or ensures its board is up and answering.
_Home_: `mmw-v2/board/supervisor.py`

**page token**:
The secret `server.py` mints afresh at every start. It is substituted for the literal `__MMW_PAGE_TOKEN__` when `index.html` is served, and the page reads it back out of `<meta name="mmw-page-token">` and sends it as the `X-MMW-Token` header on every non-`GET` request. `gates.py` refuses any such request whose `Host`, `Origin` and `X-MMW-Token` do not all match this process's own address and this start's token, so a write from another origin, from a stale page, or from a bare `curl` gets `403`. Because it is new per start, the meta tag is also the evidence that the board answering is the one this run started.
_Avoid_: CSRF token, session token, API key
_Home_: `mmw-v2/board/server.py`
