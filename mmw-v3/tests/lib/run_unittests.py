"""Discover test_*.py under a directory, optionally filter by -k, run unittest.

Usage: python run_unittests.py <dir> <pattern>

<pattern> is empty for the whole suite, or the same substring / glob
python3 -m unittest -k accepts. A caller that needs an extra case on the
suite (ui-acceptance's MMW_FORCE_SKIP injection) imports `discover` and
`run` and adds it before `run`.

Prints `ran <n> skipped <n>` on stdout. A skip count other than 0, a run
count of 0, or a failed test exits 1 and does not return success to the
caller; the suite's run.sh then withholds `all passed`.
"""
import sys
import unittest


def discover(here, name_pattern):
    loader = unittest.defaultTestLoader
    if name_pattern:
        if "*" not in name_pattern:
            name_pattern = f"*{name_pattern}*"
        loader.testNamePatterns = [name_pattern]
    return loader.discover(here, pattern="test_*.py")


def run(suite):
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    ran = result.testsRun
    skipped = len(result.skipped)
    print(f"ran {ran} skipped {skipped}")
    if skipped:
        print(f"refusing: skipped {skipped}", file=sys.stderr)
        return 1
    if ran < 1:
        print("refusing: ran 0", file=sys.stderr)
        return 1
    if not result.wasSuccessful():
        print("failures above", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run(discover(sys.argv[1], sys.argv[2])))
