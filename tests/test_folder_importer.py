#!/usr/bin/env python3
"""文件夹批量导入测试：文件名解析、扫描、导入。"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import paths  # noqa: E402


class TestParseName(unittest.TestCase):
    @staticmethod
    def _p(raw, artist_first=True, known=None):
        from folder_importer import parse_name

        return parse_name(raw, artist_first, known or set())

    def test_common_formats(self):
        cases = [
            ("周杰伦 - 晴天", True, "晴天", "周杰伦"),
            ("晴天 - 周杰伦", False, "晴天", "周杰伦"),
            ("01. 周杰伦 - 晴天", True, "晴天", "周杰伦"),
            ("01 - 周杰伦 - 晴天", True, "晴天", "周杰伦"),
            ("周杰伦-晴天", True, "晴天", "周杰伦"),
            ("周杰伦《晴天》", True, "晴天", "周杰伦"),
            ("[周杰伦] 晴天", True, "晴天", "周杰伦"),
            ("晴天 (周杰伦)", True, "晴天", "周杰伦"),
            ("晴天", True, "晴天", ""),
            ("2002年的第一场雪", True, "2002年的第一场雪", ""),
        ]
        for raw, artist_first, song, artist in cases:
            got = self._p(raw, artist_first)
            self.assertEqual((got[0], got[1]), (song, artist), f"文件名: {raw}")

    def test_known_artist_corrects_swap(self):
        song, artist, note = self._p("晴天 - 周杰伦", True, {"周杰伦", "朴树"})
        self.assertEqual((song, artist), ("晴天", "周杰伦"))
        self.assertEqual(note, "已知歌手校正")

    def test_order_toggle(self):
        self.assertEqual(self._p("甲 - 乙", True)[:2], ("乙", "甲"))
        self.assertEqual(self._p("甲 - 乙", False)[:2], ("甲", "乙"))


class TestScanAndImport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rss_folder_")
        paths.set_data_root(os.path.join(self.tmp, "main_data"))
        from main import initialize_system

        initialize_system(quiet=True)
        self.music = os.path.join(self.tmp, "music")
        os.makedirs(self.music)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scan_only_audio(self):
        from folder_importer import scan_folder

        for name in ("周杰伦 - 晴天.mp3", "周杰伦 - 晴天.lrc", "朴树 - 平凡之路.flac"):
            open(os.path.join(self.music, name), "w", encoding="utf-8").close()

        files = scan_folder(self.music)
        self.assertEqual(len(files), 2)
        self.assertTrue(any(f["song_name"] == "晴天" and f["artist"] == "周杰伦" for f in files))

    def test_import_stores_local_path(self):
        from folder_importer import import_into_playlist, scan_folder
        from song_manager import load_songs

        path = os.path.join(self.music, "测试手 - 测试歌.mp3")
        open(path, "w", encoding="utf-8").close()

        added = import_into_playlist("default", scan_folder(self.music))
        self.assertEqual(added, 1)

        stored = [s for s in load_songs("default") if s["song_name"] == "测试歌"][0]
        self.assertEqual(stored["local_path"], path)

    def test_import_new_playlist_and_dedupe(self):
        from folder_importer import import_as_new_playlist, import_into_playlist, scan_folder

        open(os.path.join(self.music, "周杰伦 - 晴天.mp3"), "w", encoding="utf-8").close()
        files = scan_folder(self.music)

        playlist_id, count = import_as_new_playlist("导入测试", self.music, files)
        self.assertEqual(count, 1)
        self.assertEqual(import_into_playlist(playlist_id, files), 0)


if __name__ == "__main__":
    unittest.main()
