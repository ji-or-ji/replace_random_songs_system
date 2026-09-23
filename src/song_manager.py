"""
歌曲数据管理：读写 songs.yaml、校验、统计、随机选择入口。

每首歌以 UUID 作为唯一标识（字符串），避免旧版"自增整数 vs UUID"混用的问题。
"""

import datetime
import uuid

from config_manager import get_current_playlist_id, update_song_count
from paths import playlist_songs_file
from storage import load_yaml, save_yaml

SONG_FIELDS = ("id", "song_name", "artist", "url", "requested_by", "created_at", "last_modified")


def _now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def new_song_id():
    return str(uuid.uuid4())


def normalize_song(raw):
    """把任意来源的歌曲 dict 规范成标准结构，返回 (song, changed)。"""
    changed = False
    song = dict(raw) if isinstance(raw, dict) else {}

    # 兼容旧字段名 url_list
    if "url" not in song and "url_list" in song:
        song["url"] = song.pop("url_list")
        changed = True
    # 兼容旧字段名 local_file
    if "local_path" not in song and "local_file" in song:
        song["local_path"] = song.pop("local_file")
        changed = True
    # 旧版 url 可能是列表
    if isinstance(song.get("url"), (list, tuple)):
        song["url"] = song["url"][0] if song["url"] else ""
        changed = True

    for key in ("song_name", "artist", "url", "requested_by", "local_path"):
        if not isinstance(song.get(key), str):
            song[key] = "" if song.get(key) is None else str(song[key])
            changed = True

    if not song.get("id"):
        song["id"] = new_song_id()
        changed = True
    else:
        song["id"] = str(song["id"])

    if not song.get("created_at"):
        song["created_at"] = _now_str()
        changed = True
    if not song.get("last_modified"):
        song["last_modified"] = song["created_at"]
        changed = True

    # 去掉未预期的键，保持文件干净（保留未知键以免丢数据）
    return song, changed


def load_songs(playlist_id=None):
    """加载指定/当前歌单的歌曲列表；会自动补齐缺失字段并回写。"""
    pid = playlist_id or get_current_playlist_id()
    if not pid:
        return []

    data = load_yaml(playlist_songs_file(pid), default={})
    raw_songs = data.get("songs") if isinstance(data, dict) else None
    if not isinstance(raw_songs, list):
        raw_songs = []

    songs = []
    healed = False
    for raw in raw_songs:
        song, changed = normalize_song(raw)
        songs.append(song)
        healed = healed or changed

    if healed:
        save_songs(songs, pid)
    else:
        update_song_count(pid, len(songs))
    return songs


def save_songs(songs, playlist_id=None):
    """保存歌曲列表到 songs.yaml。"""
    pid = playlist_id or get_current_playlist_id()
    if not pid:
        print("[错误] 没有可用的歌单，无法保存歌曲")
        return False
    try:
        save_yaml(playlist_songs_file(pid), {"songs": songs})
        update_song_count(pid, len(songs))
        return True
    except OSError as exc:
        print(f"[错误] 保存歌曲失败: {exc}")
        return False


def filter_valid_songs(songs):
    """有效歌曲：歌名非空。"""
    valid = []
    for song in songs or []:
        if isinstance(song, dict) and str(song.get("song_name", "")).strip():
            valid.append(song)
    return valid


def find_song_index(songs, song_id):
    for index, song in enumerate(songs or []):
        if song.get("id") == song_id:
            return index
    return -1


def get_songs_statistics(songs):
    """统计歌曲数量与各点歌人分布。"""
    valid_songs = filter_valid_songs(songs)
    requesters = {}
    for song in valid_songs:
        requester = song.get("requested_by") or "未知"
        requesters[requester] = requesters.get(requester, 0) + 1
    return {
        "total_songs": len(songs or []),
        "valid_songs": len(valid_songs),
        "invalid_songs": len(songs or []) - len(valid_songs),
        "requesters": requesters,
    }


def display_statistics(statistics, playlist_id=None):
    from config_manager import playlist_name

    title = ""
    if playlist_id:
        title = f"（歌单: {playlist_name(playlist_id)}）"
    print(f"\n📊 歌曲统计信息 {title}")
    print("=" * 40)
    print(f"总歌曲数: {statistics['total_songs']}")
    print(f"有效歌曲: {statistics['valid_songs']}")
    print(f"无效歌曲: {statistics['invalid_songs']}")
    print("\n👥 点歌人统计:")
    if statistics["requesters"]:
        for requester, count in sorted(
            statistics["requesters"].items(), key=lambda item: (-item[1], item[0])
        ):
            print(f"  {requester}: {count}首")
    else:
        print("  （暂无）")
    print("=" * 40)


def get_random_song(playlist_id=None, songs=None):
    """随机点歌入口，交由防重复模块决定最终结果。"""
    from duplicate_prevention_manager import pick_song

    pid = playlist_id or get_current_playlist_id()
    if not pid:
        return None
    if songs is None:
        songs = load_songs(pid)
    return pick_song(pid, songs)


def append_song(playlist_id, song):
    """向歌单追加一首歌并保存。"""
    songs = load_songs(playlist_id)
    songs.append(song)
    return save_songs(songs, playlist_id)


def remove_song(playlist_id, song_id):
    songs = load_songs(playlist_id)
    index = find_song_index(songs, song_id)
    if index < 0:
        return False
    del songs[index]
    return save_songs(songs, playlist_id)
