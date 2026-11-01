from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'board/codeversion.py'
EXPECTED=(
    'verify-ticket/scripts/events.py','verify-ticket/scripts/issue_tree.py',
    'dispatch/scripts/ghlist.py','dispatch/scripts/models.py','dispatch/scripts/statedir.py',
    'dispatch/scripts/tracker.py','dispatch/roles.json',
)


def load(path):
    spec=importlib.util.spec_from_file_location('tested_board_codeversion',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class CodeVersionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        board=self.root/'board';board.mkdir()
        (board/'codeversion.py').write_bytes(SOURCE.read_bytes())
        (board/'gates.py').write_text('marker=1\n')
        (board/'page').mkdir();(board/'page/index.html').write_text('first page')
        for relative in EXPECTED:
            path=self.root/'tools'/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('initial\n')
        self.module=load(board/'codeversion.py')

    def test_v5_once_loaded_consumers_are_real_adjacent_files(self):
        module=load(SOURCE)
        self.assertEqual(set(module.LOADED),{ROOT/'tools'/relative for relative in EXPECTED})
        self.assertTrue(all(p.is_file() for p in module.LOADED))

    def test_a_change_requires_two_agreeing_reads(self):
        watch=self.module.Watch();self.assertFalse(watch.changed())
        path=self.root/'board/gates.py';path.write_text('second\n')
        self.assertFalse(watch.changed());self.assertTrue(watch.changed())

    def test_a_second_change_resets_the_settling_read(self):
        watch=self.module.Watch();path=self.root/'board/gates.py'
        path.write_text('second\n');self.assertFalse(watch.changed())
        path.write_text('third\n');self.assertFalse(watch.changed());self.assertTrue(watch.changed())

    def test_events_roles_and_origin_resolver_changes_restart_the_consumer(self):
        for relative in ('verify-ticket/scripts/events.py','dispatch/roles.json','dispatch/scripts/tracker.py'):
            with self.subTest(file=relative):
                watch=self.module.Watch();path=self.root/'tools'/relative
                path.write_text(path.read_text()+'changed\n')
                self.assertFalse(watch.changed());self.assertTrue(watch.changed())

    def test_page_edits_and_unchanged_source_content_need_no_restart(self):
        watch=self.module.Watch();(self.root/'board/page/index.html').write_text('second page')
        (self.root/'board/gates.py').touch()
        self.assertFalse(watch.changed());self.assertFalse(watch.changed())


if __name__=='__main__':unittest.main()
