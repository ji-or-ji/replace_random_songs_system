"""
歌单管理：创建 / 删除 / 切换 / 查看 / 导入。
"""

import datetime
import json
import os
import re
import shutil

from config_manager import (
    delete_playlist_entry,
    get_current_playlist_id,
    get_playlists,
    playlist_name,
    register_playlist,
    set_current_playlist,
)
from history_manager import record_operation
from paths import (
    ensure_dir,
    playlist_dir,
    playlist_operate_history_file,
    playlist_play_history_file,
    playlist_requesters_file,
    playlist_songs_file,
)
from song_manager import load_songs, normalize_song, save_songs
from requester_manager import save_requesters
from storage import load_yaml, save_yaml


def sanitize_id(name):
    """把歌单名转成安全的目录名。"""
    slug = (name or "").strip().lower()
    slug = re.sub(r"\s+", "_", slug)
    slug = re.sub(r"[^0-9a-z_\u4e00-\u9fff\-]", "", slug)
    return slug or "playlist"


def unique_playlist_id(name, existing=None):
    existing = set(existing if existing is not None else get_playlists().keys())
    base = sanitize_id(name)
    candidate = base
    index = 2
    while candidate in existing:
        candidate = f"{base}_{index}"
        index += 1
    return candidate


def ensure_playlist_files(playlist_id, songs=None, requesters=None):
    """创建歌单的数据文件（幂等），返回目录路径。"""
    ensure_dir(playlist_dir(playlist_id))
    ensure_dir(os.path.join(playlist_dir(playlist_id), "music_files"))
    songs = songs or []
    requesters = requesters or []
    save_yaml(playlist_songs_file(playlist_id), {"songs": songs})
    save_yaml(playlist_requesters_file(playlist_id), {"requesters": requesters})
    for path in (
        playlist_play_history_file(playlist_id),
        playlist_operate_history_file(playlist_id),
    ):
        if not os.path.exists(path):
            open(path, "a", encoding="utf-8").close()
    return playlist_dir(playlist_id)


def create_playlist(create_files=True):
    """交互式创建空白歌单，返回新的歌单 ID（失败返回 None）。"""
    print("\n🎵 创建歌单")
    print("=" * 30)
    while True:
        name = input("请输入歌单名称: ").strip()
        if name:
            break
        print("歌单名称不能为空，请重新输入")
    description = input("请输入歌单描述（可留空）: ").strip()

    playlist_id = unique_playlist_id(name)
    register_playlist(playlist_id, name, description)
    if create_files:
        ensure_playlist_files(playlist_id)
    record_operation("创建歌单", f"歌单: {name}", playlist_id=playlist_id)
    print(f"✅ 已创建歌单: {name}（ID: {playlist_id}）")
    return playlist_id


def delete_playlist():
    playlists = get_playlists()
    if len(playlists) <= 1:
        print("❌ 至少需要保留一个歌单")
        return
    current = get_current_playlist_id()

    print("\n🎵 删除歌单")
    print("=" * 30)
    items = list(playlists.items())
    for index, (pid, entry) in enumerate(items, 1):
        marker = "（当前）" if pid == current else ""
        print(f"{index}. {entry['name']} - {entry.get('song_count', 0)}首歌曲{marker}")
    try:
        choice = int(input("\n请选择要删除的歌单编号: ").strip())
    except ValueError:
        print("❌ 请输入有效的数字")
        return
    if not (1 <= choice <= len(items)):
        print("❌ 无效的选择")
        return

    pid, entry = items[choice - 1]
    if pid == current:
        print("❌ 不能删除当前正在使用的歌单，请先切换")
        return
    if input(f"确定删除歌单 '{entry['name']}' 吗？此操作不可恢复！(y/N): ").strip().lower() != "y":
        print("取消删除")
        return

    delete_playlist_entry(pid)
    target_dir = playlist_dir(pid)
    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir, ignore_errors=True)
    record_operation("删除歌单", f"歌单: {entry['name']}")
    print(f"✅ 已删除歌单: {entry['name']}")


