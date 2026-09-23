#!/usr/bin/env python3
"""自动跳转测试：URL 占位符、自带链接优先级、优先搜索开关。"""

import os
import shutil
import sys
import tempfile
import unittest
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import auto_jump_manager  # noqa: E402
import paths  # noqa: E402


class TestExpandUrl(unittest.TestCase):
    def test_placeholders(self):
        song = {"song_name": "晴天", "artist": "周杰伦"}
        url = auto_jump_manager.expand_url(
            "https://search.bilibili.com/all?keyword={query}&s={song}&a={artist}", song
        )
        self.assertEqual(url, "https://search.bilibili.com/all?keyword=" + quote("晴天 周杰伦")
                         + "&s=" + quote("晴天") + "&a=" + quote("周杰伦"))

    def test_empty_template(self):
        self.assertEqual(auto_jump_manager.expand_url("", {"song_name": "x"}), "")


class TestAutoJump(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rss_jump_")
        paths.set_data_root(os.path.join(self.tmp, "main_data"))
        from main import initialize_system

        initialize_system(quiet=True)
        self.opened = []
        self._real_open = auto_jump_manager.webbrowser.open
        auto_jump_manager.webbrowser.open = lambda url: self.opened.append(url)

    def tearDown(self):
        auto_jump_manager.webbrowser.open = self._real_open
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _config(self, **overrides):
        config = {
            "enabled": True,
            "mode": "search",
            "custom_url": "",
            "delay": 0,
            "prefer_search": False,
        }
        config.update(overrides)
        return config

    def test_song_url_wins_by_default(self):
        song = {"song_name": "晴天", "artist": "周杰伦", "url": "https://y.qq.com/song/x"}
        auto_jump_manager.auto_jump(song, self._config(), verbose=False)
        self.assertEqual(self.opened, ["https://y.qq.com/song/x"])

    def test_prefer_search_ignores_song_url(self):
        song = {"song_name": "晴天", "artist": "周杰伦", "url": "https://y.qq.com/song/x"}
        auto_jump_manager.auto_jump(song, self._config(prefer_search=True), verbose=False)
        self.assertEqual(len(self.opened), 1)
        self.assertIn("search.bilibili.com", self.opened[0])
        self.assertIn(quote("晴天 周杰伦"), self.opened[0])

    def test_custom_url_placeholder(self):
        song = {"song_name": "晴天", "artist": "周杰伦", "url": "https://y.qq.com/song/x"}
        config = self._config(
            mode="custom",
            custom_url="https://search.bilibili.com/all?keyword={query}",
            prefer_search=True,
        )
        auto_jump_manager.auto_jump(song, config, verbose=False)
        self.assertEqual(
            self.opened, ["https://search.bilibili.com/all?keyword=" + quote("晴天 周杰伦")]
        )

    def test_disabled_does_nothing(self):
        auto_jump_manager.auto_jump(
            {"song_name": "x", "url": "https://a"}, self._config(enabled=False), verbose=False
        )
        self.assertEqual(self.opened, [])

    def test_local_playback_disabled_by_default(self):
        from auto_jump_manager import try_local_playback

        self.assertFalse(try_local_playback({"song_name": "x", "local_path": __file__}, verbose=False))

    def test_local_playback_missing_file(self):
        from auto_jump_manager import try_local_playback
        from config_manager import get_local_playback, save_local_playback

        config = get_local_playback()
        config["enabled"] = True
        save_local_playback(config)

        song = {"song_name": "x", "local_path": "C:/nope/none.mp3"}
        self.assertFalse(try_local_playback(song, verbose=False))


if __name__ == "__main__":
    unittest.main()
