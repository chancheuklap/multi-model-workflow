# Interface parity

Whether an interface matches the design it was built from is `scripts/visual-parity.py`, next to this skill's `SKILL.md`. It renders each named scene from a handoff package directory offline, opens the same scene on the implementation, and compares the two by accessibility tree and by pixels at two viewports.

Two agents come here. The one **writing** the criterion needs the shape below. The one **reading** a `DIFF` line needs the last section.

## The handoff package directory

A Claude Design project downloaded as a handoff package, holding five things: the component's `.dc.html`, its `styles/`, its `data/`, `support.js`, and a `scenes.json` naming every scene. A directory missing any of them cannot be rendered. No scene name contains `/`: each one is served from a page at `/__parity-<name>.dc.html` that loads `./support.js`, and a slash puts that page in a subdirectory where `support.js` is not.

## What it presumes of the implementation

The handoff package side is pinned by this script. The implementation side is not: the script opens `<impl url>?<scene props>` and expects to find the interface already in that scene. Something in the product has to answer those parameters. That is a capability someone builds, in some ticket, and the spec's `## Testing Decisions` is where it is decided — what form it takes, and which builds carry it. A criterion written against a spec that never decided it names a state nothing can arrive at, and fails the first night it runs. When you reach that, do not compose a command anyway: stop, and take it back to the `to-spec` skill.

## The criterion, in one shape

Nobody types this command. It is written onto the ticket as a criterion, and a run of `verify-ticket.py` hands it to a shell months later with no model in between. So it carries a path written out in full:

```
CHECK: uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py --baseline <handoff package dir> --impl <url> --scenes <name,name> --max-pct 1
EXPECT: PARITY OK <passed>/<total>
```

**That path stays literal, and stays exactly this one.** Everywhere else an agent reaches a script in this skill by resolving it from the skill's own location, because an agent knows where its host put the skill. A shell does not. `~/.agents/skills` is the install location `mmw-v2/install.sh` creates unconditionally on every machine, for every host, which makes it the one path a ticket can name and still run a year later on another checkout. Writing the resolved absolute path of your own machine into a ticket breaks it for every other machine; writing a placeholder breaks it immediately.

An implementation that is not a page on a web server — a desktop application, say — is compared where it already runs: `--cdp <debugging port url>` names its debugging port, `--impl` still names the address to navigate to, and `--impl-title` picks the window when there is more than one. The application has to be running when the criterion runs, and is left running afterwards. What is compared is what its renderer draws, so the size of its operating-system window is not: a window minimum is the user's to check, not this script's.

## Reading what it printed

Three exit codes.

- **`0`**, one line `PARITY OK <passed>/<total>`: every scene matched at every viewport.
- **`1`**: one `DIFF` line per failing scene and viewport.
- **`2`** with `NEGATIVE CONTROL FAILED`: the run's own control — a render of the handoff package with an error inserted into it — was not caught, so nothing this run says about parity can be trusted, and no parity conclusion is printed at all.

A failure line reads `DIFF <scene> <viewport> <pct>% box=… — <reasons>`, and the reasons after the dash are where the failure is named. Only a difference in the accessibility tree brings lines out under it: `baseline`, `impl`, `only in baseline`, `only in impl`. A size difference, a pixel difference or a console error prints the `DIFF` line alone.

`--out <dir>` keeps the screenshots for the user to look at.
