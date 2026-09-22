#!/usr/bin/env python3
"""命令行入口测试（静默抽歌、参数解析、歌单解析、退出码）。"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import cli  # noqa: E402
import paths  # noqa: E402


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rss_cli_")
        paths.set_data_root(os.path.join(self.tmp, "main_data"))
        from main import initialize_system

        initialize_system(quiet=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, argv):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = cli.main(argv)
        return code, buffer.getvalue()

    def test_default_is_silent(self):
        args = cli.build_parser().parse_args([])
        self.assertFalse(args.gui)
        self.assertEqual(args.count, 1)

    def test_gui_flag_parsed(self):
        args = cli.build_parser().parse_args(["--gui"])
        self.assertTrue(args.gui)

    def test_resolve_playlist(self):
        self.assertEqual(cli.resolve_playlist("default"), "default")
        self.assertEqual(cli.resolve_playlist("默认歌单"), "default")
        self.assertEqual(cli.resolve_playlist(None), "default")
        self.assertIsNone(cli.resolve_playlist("不存在的歌单"))

    def test_headless_default_outputs_one_song(self):
        code, out = self._run([])
        self.assertEqual(code, 0)
        self.assertTrue(out.strip())

    def test_headless_json(self):
        code, out = self._run(["--json"])
        self.assertEqual(code, 0)
        data = json.loads(out.strip().splitlines()[-1])
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["playlist"], "default")
        self.assertTrue(data["songs"][0]["song_name"])

    def test_count_and_no_save(self):
        code, out = self._run(["-n", "3", "--quiet", "--no-save"])
        self.assertEqual(code, 0)
        names = [line for line in out.strip().splitlines() if line.strip()]
        self.assertEqual(len(names), 3)

    def test_unknown_playlist_returns_error(self):
        code, _ = self._run(["-p", "nope"])
        self.assertEqual(code, 1)

    def test_list_playlists(self):
        code, out = self._run(["--list-playlists"])
        self.assertEqual(code, 0)
        self.assertIn("default", out)

    def test_json_jump_overrides_do_not_crash(self):
        code, out = self._run(["--no-save", "--jump-delay", "0", "--jump-mode", "search", "--json"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out.strip().splitlines()[-1])["songs"])


if __name__ == "__main__":
    unittest.main()
