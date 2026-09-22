"""
防重复播放：核心算法 + 设置菜单。

设计要点（相对旧版的改进）：
  * 以 UUID 字符串标识歌曲，不再混用自增整数；
  * 播放记录会随"歌曲已删除""超出时间窗口""时间戳损坏"而自动清理，规模有上界；
  * 两种模式：
      - time_window：窗口内播放过的歌不再出现；
      - cycle      ：整轮内不重复，直到所有歌都播放过再重置；
  * reset_on_all_played：当无歌可选时是否自动重置；
  * avoid_immediate_repeat：始终避免与"上一首"紧挨着重播。
"""

import datetime
import random

from config_manager import get_current_playlist_id, get_prevention, playlist_name, save_prevention
from history_manager import record_operation

TIME_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S")


def _now():
    return datetime.datetime.now()


def _fmt(moment):
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def _parse_time(value):
    """解析播放时间，失败返回 None（不让一条坏记录把整个流程打崩）。"""
    if not isinstance(value, str):
        return None
    for fmt in TIME_FORMATS:
        try:
            return datetime.datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _clean_records(records, valid_ids, mode, window_seconds, now):
    """清理播放记录：丢弃无效项、已删除歌曲、超窗口记录。"""
    valid_set = {str(i) for i in valid_ids if i}
    cleaned = []
    for record in records or []:
        if not isinstance(record, dict):
            continue
        song_id = record.get("song_id")
        if song_id is None:
            continue
        song_id = str(song_id)
        if song_id not in valid_set:
            continue
        play_time = _parse_time(record.get("play_time"))
        if play_time is None:
            continue
        if mode == "time_window" and (now - play_time).total_seconds() > window_seconds:
            continue
        cleaned.append(
            {
                "song_id": song_id,
                "song_name": record.get("song_name", ""),
                "play_time": record.get("play_time"),
            }
        )
    return cleaned


def _blocked_ids(records, mode):
    return {record["song_id"] for record in records}


def pick_song(playlist_id, songs, persist=True):
    """按防重复策略从 songs 中随机挑一首。

    返回歌曲 dict；无可选且不允许重置时返回 None。
    persist=False 时不写回防重复状态（用于预览 / 静默模式）。
    """
    valid_songs = [
        song
        for song in (songs or [])
        if isinstance(song, dict) and str(song.get("song_name", "")).strip()
    ]
    if not valid_songs:
        return None

    cfg = get_prevention(playlist_id)
    if not cfg.get("enabled", True):
        return random.choice(valid_songs)

    now = _now()
    mode = cfg.get("mode", "time_window")
    window_minutes = max(0, int(cfg.get("time_window_minutes", 60)))
    window_seconds = window_minutes * 60
    valid_ids = [song.get("id") for song in valid_songs]

    records = _clean_records(cfg.get("played_songs") or [], valid_ids, mode, window_seconds, now)
    blocked = _blocked_ids(records, mode)

    if cfg.get("avoid_immediate_repeat", True) and records:
        blocked.add(records[-1]["song_id"])

    available = [song for song in valid_songs if song.get("id") not in blocked]

    if not available:
        if cfg.get("reset_on_all_played", True):
            records = []
            cfg["last_reset_time"] = _fmt(now)
            available = valid_songs
        else:
            if persist:
                cfg["played_songs"] = records
                save_prevention(playlist_id, cfg)
            return None

    chosen = random.choice(available)
    if persist:
        records.append(
            {
                "song_id": chosen.get("id"),
                "song_name": chosen.get("song_name", ""),
                "play_time": _fmt(now),
            }
        )
        cfg["played_songs"] = records
        save_prevention(playlist_id, cfg)
    return chosen


def get_summary(playlist_id):
    """返回当前防重复设置的可读摘要（供展示）。"""
    cfg = get_prevention(playlist_id)
    mode = cfg.get("mode", "time_window")
    window_minutes = int(cfg.get("time_window_minutes", 60))
    return {
        "enabled": bool(cfg.get("enabled", True)),
        "mode": mode,
        "mode_text": "时间窗口模式" if mode == "time_window" else "整轮不重复模式",
        "time_window_minutes": window_minutes,
        "time_window_text": f"{window_minutes // 60}小时{window_minutes % 60}分钟",
        "reset_on_all_played": bool(cfg.get("reset_on_all_played", True)),
        "avoid_immediate_repeat": bool(cfg.get("avoid_immediate_repeat", True)),
        "played_count": len(cfg.get("played_songs") or []),
        "last_reset_time": cfg.get("last_reset_time"),
    }


# ---------------------------------------------------------------------------
# 设置菜单
# ---------------------------------------------------------------------------

def _current():
    pid = get_current_playlist_id()
    return pid, playlist_name(pid), get_prevention(pid)


def toggle_enabled():
    pid, name, cfg = _current()
    cfg["enabled"] = not cfg.get("enabled", True)
    save_prevention(pid, cfg)
    state = "启用" if cfg["enabled"] else "关闭"
    record_operation("切换防重复功能", f"歌单: {name}, 状态: {state}")
    print(f"✅ 已{state}防重复功能")


def set_mode():
    pid, name, cfg = _current()
    print("\n🔄 防重复模式设置")
    print("=" * 30)
    print("1. ⏰ 时间窗口模式（窗口内不重复）")
    print("2. 🔁 整轮不重复模式（全部播完再重置）")
    choice = input("请选择模式: ").strip()
    if choice == "1":
        cfg["mode"] = "time_window"
    elif choice == "2":
        cfg["mode"] = "cycle"
    else:
        print("❌ 无效的选择")
        return
    save_prevention(pid, cfg)
    record_operation("设置防重复模式", f"歌单: {name}, 模式: {cfg['mode']}")
    print(f"✅ 已切换为{get_summary(pid)['mode_text']}")