def switch_playlist():
    playlists = get_playlists()
    if len(playlists) <= 1:
        print("❌ 只有一个歌单，无需切换")
        return
    current = get_current_playlist_id()

    print("\n🎵 切换歌单")
    print("=" * 30)
    items = list(playlists.items())
    for index, (pid, entry) in enumerate(items, 1):
        marker = "（当前）" if pid == current else ""
        print(f"{index}. {entry['name']} - {entry.get('song_count', 0)}首歌曲{marker}")
    try:
        choice = int(input("\n请选择要切换到的歌单编号: ").strip())
    except ValueError:
        print("❌ 请输入有效的数字")
        return
    if not (1 <= choice <= len(items)):
        print("❌ 无效的选择")
        return

    pid, entry = items[choice - 1]
    if pid == current:
        print("❌ 已经是当前歌单")
        return
    old_name = playlist_name(current)
    if set_current_playlist(pid):
        record_operation("切换歌单", f"从 '{old_name}' 切换到 '{entry['name']}'", playlist_id=pid)
        print(f"✅ 已切换到歌单: {entry['name']}")


def view_all_playlists():
    print("\n🎵 歌单信息")
    print("=" * 50)
    current = get_current_playlist_id()
    from duplicate_prevention_manager import get_summary

    for pid, entry in get_playlists().items():
        marker = "🎯 当前歌单" if pid == current else ""
        print(f"📁 {entry['name']} {marker}")
        print(f"   ID: {pid}")
        print(f"   描述: {entry.get('description') or '（无）'}")
        print(f"   歌曲数量: {entry.get('song_count', 0)}")
        print(f"   创建时间: {entry.get('created_at') or '未知'}")
        summary = get_summary(pid)
        if summary["enabled"]:
            print(
                f"   防重复: {summary['mode_text']}，"
                f"已记录 {summary['played_count']} 首"
            )
        else:
            print("   防重复: 关闭")
        print("-" * 50)


def _read_external_songs(path):
    """从 yaml/json/txt 读取歌曲列表，返回标准化的歌曲 dict 列表。"""
    lower = path.lower()
    raw_songs = []
    if lower.endswith((".yaml", ".yml", ".json")):
        if lower.endswith(".json"):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = load_yaml(path, default={})
        if isinstance(data, dict):
            raw_songs = data.get("songs") or []
        elif isinstance(data, list):
            raw_songs = data
    elif lower.endswith(".txt"):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if " - " in line:
                    song_name, artist = line.split(" - ", 1)
                else:
                    song_name, artist = line, ""
                raw_songs.append({"song_name": song_name.strip(), "artist": artist.strip()})
    else:
        raise ValueError("不支持的文件类型（仅支持 .yaml/.yml/.json/.txt）")

    songs = []
    for raw in raw_songs:
        if not isinstance(raw, dict):
            continue
        song, _ = normalize_song(raw)
        song["requested_by"] = song.get("requested_by") or "导入"
        songs.append(song)
    return songs


def import_external_playlist():
    print("\n🎵 从外部文件导入歌单")
    print("=" * 40)
    path = input("请输入文件路径（支持 .yaml/.yml/.json/.txt）: ").strip().strip('"')
    if not path:
        print("❌ 路径不能为空")
        return
    if not os.path.exists(path):
        print(f"❌ 文件不存在: {path}")
        return
    while True:
        name = input("请输入新歌单名称: ").strip()
        if name:
            break
        print("歌单名称不能为空，请重新输入")

    try:
        songs = _read_external_songs(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"❌ 读取失败: {exc}")
        return

    pid = unique_playlist_id(name)
    register_playlist(pid, name, f"从外部导入: {os.path.basename(path)}")
    ensure_playlist_files(pid, songs=songs)
    record_operation("导入歌单", f"歌单: {name}, 歌曲数: {len(songs)}", playlist_id=pid)
    print(f"✅ 已导入歌单: {name}（{len(songs)} 首歌曲，ID: {pid}）")


def playlist_menu():
    while True:
        print(f"\n🎵 歌单管理（当前歌单: {playlist_name(get_current_playlist_id())}）")
        print("=" * 40)
        print("1. 从外部文件导入")
        print("2. 从 QQ 音乐歌单导入")
        print("3. 创建空白歌单")
        print("4. 删除歌单")
        print("5. 切换歌单")
        print("6. 查看所有歌单")
        print("7. 返回设置菜单")
        choice = input("请选择操作: ").strip()
        if choice == "1":
            import_external_playlist()
        elif choice == "2":
            from qq_importer import import_qq_playlist_interactive

            import_qq_playlist_interactive()
        elif choice == "3":
            create_playlist()
        elif choice == "4":
            delete_playlist()
        elif choice == "5":
            switch_playlist()
        elif choice == "6":
            view_all_playlists()
        elif choice == "7":
            break
        else:
            print("❌ 无效的选择，请重新输入")
