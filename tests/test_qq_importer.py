#!/usr/bin/env python3
"""QQ 歌单导入测试（不联网，全部用假数据 / 打桩）。"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import paths  # noqa: E402


class TestQQImporter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rss_qq_")
        paths.set_data_root(os.path.join(self.tmp, "main_data"))
        from main import initialize_system

        initialize_system()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_extract_playlist_id(self):
        from qq_importer import extract_playlist_id

        self.assertEqual(extract_playlist_id("123456"), "123456")
        self.assertEqual(
            extract_playlist_id("https://y.qq.com/n/ryqq_v2/playlist/98765"), "98765"
        )

    def test_import_and_dedup(self):
        import qq_importer
        from song_manager import load_songs

        fake = [
            {"song_name": "晴天", "artist": "周杰伦", "url": "https://y.qq.com/x"},
            {"song_name": "新歌", "artist": "某歌手", "url": ""},
        ]
        qq_importer.fetch_qq_playlist = lambda playlist_id, timeout=15: list(fake)

        # 新建歌单导入
        pid, count = qq_importer.import_qq_playlist("555", new_playlist_name="QQ导入")
        self.assertEqual(count, 2)
        self.assertEqual(len(load_songs(pid)), 2)

        # 再同步一次：都已存在，应全部去重
        _, added = qq_importer.import_qq_playlist("555", target_playlist_id=pid)
        self.assertEqual(added, 0)
        self.assertEqual(len(load_songs(pid)), 2)

        # 对方歌单新增一首后，再同步应只加 1 首
        fake.append({"song_name": "又一首", "artist": "歌手丙", "url": ""})
        qq_importer.fetch_qq_playlist = lambda playlist_id, timeout=15: list(fake)
        _, added = qq_importer.import_qq_playlist("555", target_playlist_id=pid)
        self.assertEqual(added, 1)
        self.assertEqual(len(load_songs(pid)), 3)

    def test_sync_requires_config(self):
        import qq_importer

        with self.assertRaises(RuntimeError):
            qq_importer.sync_qq_playlist(verbose=False)


if __name__ == "__main__":
    unittest.main()
