#!/usr/bin/env python3
"""Public retro command through temporary Git, fake gh comments and fake nmem."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MMW = HERE.parents[1]
SCRIPT = MMW / "skills" / "retro" / "scripts" / "retro.py"
EVENTS = MMW / "skills" / "verify-ticket" / "scripts" / "events.py"
spec = importlib.util.spec_from_file_location("retro_events", EVENTS)
events = importlib.util.module_from_spec(spec)
spec.loader.exec_module(events)
REPOSITORY = "sample/retro-test"
SPACE = "sample__retro-test"
CATEGORIES = ("Navigation", "Automated checks", "Coding standards", "Global AGENTS.md",
              "Tool economy", "No-ops", "Information access")
NAMES = {"complete-none": "RETRO-COMPLETE-NONE-OK",
         "default-caller-repo": "RETRO-DEFAULT-CALLER-REPO-OK",
         "partial-evidence": "RETRO-PARTIAL-EVIDENCE-OK",
         "proposal-threshold": "RETRO-PROPOSAL-THRESHOLD-OK",
         "prompt-and-record-contract": "RETRO-PROMPT-AND-RECORD-CONTRACT-OK",
         "retry-finalize": "RETRO-RETRY-FINALIZE-OK"}


def git(*args: str, cwd: Path) -> str:
    run = subprocess.run(["git", *args], cwd=cwd, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert run.returncode == 0, run.stderr
    return run.stdout.strip()


class Fixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mmw-retro-test-")
        self.root = Path(self.temp.name)
        self.checkout = self.root / "repo"
        self.origin = self.root / "origin.git"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for command, source in (("gh", "fake_gh.py"), ("nmem", "fake_nmem.py")):
            target = HERE / source
            target.chmod(0o755)
            (self.bin / command).symlink_to(target)
        self.gh_path = self.root / "gh.json"
        self.mem_path = self.root / "nmem.json"
        self.trace_path = self.root / "trace.jsonl"
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                        RETRO_GH_STATE=str(self.gh_path), RETRO_NMEM_STATE=str(self.mem_path),
                        RETRO_TRACE_PATH=str(self.trace_path), NMEM_SPACE=SPACE,
                        MMW_HOME=str(self.root / "mmw-home"))
        git("init", "--bare", str(self.origin), cwd=self.root)
        git("clone", str(self.origin), str(self.checkout), cwd=self.root)
        git("config", "user.email", "retro@test.invalid", cwd=self.checkout)
        git("config", "user.name", "Retro test", cwd=self.checkout)
        git("checkout", "-b", "project", cwd=self.checkout)
        (self.checkout / "README.md").write_text("project root\n", encoding="utf-8")
        git("add", "README.md", cwd=self.checkout)
        git("commit", "-m", "project base", cwd=self.checkout)
        self.base = git("rev-parse", "HEAD", cwd=self.checkout)
        git("push", "origin", "project", cwd=self.checkout)
        git("checkout", "-b", "spec-base", cwd=self.checkout)
        (self.checkout / "retro-target.md").write_text("## Context\nKeep line.\nChange this.\n", encoding="utf-8")
        git("add", "retro-target.md", cwd=self.checkout)
        git("commit", "-m", "land one retro target", cwd=self.checkout)
        self.landed = git("rev-parse", "HEAD", cwd=self.checkout)
        git("push", "origin", "spec-base", cwd=self.checkout)
        git("fetch", "origin", cwd=self.checkout)
        self.issues = {}
        self.next_id = 101
        self.add_issue(70, "Spec", "## Problem Statement\nNeed an evidence retro.\n\n"
                       "## User Stories\n- As owner I get a receipt.\n\n"
                       "## Out of Scope\nNo automatic behavior changes.\n", parent=None)
        self.add_issue(71, "Ticket", "Ticket work", parent={"number": 70})
        self.add_issue(60, "Earlier ticket", "Earlier work", parent={"number": 50})
        self.event(70, "spec.opened", "NIGHT OPENED", ticket=None,
                   into="spec-base", project="project")
        self.event(71, "ticket.checked", "same cause in check", ticket=71,
                   run="self", result="unmet", commit=self.landed)
        self.event(70, "spec.closed", "NIGHT SUMMARY", ticket=None,
                   memory_closing={"status": "complete", "total": 0, "returned": 0, "decisions": []})
        self.tree = {"number": 70, "title": "Spec", "state": "CLOSED",
                     "subIssuesSummary": {"total": 1, "completed": 1},
                     "subIssues": {"nodes": [{"number": 71, "title": "Ticket", "state": "CLOSED",
                                             "labels": {"nodes": [], "totalCount": 0},
                                             "blockedBy": {"nodes": [], "totalCount": 0},
                                             "subIssuesSummary": {"total": 0, "completed": 0},
                                             "subIssues": {"nodes": []}}]}}
        self.memories = {}
        self.save()

    def close(self):
        self.temp.cleanup()

    def add_issue(self, number: int, title: str, body: str, parent: dict | None):
        self.issues[str(number)] = {"title": title, "body": body, "parent": parent,
                                    "comments": [], "labels": []}

    def event(self, number: int, name: str, line: str, *, ticket: int | None, **fields) -> str:
        body = events.build(name, ticket=ticket, spec=70, line=line, **fields)
        ident = self.next_id
        self.next_id += 1
        url = f"https://github.com/{REPOSITORY}/issues/{number}#issuecomment-{ident}"
        self.issues[str(number)]["comments"].append({"id": ident, "body": body, "url": url})
        return url

    def save(self):
        self.gh_path.write_text(json.dumps({"repository": REPOSITORY, "issues": self.issues,
                                            "tree": self.tree, "proposals": [], "next_comment": 5000,
                                            "calls": []}), encoding="utf-8")
        self.mem_path.write_text(json.dumps({"memories": self.memories, "calls": []}), encoding="utf-8")

    def state(self, name: str) -> dict:
        return json.loads((self.gh_path if name == "gh" else self.mem_path).read_text(encoding="utf-8"))

    def update(self, name: str, **updates):
        value = self.state(name)
        value.update(updates)
        (self.gh_path if name == "gh" else self.mem_path).write_text(json.dumps(value), encoding="utf-8")

    def trace(self) -> list[dict]:
        return [json.loads(line) for line in self.trace_path.read_text(encoding="utf-8").splitlines()]

    def run(self, *args: str, ok: bool = True) -> dict | str:
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.checkout),
                                 "--repository", REPOSITORY, *args],
                                env=self.env, cwd=self.checkout, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if ok:
            assert result.returncode == 0, f"{args}: {result.stderr}\n{result.stdout}"
            return json.loads(result.stdout)
        assert result.returncode != 0, f"{args} unexpectedly passed"
        return result.stderr

    def run_default(self, *args: str) -> dict:
        result = subprocess.run([sys.executable, str(SCRIPT), *args], env=self.env,
                                cwd=self.checkout, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert result.returncode == 0, f"{args}: {result.stderr}\n{result.stdout}"
        return json.loads(result.stdout)

    def analysis(self, gathered: dict, problems: list[dict] | None = None) -> dict:
        problems = problems or []
        categories = {name: "none" for name in CATEGORIES}
        for problem in problems:
            categories[problem["category"]] = f"candidate: {problem['cause']}"
        return {"spec": 70, "task_root": gathered["task_root"],
                "evidence_checked": gathered["evidence_checked"],
                "previous_proposals": [], "categories": categories,
                "problems": problems,
                "intent_reconciliation": {"expected": "Receipt for the owner",
                                          "observed": "ticket event and landing commit",
                                          "gap": "aligned"},
                "review_learning": "none", "observed": gathered["observed"]}

    def finish(self, analysis: dict) -> dict:
        path = self.root / "analysis.json"
        path.write_text(json.dumps(analysis), encoding="utf-8")
        return self.run("finalize", "70", str(path))

    def assert_receipt(self, result: str):
        rows = self.state("gh")["issues"]["70"]["comments"]
        retro = [events.parse(row["body"])[1] for row in rows
                 if events.parse(row["body"])[0] == "event" and
                 events.parse(row["body"])[1].get("event") == "spec.retroed"]
        assert retro[-1]["result"] == result, retro
        assert events.fold(rows, issue=70)["spec_retroed"]["payload"] == retro[-1]
        return retro[-1]


def current_problem(f: Fixture, earlier: bool = True, prompt: bool = False) -> dict:
    current = f.issues["71"]["comments"][0]["url"]
    prior = f.event(60, "ticket.checked", "same cause in check", ticket=60,
                    run="self", result="unmet", commit=f.base) if earlier else None
    f.save()
    if earlier:
        f.update("nmem", memories={"prior-retro": {"id": "prior-retro", "space_id": SPACE,
                 "content": f"Spec: {REPOSITORY}#69\n## Problems observed\n"
                            f"### Automated checks: same cause\nEvidence: {prior}\n"}})
    body = "Owner approval requested; no behavior is applied here."
    proposal = {"repository": REPOSITORY, "title": "Prevent same cause", "body": body}
    if prompt:
        proposal["prompt_change"] = {
            "target_file": "retro-target.md", "heading": "Context", "source": current,
            "current_passage": "Keep line.\nChange this.",
            "proposed_passage": "Keep line.\nChange that.",
            "changes_made": {"context_or_constraints": "No additional context",
                             "ambiguity": "Clarifies the ambiguous action",
                             "success_criteria_or_requirement": "No additional criterion",
                             "timing": "No timing change"},
            "expected_behavior": "Agent follows the clarified action"}
    return {"category": "Automated checks", "cause": "same cause", "evidence": [current],
            "handled_here": "Accepted in this run", "prevention": {"destination": "script",
                                                             "text": "Check before a future run"},
            "earlier_occurrences": [{"memory_id": "prior-retro", "evidence": prior}] if earlier else [],
            "proposal": proposal}


def complete_none(f: Fixture):
    baseline = (MMW.parent / "docs" / "notes" / "stage-two-shared-experience-layer.md").read_text(encoding="utf-8")
    fixed = baseline.split("#### `retro/SKILL.md` 的固定执行 prompt", 1)[1].split("```text", 1)[1].split("```", 1)[0].strip()
    skill = (MMW / "skills" / "retro" / "SKILL.md").read_text(encoding="utf-8")
    assert fixed in skill, "all four phases and seven categories must retain the exact fixed prompt"
    assert skill.startswith("---\nname: retro\ndescription: Retrospect one completed MMW spec night")
    gathered = f.run("gather", "70")
    assert gathered["task_root"] == {"kind": "standalone-spec", "number": 70}
    assert gathered["observed"]["base_commit"] == f.base
    assert gathered["commits"][0]["sha"] == f.landed
    assert all(x["status"] == "present" for x in gathered["evidence_checked"])
    assert gathered["tickets"][0]["events"]
    outcome = f.finish(f.analysis(gathered))
    receipt = f.assert_receipt("recorded")
    assert outcome["problem_count"] == receipt["problem_count"] == 0
    assert outcome["proposals"] == receipt["proposals"] == []
    row = f.state("nmem")["memories"][outcome["retro_memory"]]
    for heading in ("Spec:", "Task root:", "Evidence checked:", "## Previous proposals",
                    "## Problems observed", "## Intent reconciliation", "## Review learning", "Observed:"):
        assert heading in row["content"], heading
    assert row["labels"] == ["mmw-retro"] and row["unit_type"] == "event"


def default_caller_repo(f: Fixture):
    git("remote", "set-url", "origin", f"git@github.com:{REPOSITORY}.git", cwd=f.checkout)
    gathered = f.run_default("gather", "70")
    assert gathered["spec_url"] == f"https://github.com/{REPOSITORY}/issues/70"
    assert gathered["observed"]["base_commit"] == f.base


def partial_evidence(f: Fixture):
    f.issues["70"]["body"] = f.issues["70"]["body"].replace("## User Stories", "## Unknown")
    f.issues["71"]["comments"].append({"id": 400, "url":
        f"https://github.com/{REPOSITORY}/issues/71#issuecomment-400",
        "body": "broken event evidence\n\n<!-- mmw {not-json} -->"})
    f.save()
    gathered = f.run("gather", "70")
    missing = [x["source"] for x in gathered["evidence_checked"] if x["status"] != "present"]
    assert any("User Stories" in x for x in missing)
    assert any(x["status"] == "unreadable" and "comment 400" in x["source"]
               for x in gathered["evidence_checked"]), gathered["evidence_checked"]
    problem = current_problem(f, earlier=True)
    gathered = f.run("gather", "70")
    analysis = f.analysis(gathered, [problem])
    outcome = f.finish(analysis)
    receipt = f.assert_receipt("recorded")
    assert receipt["evidence"] == "partial" and receipt["unreadable_sources"] == missing
    content = f.state("nmem")["memories"][outcome["retro_memory"]]["content"]
    assert "[missing]" in content and "[unreadable]" in content
    assert len(f.state("gh")["proposals"]) == 1
    # An unreadable source cannot itself support a different problem.
    invalid = problem.copy()
    invalid["evidence"] = [f"https://github.com/{REPOSITORY}/issues/71#issuecomment-400"]
    invalid["earlier_occurrences"] = []
    invalid["proposal"] = None
    latest = f.run("gather", "70")
    path = f.root / "unreadable.json"
    path.write_text(json.dumps(f.analysis(latest, [invalid])), encoding="utf-8")
    error = f.run("finalize", "70", str(path), ok=False)
    assert "https://github.com/sample/" in error and "because" in error and "gather 70" in error, error
    assert len(f.state("gh")["proposals"]) == 1


def proposal_threshold(f: Fixture):
    problem = current_problem(f)
    gathered = f.run("gather", "70")
    assert gathered["proposed_memory_ids"] == []
    search = f.run("search", "Automated checks", "same cause")
    assert search["matches"][0]["id"] == "prior-retro"
    outcome = f.finish(f.analysis(gathered, [problem]))
    proposal = f.state("gh")["proposals"][0]
    assert proposal["labels"] == ["needs-triage"] and proposal["repository"] == REPOSITORY
    assert gathered["spec_url"] in proposal["body"] and problem["evidence"][0] in proposal["body"]
    assert f.state("nmem")["memories"][outcome["retro_memory"]]["content"].find(proposal["url"]) > 0
    receipt = f.assert_receipt("recorded")
    assert receipt["proposals"] == [900]
    trace = f.trace()
    created = next(i for i, call in enumerate(trace) if call["source"] == "gh" and
                   call["args"][:2] == ["issue", "create"])
    memory = next(i for i, call in enumerate(trace) if call["source"] == "nmem" and
                  call["args"][:2] == ["memories", "add"])
    posted = next(i for i, call in enumerate(trace) if call["source"] == "gh" and
                  call["args"][:3] == ["issue", "comment", "70"])
    assert created < memory < posted, trace
    # One occurrence cannot qualify by severity, title or category alone.
    weak = current_problem(f, earlier=False)
    weak["proposal"]["title"] = "Weak proposed change"
    gathered = f.run("gather", "70")
    path = f.root / "weak.json"
    path.write_text(json.dumps(f.analysis(gathered, [weak])), encoding="utf-8")
    assert "proposal has no two indep" in f.run("finalize", "70", str(path), ok=False)
    # Two comments on one ticket are two representations, not two occurrences.
    same = f.event(71, "ticket.checked", "same cause again", ticket=71,
                   run="self", result="unmet", commit=f.landed)
    f.save()
    weak["evidence"].append(same)
    latest = f.run("gather", "70")
    path.write_text(json.dumps(f.analysis(latest, [weak])), encoding="utf-8")
    assert "proposal has no two indep" in f.run("finalize", "70", str(path), ok=False)
    # A proposed Worker Memory with an actual blocking event reaches the other
    # threshold without borrowing the older Memory as an occurrence.
    blocked = f.event(71, "ticket.returned", "same cause blocked the ticket", ticket=71)
    manifest = {"status": "complete", "total": 1, "returned": 1,
                "decisions": [{"memory_id": "worker-memory", "decision": "propose",
                               "reason": "prevent the blocker", "evidence": blocked}]}
    f.issues["70"]["comments"][1]["body"] = events.build(
        "spec.closed", ticket=None, spec=70, line="NIGHT SUMMARY", memory_closing=manifest)
    f.save()
    blocker = weak.copy()
    blocker["evidence"] = [blocked]
    blocker["proposal"] = {"repository": REPOSITORY, "title": "Prevent blocker",
                            "body": "Proposed Worker Memory worker-memory has one actual blocker."}
    latest = f.run("gather", "70")
    assert latest["proposed_memory_ids"] == ["worker-memory"]
    outcome = f.finish(f.analysis(latest, [blocker]))
    assert outcome["proposals"] and f.assert_receipt("recorded")["proposals"] == [900]
    # The repeated-cause threshold also admits two independent commit sources
    # with no event in the current problem.
    commits = Fixture()
    try:
        git("commit", "--allow-empty", "-m", "validator rejects absent input file", cwd=commits.checkout)
        first = git("rev-parse", "HEAD", cwd=commits.checkout)
        git("commit", "--allow-empty", "-m", "missing input causes validator exit", cwd=commits.checkout)
        second = git("rev-parse", "HEAD", cwd=commits.checkout)
        git("push", "origin", "spec-base", cwd=commits.checkout)
        git("fetch", "origin", cwd=commits.checkout)
        evidence = [f"https://github.com/{REPOSITORY}/commit/{sha}" for sha in (first, second)]
        commit_problem = {"category": "Automated checks", "cause": "validator fails when its input file is absent",
                          "evidence": evidence, "handled_here": "Accepted in this run",
                          "prevention": {"destination": "script", "text": "Check future commits"},
                          "earlier_occurrences": [], "proposal": {"repository": REPOSITORY,
                          "title": "Prevent repeated commits", "body": "Owner approval requested."}}
        latest = commits.run("gather", "70")
        assert {row["sha"] for row in latest["commits"]} >= {first, second}
        outcome = commits.finish(commits.analysis(latest, [commit_problem]))
        assert outcome["proposals"] == [f"https://github.com/{REPOSITORY}/issues/900"]
        assert commits.assert_receipt("recorded")["proposals"] == [900]
    finally:
        commits.close()
    # Semantic retrieval can match the same cause even when the original event
    # and older Retro Memory use different words from the current analysis.
    semantic = Fixture()
    try:
        current = semantic.event(71, "ticket.checked", "missing input blocks validator",
                                 ticket=71, run="self", result="unmet", commit=semantic.landed)
        prior = semantic.event(60, "ticket.checked", "input absent makes validator exit",
                               ticket=60, run="self", result="unmet", commit=semantic.base)
        semantic.save()
        cause = "validator fails when input is missing"
        semantic.update("nmem", memories={"prior-retro": {
            "id": "prior-retro", "space_id": SPACE,
            "content": f"Spec: {REPOSITORY}#69\n## Problems observed\n"
                       f"### Automated checks: absent input rejected\nEvidence: {prior}\n"}},
            semantic_aliases={f"Automated checks {cause}": ["prior-retro"]})
        semantic_problem = {"category": "Automated checks", "cause": cause,
                            "evidence": [current], "handled_here": "Accepted in this run",
                            "prevention": {"destination": "script", "text": "Check input first"},
                            "earlier_occurrences": [{"memory_id": "prior-retro", "evidence": prior}],
                            "proposal": {"repository": REPOSITORY, "title": "Check missing input",
                                         "body": "Owner approval requested."}}
        latest = semantic.run("gather", "70")
        outcome = semantic.finish(semantic.analysis(latest, [semantic_problem]))
        assert outcome["proposals"] and semantic.assert_receipt("recorded")["proposals"] == [900]
    finally:
        semantic.close()


def prompt_and_record_contract(f: Fixture):
    problem = current_problem(f, prompt=True)
    prior_url = f"https://github.com/{REPOSITORY}/issues/800"
    landed_url = f"https://github.com/{REPOSITORY}/issues/801"
    memories = f.state("nmem")["memories"]
    memories["prior-retro"]["content"] += (f"\n## Previous proposals\n"
                                                 f"- {prior_url} — no evidence found\n"
                                                 f"- {landed_url} — landed in retro-target.md\n")
    f.update("nmem", memories=memories)
    gathered = f.run("gather", "70")
    analysis = f.analysis(gathered, [problem])
    analysis["previous_proposals"] = [{"url": prior_url, "status": "no-evidence-found",
                                       "evidence": "none"},
                                      {"url": landed_url, "status": "landed",
                                       "evidence": "retro-target.md"}]
    result = f.finish(analysis)
    body = f.state("gh")["proposals"][0]["body"]
    for part in ("Current complete passage:\nKeep line.\nChange this.",
                 "Proposed complete passage:\nKeep line.\nChange that.",
                 "Changes Made:", "context_or_constraints:", "ambiguity:",
                 "success_criteria_or_requirement:", "timing:", "Expected behavior:"):
        assert part in body, part
    content = f.state("nmem")["memories"][result["retro_memory"]]["content"]
    for part in ("Evidence:", "Handled here:", "Prevention:", "Earlier occurrences:",
                 "Proposal:", "Expected:", "Observed:", "Gap:",
                 f"{prior_url} — 没找到证据", f"{landed_url} — 已落地：retro-target.md"):
        assert part in content, part
    bad = f.analysis(f.run("gather", "70"), [problem])
    bad["problems"][0]["proposal"]["prompt_change"]["changes_made"].pop("timing")
    path = f.root / "bad.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    assert "prompt_change needs all fo" in f.run("finalize", "70", str(path), ok=False)
    problem["proposal"]["prompt_change"]["changes_made"]["timing"] = "No timing change"
    no_change = f.analysis(f.run("gather", "70"), [problem])
    no_change["problems"][0]["proposal"]["prompt_change"]["proposed_passage"] = "Keep line.\nChange this."
    path.write_text(json.dumps(no_change), encoding="utf-8")
    assert "prompt proposal does not" in f.run("finalize", "70", str(path), ok=False)
    malformed = f.analysis(f.run("gather", "70"), [problem])
    malformed["observed"] = "unreadable shape"
    path.write_text(json.dumps(malformed), encoding="utf-8")
    refusal = f.run("finalize", "70", str(path), ok=False)
    assert "observed must contain" in refusal and "because" in refusal and "gather 70" in refusal
    # A current repository file and a rerunnable observed check are valid
    # primary evidence for problems without satisfying the proposal threshold.
    sources = Fixture()
    try:
        gathered = sources.run("gather", "70")
        problems = [
            {"category": "Information access", "cause": "Change this.",
             "evidence": ["retro-target.md"], "handled_here": "Found in the current file",
             "prevention": {"destination": "none", "text": "No change proposed"},
             "earlier_occurrences": [], "proposal": None},
            {"category": "Automated checks", "cause": "Keep line.",
             "evidence": ["check:rg -n 'Keep line.' retro-target.md"],
             "handled_here": "Observed the read-only check output",
             "prevention": {"destination": "none", "text": "No change proposed"},
             "earlier_occurrences": [], "proposal": None},
        ]
        result = sources.finish(sources.analysis(gathered, problems))
        assert result["problem_count"] == 2 and result["proposals"] == []
        assert sources.assert_receipt("recorded")["problem_count"] == 2
        content = sources.state("nmem")["memories"][result["retro_memory"]]["content"]
        assert "retro-target.md" in content and "check:rg -n 'Keep line.'" in content
    finally:
        sources.close()


def retry_finalize(f: Fixture):
    problem = current_problem(f)
    gathered = f.run("gather", "70")
    ticket_before = f.state("gh")["issues"]["71"]["comments"]
    fold_before = events.fold(ticket_before, issue=71)
    closed_before = [events.parse(c["body"])[1] for c in f.state("gh")["issues"]["70"]["comments"]
                     if events.parse(c["body"])[0] == "event" and
                     events.parse(c["body"])[1].get("event") == "spec.closed"]
    f.update("nmem", fail_add_once=True)
    analysis = f.analysis(gathered, [problem])
    first = f.finish(analysis)
    assert first["result"] == "unrecorded"
    f.assert_receipt("unrecorded")
    assert not f.state("nmem")["memories"].get(f"mmw-retro-{SPACE}-spec-70")
    assert len(f.state("gh")["proposals"]) == 1
    assert f.state("gh")["issues"]["71"]["comments"] == ticket_before
    assert events.fold(f.state("gh")["issues"]["71"]["comments"], issue=71) == fold_before
    assert [events.parse(c["body"])[1] for c in f.state("gh")["issues"]["70"]["comments"]
            if events.parse(c["body"])[0] == "event" and
            events.parse(c["body"])[1].get("event") == "spec.closed"] == closed_before
    # The incomplete receipt is a spec comment; gather's inventory remains the
    # same source list, and the latest receipt replaces it in the fold.
    next_gather = f.run("gather", "70")
    second = f.finish(f.analysis(next_gather, [problem]))
    assert second["result"] == "recorded"
    assert len(f.state("gh")["proposals"]) == 1
    assert len(f.state("nmem")["memories"]) == 2  # earlier + one fixed id
    assert f.assert_receipt("recorded")["retro_memory"] == second["retro_memory"]
    assert f.state("gh")["issues"]["71"]["comments"] == ticket_before
    assert events.fold(f.state("gh")["issues"]["71"]["comments"], issue=71) == fold_before
    assert [events.parse(c["body"])[1] for c in f.state("gh")["issues"]["70"]["comments"]
            if events.parse(c["body"])[0] == "event" and
            events.parse(c["body"])[1].get("event") == "spec.closed"] == closed_before
    assert len([c for c in f.state("gh")["issues"]["70"]["comments"]
                if '"event":"spec.closed"' in c["body"]]) == 1


FUNCTIONS = {"complete-none": complete_none, "default-caller-repo": default_caller_repo,
             "partial-evidence": partial_evidence,
             "proposal-threshold": proposal_threshold,
             "prompt-and-record-contract": prompt_and_record_contract,
             "retry-finalize": retry_finalize}


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else "all"
    if wanted != "all" and wanted not in FUNCTIONS:
        raise SystemExit("unknown retro scenario: " + wanted)
    for name in FUNCTIONS if wanted == "all" else [wanted]:
        fixture = Fixture()
        try:
            FUNCTIONS[name](fixture)
            print(NAMES[name])
        finally:
            fixture.close()
    if wanted == "all":
        print("all passed")


if __name__ == "__main__":
    main()
