from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "dispatch" / "scripts" / "ghlist.py"
spec = importlib.util.spec_from_file_location("ghlist_under_test", SCRIPT)
ghlist = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ghlist)


def response(status: int, rows=None, etag=None, next_url=None):
    headers = [f"HTTP/2 {status} {'OK' if status == 200 else 'Not Modified'}"]
    if etag:
        headers.append(f"ETag: {etag}")
    if next_url:
        headers.append(f'Link: <{next_url}>; rel="next"')
    body = "" if rows is None else json.dumps(rows)
    return (0 if status == 200 else 1, "\n".join(headers) + "\n\n" + body, "")


class TwoPageGh:
    def __init__(self):
        self.calls = []
        self.first = "repos/o/r/issues/1/comments?per_page=100"
        self.second = "https://api.github.test/repos/o/r/issues/1/comments?per_page=100&page=2"

    def __call__(self, args):
        self.calls.append(args)
        url = args[2]
        tag = '"one"' if url == self.first else '"two"'
        if f"If-None-Match: {tag}" in args:
            return response(304)
        return response(200, [{"id": 1 if url == self.first else 2}], tag,
                        self.second if url == self.first else None)


class ConditionalListReaderTest(unittest.TestCase):
    def test_second_read_sends_each_pages_etag(self):
        gh = TwoPageGh()
        reader = ghlist.ConditionalListReader(gh)
        reader.read(gh.first)
        reader.read(gh.first)
        self.assertEqual([call[2] for call in gh.calls],
                         [gh.first, gh.second, gh.first, gh.second])
        self.assertIn('If-None-Match: "one"', gh.calls[2])
        self.assertIn('If-None-Match: "two"', gh.calls[3])

    def test_not_modified_returns_the_cached_list(self):
        gh = TwoPageGh()
        reader = ghlist.ConditionalListReader(gh)
        first = reader.read(gh.first)
        self.assertEqual(reader.read(gh.first), first)

    def test_full_last_page_is_read_again(self):
        first = "repos/o/r/issues/1/comments?per_page=100"
        second = "https://api.github.test/comments?page=2&per_page=100"
        calls = []

        def gh(args):
            calls.append(args)
            if args[2] == second:
                return response(200, [{"id": 101}], '"second"')
            if 'If-None-Match: "full"' in args:
                return response(304)
            rows = [{"id": n} for n in range(1, 101)]
            return response(200, rows, '"full"', second if len(calls) > 1 else None)

        reader = ghlist.ConditionalListReader(gh)
        self.assertEqual(len(reader.read(first)), 100)
        self.assertEqual(len(reader.read(first)), 101)
        self.assertNotIn('If-None-Match: "full"', calls[1])
        self.assertEqual(calls[2][2], second)

    def test_not_modified_without_a_cached_page_fails(self):
        reader = ghlist.ConditionalListReader(lambda args: response(304))
        with self.assertRaisesRegex(ghlist.ListReadError, "304 without a cached page"):
            reader.read("repos/o/r/issues/1/comments?per_page=100")

    def test_failed_read_names_the_address(self):
        address = "repos/o/r/issues/1/comments?per_page=100"
        failures = [
            lambda args: (1, "HTTP/2 502 Bad Gateway\n\n", "bad gateway"),
            lambda args: (0, "HTTP/2 200 OK\n\nnot-json", ""),
            lambda args: (0, "HTTP/2 200 OK\n\n{}", ""),
        ]
        for index, gh in enumerate(failures):
            with self.subTest(gh=gh):
                with self.assertRaises(ghlist.ListReadError) as caught:
                    ghlist.ConditionalListReader(gh).read(address)
                self.assertIn(address, str(caught.exception))
                if index == 0:
                    self.assertTrue("HTTP 502" in str(caught.exception)
                                    or "gh exited 1" in str(caught.exception))

    def test_counts_billed_and_not_modified(self):
        gh = TwoPageGh()
        reader = ghlist.ConditionalListReader(gh)
        self.assertEqual(reader.read(gh.first), [{"id": 1}, {"id": 2}])
        self.assertEqual(reader.read(gh.first), [{"id": 1}, {"id": 2}])
        self.assertEqual(reader.reads, {"billed": 2, "not_modified": 2})

    def test_a_page_without_an_etag_is_read_again(self):
        calls = []

        def gh(args):
            calls.append(args)
            return response(200, [{"id": 1}], None)

        reader = ghlist.ConditionalListReader(gh)
        address = "repos/o/r/issues/1/comments?per_page=100"
        self.assertEqual(reader.read(address), [{"id": 1}])
        self.assertEqual(reader.read(address), [{"id": 1}])
        self.assertFalse(any("If-None-Match:" in value for value in calls[1]))


if __name__ == "__main__":
    unittest.main()
