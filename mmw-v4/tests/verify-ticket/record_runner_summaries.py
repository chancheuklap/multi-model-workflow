import json
import os
import shlex
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DEST = Path(__file__).resolve().parents[2] / 'skills/verify-ticket/scripts/runner-summaries.json'


def record(runner, directory, args, success):
    command = (["uv", "run", "--with", "pytest==9.1.1", "python", "-m", "pytest"]
               if runner == "pytest" else
               ["npm", "exec", "--yes", "--package", "vitest@5.0.5", "--", "vitest", "run", "--globals"])
    env = {**os.environ, "NO_COLOR": "1", "TERM": "dumb"}
    env.pop("FORCE_COLOR", None)
    result = subprocess.run(command + args, cwd=directory, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    lines = result.stdout.splitlines()
    summary = next(line for line in reversed(lines)
                   if (" in " in line and line.rstrip('= ').endswith(('s', ')'))
                       if runner == "pytest" else
                       (line.strip().startswith("Tests ") or "No test files found" in line)))
    return {"command": shlex.join(command + args), "exit": result.returncode,
            "success": success, "summary": summary, "output": result.stdout}


def main():
    data = json.loads(DEST.read_text())
    with tempfile.TemporaryDirectory(prefix="mmw-runner-summaries-") as tmp:
        root = Path(tmp)
        (root / 'test_cases.py').write_text('''import time
import warnings
import pytest

def test_pass():
    assert True

def test_warning():
    warnings.warn("recorded warning", UserWarning)

@pytest.mark.xfail(reason="recorded expected failure")
def test_xfail():
    assert False

@pytest.mark.xfail(reason="recorded unexpected pass")
def test_xpass():
    assert True

@pytest.mark.skip(reason="recorded skip")
def test_skip():
    pass

def test_fail():
    assert False

@pytest.fixture
def broken():
    raise RuntimeError("recorded setup error")

def test_error(broken):
    pass

def test_long():
    time.sleep(61)
''')
        (root / 'test_subtests.py').write_text('''import pytest

def test_subtests(subtests):
    for number in (1, 2):
        with subtests.test(number=number):
            assert number > 0

def test_subtest_failure(subtests):
    with subtests.test():
        assert False

def test_subtest_skipped(subtests):
    with subtests.test():
        pytest.skip("recorded subtest skip")
''')
        (root / 'empty').mkdir()
        (root / 'cases.test.js').write_text('''test('selected', () => expect(1).toBe(1));
for (let n = 0; n < 5; n++) test(`other ${n}`, () => expect(1).toBe(1));
''')
        (root / 'failed.test.js').write_text("test('failure', () => expect(1).toBe(2));\ntest('pass', () => expect(1).toBe(1));\n")
        (root / 'only-failed.test.js').write_text("test('failure', () => expect(1).toBe(2));\n")
        (root / 'todo.test.js').write_text("test('pass', () => expect(1).toBe(1));\ntest.todo('later');\n")
        (root / 'todo-skip.test.js').write_text("test('pass', () => expect(1).toBe(1));\ntest.todo('later');\ntest.skip('skip', () => {});\n")
        (root / 'todo-only.test.js').write_text("test.todo('later');\n")
        (root / 'skip-only.test.js').write_text("test.skip('skip', () => {});\n")
        cases = []
        for quiet in ([], ['-q']):
            for selector, success in [('pass or warning or xfail or xpass', True),
                                      ('xfail', True), ('xpass', True),
                                      ('pass or skip', False), ('fail or pass', False),
                                      ('error or pass', False), ('skip', False),
                                      ('long', True)]:
                cases.append(('pytest', root, quiet + ['test_cases.py', '-k', selector], success))
            for name in ('pass', 'warning', 'xfail', 'xpass'):
                cases.append(('pytest', root, quiet + [f'test_cases.py::test_{name}'], True))
            cases.append(('pytest', root, quiet + ['empty'], False))
        for quiet in ([], ['-q']):
            cases.append(('pytest', root, quiet + ['test_cases.py::test_long'], True))
            for name, success in [('subtests', True), ('subtest_failure', False),
                                  ('subtest_skipped', False)]:
                if quiet or name != 'subtest_skipped':
                    cases.append(('pytest', root, quiet + [f'test_subtests.py::test_{name}'], success))
        cases += [('vitest', root, ['cases.test.js'], True),
                  ('vitest', root, ['cases.test.js', '-t', 'selected'], True),
                  ('vitest', root, ['cases.test.js', '-t', 'no-matching-test'], False),
                  ('vitest', root, ['failed.test.js'], False),
                  ('vitest', root, ['only-failed.test.js'], False),
                  ('vitest', root, ['missing.test.js'], False),
                  ('vitest', root, ['todo.test.js'], True),
                  ('vitest', root, ['todo-skip.test.js'], True),
                  ('vitest', root, ['todo-only.test.js'], False),
                  ('vitest', root, ['skip-only.test.js'], False)]
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda case: record(*case), cases))
        for runner, version in [('pytest', '9.1.1'), ('vitest', '5.0.5')]:
            data[runner]['version'] = version
            data[runner]['fixture_source'] = 'mmw-v4/tests/verify-ticket/record_runner_summaries.py'
            data[runner]['samples'] = [result for case, result in zip(cases, results) if case[0] == runner]
        DEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        for runner in data:
            print(f"{runner}: recorded {len(data[runner]['samples'])} summaries")


if __name__ == '__main__':
    main()
