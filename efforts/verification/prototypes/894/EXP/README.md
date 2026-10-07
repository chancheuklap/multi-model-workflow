# Experiment: driving parrot under an MMW lease (spec #894 §1)

agentflow branch `exp/894-parrot-driving` (local only, not pushed), worktree
`/Users/cheuklapchan/agentflow/.worktrees/exp-894-parrot`. Harness code is in commits
`4b28b5526` (`.mmw/parrot/`, parrot port patch), `35de19c09` (doctor fix) and
`f91f5a03a` (Gateway harness made to start again); the head of the branch is `f91f5a03a`.

Each observation is labelled **[measured]** (seen in a run on 2026-10-08) or
**[code]** (read from the code at agentflow `dev` 278202229).

## 1. Question and bar

Three of spec #894's assumptions are checked here before tickets are cut:

- (a) Does parrot need a Gateway while it runs, and what for? Is it true that with no address set, parrot falls back to the production Gateway `https://capyapi.cn`?
- (b) What are hedgehog's backend port and debug port, and are they hard-coded?
- (c) Can two parrot Electron instances run at once without interfering through ports, user data, the single-instance lock or shared files?
- How many ports does each product really need (the spec assumes Gateway 7, parrot 2, hedgehog 2)?
- Could a `--break "<METHOD> /route"` fault switch target parrot's backend?

The bar for "yes":

- Two leased runs each start a Gateway and then parrot, all on their own ports.
- The same screen is operated in both over `connectOverCDP`.
- Both are screenshotted and stopped.
- Every port goes quiet, the evidence is still there afterwards, and the owner's own parrot data is never touched.
- No connection leaves loopback.

## 2. How to run

From the worktree, with the installed lease script `L=~/.agents/skills/ui-acceptance/scripts/lease.py`:

```
cd /Users/cheuklapchan/agentflow/.worktrees/exp-894-parrot
(cd desktop-parrot && pnpm install --frozen-lockfile --prefer-offline)
python3 $L run . -- uv run python .mmw/parrot/harness/parrot.py start        # Gateway, then parrot
python3 $L run . -- uv run python .mmw/parrot/harness/parrot.py doctor
node .mmw/parrot/drive/settings.mjs <cdp> <renderer> <evidence-dir>          # values from `discover`
python3 $L run . -- uv run python .mmw/parrot/harness/parrot.py stop         # parrot, then Gateway
python3 $L release .
```

- `start --no-gateway` starts parrot with its Gateway address pointing at a quiet port inside the lease.
- The second instance was a detached worktree at the same commit, `git worktree add --detach .worktrees/exp-894-parrot-b exp/894-parrot-driving`, with the same commands. It has since been removed, together with its lease instance.
- There is no evidence page: two screenshots and one `drive.json` per instance are easier to read directly. They were kept in the experiment session's scratch directory and are not committed; the owner saw one of them in the report of 2026-10-08.

## 3. Legend

There is no evidence page, so there are no markers. In `drive.json`:

- `requests` lists every request the renderer made while the screen was operated.
- `status` is the text of the title-bar status pill.

## 4. Rounds

### Round 2, 2026-10-08: two leased runs at once, each with its own Gateway

**What changed since round 1.** The Gateway harness on agentflow `dev` could not start (first item below), so commit `f91f5a03a` patched it on the temp branch:

- placeholder GlitchTip variables;
- an empty `error-pipeline.env`;
- `up` of the four services only (postgres, pgbouncer, redis, gateway).

**Observations.**

- **[measured] The Gateway harness on `dev` is broken.**
  - `start` fails at `docker compose config` with `required variable LOCAL_PROD_GLITCHTIP_DB_PASSWORD is missing a value`.
  - The cause: `docker/compose.local-prod.yml` gained GlitchTip in dc15a8d0a (2026-10-01), and `.mmw/harness/target.py` never learned about it.
  - Today every agentflow journey fails at `start`.
- **[measured] Both instances started under their own leases.**
  - Slot 0 is ports 21000–21019, slot 1 is 21020–21039. Each segment was laid out as: Gateway at offset +3 (postgres +4, pgbouncer +5, redis +6), parrot backend +7, CDP +8, Vite renderer dev server +9.
  - Time to ready: 2 min 15 s for A and 1 min 45 s for B. The Docker image build and the account seeding take most of it.
  - `doctor` passed on both. Every listener belonged to that instance's own process group, and the version was the source commit.
