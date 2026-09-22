"""
历史记录：操作历史与播放历史。

同时写入「当前歌单」的日志和全局日志，便于单歌单排查与整体追溯。
日志为纯文本，一行一条，方便直接用记事本查看。
"""

import datetime

import paths
from storage import append_line, load_yaml, read_lines, save_yaml


def _timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _resolve_playlist(playlist_id):
    if playlist_id:
        return playlist_id
    from config_manager import get_current_playlist_id

    return get_current_playlist_id()


def record_operation(action, details="", result="成功", playlist_id=None):
    """记录一次操作，写入歌单级与全局操作日志。"""
    pid = _resolve_playlist(playlist_id)
    line = f"[{_timestamp()}] {action} - {details} - 结果: {result}"
    try:
        if pid:
            append_line(paths.playlist_operate_history_file(pid), line)
        append_line(paths.GLOBAL_OPERATE_HISTORY_FILE, f"[{pid or '-'}] {line}")
        return True
    except OSError as exc:
        print(f"[警告] 写入操作历史失败: {exc}")
        return False


def record_play(song, playlist_id=None):
    """记录一次播放，写入歌单级与全局播放日志，并累加系统统计。"""
    pid = _resolve_playlist(playlist_id)
    song_name = (song or {}).get("song_name", "未知")
    artist = (song or {}).get("artist", "") or "未知"
    requester = (song or {}).get("requested_by", "") or "未知"
    line = f"[{_timestamp()}] 播放 - 歌曲: {song_name} - 歌手: {artist} - 点歌人: {requester}"
    try:
        if pid:
            append_line(paths.playlist_play_history_file(pid), line)
        append_line(paths.GLOBAL_PLAY_HISTORY_FILE, f"[{pid or '-'}] {line}")
    except OSError as exc:
        print(f"[警告] 写入播放历史失败: {exc}")
    _increment_play_count()
    return True


def _increment_play_count():
    stats = load_yaml(paths.SYSTEM_STATS_FILE, default={})
    if not isinstance(stats, dict):
        stats = {}
    stats["total_plays"] = int(stats.get("total_plays", 0)) + 1
    stats["last_play_time"] = _timestamp()
    try:
        save_yaml(paths.SYSTEM_STATS_FILE, stats)
    except OSError:
        pass


def get_play_count():
    stats = load_yaml(paths.SYSTEM_STATS_FILE, default={})
    if not isinstance(stats, dict):
        return 0
    return int(stats.get("total_plays", 0))


def view_operation_history(playlist_id=None, limit=50):
    """显示操作历史（歌单级优先，回落到全局）。"""
    pid = _resolve_playlist(playlist_id)
    lines = read_lines(paths.playlist_operate_history_file(pid), limit=limit, newest_first=True) if pid else []
    scope = f"歌单 '{pid}'"
    if not lines:
        lines = read_lines(paths.GLOBAL_OPERATE_HISTORY_FILE, limit=limit, newest_first=True)
        scope = "全局"
    print(f"\n📜 操作历史记录（{scope}，最近 {limit} 条）")
    print("=" * 60)
    if not lines:
        print("暂无操作记录")
    else:
        for index, line in enumerate(lines, 1):
            print(f"{index}. {line}")
    print("=" * 60)


def view_play_history(playlist_id=None, limit=50):
    """显示播放历史（歌单级优先，回落到全局）。"""
    pid = _resolve_playlist(playlist_id)
    lines = read_lines(paths.playlist_play_history_file(pid), limit=limit, newest_first=True) if pid else []
    scope = f"歌单 '{pid}'"
    if not lines:
        lines = read_lines(paths.GLOBAL_PLAY_HISTORY_FILE, limit=limit, newest_first=True)
        scope = "全局"
    print(f"\n🎧 播放历史记录（{scope}，最近 {limit} 条）")
    print("=" * 60)
    if not lines:
        print("暂无播放记录")
    else:
        for index, line in enumerate(lines, 1):
            print(f"{index}. {line}")
    print("=" * 60)
