#!/usr/bin/env python3
"""
旧数据迁移：把旧版 JSON 歌曲文件转换为新版 YAML 歌单。

旧版格式（songs_list.json）:
    {"songs": [{"song_name": ..., "artist": ..., "url_list": [...], "requested_by": ...}, ...]}

用法:
    python scripts/migrate_json_to_yaml.py <旧songs_list.json> <目标歌单名>
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from playlist_manager import ensure_playlist_files, register_playlist, unique_playlist_id  # noqa: E402
from song_manager import normalize_song  # noqa: E402


def convert(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw_songs = data.get("songs") if isinstance(data, dict) else data
    if not isinstance(raw_songs, list):
        raise ValueError("文件里没有找到 songs 列表")
    songs = []
    for raw in raw_songs:
        if isinstance(raw, dict):
            song, _ = normalize_song(raw)
            song["requested_by"] = song.get("requested_by") or "导入"
            songs.append(song)
    return songs


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    json_path, playlist_name = sys.argv[1], sys.argv[2]
    if not os.path.exists(json_path):
        print(f"文件不存在: {json_path}")
        return 1

    songs = convert(json_path)
    playlist_id = unique_playlist_id(playlist_name)
    register_playlist(playlist_id, playlist_name, "由旧版 JSON 迁移")
    ensure_playlist_files(playlist_id, songs=songs)
    print(f"✅ 已迁移 {len(songs)} 首歌曲到歌单「{playlist_name}」(ID: {playlist_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
