"""Discover test_*.py under a directory, optionally filter by -k, run unittest.

Usage: python run_unittests.py <dir> <pattern> [--force-skip]

<pattern> is empty for the whole suite, or the same substring / glob
python3 -m unittest -k accepts. --force-skip adds one skipped test so a
runner can prove it refuses a skip count other than 0.

Prints `ran <n> skipped <n>` on stdout. A skip count other than 0, a run
count of 0, or a failed test exits 1 and does not return success to the
caller; the suite's run.sh then withholds `all passed`.
"""
import sys
import unittest

here = sys.argv[1]
name_pattern = sys.argv[2]
force_skip = "--force-skip" in sys.argv[3:]
loader = unittest.defaultTestLoader
if name_pattern:
    if "*" not in name_pattern:
        name_pattern = f"*{name_pattern}*"
    loader.testNamePatterns = [name_pattern]
suite = loader.discover(here, pattern="test_*.py")
if force_skip:
    class _ForceSkip(unittest.TestCase):
        def test_mmw_force_skip(self):
            self.skipTest("MMW_FORCE_SKIP=1")
    suite.addTest(_ForceSkip("test_mmw_force_skip"))
result = unittest.TextTestRunner(verbosity=1).run(suite)
ran = result.testsRun
skipped = len(result.skipped)
print(f"ran {ran} skipped {skipped}")
if skipped:
    print(f"refusing: skipped {skipped}", file=sys.stderr)
    sys.exit(1)
if ran < 1:
    print("refusing: ran 0", file=sys.stderr)
    sys.exit(1)
if not result.wasSuccessful():
    print("failures above", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
