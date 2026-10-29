# Host evidence for ticket #1446

Measured on 2026-10-29. This snapshot records the successful Codex candidate run and the external Claude failure. It does not assert that AC3 passed.

## Successful process checks

- `bash mmw-v4/tests/session-start/run.sh` printed `ran 8 skipped 0` and `all passed`.
- `bash mmw-v4/tests/install/run.sh` ran 15 tests and printed `OK` and `all passed`. Legacy files and rollback delegation use synthetic test repositories. No historical installer ran.

The first per-turn regression test failed because the old hook returned SessionStart for a UserPromptSubmit event. The first installer regression test failed because the old SessionStart registration retained its source whitelist.

## Codex live capture

Host version was `codex-cli 0.165.0`. The installed `codex app-server` CLI used a temporary CODEX_HOME, a private auth.json copy, installer-generated trusted hooks, a temporary MMW_HOME and a temporary notes repository. Capture wrappers forwarded native events to the candidate hook. No hook-trust bypass was used.

The model quoted the SessionStart pointer and the UserPromptSubmit reminder without tools. Four subsequent messages each captured UserPromptSubmit and a successful Stop with stop_hook_active=false. Resume captured source=resume. Manual compaction through thread/compact/start captured source=compact, and the model quoted the compact pointer on continuation. A malformed advisory-hook input returned a diagnostic and exit 0; the model still answered AVAILABLE.

The temporary definitions were a review packet containing a checked note and amber receipt with identifier cobalt-731, and a delivery window that is the owner's scheduled 17-minute delivery interval with identifier moss-482. A passed review packet waits for the delivery window.

### The owner-question sample

**Question.** What does a review packet contain? Answer in one short sentence.

> A review packet contains a checked note with its amber receipt, identified by cobalt-731.

Glossary reads recorded for this answer: 2.

**Question.** Give me a short implementation report for the review packet. The local check has passed and no release has happened.

> The review packet contains a checked note with its amber receipt, identified by cobalt-731. The local check passed, and it is ready for delivery; no release has occurred.

Glossary reads recorded for this answer: 0.

**Question.** For the delivery window, should delivery run as soon as a packet passes or wait for the window? Choose the option consistent with the project's definition and explain why.

> Wait for the delivery window: the owner’s scheduled 17-minute delivery interval, identified by moss-482. The project explicitly requires a passed review packet to wait for that interval before delivery.

Glossary reads recorded for this answer: 1.

**Question.** Explain the delivery window page in two sentences. Tell me what a review packet on that page means without asking me to look back at another answer.

> The delivery window is the owner’s scheduled 17-minute delivery interval, identified by moss-482, which a passed review packet must wait for before delivery. A review packet is a checked note with its amber receipt, identified by cobalt-731; it is ready for delivery but is not a release.

Glossary reads recorded for this answer: 0.

The sample used the glossary source names and both distinguishing definitions. No backward reference such as "see above" appeared. The implementation report reused the review packet definition without a file read. The delivery-window question read its definition after the topic changed. The page explanation reused both definitions without a file read. This sample does not establish permanent prose quality.

## Claude external environment FAILURE

Host version was `2.1.312 (Claude Code)`. In temporary hook/config/MMW directories, live inference returned the following response.

> API Error: 400 This organization has been disabled. An organization admin can appeal at https://console.anthropic.com/appeal

Reusing the existing keychain access token, including the existing account metadata, and reusing a private credential-file copy produced the same response. Authentication status reported logged in, which did not prove inference availability. No account repair or live-setting change was attempted. Claude startup delivery, successive-turn glossary use, resume, completion, reminder-failure availability and real compaction remain unproven. No Claude case is a passed or skipped pass.

## Coverage limits and rerun

The required two-host probe is `python3 mmw-v4/tests/session-start/verify_hosts.py`. Its default run records exact prompts, answers, glossary reads, native hook fields, hook outputs, old reply-check blocks and continuations in `.scratch/session-start-hosts/latest.json`. It prints HOST CHECK PASS only after both hosts meet every required case. Diagnostic single-host runs never print that token.

The old comparison replays the v4 hook code at 8cc6702d0b989477f70e1d7ba8487944d02fd30f with the same synthetic questions and author-approved principle text. The initial old-comparison assertion incorrectly expected the startup quotation to survive the old Stop rewrite. That assertion applies only to the new hook in the rerunnable probe. The full baseline comparison is not claimed by this snapshot.

SessionStart compact schemas and outputs for both host arguments are process fixtures. Only the Codex compact event described in this snapshot is a real capture. The native evidence uses the Codex app-server CLI and Claude print stream-json, not their terminal UIs. The orchestrator owns the separate fresh-agent walk and full all-tier gate.

The common additionalContext contracts were checked against [official OpenAI documentation](https://learn.chatgpt.com/docs/hooks) and [Claude Code hooks documentation](https://code.claude.com/docs/en/hooks). The probe uses no blocking hook decision.

The installed runtime, live hooks, installed checkout, production rollback behavior and five authoring-baseline files were left unchanged.
