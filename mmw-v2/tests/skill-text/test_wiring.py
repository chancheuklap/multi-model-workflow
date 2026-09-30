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
DISPATCH = 'mmw-v2/skills/dispatch'


class Wiring(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mmw-wiring-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write('mmw-v2/skills.txt', 'self/example\nself/dispatch\nself/verify-ticket\n')
        self.fixture('locations.py', DISPATCH + '/scripts/locations.py')
        self.fixture('roles.json', DISPATCH + '/roles.json')

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
                dest = self.write(DISPATCH + '/scripts/' + name, content)
                resume = None
                if name == 'dispatch.sh':
                    resume = self.write(DISPATCH + '/references/night.md',
                                        '`bash scripts/dispatch.sh resume <n> "first\nsecond"`\n')
                result = self.check()
                self.assert_status(result, 1)
                self.assertRegex(result.stdout, (r'night.md' if resume else name) + r':\d+: class 8 ')
                dest.unlink()
                if resume:
                    resume.unlink()
        self.write(DISPATCH + '/scripts/dispatch.sh',
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
        self.write(DISPATCH + '/scripts/dispatch.sh',
                   'research_one() {\nnew_prompt="Research this.\nMore data."\n'
                   'session="$(start_session "$host" "$model" "$effort" "$cwd" "$new_prompt" "$title")"\n}\n')
        result = self.check()
        self.assert_status(result, 1)
        self.assertRegex(result.stdout, r'dispatch.sh:\d+: class 8 ')

    def test_wiring_path_literal_class(self):
        samples = [
            ('mmw-v2/board/example.py', (FIXTURES / 'class-10.py').read_text(), 'mmw-v2/skills/absent'),
            ('mmw-v2/board/example.py', 'target = "skills/absent/scripts"\n', 'mmw-v2/skills/absent/scripts'),
            (DISPATCH + '/scripts/example.py', 'target = HERE.parents[1] / "absent"\n', 'mmw-v2/skills/absent'),
            (DISPATCH + '/scripts/runners/example.sh', 'target="$(dirname "$HERE")/absent.py"\n', DISPATCH + '/scripts/absent.py'),
            (DISPATCH + '/scripts/example.sh', 'target="$SKILL_ROOT/scripts/absent.py"\n', DISPATCH + '/scripts/absent.py'),
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
            6: DISPATCH + '/scripts/relay.py',
            7: MODE + '/SKILL.md',
            9: MODE + '/SKILL.md',
            11: DISPATCH + '/scripts/dispatch.sh',
            12: DISPATCH + '/scripts/dispatch.sh',
        }
        target = targets[category]
        suffix = Path(target).suffix
        self.fixture(f'class-{category}{suffix}', target)
        if category == 5:
            self.write(MODE + '/principles/principle-evidence.md',
                       '---\nname: principle-evidence\ndescription: Apply when evidence is required.\n---\n# Evidence\n')
        if category == 7:
            self.write(MODE + '/playbooks/work-a-ticket.md',
                       '### Work\n\n1. **Claim.** Use the `example` skill.\n'
                       '2. **Get reviewed.** Use the `example` skill.\n')
        if category == 9:
            self.write('mmw-v2/skills.txt', 'self/example\nengineering/upstream-example\n')
            self.write('mmw-v2/upstream/skills/engineering/upstream-example/SKILL.md',
                       '---\nname: upstream-example\ndescription: Use when needed.\n'
                       'disable-model-invocation: true\n---\n# Upstream\n')

    def test_wiring_reported_classes(self):
        batches = {2: 'B1', 3: 'B2 end', 5: 'B1', 6: 'B2 end',
                   7: 'B1', 9: 'B1', 11: 'B2 end', 12: 'B2'}
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

    def test_wiring_pointer_class_targets(self):
        path = 'mmw-v2/skills/example/SKILL.md'
        self.write(path, '`mmw work-a-ticket#Claim`\n`mmw#Re-entry`\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertIn('pending work-a-ticket (not built yet)', result.stdout)
        self.write(MODE + '/playbooks/work-a-ticket.md', '### Work\n\n#### Claim\n\n#### Get reviewed\n')
        self.write(MODE + '/SKILL.md', '# MMW\n\n## Re-entry\n')
        self.assert_status(self.check(), 0)
        self.write(MODE + '/SKILL.md', '# MMW\n\n## Autonomy\n')
        self.assert_status(self.check(), 1)
        self.write(MODE + '/SKILL.md', '# MMW\n\n## Re-entry\n')
        self.write(MODE + '/playbooks/work-a-ticket.md', '### Claim\n\n#### Get reviewed\n')
        self.assert_status(self.check(), 1)
        self.write(MODE + '/playbooks/work-a-ticket.md', '1. **Claim.** Do the work.\n\n2. **Get reviewed.** Read the report.\n')
        self.assert_status(self.check(), 0)
        self.write(MODE + '/playbooks/work-a-ticket.md', '### Work\n\n#### Get reviewed\n')
        self.assert_status(self.check(), 1)
        self.write(MODE + '/imports.tsv', 'type\tpath\nplaybook\t' + MODE + '/playbooks/work-a-ticket.md\n')
        result = self.check()
        self.assert_status(result, 1)
        self.assertIn('imported playbook', result.stdout)
        (self.root / (MODE + '/imports.tsv')).unlink()
        (self.root / (MODE + '/playbooks/work-a-ticket.md')).unlink()
        self.write(DISPATCH + '/roles.json', '{"worker":{"playbook":"work-a-ticket","wakes":{"reviewer.reported":"Wrong"}}}')
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
        self.write(DISPATCH + '/scripts/dispatch.sh', 'new_one() {\nstart_session h m e cwd "Read /checkout/mmw-v2/skills/mmw/SKILL.md" title\n}\ncase "$1" in\n lonely) echo ok ;;\nesac\n')
        self.write('mmw-v2/board/example.py', 'target = "skills/dispatch/scripts"\n')
        self.write('mmw-v2/skills.txt', 'self/example\nengineering/upstream-example +model-invoked\n')
        self.write('mmw-v2/upstream/skills/engineering/upstream-example/SKILL.md', '# Upstream\n')
        result = self.check('--graph')
        self.assert_status(result, 0)
        categories = {int(line.rsplit(' : ', 1)[1]) for line in result.stdout.splitlines()}
        self.assertTrue({1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12} <= categories, result.stdout)
        self.assertIn('mmw-v2/skills/example/SKILL.md -> mmw work-a-ticket#Claim : 1', result.stdout)
        self.assertIn(MODE + '/SKILL.md -> ' + DISPATCH + '/scripts/dispatch.sh#lonely : 11', result.stdout)
        self.assertTrue(all(' -> ' in line and ' : ' in line for line in result.stdout.splitlines()), result.stdout)

    def test_wiring_unreadable_registry_exits_2(self):
        registry = self.root / (DISPATCH + '/scripts/locations.py')
        registry.unlink()
        result = self.check()
        self.assert_status(result, 2)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertIn('bash mmw-v2/install.sh --check', result.stdout)
        self.fixture('locations.py', MODE + '/scripts/locations.py')
        self.assert_status(self.check(), 0)
        self.write(DISPATCH + '/roles.json', 'not json')
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
        self.write(DISPATCH + '/scripts/statedir.py',
                   (LIB.parents[1] / 'skills/dispatch/scripts/statedir.py').read_text())
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
        file = self.root / (DISPATCH + '/scripts/locations.py')
        file.write_text(file.read_text() + "\nWHERE_ROWS = {'worker': {'fresh': {'step': 'Typo'}}}\n")
        result = self.check()
        self.assert_status(result, 1)
        self.assertIn('locations.py', result.stdout)

    def test_wiring_dispatch_nested_case_commands(self):
        self.write(DISPATCH + '/scripts/dispatch.sh',
                   'case "${1:-}" in\n first) case "$2" in foo) echo ok ;; esac ;;\n'
                   ' lonely) lonely_one ;;\nesac\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertRegex(result.stdout, r'class 11 lonely ')
        self.assertNotRegex(result.stdout, r'class 11 foo ')

    def test_wiring_added_start_prompt_with_continuation(self):
        self.write(DISPATCH + '/scripts/dispatch.sh',
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

    def test_wiring_frozen_paths_rejects_other_checkout(self):
        self.write('.mmw/installed-root', str(self.root / 'installed/mmw-v2'))
        self.write(DISPATCH + '/scripts/dispatch.sh',
                   'research_one() {\nprompt="Read /other/checkout/mmw-v2/skills/mmw/SKILL.md"\n'
                   'start_session "$host" "$model" "$effort" "$cwd" "$prompt" "$title"\n}\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertRegex(result.stdout, r'(?m)^report: .*: class 12 ')
        self.write(DISPATCH + '/scripts/dispatch.sh',
                   'research_one() {\nprompt="Read ' + str(self.root / 'installed/mmw-v2/skills/mmw/SKILL.md') + '"\n'
                   'start_session "$host" "$model" "$effort" "$cwd" "$prompt" "$title"\n}\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertNotRegex(result.stdout, r'(?m)^report: .*: class 12 ')

    def test_wiring_reference_commands_and_import_names(self):
        self.write(MODE + '/scripts/dispatch.sh', 'case "$1" in\n known) echo ok ;;\nesac\n')
        self.write(MODE + '/playbooks/work-a-ticket.md',
                   '#### Claim\n\nRun `scripts/dispatch.sh missing`.\n\n#### Get reviewed\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertRegex(result.stdout, r'(?m)^report: .*: class 2 .*missing')
        self.write(MODE + '/playbooks/work-a-ticket.md',
                   '#### Claim\n\nRun `scripts/dispatch.sh known`.\n\n#### Get reviewed\n')
        self.assertNotRegex(self.check().stdout, r'(?m)^report: .*: class 2 ')
        self.write(MODE + '/imports.tsv', 'type\tpath\nplaybook\t' + MODE + '/playbooks/imported.md\n')
        self.write(MODE + '/playbooks/imported.md', 'Use the old-skill skill.\n')
        self.assertRegex(self.check().stdout, r'(?m)^report: .*: class 2 .*old-skill')
        self.write('mmw-v2/skills/example/SKILL.md', '# Example\n')
        self.write(MODE + '/references/pstack-names.md', '| old-skill | example |\n')
        self.assertNotRegex(self.check().stdout, r'(?m)^report: .*: class 2 .*old-skill')

    def test_wiring_event_sources_and_duplicate_handlers(self):
        self.write(DISPATCH + '/roles.json', '{"night-orchestrator":{"playbook":"work-a-ticket","wakes":{"*":"Claim"}}}')
        self.write(MODE + '/playbooks/work-a-ticket.md', '#### Claim\nHandle the wake.\n')
        self.write(DISPATCH + '/scripts/watchdog.py',
                   'alerts = [\n' + ''.join('{"text":"watchdog: alert%d"},\n' % i for i in range(8)) + ']\n')
        self.write(DISPATCH + '/scripts/relay.py', 'RECOVERED = "relay.recovered"\n')
        self.write(DISPATCH + '/scripts/turn-guard.py', 'text = "MMW turn guard: held"\n')
        graph = self.check('--graph')
        self.assert_status(graph, 0)
        for event in ['relay.recovered', 'MMW turn guard:'] + [f'watchdog: alert{i}' for i in range(8)]:
            self.assertIn('night-orchestrator/' + event + ' -> ', graph.stdout)
        self.write(MODE + '/playbooks/work-a-ticket.md', '#### Claim\nHandle the wake.\n\n#### Claim\nHandle it again.\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertRegex(result.stdout, r'(?m)^report: .*: class 6 .*2 handlers')

    def test_wiring_combined_alert_template_and_fourth_start(self):
        self.write(DISPATCH + '/scripts/watchdog.py',
                   'alerts = [{"text":"watchdog: one"}, {"text":"watchdog: two"}]\n'
                   'text = "\\n".join(alert["text"] for alert in alerts)\n'
                   'send(runner, session, text)\n')
        self.assert_status(self.check(), 1)
        (self.root / (DISPATCH + '/scripts/watchdog.py')).unlink()
        self.write(DISPATCH + '/scripts/dispatch.sh',
                   'start_one() {\nprompt="Use the implement skill.\npacket"\n'
                   'start_session "$host" "$model" "$effort" "$cwd" "$prompt" "$title"\n'
                   'extra_prompt="Use the implement skill.\nnew kind"\n'
                   'start_session "$host" "$model" "$effort" "$cwd" "$extra_prompt" "$title"\n}\n')
        self.assert_status(self.check(), 1)

    def test_wiring_registry_mode_call_is_not_exempt(self):
        registry = self.root / (DISPATCH + '/scripts/locations.py')
        registry.write_text(registry.read_text() + '\nBAD = "mmw start 1 worker"\n')
        result = self.check()
        self.assert_status(result, 0)
        self.assertRegex(result.stdout, r'(?m)^report: .*locations.py:\d+: class 3 capability script calls a mode command directly$')

    def test_wiring_product_syntax_error_is_not_installation_failure(self):
        self.write('mmw-v2/board/page.py', 'def broken(:\n')
        result = self.check()
        self.assert_status(result, 1)
        self.assertIn('mmw-v2/board/page.py:1:', result.stdout)
        self.assertTrue(result.stdout.splitlines()[1].startswith('Next:'), result.stdout)
        self.assertTrue(result.stdout.splitlines()[2].startswith('Why:'), result.stdout)
        self.assertNotIn('install.sh --check', result.stdout)

    def test_wiring_resume_text_at_call_sites(self):
        self.write(DISPATCH + '/scripts/dispatch.sh',
                   'resume_one() {\n local text="$2"\n runner send "$ident" "$text"\n}\n')
        for path in (DISPATCH + '/references/night.md',
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
        self.write(DISPATCH + '/scripts/dispatch.sh',
                   'new_one() {\nstart_session h m e cwd "Read ' + str(installed / 'skills/mmw/SKILL.md') + '" title\n}\n')
        # Run the production path from a disposable checkout, never this machine's state.
        lib = self.root / 'mmw-v2/tests/lib'
        lib.mkdir(parents=True)
        for name in ('check_wiring.py', 'skill_text.py'):
            shutil.copy(LIB / name, lib / name)
        self.write(DISPATCH + '/scripts/statedir.py',
                   (LIB.parents[1] / 'skills/dispatch/scripts/statedir.py').read_text())
        env = {k: v for k, v in os.environ.items() if not k.startswith(('MMW_', 'NMEM_'))}
        env['MMW_HOME'] = str(state)
        result = subprocess.run([sys.executable, str(lib / 'check_wiring.py')],
                                env=env, capture_output=True, text=True)
        self.assert_status(result, 0)
        self.assertRegex(result.stdout, r'(?m)^report: .*: class 9 .*installation copy still has invocation switch$')
        self.assertNotRegex(result.stdout, r'(?m)^report: .*: class 12 ')
        isolated = self.check()
        self.assertNotIn('installation copy still has invocation switch', isolated.stdout)
        self.assertRegex(isolated.stdout, r'(?m)^report: .*: class 12 ')
