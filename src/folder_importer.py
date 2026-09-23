"""
从文件夹批量导入歌曲。

扫描目录下的音频文件，并从文件名推断歌名与歌手。规则与 GUI（.NET 版）保持一致：
  歌手 - 歌名 / 歌名 - 歌手 / 歌手《歌名》 / [歌手] 歌名 / 歌名 (歌手) / 带音轨号前缀 …
若某一侧命中「已知歌手」（来自现有歌单），会自动校正被调换的顺序。
"""

import os
import re

AUDIO_EXTENSIONS = {
    ".mp3", ".flac", ".m4a", ".wav", ".aac", ".ogg", ".wma", ".ape", ".opus", ".m4b",
}
SEPARATORS = [" - ", " – ", " — ", "-", "–", "—", "_", "|", "｜"]
IMPORT_REQUESTER = "本地导入"

_LEADING_TRACK = re.compile(r"^(?:\s*[\[\(]\d{1,4}[\]\)][\s.\-_|｜]*|\d{1,4}[\s.\-_|｜]+)+")
_BRACKET_TITLE = re.compile(r"^(?P<a>.+?)\s*[《<](?P<t>.+?)[》>]\s*$")
_BRACKET_ARTIST = re.compile(r"^\s*\[(?P<a>[^\]]+)\]\s*(?P<t>.+)$")
_PAREN_ARTIST = re.compile(r"^(?P<t>.+?)\s*[\(（](?P<a>[^\)）]+)[\)）]\s*$")


def _normalize_known(known_artists):
    return {str(a).strip().lower() for a in (known_artists or set()) if str(a).strip()}


def collect_known_artists():
    """收集现有各歌单里出现过的歌手名（用于校正调换的顺序）。"""
    from config_manager import get_playlists
    from paths import playlist_songs_file
    from storage import load_yaml

    artists = set()
    for playlist_id in get_playlists():
        data = load_yaml(playlist_songs_file(playlist_id), default={}) or {}
        for song in (data.get("songs") or []):
            if isinstance(song, dict) and (song.get("artist") or "").strip():
                artists.add(song["artist"].strip())
    return artists


def parse_name(raw, artist_first=True, known_artists=None):
    """从文件名（不含扩展名）推断 (歌名, 歌手, 说明)。"""
    known = _normalize_known(known_artists)
    text = (raw or "").replace("\u3000", " ").strip()
    text = _LEADING_TRACK.sub("", text).strip()
    if not text:
        return ((raw or "").strip(), "", "空文件名")

    match = _BRACKET_TITLE.match(text)
    if match:
        return (match.group("t").strip(), match.group("a").strip(), "《歌名》格式")

    match = _BRACKET_ARTIST.match(text)
    if match:
        return (match.group("t").strip(), match.group("a").strip(), "[]格式")

    for separator in SEPARATORS:
        index = text.find(separator)
        if index <= 0:
            continue
        left = text[:index].strip()
        right = text[index + len(separator):].strip()
        if not left or not right:
            continue

        left_known = left.lower() in known
        right_known = right.lower() in known
        if left_known and not right_known:
            return (right, left, "已知歌手校正")
        if right_known and not left_known:
            return (left, right, "已知歌手校正")
        return (right, left, "") if artist_first else (left, right, "")

    match = _PAREN_ARTIST.match(text)
    if match:
        return (match.group("t").strip(), match.group("a").strip(), "()格式·请确认")

    return (text, "", "未识别出歌手")


def scan_folder(folder, recursive=False, artist_first=True, known_artists=None):
    """扫描目录，返回 [{file_path, file_name, song_name, artist, note}]。"""
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"文件夹不存在: {folder}")

    known = _normalize_known(known_artists)
    if recursive:
        paths = [os.path.join(root, name)
                 for root, _dirs, files in os.walk(folder)
                 for name in files]
    else:
        paths = [os.path.join(folder, name) for name in os.listdir(folder)]

    results = []
    for path in sorted(paths, key=lambda p: p.lower()):
        if not os.path.isfile(path):
            continue
        if os.path.splitext(path)[1].lower() not in AUDIO_EXTENSIONS:
            continue
        stem = os.path.splitext(os.path.basename(path))[0]
        song_name, artist, note = parse_name(stem, artist_first, known)
        results.append({
            "file_path": path,
            "file_name": os.path.basename(path),
            "song_name": song_name,
            "artist": artist,
            "note": note,
        })
    return results


def _key(song):
    return ((song.get("song_name") or "").strip().lower(),
            (song.get("artist") or "").strip().lower())


def import_into_playlist(playlist_id, parsed):
    """按 歌名+歌手 去重后合并进指定歌单，返回新增数量。"""
    from song_manager import load_songs, normalize_song, save_songs

    songs = load_songs(playlist_id)
    existing = {_key(song) for song in songs}

    added = 0
    for item in parsed:
        song, _ = normalize_song({
            "song_name": item["song_name"],
            "artist": item["artist"],
            "local_path": item["file_path"],
            "requested_by": IMPORT_REQUESTER,
        })
        key = _key(song)
        if key in existing:
            continue
        existing.add(key)
        songs.append(song)
        added += 1
    save_songs(songs, playlist_id)
    return added


def import_as_new_playlist(name, folder, parsed):
    """导入为新歌单，返回 (歌单ID, 新增数量)。"""
    from playlist_manager import ensure_playlist_files, register_playlist, unique_playlist_id

    playlist_id = unique_playlist_id(name)
    register_playlist(playlist_id, name, f"从文件夹导入: {folder}")
    ensure_playlist_files(playlist_id, songs=[])
    added = import_into_playlist(playlist_id, parsed)
    return playlist_id, added


def import_folder_interactive():
    """交互式：从文件夹批量导入（供命令行菜单调用）。"""
    folder = input("请输入文件夹路径: ").strip().strip('"')
    if not folder or not os.path.isdir(folder):
        print(f"❌ 文件夹不存在: {folder}")
        return

    recursive = input("包含子文件夹? (y/N): ").strip().lower() == "y"
    order = input("文件名顺序 [1] 歌手-歌名  [2] 歌名-歌手 (默认 1): ").strip()
    artist_first = order != "2"

    parsed = scan_folder(folder, recursive, artist_first, collect_known_artists())
    if not parsed:
        print("❌ 该文件夹里没有音频文件")
        return

    print(f"\n解析到 {len(parsed)} 个音频文件，预览前 15 条：")
    for item in parsed[:15]:
        note = f"  [{item['note']}]" if item["note"] else ""
        print(f"  {item['song_name']} — {item['artist'] or '（未识别）'}{note}")
    if len(parsed) > 15:
        print(f"  …（其余 {len(parsed) - 15} 条略）")

    merge = input("\n合并进当前歌单? (y/N): ").strip().lower() == "y"
    if merge:
        from config_manager import get_current_playlist_id, playlist_name

        target = get_current_playlist_id()
        added = import_into_playlist(target, parsed)
        print(f"✅ 已合并进「{playlist_name(target)}」：新增 {added} 首（共解析 {len(parsed)} 个文件）")
        return

    from config_manager import playlist_name

    default_name = os.path.basename(os.path.normpath(folder)) or "文件夹导入"
    name = input(f"新歌单名称 (默认 {default_name}): ").strip() or default_name
    playlist_id, added = import_as_new_playlist(name, folder, parsed)
    print(f"✅ 已导入为新歌单「{playlist_name(playlist_id)}」：{added} 首")