def set_time_window():
    pid, name, cfg = _current()
    current_minutes = int(cfg.get("time_window_minutes", 60))
    print("\n⏰ 设置时间窗口")
    print("=" * 30)
    print(f"当前时间窗口: {current_minutes // 60}小时{current_minutes % 60}分钟")
    try:
        hours = int(input("请输入小时数 (0-48): ").strip())
        minutes = int(input("请输入分钟数 (0-59): ").strip())
    except ValueError:
        print("❌ 请输入有效的数字")
        return
    if not (0 <= hours <= 48 and 0 <= minutes <= 59):
        print("❌ 时间范围无效")
        return
    total = hours * 60 + minutes
    cfg["time_window_minutes"] = total
    cfg["mode"] = "time_window"
    save_prevention(pid, cfg)
    record_operation("设置时间窗口", f"歌单: {name}, 时间: {hours}小时{minutes}分钟")
    print(f"✅ 已设置时间窗口为 {hours}小时{minutes}分钟")


def toggle_reset_on_all_played():
    pid, name, cfg = _current()
    cfg["reset_on_all_played"] = not cfg.get("reset_on_all_played", True)
    save_prevention(pid, cfg)
    state = "启用" if cfg["reset_on_all_played"] else "关闭"
    record_operation("切换播放后重置", f"歌单: {name}, 状态: {state}")
    print(f"✅ 已{state}「无可选时自动重置」")


def toggle_avoid_immediate_repeat():
    pid, name, cfg = _current()
    cfg["avoid_immediate_repeat"] = not cfg.get("avoid_immediate_repeat", True)
    save_prevention(pid, cfg)
    state = "启用" if cfg["avoid_immediate_repeat"] else "关闭"
    record_operation("切换即时去重", f"歌单: {name}, 状态: {state}")
    print(f"✅ 已{state}「避免连播同一首」")


def view_played_songs():
    pid, name, cfg = _current()
    records = cfg.get("played_songs") or []
    print(f"\n📜 播放记录（歌单: {name}）")
    print("=" * 60)
    if not records:
        print("暂无播放记录")
    else:
        for index, record in enumerate(records, 1):
            print(f"{index}. {record.get('song_name', '未知')}")
            print(f"   播放时间: {record.get('play_time', '未知时间')}")
    print(f"\n📊 共 {len(records)} 条记录")
    print("=" * 60)


def reset_played_songs():
    pid, name, cfg = _current()
    count = len(cfg.get("played_songs") or [])
    if count == 0:
        print("❌ 当前没有播放记录需要重置")
        return
    confirm = input(f"确定重置播放记录吗？将清除 {count} 条记录 (y/N): ").strip().lower()
    if confirm != "y":
        print("取消重置")
        return
    cfg["played_songs"] = []
    cfg["last_reset_time"] = _fmt(_now())
    save_prevention(pid, cfg)
    record_operation("重置播放记录", f"歌单: {name}, 清除记录: {count}条")
    print(f"✅ 已重置播放记录，清除了 {count} 条")


def view_settings():
    pid, name, _ = _current()
    summary = get_summary(pid)
    print(f"\n🔄 防重复功能设置（歌单: {name}）")
    print("=" * 50)
    print(f"1. 功能状态: {'✅ 启用' if summary['enabled'] else '❌ 关闭'}")
    print(f"2. 模式: {summary['mode_text']}")
    if summary["mode"] == "time_window":
        print(f"3. 时间窗口: {summary['time_window_text']}")
    print(f"4. 无可选时自动重置: {'✅ 是' if summary['reset_on_all_played'] else '❌ 否'}")
    print(f"5. 避免连播同一首: {'✅ 是' if summary['avoid_immediate_repeat'] else '❌ 否'}")
    print(f"6. 当前已记录播放: {summary['played_count']}首")
    if summary["last_reset_time"]:
        print(f"7. 上次重置时间: {summary['last_reset_time']}")
    print("=" * 50)


def duplicate_prevention_menu():
    while True:
        pid, name, cfg = _current()
        mode = cfg.get("mode", "time_window")
        state = "✅ 启用" if cfg.get("enabled", True) else "❌ 关闭"
        print(f"\n🔄 防重复功能设置（歌单: {name}，状态: {state}）")
        print("=" * 50)
        print("1. 启用/关闭防重复功能")
        print("2. 设置防重复模式")
        if mode == "time_window":
            print("3. 设置时间窗口")
        print("4. 启用/关闭「无可选时自动重置」")
        print("5. 启用/关闭「避免连播同一首」")
        print("6. 查看播放记录")
        print("7. 手动重置播放记录")
        print("8. 查看当前设置")
        print("9. 返回设置菜单")
        choice = input("请选择操作: ").strip()

        if choice == "1":
            toggle_enabled()
        elif choice == "2":
            set_mode()
        elif choice == "3" and mode == "time_window":
            set_time_window()
        elif choice == "4":
            toggle_reset_on_all_played()
        elif choice == "5":
            toggle_avoid_immediate_repeat()
        elif choice == "6":
            view_played_songs()
        elif choice == "7":
            reset_played_songs()
        elif choice == "8":
            view_settings()
        elif choice == "9":
            break
        else:
            print("❌ 无效的选择，请重新输入")
