#!/usr/bin/env python3
"""核心功能测试：初始化、配置、歌单、防重复逻辑。"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import paths  # noqa: E402


class TempDataTestCase(unittest.TestCase):
    """每个用例把数据根目录指向临时目录，互不干扰。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rss_test_")
        paths.set_data_root(os.path.join(self.tmp, "main_data"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestConfig(TempDataTestCase):
    def test_deep_merge(self):
        from config_manager import deep_merge

        base = {"a": 1, "b": {"c": 2, "d": 3}}
        merged = deep_merge(base, {"b": {"c": 9}, "e": 5})
        self.assertEqual(merged["b"]["c"], 9)
        self.assertEqual(merged["b"]["d"], 3)
        self.assertEqual(merged["e"], 5)
        # 原对象不被修改
        self.assertEqual(base["b"]["c"], 2)

    def test_initialize_creates_default_playlist(self):
        from main import initialize_system
        from config_manager import get_current_playlist_id, get_playlists
        from song_manager import load_songs

        initialize_system()
        playlists = get_playlists()
        self.assertIn("default", playlists)
        self.assertEqual(get_current_playlist_id(), "default")
        songs = load_songs("default")
        self.assertEqual(len(songs), 5)
        # 每首歌都有 UUID
        for song in songs:
            self.assertTrue(song["id"])

    def test_initialize_is_idempotent(self):
        from main import initialize_system
        from song_manager import load_songs

        initialize_system()
        initialize_system()
        self.assertEqual(len(load_songs("default")), 5)


class TestSongs(TempDataTestCase):
    def setUp(self):
        super().setUp()
        from main import initialize_system

        initialize_system()

    def test_normalize_legacy_fields(self):
        from song_manager import normalize_song

        song, changed = normalize_song({"song_name": "旧歌", "url_list": ["http://a"]})
        self.assertTrue(changed)
        self.assertEqual(song["url"], "http://a")
        self.assertNotIn("url_list", song)
        self.assertTrue(song["id"])

    def test_statistics(self):
        from song_manager import get_songs_statistics, load_songs

        stats = get_songs_statistics(load_songs("default"))
        self.assertEqual(stats["valid_songs"], 5)
        self.assertEqual(stats["invalid_songs"], 0)
        self.assertEqual(sum(stats["requesters"].values()), 5)

    def test_add_and_save(self):
        from song_manager import append_song, load_songs, new_song_id

        append_song(
            "default",
            {
                "id": new_song_id(),
                "song_name": "测试曲",
                "artist": "测试手",
                "url": "",
                "requested_by": "阿澈",
                "created_at": "2026/01/01 00:00:00",
                "last_modified": "2026/01/01 00:00:00",
            },
        )
        songs = load_songs("default")
        self.assertEqual(len(songs), 6)
        self.assertIn("测试曲", [song["song_name"] for song in songs])


class TestDuplicatePrevention(TempDataTestCase):
    def setUp(self):
        super().setUp()
        from main import initialize_system

        initialize_system()

    def _set(self, **fields):
        from config_manager import get_prevention, save_prevention

        cfg = get_prevention("default")
        cfg.update(fields)
        save_prevention("default", cfg)

    def test_cycle_no_repeat_until_all_played(self):
        from song_manager import get_random_song, load_songs

        self._set(enabled=True, mode="cycle", avoid_immediate_repeat=False, reset_on_all_played=True)
        seen = []
        for _ in range(5):
            song = get_random_song("default")
            self.assertIsNotNone(song)
            seen.append(song["id"])
        self.assertEqual(len(set(seen)), 5)  # 五首各不相同
        # 第六次会重置并继续
        self.assertIsNotNone(get_random_song("default"))

    def test_time_window_blocks_repeat(self):
        from song_manager import get_random_song

        self._set(
            enabled=True,
            mode="time_window",
            time_window_minutes=60,
            avoid_immediate_repeat=False,
            reset_on_all_played=True,
        )
        seen = {get_random_song("default")["id"] for _ in range(5)}
        self.assertEqual(len(seen), 5)

    def test_time_window_without_reset_returns_none(self):
        from song_manager import get_random_song

        self._set(
            enabled=True,
            mode="time_window",
            time_window_minutes=60,
            avoid_immediate_repeat=False,
            reset_on_all_played=False,
        )
        for _ in range(5):
            self.assertIsNotNone(get_random_song("default"))
        self.assertIsNone(get_random_song("default"))

    def test_corrupt_record_is_skipped(self):
        from config_manager import get_prevention, save_prevention
        from song_manager import get_random_song

        self._set(enabled=True, mode="time_window", avoid_immediate_repeat=False)
        cfg = get_prevention("default")
        cfg["played_songs"] = [
            {"song_id": "不存在的id", "song_name": "幽灵", "play_time": "坏时间戳"},
            {"song_id": None, "song_name": "空id", "play_time": "2020-01-01 00:00:00"},
        ]
        save_prevention("default", cfg)
        song = get_random_song("default")  # 不应抛异常
        self.assertIsNotNone(song)

    def test_records_are_bounded(self):
        from config_manager import get_prevention
        from song_manager import get_random_song

        self._set(enabled=True, mode="time_window", time_window_minutes=60, avoid_immediate_repeat=False)
        # 注入一批早已过期的记录
        cfg = get_prevention("default")
        cfg["played_songs"] = [
            {"song_id": "x", "song_name": "旧", "play_time": "2000-01-01 00:00:00"}
        ]
        from config_manager import save_prevention

        save_prevention("default", cfg)
        get_random_song("default")
        self.assertLessEqual(len(get_prevention("default")["played_songs"]), 5)


class TestPlaylist(TempDataTestCase):
    def test_sanitize_and_unique_id(self):
        from playlist_manager import sanitize_id, unique_playlist_id

        self.assertEqual(sanitize_id("My Songs!"), "my_songs")
        self.assertEqual(sanitize_id("中文 歌单"), "中文_歌单")
        self.assertEqual(unique_playlist_id("default", existing={"default"}), "default_2")

    def test_ensure_playlist_files(self):
        from playlist_manager import ensure_playlist_files, register_playlist
        from song_manager import load_songs
        from requester_manager import load_requesters

        register_playlist("demo", "演示歌单")
        ensure_playlist_files("demo", songs=[], requesters=[{"name": "小满", "email": "", "notes": ""}])
        self.assertEqual(load_songs("demo"), [])
        self.assertEqual([r["name"] for r in load_requesters("demo")], ["小满"])


if __name__ == "__main__":
    unittest.main()
