# Gate format self-test

The gate format (`CHECK:` / `EXPECT:`, pass = exit 0 **and** marker in output) is a measuring instrument, and an instrument proves itself before it measures anything. Two gates below do that: one honest gate that fails when its outcome is absent, and one broken gate that reports success no matter what. `tests/run.sh` runs both and prints the verdicts; the expected verdicts are recorded here so a change to the format or the runner is caught.

## Honest gate (expected: FAIL in this repo)

```
- [ ] The repository has a file named MISSING-ON-PURPOSE.txt
  CHECK: test -f MISSING-ON-PURPOSE.txt && echo GATE_OK
  EXPECT: GATE_OK
```

The check observes the outcome directly (the file), exits nonzero when the file is absent, and prints the marker only after the assertion passed. The file does not exist, so the gate must fail: exit code 1, no marker. A gate that fails when its outcome is absent is a gate that can be trusted when it passes.

## Broken gate (expected: PASS, and that is the defect)

```
- [ ] The repository has a file named MISSING-ON-PURPOSE.txt
  CHECK: echo GATE_OK
  EXPECT: GATE_OK
```

Same criterion, same marker, same absent file — and the gate passes, because the command never looks at the file. Exit 0 and marker present satisfy the two conditions; the conditions were met by an emitter, not by an observation. This is the shape the authoring rule "observe the outcome directly" exists to forbid. Neither the double condition nor any lint can see through it: only the author, by asking whether the command can fail.

## Recorded run

`bash mmw-v2/skills/self-check/tests/run.sh` (2026-08-25):

```
honest gate: exit=1 marker=absent -> FAIL   (expected FAIL)
broken gate: exit=0 marker=present -> PASS  (expected PASS — and that is the defect the format cannot catch)
GATE-SELFTEST OK
```
