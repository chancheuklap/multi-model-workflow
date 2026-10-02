"""Wiring check CLI on disposable repository-shaped trees."""
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

LIB = Path(__file__).resolve().parents[1] / 'lib'
SCRIPT = LIB / 'check_wiring.py'
FIXTURES = Path(__file__).resolve().parent / 'fixtures/wiring'
MODE = 'mmw-v2/skills/mmw'
WORK_ROUTE = '\n## Playbooks\n\n- **Work.** Do the work. `playbooks/work-a-ticket.md`.\n'


class Wiring(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mmw-wiring-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write('mmw-v2/skills.txt', 'self/example\nself/dispatch\nself/verify-ticket\n')
        self.fixture('locations.py', MODE + '/scripts/locations.py')
        self.fixture('roles.json', MODE + '/roles.json')

    def write(self, path, text):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding='utf-8')
        return dest

    def fixture(self, name, path):
        return self.write(path, (FIXTURES / name).read_text(encoding='utf-8'))

    def check(self, *args, script=SCRIPT):
        return subprocess.run([sys.executable, str(script), '--root', str(self.root), *args],
                              capture_output=True, text=True)

    def assert_status(self, result, status):
        self.assertEqual(result.returncode, status, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)

    def findings(self, result, category):
        output = result.stdout + result.stderr
        self.assertIn(result.returncode, (0, 1), output)
        self.assertNotIn('Traceback', output)
        if result.returncode == 1:
            self.assertIn('connections do not resolve', result.stdout)
        return re.findall(rf'(?m)^(?:report: )?(\S+:\d+: class {category} .+)$',
                          result.stdout)

    def test_wiring_class2_reports_a_missing_file_of_a_named_skill(self):
        self.write('mmw-v2/skills/example/SKILL.md', '# Example\n')
        self.write(MODE + '/SKILL.md',
                   "Read the `example` skill's `references/absent.md`.\n"
                   'Use the `absent` skill.\n')
        self.assertEqual(self.findings(self.check(), 2), [
            MODE + '/SKILL.md:1: class 2 mmw-v2/skills/example/references/absent.md does not exist',
            MODE + '/SKILL.md:2: class 2 absent is not in skills.txt',
        ])

    def test_wiring_class2_resolves_a_named_skill_file_in_that_skill(self):
        self.write('mmw-v2/skills/example/SKILL.md', '# Example\n')
        self.write('mmw-v2/skills/example/references/present.md', '# Present\n')
        self.write('mmw-v2/skills/example/scripts/dispatch.sh',
                   'case "$1" in\n run) echo ok ;;\nesac\n')
        content = ("Read the `example` skill's `references/present.md`.\n"
                   "Run the `example` skill's `scripts/dispatch.sh run`.\n"
                   "Start an `example` session. Read that skill's `references/present.md`.\n")
        self.write(MODE + '/SKILL.md', content)
        self.assertEqual(self.findings(self.check(), 2), [])
        forms = (
            "1. **Claim.** The `example` skill's `references/present.md`.",
            "- The `example` skill's `references/present.md`.",
            "(The `example` skill's `references/present.md`)",
        )
        self.write(MODE + '/playbooks/named-paths.md', '\n'.join(forms) + '\n')
        self.assertEqual(self.findings(self.check(), 2), [])
        self.write(MODE + '/SKILL.md', content.replace('dispatch.sh run', 'dispatch.sh walk'))
        self.assertEqual(self.findings(self.check(), 2), [
            MODE + '/SKILL.md:2: class 2 scripts/dispatch.sh has no subcommand walk',
        ])

    def test_wiring_class2_skips_placeholders_and_prose(self):
        self.write(MODE + '/references/examples.md',
                   '`principles/principle-<slug>.md`\n`references/x.md`\n`scripts/y.py`\n'
                   'Read the scoped skills, the other skill and the whole skill. '
                   'Ignore the `example` skills and the example skills.\n'
                   '`references/absent.md`\n')
        self.assertEqual(self.findings(self.check(), 2), [
            MODE + '/references/examples.md:5: class 2 references/absent.md does not exist',
        ])

    def test_wiring_class2_imported_file_has_no_pstack_names_allowance(self):
        path = MODE + '/playbooks/imported.md'
        self.write(path, 'Use the `old-skill` skill.\n')
        self.write(MODE + '/imports.tsv', 'type\tpath\nplaybook\t' + path + '\n')
        self.write(MODE + '/references/pstack-names.md', '| old-skill | example |\n')
        self.write('mmw-v2/skills/example/SKILL.md', '# Example\n')
        self.assertEqual(self.findings(self.check(), 2), [
            path + ':1: class 2 old-skill is not in skills.txt',
        ])

    def test_wiring_class5_reports_a_bold_citation_of_a_missing_principle(self):
        self.write(MODE + '/principles/principle-evidence.md',
                   '---\nname: principle-evidence\ndescription: Use evidence.\n---\n# Evidence\n')
        path = MODE + '/playbooks/citations.md'
        self.write(path, 'Read (**principle-evidence**).\nRead (**principle-absent**).\n')
        self.assertEqual(self.findings(self.check(), 5), [
            path + ':2: class 5 principle-absent has no principle file',
        ])
        self.write(MODE + '/SKILL.md', '- **Absent** (**principle-absent**). Use evidence.\n')
        self.assertEqual(self.findings(self.check(), 5), [
            MODE + '/SKILL.md:1: class 5 principle-absent has no principle file',
            path + ':2: class 5 principle-absent has no principle file',
        ])

    def test_wiring_class5_reports_a_citation_in_another_form(self):
        self.write(MODE + '/principles/principle-evidence.md', '# Evidence\n')
        path = MODE + '/playbooks/citations.md'
        valid = ('(**principle-evidence**)\n`principles/principle-evidence.md`\n'
                 '`principle-<slug>`, `(principle-<slug>)`, the **<display>** principle.\n')
        self.write(path, valid)
        self.assertEqual(self.findings(self.check(), 5), [])
        self.write(path, valid + '(principle-evidence)\n'
                   'the **evidence** principle\n'
                   '[Evidence](../principles/principle-evidence.md)\n')
        findings = self.findings(self.check(), 5)
        self.assertEqual(len(findings), 3, findings)
        for line, finding in zip((4, 5, 6), findings):
            self.assertRegex(finding, '^' + re.escape(path) +
                             rf':{line}: class 5 .+ is not the citation form \*\*principle-<slug>\*\*$')
        self.write(MODE + '/imports.tsv', 'type\tpath\nplaybook\t' + path + '\n')
        self.assertEqual(self.findings(self.check(), 5), [])
        self.write(path, valid + '(principle-absent)\n')
        self.assertEqual(self.findings(self.check(), 5), [
            path + ':4: class 5 principle-absent has no principle file',
        ])

    def test_wiring_class9_slash_form_of_a_switched_skill_needs_no_marker(self):
        self.reported_fixture(9)
        self.write(MODE + '/SKILL.md', 'Tell the user to run `/upstream-example`.\n')
        self.assertEqual(self.findings(self.check(), 9), [])

    def test_wiring_class9_named_form_of_a_switched_skill_needs_the_marker(self):
        self.reported_fixture(9)
        self.write(MODE + '/SKILL.md',
                   '# MMW\n\n- A survey → the `upstream-example` skill.\n'
                   'Use the `upstream-example` skill again.\n')
        self.assertEqual(self.findings(self.check(), 9), [
            MODE + '/SKILL.md:3: class 9 upstream-example is named for the model '
            'and has disable-model-invocation; it needs +model-invoked in skills.txt',
        ])
        self.write('mmw-v2/skills.txt', 'engineering/upstream-example +model-invoked\n')
        self.assertEqual(self.findings(self.check(), 9), [])
        self.write('mmw-v2/skills.txt', 'engineering/upstream-example\n')
        self.write(MODE + '/SKILL.md', '# MMW\n')
        self.write(MODE + '/references/named-skill.md', '- The `upstream-example` skill owns this method.\n')
        self.assertEqual(self.findings(self.check(), 9), [
            MODE + '/references/named-skill.md:1: class 9 upstream-example is named for the model '
            'and has disable-model-invocation; it needs +model-invoked in skills.txt',
        ])

    def test_wiring_class9_route_and_step_forms_need_the_marker(self):
        self.reported_fixture(9)
        self.write(MODE + '/SKILL.md', '# MMW\n\n- A survey → `upstream-example`.\n')
        path = MODE + '/playbooks/survey.md'
        self.write(path, '1. **Claim.** Run `upstream-example` first.\n'
                   '   Use `upstream-example` again.\n')
        self.write(MODE + '/references/rules.md',
                   "1. **Peers.** Upstream's `upstream-example` names its peers.\n")
        self.assertEqual(self.findings(self.check(), 9), [
            MODE + '/SKILL.md:3: class 9 upstream-example is named for the model '
            'and has disable-model-invocation; it needs +model-invoked in skills.txt',
            path + ':1: class 9 upstream-example is named for the model '
            'and has disable-model-invocation; it needs +model-invoked in skills.txt',
        ])

    def test_wiring_class9_skill_without_switch_needs_no_marker(self):
        self.reported_fixture(9)
        path = 'mmw-v2/upstream/skills/engineering/plain-example'
        self.write(path + '/SKILL.md', '---\nname: plain-example\n---\n# Plain\n')
        self.write('mmw-v2/skills.txt',
                   'engineering/upstream-example\nengineering/plain-example\n')
        self.write(MODE + '/SKILL.md',
                   'Use the `plain-example` skill.\nThe upstream-example is a bare name.\n')
        self.assertEqual(self.findings(self.check(), 9), [])
        graph = self.check('--graph')
        self.assertIn(graph.returncode, (0, 1), graph.stdout + graph.stderr)
        self.assertNotIn('Traceback', graph.stdout + graph.stderr)
        self.assertIn(MODE + '/SKILL.md -> ' + path + ' : 9', graph.stdout.splitlines())
        self.assertNotIn(MODE + '/SKILL.md -> mmw-v2/upstream/skills/engineering/upstream-example : 9',
                         graph.stdout.splitlines())

    def test_skill_mentions_tells_model_forms_from_the_slash_form(self):
        sys.path.insert(0, str(LIB))
        try:
            import skill_text
        finally:
            sys.path.remove(str(LIB))
        names = {'example', 'other-example', 'upstream-example'}
        text = ('---\nname: sample\ndescription: the `hidden` skill\n---\n'
                'The `example` skill owns a method.\n'
                'Use the example skill and the `absent` skill.\n'
                '- Survey → `upstream-example`.\n'
                '1. **Claim.** Run `example`.\n'
                '   Continue with `other-example`.\n'
                '\nRead `example` outside a step.\n'
                'Tell the user to run `/upstream-example` or `/loop`.\n'
                'the scoped skills, the other skill, the whole skill, the example skill-set.\n'
                'Ignore the `example` skills and the example skills.\n'
                'the `example skill is unpaired.\nthe example` skill is unpaired.\n'
                'prototype, research, teach, `example`.\n'
                '<!-- the `hidden` skill\n`/hidden` -->\n'
                '```text\nthe `hidden` skill\n```\n'
                '~~~~text\n`/hidden`\n~~~\n~~~~\n')
        mentions = skill_text.skill_mentions(text, names)
        self.assertEqual([(m.name, m.line, m.form, m.by_model) for m in mentions], [
            ('example', 5, 'qualified', True),
            ('example', 6, 'qualified', True),
            ('absent', 6, 'qualified', True),
            ('upstream-example', 7, 'route', True),
            ('example', 8, 'step', True),
            ('other-example', 9, 'step', True),
            ('upstream-example', 12, 'slash', False),
            ('loop', 12, 'slash', False),
        ])
        self.assertEqual([m.offset for m in mentions], [
            text.index('The `example`'), text.index('the example skill and'),
            text.index('the `absent`'), text.index('`upstream-example`'),
            text.index('`example`.', text.index('1. **Claim.**')),
            text.index('`other-example`'), text.index('`/upstream-example`'),
            text.index('`/loop`'),
        ])
        self.assertEqual([m.form for m in skill_text.skill_mentions(text, names, steps=False)],
                         ['qualified', 'qualified', 'qualified', 'route', 'slash', 'slash'])
        masked = skill_text.prose_mask(text)
        self.assertEqual(len(masked), len(text))
        self.assertEqual([i for i, c in enumerate(masked) if c == '\n'],
                         [i for i, c in enumerate(text) if c == '\n'])
        paths = [
            ("the `example` skill's `references/present.md`", 'example'),
            ("The `example` skill's `references/present.md`", 'example'),
            ("1. **Claim.** The `example` skill's `references/present.md`.", 'example'),
            ("- The `example` skill's `references/present.md`.", 'example'),
            ("(The `example` skill's `references/present.md`)", 'example'),
            ("the `example` skill's\n`references/present.md`", 'example'),
            ("the example skill's `references/present.md`", 'example'),
            ("the `absent` skill's `references/present.md`", 'absent'),
            ("an `example` session. Read that skill's `references/present.md`", 'example'),
            ("the `example` skill. Then `other-example`; that skill's `references/present.md`",
             'other-example'),
            ("`example`\nthat skill's `references/present.md`", None),
            ("`/example`; that skill's `references/present.md`", None),
            ('Read `references/present.md`.', None),
        ]
        for source, expected in paths:
            with self.subTest(source=source):
                offset = source.index('`references/present.md`')
                self.assertEqual(skill_text.skill_of_path(source, offset, names), expected)
                self.assertEqual(skill_text.skill_of_path(source, offset + 1, names), expected)
        for source in (
            "1. **Claim.** The `example` skill owns this method.",
            "- The `example` skill owns this method.",
            "(The `example` skill owns this method)",
        ):
            with self.subTest(source=source):
                self.assertEqual([(m.name, m.form) for m in skill_text.skill_mentions(source, names, False)],
                                 [('example', 'qualified')])
        source = ('```html\n<!-- an unfinished code example\n```\n'
                  'Use the `example` skill. <!-- the `hidden` skill -->\n')
        self.assertEqual([(m.name, m.line) for m in skill_text.skill_mentions(source, names)],
                         [('example', 4)])
        self.assertEqual([(m.name, m.form) for m in skill_text.skill_mentions(
            'the `Missing-Skill` skill. `/Missing-Skill`', names)],
                         [('Missing-Skill', 'qualified'), ('Missing-Skill', 'slash')])
        self.assertEqual(skill_text.skill_mentions('An example: `` the `X` skill ``.', names), [])

    def test_wiring_pointer_class(self):
        path = 'mmw-v2/skills/example/SKILL.md'
        self.fixture('class-1.md', path)
        result = self.check()
        self.assert_status(result, 1)
        self.assertRegex(result.stdout, r'(?m)^mmw-v2/skills/example/SKILL.md:1: class 1 ')

    def test_wiring_one_line_class(self):
        samples = {
            'relay.py': (FIXTURES / 'class-8.py').read_text(),
            'watchdog.py': 'alert = {"text": "watchdog: first\\nsecond"}\n',
            'turn-guard.py': 'text = "MMW turn guard: first\\nsecond"\n',
            'dispatch.sh': 'resume_one() {\n text="$2"\n runner send "$ident" "$text"\n}\n',
        }
        for name, content in samples.items():
            with self.subTest(name=name):
                dest = self.write(MODE + '/scripts/' + name, content)
                resume = None
                if name == 'dispatch.sh':
                    resume = self.write(MODE + '/references/night.md',
                                        '`bash scripts/dispatch.sh resume <n> "first\nsecond"`\n')
                result = self.check()
                self.assert_status(result, 1)
                self.assertRegex(result.stdout, (r'night.md' if resume else name) + r':\d+: class 8 ')
                dest.unlink()
                if resume:
                    resume.unlink()
        self.write(MODE + '/scripts/dispatch.sh',
                   'start_one() {\ncase "$kind" in\n'
                   'worker) prompt="Use the implement skill.\npacket" ;;\n'
                   'reviewer) prompt="Use the code-review skill.\npacket" ;;\nesac\n'
                   'start_session "$host" "$model" "$effort" "$cwd" "$prompt" "$title"\n}\n'
                   'advise_one() {\nprompt="Use the advisor skill."$\'\\n\'"$body"\n'
                   'start_session "$host" "$model" "$effort" "$cwd" "$prompt" "$title"\n}\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertEqual(len(re.findall(r'^report: .*dispatch.sh:\d+: class 8 ',
                                                    result.stdout, re.M)), 3)

    def test_wiring_reads_start_prompts_added_later(self):
        self.write(MODE + '/scripts/dispatch.sh',
                   'research_one() {\nnew_prompt="Research this.\nMore data."\n'
                   'session="$(start_session "$host" "$model" "$effort" "$cwd" "$new_prompt" "$title")"\n}\n')
        result = self.check()
        self.assert_status(result, 1)
        self.assertRegex(result.stdout, r'dispatch.sh:\d+: class 8 ')

    def test_wiring_path_literal_class(self):
        samples = [
            ('mmw-v2/board/example.py', (FIXTURES / 'class-10.py').read_text(), 'mmw-v2/skills/absent'),
            ('mmw-v2/board/example.py', 'target = "skills/absent/scripts"\n', 'mmw-v2/skills/absent/scripts'),
            (MODE + '/scripts/example.py', 'target = HERE.parents[1] / "absent"\n', 'mmw-v2/skills/absent'),
            (MODE + '/scripts/runners/example.sh', 'target="$(dirname "$HERE")/absent.py"\n', MODE + '/scripts/absent.py'),
            (MODE + '/scripts/example.sh', 'target="$SKILL_ROOT/scripts/absent.py"\n', MODE + '/scripts/absent.py'),
        ]
        for path, text, target in samples:
            with self.subTest(text=text):
                dest = self.write(path, text)
                result = self.check()
                self.assert_status(result, 1)
                self.assertRegex(result.stdout, r'(?m)^(?!report:).*:\d+: class 10 ')
                endpoint = self.root / target
                endpoint.parent.mkdir(parents=True, exist_ok=True)
                endpoint.touch()
                result = self.check()
                self.assert_status(result, 0)
                self.assertRegex(result.stdout, r'report: .*:\d+: class 10 ')
                endpoint.unlink()
                if (self.root / 'mmw-v2/skills/absent').is_dir():
                    shutil.rmtree(self.root / 'mmw-v2/skills/absent')
                dest.unlink()

    def reported_fixture(self, category):
        targets = {
            2: MODE + '/SKILL.md',
            3: 'mmw-v2/skills/example/scripts/example.py',
            5: MODE + '/SKILL.md',
            6: MODE + '/scripts/relay.py',
            7: MODE + '/SKILL.md',
            9: MODE + '/SKILL.md',
            11: MODE + '/scripts/dispatch.sh',
            12: MODE + '/scripts/dispatch.sh',
        }
        target = targets[category]
        suffix = Path(target).suffix
        self.fixture(f'class-{category}{suffix}', target)
        if category == 5:
            self.write(MODE + '/principles/principle-evidence.md',
                       '---\nname: principle-evidence\ndescription: Apply when evidence is required.\n---\n# Evidence\n')
        if category == 7:
            self.write('mmw-v2/skills/example/SKILL.md', '# Example\n')
            self.write(MODE + '/playbooks/work-a-ticket.md',
                       '### Work\n\n1. **Claim.** Use the `example` skill.\n'
                       '2. **Get reviewed.** Use the `example` skill.\n')
        if category == 9:
            self.write('mmw-v2/skills.txt', 'self/example\nengineering/upstream-example\n')
            self.write('mmw-v2/upstream/skills/engineering/upstream-example/SKILL.md',
                       '---\nname: upstream-example\ndescription: Use when needed.\n'
                       'disable-model-invocation: true\n---\n# Upstream\n')

    def test_wiring_reported_classes(self):
        batches = {3: 'B2 end', 6: 'B2 end', 11: 'B2 end', 12: 'B2'}
        for category, batch in batches.items():
            with self.subTest(category=category):
                self.setUp()
                self.reported_fixture(category)
                result = self.check()
                self.assert_status(result, 0)
                self.assertRegex(result.stdout, rf'(?m)^report: .*:\d+: class {category} ')
                if category == 6:
                    self.assertRegex(result.stdout, r'(?m)^report: .*: class 6 worker/unhandled.event has no registered handler$')
                copied = self.root / 'checker'
                copied.mkdir()
                shutil.copy(LIB / 'skill_text.py', copied)
                script = self.write('checker/check_wiring.py', SCRIPT.read_text().replace(
                    f"{category}: Policy(False, '{batch}')", f"{category}: Policy(True, '{batch}')"))
                result = self.check(script=script)
                self.assert_status(result, 1)
                self.assertRegex(result.stdout, rf'(?m)^(?!report:).*:\d+: class {category} ')
                if category == 6:
                    self.assertRegex(result.stdout, r'(?m)^(?!report:).*: class 6 worker/unhandled.event has no registered handler$')

    def test_wiring_b1_classes_fail(self):
        repairs = {
            2: (MODE + '/playbooks/missing.md', '### Missing\n'),
            5: (MODE + '/principles/principle-evidence.md',
                '---\nname: principle-evidence\ndescription: Apply when evidence is required.\n'
                '---\n# Wrong display name\n'),
            7: (MODE + '/SKILL.md', '# MMW\n' + WORK_ROUTE),
            9: ('mmw-v2/skills.txt', 'self/example\nengineering/upstream-example +model-invoked\n'),
        }
        for category, (path, text) in repairs.items():
            with self.subTest(category=category):
                self.setUp()
                self.reported_fixture(category)
                result = self.check()
                self.assert_status(result, 1)
                self.assertIn('connections do not resolve', result.stdout)
                self.assertRegex(result.stdout, rf'(?m)^(?!report:).*:\d+: class {category} ')
                self.write(path, text)
                result = self.check()
                self.assert_status(result, 0)
                self.assertNotRegex(result.stdout, rf'(?m)^(?:report: )?.*:\d+: class {category} ')

    def test_wiring_pointer_class_targets(self):
        path = 'mmw-v2/skills/example/SKILL.md'
        self.write(path, '`mmw work-a-ticket#Claim`\n`mmw#Re-entry`\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertIn('pending work-a-ticket (not built yet)', result.stdout)
        self.write(MODE + '/playbooks/work-a-ticket.md', '### Work\n\n#### Claim\n\n#### Get reviewed\n')
        self.write(MODE + '/SKILL.md', '# MMW\n\n## Re-entry\n' + WORK_ROUTE)
        self.assert_status(self.check(), 0)
        self.write(MODE + '/SKILL.md', '# MMW\n\n## Autonomy\n' + WORK_ROUTE)
        result = self.check()
        self.assert_status(result, 1)
        self.assertRegex(result.stdout, r'(?m)^(?!report: ).*: class 1 mmw#Re-entry ')
        self.write(MODE + '/SKILL.md', '# MMW\n\n## Re-entry\n' + WORK_ROUTE)
        self.write(MODE + '/playbooks/work-a-ticket.md', '### Claim\n\n#### Get reviewed\n')
        result = self.check()
        self.assert_status(result, 1)
        self.assertRegex(result.stdout, r'(?m)^(?!report: ).*: class 1 mmw work-a-ticket#Claim ')
        self.write(MODE + '/playbooks/work-a-ticket.md', '1. **Claim.** Do the work.\n\n2. **Get reviewed.** Read the report.\n')
        self.assert_status(self.check(), 0)
        self.write(MODE + '/playbooks/work-a-ticket.md', '### Work\n\n#### Get reviewed\n')
        result = self.check()
        self.assert_status(result, 1)
        self.assertRegex(result.stdout, r'(?m)^(?!report: ).*: class 1 mmw work-a-ticket#Claim ')
        self.write(MODE + '/imports.tsv', 'type\tpath\nplaybook\t' + MODE + '/playbooks/work-a-ticket.md\n')
        result = self.check()
        self.assert_status(result, 1)
        self.assertIn('imported playbook', result.stdout)
        (self.root / (MODE + '/imports.tsv')).unlink()
        (self.root / (MODE + '/playbooks/work-a-ticket.md')).unlink()
        self.write(MODE + '/roles.json', '{"worker":{"playbook":"work-a-ticket","wakes":{"reviewer.reported":"Wrong"}}}')
        result = self.check()
        self.assert_status(result, 1)
        self.assertRegex(result.stdout, r'roles.json:\d+: class 1 ')

    def test_wiring_classes_without_objects(self):
        result = self.check()
        self.assert_status(result, 0)
        for category in (2, 5, 7, 9, 12):
            self.assertIn(f'report: class {category}: no objects yet', result.stdout)

    def test_wiring_scan_scope(self):
        bad = 'Run mmw work-a-ticket#Wrong.\n'
        for path in ('docs/bad.md', 'archive/skills/bad.md', 'deprecated/bad.py',
                     'mmw-v2/tests/bad.py', 'mmw-v2/tests/fixtures/bad.md'):
            self.write(path, bad)
        result = self.check()
        self.assert_status(result, 0)
        self.assertNotIn('Wrong', result.stdout)
        self.write('mmw-v2/prompt/tests/run.sh', 'pointer="mmw work-a-ticket#Wrong"\n')
        self.assert_status(self.check(), 1)
        (self.root / 'mmw-v2/prompt/tests/run.sh').unlink()
        self.write('mmw-v2/install.sh', 'pointer="mmw work-a-ticket#Wrong"\n')
        self.assert_status(self.check(), 1)
        (self.root / 'mmw-v2/install.sh').unlink()
        self.write('mmw-v2/board/page.py', 'pointer="mmw work-a-ticket#Wrong"\n')
        self.assert_status(self.check(), 1)

    def test_wiring_graph(self):
        self.write('mmw-v2/skills/example/SKILL.md', '`mmw work-a-ticket#Claim`\n')
        self.reported_fixture(2)
        self.reported_fixture(3)
        self.reported_fixture(5)
        self.reported_fixture(6)
        mode = self.root / (MODE + '/SKILL.md')
        mode.write_text(mode.read_text() + '\nUse the absent skill. Use the upstream-example skill.\nRun `dispatch.sh lonely`.\n')
        self.write(MODE + '/playbooks/work-a-ticket.md', '#### Claim\n\n#### Get reviewed\n')
        self.write(MODE + '/scripts/dispatch.sh', 'new_one() {\nstart_session h m e cwd "Read /checkout/mmw-v2/skills/mmw/SKILL.md" title\n}\ncase "$1" in\n lonely) echo ok ;;\nesac\n')
        self.write('mmw-v2/board/example.py', 'target = "skills/mmw/scripts"\n')
        self.write('mmw-v2/skills.txt', 'self/example\nengineering/upstream-example +model-invoked\n')
        self.write('mmw-v2/upstream/skills/engineering/upstream-example/SKILL.md', '# Upstream\n')
        result = self.check('--graph')
        self.assert_status(result, 1)
        categories = {int(line.rsplit(' : ', 1)[1]) for line in result.stdout.splitlines()}
        self.assertTrue({1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12} <= categories, result.stdout)
        self.assertIn('mmw-v2/skills/example/SKILL.md -> mmw work-a-ticket#Claim : 1', result.stdout)
        self.assertIn(MODE + '/SKILL.md -> ' + MODE + '/scripts/dispatch.sh#lonely : 11', result.stdout)
        self.assertTrue(all(' -> ' in line and ' : ' in line for line in result.stdout.splitlines()), result.stdout)

    def test_wiring_unreadable_registry_exits_2(self):
        registry = self.root / (MODE + '/scripts/locations.py')
        registry.unlink()
        result = self.check()
        self.assert_status(result, 2)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertIn('bash mmw-v2/install.sh --check', result.stdout)
        self.fixture('locations.py', MODE + '/scripts/locations.py')
        self.assert_status(self.check(), 0)
        self.write(MODE + '/roles.json', 'not json')
        result = self.check()
        self.assert_status(result, 2)
        self.assertIn('bash mmw-v2/install.sh --check', result.stdout)

    def test_shared_lints_run_the_wiring_check(self):
        lib = self.root / 'mmw-v2/tests/lib'
        lib.mkdir(parents=True)
        for name in ('run_shared_lints.sh', 'check_module_paths.py', 'check_upstream_em_dashes.py',
                     'check_own_skill_frontmatter.py', 'check_component_structure.py',
                     'skill_text.py', 'check_wiring.py'):
            shutil.copy(LIB / name, lib / name)
        self.write('mmw-v2/skills.txt', 'self/example\n')
        self.write('mmw-v2/skills/example/SKILL.md',
                   '---\nname: example\ndescription: Use when needed.\n---\n# Example\n')
        self.write(MODE + '/scripts/statedir.py',
                   (LIB.parents[1] / 'skills/mmw/scripts/statedir.py').read_text())
        environment = {k: v for k, v in os.environ.items() if not k.startswith(('MMW_', 'NMEM_'))}
        environment['MMW_HOME'] = str(self.root / '.mmw')
        result = subprocess.run(['bash', str(lib / 'run_shared_lints.sh')],
                                cwd=self.root, env=environment, capture_output=True, text=True)
        self.assert_status(result, 0)
        self.write('mmw-v2/skills/example/scripts/bad.py', 'pointer="mmw work-a-ticket#Wrong"\n')
        result = subprocess.run(['bash', str(lib / 'run_shared_lints.sh')],
                                cwd=self.root, env=environment, capture_output=True, text=True)
        self.assert_status(result, 1)
        self.assertIn('class 1 ', result.stdout + result.stderr)

    def test_wiring_pointer_rejects_title_suffix_and_where_typo(self):
        self.write('mmw-v2/skills/example/SKILL.md', '`mmw work-a-ticket#Claim wrongly`\n')
        self.assert_status(self.check(), 1)
        (self.root / 'mmw-v2/skills/example/SKILL.md').unlink()
        file = self.root / (MODE + '/scripts/locations.py')
        file.write_text(file.read_text() + "\nWHERE_ROWS = {'worker': {'fresh': {'step': 'Typo'}}}\n")
        result = self.check()
        self.assert_status(result, 1)
        self.assertIn('locations.py', result.stdout)

    def test_wiring_dispatch_nested_case_commands(self):
        self.write(MODE + '/scripts/dispatch.sh',
                   'case "${1:-}" in\n first) case "$2" in foo) echo ok ;; esac ;;\n'
                   ' lonely) lonely_one ;;\nesac\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertRegex(result.stdout, r'class 11 lonely ')
        self.assertNotRegex(result.stdout, r'class 11 foo ')

    def test_wiring_added_start_prompt_with_continuation(self):
        self.write(MODE + '/scripts/dispatch.sh',
                   'new_one() {\nstart_session "$host" \\\n "$model" "$effort" "$cwd" "first\nsecond" "$title"\n}\n')
        self.assert_status(self.check(), 1)

    def test_wiring_invocation_marker_resolves_installed_name(self):
        self.reported_fixture(9)
        self.write('mmw-v2/skills.txt', 'self/example\nengineering/upstream-example +model-invoked\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertNotRegex(result.stdout, r'(?m)^report: .*: class 9 ')

    def test_wiring_upstream_diff_requires_section_registration(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.email', 'fixture@example.test'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.name', 'Fixture'], check=True)
        self.write('skills/engineering/example/SKILL.md', '# Example\n\n## Method\nOriginal instructions.\n')
        subprocess.run(['git', '-C', str(self.root), 'add', 'skills'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'commit', '-qm', "Squashed 'mmw-v2/upstream/' changes"], check=True)
        path = 'mmw-v2/upstream/skills/engineering/example/SKILL.md'
        self.write(path, '# Example\n\n## Method\nChanged instructions.\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertRegex(result.stdout, r'(?m)^report: .*example/SKILL.md:\d+: class 3 ')
        self.write('mmw-v2/merge-notes/example.md', '# example\n\n### SKILL.md\n\n| `## Other` | host neutrality |\n')
        self.assertRegex(self.check().stdout, r'(?m)^report: .*example/SKILL.md:\d+: class 3 ')
        self.write('mmw-v2/merge-notes/example.md', '# example\n\n### SKILL.md\n\n| `## Other` | host neutrality |\n\n### other.md\n\n全文\n')
        self.assertRegex(self.check().stdout, r'(?m)^report: .*example/SKILL.md:\d+: class 3 ')
        self.write('mmw-v2/merge-notes/example.md', '# example\n\n### SKILL.md\n\n| `## Method` | host neutrality |\n')
        self.assertNotRegex(self.check().stdout, r'(?m)^report: .*example/SKILL.md:\d+: class 3 ')
        (self.root / 'mmw-v2/merge-notes/example.md').unlink()
        self.write('mmw-v2/merge-notes/README.md', '## 本仓自有正文的技能\n\n`example` owns its content.\n\n## Other\n')
        self.assertNotRegex(self.check().stdout, r'(?m)^report: .*example/SKILL.md:\d+: class 3 ')
        self.write('mmw-v2/merge-notes/README.md', '## Other\n\n`example` is mentioned here.\n')
        self.assertRegex(self.check().stdout, r'(?m)^report: .*example/SKILL.md:\d+: class 3 ')

    def test_wiring_upstream_added_file_registered_by_a_note_heading(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.email', 'fixture@example.test'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.name', 'Fixture'], check=True)
        self.write('skills/engineering/example/SKILL.md', '# Example\n')
        subprocess.run(['git', '-C', str(self.root), 'add', 'skills'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'commit', '-qm', "Squashed 'mmw-v2/upstream/' changes"], check=True)
        path = 'mmw-v2/upstream/skills/engineering/example/EXTRA.md'
        self.write(path, '# Extra\nAdded instructions.\n')
        finding = (r'(?m)^(?:report: )?' + re.escape(path) +
                   r':1: class 3 skills/engineering/example/EXTRA\.md has no squash original$')
        self.assertRegex(self.check().stdout, finding)
        self.write('mmw-v2/merge-notes/example.md',
                   '# example\n\n### SKILL.md\n\n| EXTRA.md | Added capability |\n')
        self.assertRegex(self.check().stdout, finding)
        self.write('mmw-v2/merge-notes/example.md',
                   '# example\n\n### EXTRA.md\n\nAdded capability.\n')
        self.assertNotRegex(self.check().stdout, finding)

    def test_wiring_upstream_frontmatter_difference_registered_by_key(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.email', 'fixture@example.test'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.name', 'Fixture'], check=True)
        original = '---\nname: example\ndescription: Original trigger.\n---\n# Example\n'
        self.write('skills/engineering/example/SKILL.md', original)
        subprocess.run(['git', '-C', str(self.root), 'add', 'skills'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'commit', '-qm', "Squashed 'mmw-v2/upstream/' changes"], check=True)
        path = 'mmw-v2/upstream/skills/engineering/example/SKILL.md'
        self.write(path, original.replace('Original trigger.', 'Changed trigger.'))
        finding = (r'(?m)^(?:report: )?' + re.escape(path) +
                   r':3: class 3 upstream difference at SKILL\.md@description is not registered in its merge-note$')
        self.assertRegex(self.check().stdout, finding)
        self.write('mmw-v2/merge-notes/example.md',
                   '# example\n\n### SKILL.md\n\n| `name` | Changed trigger |\n')
        self.assertRegex(self.check().stdout, finding)
        self.write('mmw-v2/merge-notes/example.md',
                   '# example\n\n### SKILL.md\n\n| `description` | Changed trigger |\n')
        self.assertNotRegex(self.check().stdout, finding)

    def test_wiring_upstream_prose_before_any_heading_registered_by_its_opening_words(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.email', 'fixture@example.test'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.name', 'Fixture'], check=True)
        self.write('skills/engineering/example/SKILL.md', 'Original body sentence here.\n')
        subprocess.run(['git', '-C', str(self.root), 'add', 'skills'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'commit', '-qm', "Squashed 'mmw-v2/upstream/' changes"], check=True)
        path = 'mmw-v2/upstream/skills/engineering/example/SKILL.md'
        self.write(path, 'Changed body sentence here.\n')
        finding = (r'(?m)^(?:report: )?' + re.escape(path) +
                   r':1: class 3 upstream difference at SKILL\.md#"Changed body sentence" is not registered in its merge-note$')
        self.assertRegex(self.check().stdout, finding)
        self.write('mmw-v2/merge-notes/example.md',
                   '# example\n\n### SKILL.md\n\n| Original body sentence | host neutrality |\n')
        self.assertRegex(self.check().stdout, finding)
        self.write('mmw-v2/merge-notes/example.md',
                   '# example\n\n### SKILL.md\n\n| Changed body sentence | host neutrality |\n')
        self.assertNotRegex(self.check().stdout, finding)

    def test_wiring_frozen_paths_rejects_other_checkout(self):
        self.write('.mmw/installed-root', str(self.root / 'installed/mmw-v2'))
        self.write(MODE + '/scripts/dispatch.sh',
                   'research_one() {\nprompt="Read /other/checkout/mmw-v2/skills/mmw/SKILL.md"\n'
                   'start_session "$host" "$model" "$effort" "$cwd" "$prompt" "$title"\n}\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertRegex(result.stdout, r'(?m)^report: .*: class 12 ')
        self.write(MODE + '/scripts/dispatch.sh',
                   'research_one() {\nprompt="Read ' + str(self.root / 'installed/mmw-v2/skills/mmw/SKILL.md') + '"\n'
                   'start_session "$host" "$model" "$effort" "$cwd" "$prompt" "$title"\n}\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertNotRegex(result.stdout, r'(?m)^report: .*: class 12 ')

    def test_wiring_reference_commands(self):
        self.write(MODE + '/scripts/dispatch.sh', 'case "$1" in\n known) echo ok ;;\nesac\n')
        self.write(MODE + '/playbooks/work-a-ticket.md',
                   '#### Claim\n\nRun `scripts/dispatch.sh missing`.\n\n#### Get reviewed\n')
        result = self.check()
        self.assertEqual(self.findings(result, 2), [
            MODE + '/playbooks/work-a-ticket.md:3: class 2 scripts/dispatch.sh has no subcommand missing',
        ])
        self.write(MODE + '/playbooks/work-a-ticket.md',
                   '#### Claim\n\nRun `scripts/dispatch.sh known`.\n\n#### Get reviewed\n')
        self.assertEqual(self.findings(self.check(), 2), [])

    def test_wiring_event_sources_and_duplicate_handlers(self):
        self.write(MODE + '/roles.json', '{"night-orchestrator":{"playbook":"work-a-ticket","wakes":{"*":"Claim"}}}')
        self.write(MODE + '/SKILL.md', '# MMW\n' + WORK_ROUTE)
        self.write(MODE + '/playbooks/work-a-ticket.md', '#### Claim\nHandle the wake.\n')
        self.write(MODE + '/scripts/watchdog.py',
                   'alerts = [\n' + ''.join('{"text":"watchdog: alert%d"},\n' % i for i in range(8)) + ']\n')
        self.write(MODE + '/scripts/relay.py', 'RECOVERED = "relay.recovered"\n')
        self.write(MODE + '/scripts/turn-guard.py', 'text = "MMW turn guard: held"\n')
        graph = self.check('--graph')
        self.assert_status(graph, 0)
        for event in ['relay.recovered', 'MMW turn guard:'] + [f'watchdog: alert{i}' for i in range(8)]:
            self.assertIn('night-orchestrator/' + event + ' -> ', graph.stdout)
        self.write(MODE + '/playbooks/work-a-ticket.md', '#### Claim\nHandle the wake.\n\n#### Claim\nHandle it again.\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertRegex(result.stdout, r'(?m)^report: .*: class 6 .*2 handlers')

    def test_wiring_combined_alert_template_and_fourth_start(self):
        self.write(MODE + '/scripts/watchdog.py',
                   'alerts = [{"text":"watchdog: one"}, {"text":"watchdog: two"}]\n'
                   'text = "\\n".join(alert["text"] for alert in alerts)\n'
                   'send(runner, session, text)\n')
        self.assert_status(self.check(), 1)
        (self.root / (MODE + '/scripts/watchdog.py')).unlink()
        self.write(MODE + '/scripts/dispatch.sh',
                   'start_one() {\nprompt="Use the implement skill.\npacket"\n'
                   'start_session "$host" "$model" "$effort" "$cwd" "$prompt" "$title"\n'
                   'extra_prompt="Use the implement skill.\nnew kind"\n'
                   'start_session "$host" "$model" "$effort" "$cwd" "$extra_prompt" "$title"\n}\n')
        self.assert_status(self.check(), 1)

    def test_wiring_reports_a_capability_calling_a_mode_command(self):
        self.write('mmw-v2/skills/example/scripts/example.py', 'BAD = "mmw start 1 worker"\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertRegex(result.stdout, r'(?m)^report: .*example.py:\d+: class 3 capability script calls a mode command directly$')

    def test_wiring_product_syntax_error_is_not_installation_failure(self):
        self.write('mmw-v2/board/page.py', 'def broken(:\n')
        result = self.check()
        self.assert_status(result, 1)
        self.assertIn('mmw-v2/board/page.py:1:', result.stdout)
        self.assertTrue(result.stdout.splitlines()[1].startswith('Next:'), result.stdout)
        self.assertTrue(result.stdout.splitlines()[2].startswith('Why:'), result.stdout)
        self.assertNotIn('install.sh --check', result.stdout)

    def test_wiring_resume_text_at_call_sites(self):
        self.write(MODE + '/scripts/dispatch.sh',
                   'resume_one() {\n local text="$2"\n runner send "$ident" "$text"\n}\n')
        for path in (MODE + '/references/night.md',
                     'mmw-v2/skills/design-pages/references/pull.md',
                     'mmw-v2/skills/example/scripts/continue.sh'):
            with self.subTest(path=path):
                source = self.write(path, 'bash scripts/dispatch.sh resume <n> "one line"\n')
                graph = self.check('--graph')
                self.assert_status(graph, 0)
                self.assertIn(path + ' -> live session : 8', graph.stdout)
                source.write_text('bash scripts/dispatch.sh resume <n> "first\nsecond"\n')
                result = self.check()
                self.assert_status(result, 1)
                self.assertIn(path + ':1: class 8 session template contains a newline', result.stdout)
                source.unlink()

    def test_wiring_machine_state_uses_mmw_home(self):
        state = self.root / 'isolated-state'
        state.mkdir()
        installed = self.root / 'installed/mmw-v2'
        (state / 'installed-root').write_text(str(installed))
        self.reported_fixture(9)
        self.write('mmw-v2/skills.txt', 'engineering/upstream-example +model-invoked\n')
        self.write('isolated-state/skill-copies/upstream-example/SKILL.md',
                   '---\ndisable-model-invocation: true\n---\n# Upstream\n')
        self.write(MODE + '/scripts/dispatch.sh',
                   'new_one() {\nstart_session h m e cwd "Read ' + str(installed / 'skills/mmw/SKILL.md') + '" title\n}\n')
        # Run the production path from a disposable checkout, never this machine's state.
        lib = self.root / 'mmw-v2/tests/lib'
        lib.mkdir(parents=True)
        for name in ('check_wiring.py', 'skill_text.py'):
            shutil.copy(LIB / name, lib / name)
        self.write(MODE + '/scripts/statedir.py',
                   (LIB.parents[1] / 'skills/mmw/scripts/statedir.py').read_text())
        env = {k: v for k, v in os.environ.items() if not k.startswith(('MMW_', 'NMEM_'))}
        env['MMW_HOME'] = str(state)
        result = subprocess.run([sys.executable, str(lib / 'check_wiring.py')],
                                env=env, capture_output=True, text=True)
        self.assert_status(result, 1)
        self.assertRegex(result.stdout, r'(?m)^(?!report:).*: class 9 .*installation copy still has invocation switch$')
        self.assertNotRegex(result.stdout, r'(?m)^report: .*: class 12 ')
        isolated = self.check()
        self.assertNotIn('installation copy still has invocation switch', isolated.stdout)
        self.assertRegex(isolated.stdout, r'(?m)^report: .*: class 12 ')

    def test_wiring_entry_list_label_is_a_pointer_target(self):
        registry = self.root / (MODE + '/scripts/locations.py')
        registry.write_text(registry.read_text().replace(
            "'work-a-ticket': ('Claim', 'Get reviewed')",
            "'work-a-ticket': ('Claim', 'Get reviewed', 'Adopted ticket')"))
        self.write(MODE + '/roles.json',
                   '{"worker": {"playbook": "work-a-ticket", "entry": "Adopted ticket"}}\n')
        self.write(MODE + '/SKILL.md', '# MMW\n' + WORK_ROUTE)
        bold = ('### Work a ticket\n\n'
                '**Entry.**\n'
                '- **Adopted ticket.** You picked the ticket up yourself.\n')
        self.write(MODE + '/playbooks/work-a-ticket.md', bold)
        result = self.check()
        self.assertEqual(self.findings(result, 1), [])
        self.assert_status(result, 0)
        self.write(MODE + '/playbooks/work-a-ticket.md',
                   bold.replace('- **Adopted ticket.**', '- Adopted ticket.'))
        result = self.check()
        self.assert_status(result, 1)
        self.assertRegex(
            result.stdout,
            r'(?m)^(?!report: ).*: class 1 mmw work-a-ticket#Adopted ticket has no step or section ')
        # ### is an anchor the pointer regex must refuse. A plain list item is not an anchor.
        self.write(MODE + '/playbooks/work-a-ticket.md', '### Adopted ticket\n')
        result = self.check()
        self.assert_status(result, 1)
        self.assertRegex(
            result.stdout,
            r'(?m)^(?!report: ).*: class 1 mmw work-a-ticket#Adopted ticket has no step or section ')

    def test_wiring_registered_playbook_without_route_is_pending(self):
        name = 'work-a-ticket.md'
        self.write(MODE + '/playbooks/' + name, '#### Get reviewed\n')
        result = self.check()
        self.assertRegex(result.stdout, r'class 7 pending route for ' + re.escape(name))
        sys.path.insert(0, str(LIB))
        try:
            import check_wiring
        finally:
            sys.path.remove(str(LIB))
        fails = check_wiring.CLASS_POLICY[7].pending.fails
        if fails:
            self.assert_status(result, 1)
            self.assertNotRegex(result.stdout, r'(?m)^report: .*class 7 pending route for ' + re.escape(name))
        else:
            self.assert_status(result, 0)
            self.assertRegex(result.stdout, r'(?m)^report: .*class 7 pending route for ' + re.escape(name))

    def test_wiring_unregistered_playbook_without_route_fails(self):
        name = 'side-quest.md'
        self.write(MODE + '/playbooks/' + name, '#### Get reviewed\n')
        result = self.check()
        self.assert_status(result, 1)
        self.assertRegex(
            result.stdout,
            r'(?m)^(?!report: ).*class 7 ' + re.escape(name) + r' has 0 routing rows; expected 1')