- **[measured] Ports.**
  - 8796, 9226, 5173 and 8788 never listened.
  - The `--remoteDebuggingPort` that `electron-vite dev` passed in suppressed the hard-coded 9226.
- **[measured] Operating both at once.**
  - The two drives ran in parallel: Settings tab, then two screenshots.
  - A's renderer requested only `127.0.0.1:21007` and B's only `127.0.0.1:21027`, each time on `/api/activation/status`, `/health` and `/api/config/defaults`.
  - Both show 未激活 / source-run (not activated, source run).
- **[measured] No interference.**
  - Each user-data directory holds its own `SingletonLock`, and both apps stayed alive.
  - Each backend logged its own `app.db` under its own lease directory.
  - The owner's `~/.local/share/parrot_dubbing/app.db` mtime did not change.
  - `lsof` on both process groups showed loopback connections only.
- **[measured] Stopping.**
  - B was stopped, then A, each parrot before its Gateway. Each stop took about 2 s.
  - The quit was graceful: Electron logged `before_quit`, then the backend was terminated with `killed:false`.
  - All 40 ports went quiet, no `exp-894` process or container was left, and both `release` calls returned `released: true`.
- **[measured] Evidence.** The screenshots in `$MMW_DATA_DIR/parrot/evidence` survived stop and release. `lease.py remove-instance` deletes them once the worktree is gone, so evidence has to be copied out before cleanup.
- **[measured] Leftovers.**
  - `stop` (`compose down` without `-v`) leaves two named volumes and a 2.9 GB `mmw-<instance>-gateway` image per instance. I removed mine by hand.
  - `lease.py list` reports Docker-published ports as held by colima's `ssh … [mux]` process, with an unrelated cwd. A refusal that names "product, port, pid" will name colima for a Gateway port.

### Round 1, 2026-10-08: one parrot, no Gateway listening

- **[measured]** Parrot started in 32 s with `PARROT_GATEWAY_BASE_URL` pointing at a quiet leased port.
  - The Settings screen works; the status pill reads 需要激活 (activation needed).
  - The backend logs `runtime_policy_missing_minimal_mode`.
  - `GET /api/config/defaults` returns 503 `runtime_policy_missing`, so the defaults shown are the renderer's own.
  - Nothing tried to reach the Gateway: an unactivated backend makes no Gateway call at startup.
- **[measured]** `PARROT_DUBBING_RUNTIME_ROOT` alone does not move the database. Only `PARROT_DUBBING_DB_PATH` does [code: `src/parrot_dubbing/app.py` `_lifespan` uses `get_default_db_path()`, which ignores `RUNTIME_ROOT`]. Without it, a run writes into the owner's `~/.local/share/parrot_dubbing/app.db`.

## 5. Conclusion

**Yes against the bar, but only after three changes:**

- the parrot patch (backend port read from the environment in 3 main-process files and 5 renderer files, and a fixed Vite port);
- seven state variables set by `start`;
- a repaired Gateway harness.

**(a) Gateway dependency.**

- [measured] Parrot starts and its unactivated screens work with no Gateway at all.
- [code] Everything past the activation screen needs the Gateway:
  - activation and the browser authorization;
  - the runtime policy (default parameters, render concurrency, background tasks);
  - the provider credentials Gateway hands out for speech recognition, translation and TTS;
  - billing holds, the wallet balance, error and diagnostic upload, and tamper reports.
- [code] The production fallback is real and sits in three places: `app.py`, `client_security.py` and `api/activation_routes.py`. All three read `PARROT_GATEWAY_BASE_URL`, then `GATEWAY_URL`, then `https://capyapi.cn`.
- So the rule in spec §3, "no start without the dependency's address", is right as a safety rule. It is not a liveness rule.
- Driving any real parrot feature needs an activated instance. Activation passes through a browser authorization, which is a human step under rule 3. An `MMW_AUTOMATION`-only activation seed would remove it; spec §6 names only native dialogs.

**(b) Hedgehog** [code]:

