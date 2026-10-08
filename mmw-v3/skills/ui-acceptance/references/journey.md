# Journey

Whether one end-to-end path still works against the real product is
`scripts/journey.py`.

A journey is the only oracle in this skill that starts the whole product. There are few
of them on purpose: the owner names which paths are worth one, and the default three are
money, sign-in, and one submit chain.

Two agents come here. The one **writing** the journey script or the fault-injection switch needs
**What the script gets, and what it must be** and **The fault-injection switch**. The one
**reading** a line it printed needs the last two sections.

## What the script gets, and what it must be

A journey's name is `<product>/<flow>`. Its directory is
`.mmw/<product>/journeys/<flow>/`, with an executable `run`, or a `package.json`
declaring `scripts.run`. A repository with one product uses the same name. The script
runs with that directory as its working directory, and with:

- **every key `discover` printed**, uppercased. `origin` arrives as `ORIGIN`. A key
  from a product this one needs arrives as `<PRODUCT>_<KEY>`, both parts uppercased,
  and a hyphen in the product name is an underscore. For example, a product named
  `notes-app` that prints `origin` arrives as `NOTES_APP_ORIGIN`. Read addresses from
  there. Ports come from this product's segment of the lease.
- **the lease variables.** `MMW_PORT_BASE` and `MMW_PORT_COUNT` are this product's
  segment. `MMW_DATA_DIR` is `<instance directory>/<product>`. `MMW_PRODUCT` is the
  product name. `MMW_INSTANCE`, `MMW_SLOT` and `MMW_AUTOMATION` are the same for every
  product in the run.
- **`MMW_EVIDENCE_DIR`**, an empty directory,
  `.scratch/journeys/<product>/<flow>/` under the worktree. The `--break` second pass
  uses `.scratch/journeys/<product>/<flow>/break/` and leaves the first pass's files
  where they are.

The script never receives `MMW_BREAK`. Drive the page with Playwright's own API. Exit 0
for a pass, non-zero for a failure, and make the last line of the output the first line
of the error — that line is what the oracle quotes after `at`. On failure, before the
process exits, write four files into `MMW_EVIDENCE_DIR`: `screenshot.png` (the page at
the moment of failure), `trace.zip` (the Playwright trace), `console.txt` (browser
console errors) and `requests.txt` (each response with status 400 or above, and each
request that failed).

**End by reading the result back from another page.** A journey that clicks Submit and
accepts a success message or redirect has proved only that the click handler ran. Go to
the page that owns the saved result and assert the value there, so breaking the write or
read operation makes the second pass fail for the reason the user path would fail.

At the end, `stop` runs for every product this run started, in reverse order, and every
port of each product's segment must be quiet. **The negative control** names the line a
port that still answers produces.

**A journey script starts nothing itself.** For a desktop application, `start` launches
the application with `--remote-debugging-port` set to one port of this product's segment
and `--user-data-dir` set to a directory under `MMW_DATA_DIR`. `start` also moves every
other place the product writes state under `MMW_DATA_DIR`. That includes the database,
the runtime directory, logs and temporary files. The user-data directory alone leaves
two instances sharing the database and the logs. The renderer dev server's port is also
taken from this product's segment. The product does not search for a free port of its
own. When the command line does not pass a debug port or a backend port, the product
does not choose a fixed one. A fixed port sits outside the lease, so the quiet-port
check at the end cannot see it. `discover` prints `cdp`, the debugging address. The
journey connects to it with Playwright's `connectOverCDP`, as `references/control-ui.md`
describes.

A native dialog, such as a file picker or a permission prompt, is not reachable through
the debugging port. Activation that needs a person in a browser is the same kind of
step. The product supplies a stand-in for each, and the stand-in runs only when
`MMW_AUTOMATION` is `1`. Its name is registered in `harness_markers`. A step that still
needs a person to click is reported blocked, under rule 3 of **Five rules while the
product is running**.

**A command-line product** is driven as `references/control-cli.md` describes. The tmux
session name contains `MMW_INSTANCE`. `start` opens the session and `stop` closes it.
`stories` is `"none"`, because the product has no pages, and the story oracle refuses
it. The journey runs the product's `doctor` before the script and again after a
failure, as it does for any other product.

## The fault-injection switch

The product's fault-injection switch matches the method and route the criterion's `--break` names, fails only that operation, and affects only the product process: this deliberate, controlled failure is fault injection, proving the journey notices when the operation it depends on breaks. On the second start, and only then, `journey.py` puts the exact value in `MMW_BREAK` for `start`. When the switch is active, `start` prints the exact line `BREAK ARMED <METHOD> <route>`. A non-zero second `start`, or a successful one without that line, is a refusal: the script does not run and the message points back to this reference. The switch lives in the product because only the product's own routing reaches every path its frontend takes; a forwarding proxy in front of it misses a frontend that calls its backend by another address.

The value `--break` names is one HTTP route of the product backend, written `<METHOD> /route`. A desktop application whose backend serves HTTP routes uses that route. A product with no HTTP route has no critical flow that passes `--break`. The spec that names its critical flows says why, in Testing Decisions.

## The negative control

With `--break`, the second pass starts the product again with the named operation
failing and runs the same script. `MMW_BREAK` is absent on that pass too. The evidence
directory ends in `break/`, and the script does not branch on that path; **that pass
has to fail**, or the journey did not prove the operation matters to the result it
asserted. Without `--break`, the smoke journey's second pass runs with the product
stopped and every discovered address pointing at a closed port.

After either control, `stop` runs again for every product this run started, in reverse
order, and every port of each product's segment must be quiet.
Whatever still answers is named with its port and pid on a
`JOURNEY LEFT THE PRODUCT UP` line. A helper that starts the stack when it finds nothing
answering defeats the negative control: it brings the whole stack back during the
control and leaves the next run blocked.

## Exit codes

On `JOURNEY FAILED`, the oracle prints the script's stdout and stderr first, with color
codes removed, then `JOURNEY FAILED <name> at <last non-empty line>`. The next line is
`MMW_DATA_DIR` and this run's data directory. After that, one line per file in this
run's evidence directory, or one line naming that directory and pointing back to this
reference when the script left it empty. What to fix is what the script printed.

A `start` or `discover` that fails prints one line naming the command, its command
string and its exit code, then that command's own output, or `(no output)` when the
command itself printed nothing, then a line naming `MMW_DATA_DIR`. The run exits 2.

The `--break` second pass prints the script's output only when that pass exits 0.