- The backend port is 8795. It is hard-coded in the main process (`index.ts`, `python-backend.ts`, `onboarding/desktop-activation.ts`) and in five renderer files. The Python side already reads `HEDGEHOG_PORT`.
- The CDP port is 9228, appended only when no `--remote-debugging-port` is given.
- The user-data directory is set by `HEDGEHOG_ELECTRON_USER_DATA_DIR`, and the database by `HEDGEHOG_DB_PATH`.
- Hedgehog also needs a Gateway: it reads `HEDGEHOG_GATEWAY_BASE_URL`, then `GATEWAY_URL`, then production.
- Its shape is the same as parrot's, so it was not run.

**(c) Interference.** With leased ports and every state root moved, two instances do not interfere [measured]. Without those steps they do:

- [code] With the shared default port 8796, a second instance's `clearStaleBackend` kills whatever answers `/live` with a `process_id`, which is the other instance's backend.
- [code] By default the database, logs and diagnostics are shared in `~/.local/share/parrot_dubbing`.
- [code] The single-instance lock follows the user-data directory.
- [code] Vite falls back silently from 5173 to the next free port, outside the lease.

**Port counts.**

| Product | Listening ports | Segment the spec should give it |
| --- | --- | --- |
| Gateway | 4 [measured] | 7, if the harness keeps its indices 3–6 |
| parrot, dev mode | 3 [measured]: backend, CDP, Vite renderer dev server | 3 |
| hedgehog, dev mode | 3 [code] | 3 |

A packaged build, or `electron-vite preview`, drops the Vite port. Total 7 + 3 + 3 = 13, which is within 20.

**`--break`** [code]: yes.

- Parrot's backend is FastAPI with 23 HTTP routes, plus a WebSocket at `/ws/batch/progress`. The renderer calls them directly, for example `GET /api/config/defaults` and `GET /api/activation/status`.
- Hedgehog's backend also has 23 routes.
- agentflow has no fault switch anywhere today, Gateway included.

**Contradictions with spec #894:**

- §1 and §3: parrot and hedgehog need 3 ports in dev mode, not 2.
- §3 `needs`: hedgehog needs the Gateway too, and its `start` must set `HEDGEHOG_GATEWAY_BASE_URL`.
- §6 and §9: the user-data directory is not enough isolation. `start` must also set:
  - `PARROT_DUBBING_DB_PATH` and `PARROT_DUBBING_RUNTIME_ROOT`;
  - the two log roots;
  - `RUNTIME_DIR`;
  - the renderer's backend port and the Vite port, both in addition to the backend port.
- §9: agentflow's `.gitignore` lets through only the root layout (`.mmw/*` plus four exceptions). New files under `.mmw/<product>/` are silently ignored until it is changed.
- §9: the agentflow migration also has to fix the GlitchTip-era Gateway harness first.

## 6. Reusable parts

- `.mmw/parrot/harness/parrot.py` in the agentflow worktree:
  - `SEGMENTS` (l. 40), `segment_env` (l. 56): the per-product port and data split of spec §3.
  - `checked_gateway_origin` (l. 131): refuses any Gateway address that is not loopback inside this lease. The real `start` should keep this.
  - The `env.update` block in `start` (l. 144) is the full list of parrot variables a `start` must set.
  - `DEAD_PROXY` (l. 44) is a belt-and-braces block on any non-loopback HTTP from the backend.
  - `doctor` (l. 222): pid, version and ports, with each listener's process group compared to the recorded one. It is read-only.
  - `stop` (l. 255): sends SIGTERM to the process group `start` created and nothing else, then stops the Gateway.
- `.mmw/parrot/drive/settings.mjs`: `connectOverCDP`, picks the page by renderer URL, records requests, takes screenshots, then disconnects without quitting Electron.
- `desktop-parrot/src/main/python-backend.ts:31`, `index.ts:53`, `onboarding/desktop-activation.ts:34`, five renderer `BACKEND_URL` constants, and `electron.vite.config.ts:30`. This is the shape of the agentflow ticket: one source for the port, read from the environment only under `MMW_AUTOMATION`, as §9 says.
- `.mmw/harness/target.py`, the `exp/894` lines (l. 510–517, 532, 725): the minimum repair for the Gateway harness.
