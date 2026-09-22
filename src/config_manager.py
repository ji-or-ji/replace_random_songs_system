"""
全局配置与歌单注册表的数据访问层。

配置单一来源：main_data/global/global_config.yaml。
歌单元信息（名称/描述/防重复设置/播放记录）都挂在这个文件的 playlists 映射下。
读取时统一与默认值深合并，因此旧配置缺字段也能正常跑。
"""

import copy
import datetime

import paths
from storage import load_yaml, save_yaml

SYSTEM_VERSION = "2.1"

DEFAULT_AUTO_JUMP = {
    "enabled": False,
    "mode": "search",  # search | custom
    "custom_url": "",
    "delay": 3,
    "prefer_search": False,  # True = 忽略歌曲自带链接，一律走模式（搜索/自定义）
}

DEFAULT_QQ_SYNC = {
    "enabled": True,
    "playlist_id": "",
    "auto_on_start": True,
}

DEFAULT_PREVENTION = {
    "enabled": True,
    "mode": "time_window",  # time_window | cycle
    "time_window_minutes": 60,
    "reset_on_all_played": True,
    "avoid_immediate_repeat": True,
    "last_reset_time": None,
    "played_songs": [],
}

DEFAULT_PLAYLIST = {
    "name": "",
    "description": "",
    "created_at": None,
    "song_count": 0,
    "duplicate_prevention": DEFAULT_PREVENTION,
}

DEFAULT_GLOBAL = {
    "system_version": SYSTEM_VERSION,
    "initialized_at": None,
    "current_playlist": None,
    "auto_jump": DEFAULT_AUTO_JUMP,
    "qq_sync": DEFAULT_QQ_SYNC,
    "playlists": {},
}


def _now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def deep_merge(base, override):
    """把 override 叠加到 base 上（dict 递归合并，其它类型直接覆盖），返回新对象。"""
    if not isinstance(base, dict):
        base = {}
    result = copy.deepcopy(base)
    if isinstance(override, dict):
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
    return result


# ---------------------------------------------------------------------------
# 全局配置
# ---------------------------------------------------------------------------

def load_global_config():
    """读取全局配置，缺失字段用默认值补齐。"""
    raw = load_yaml(paths.GLOBAL_CONFIG_FILE, default=None)
    if not isinstance(raw, dict):
        raw = {}
    return deep_merge(DEFAULT_GLOBAL, raw)


def save_global_config(config):
    save_yaml(paths.GLOBAL_CONFIG_FILE, config)
    return True


def config_exists():
    import os

    return os.path.exists(paths.GLOBAL_CONFIG_FILE)


# ---------------------------------------------------------------------------
# 歌单注册表
# ---------------------------------------------------------------------------

def get_playlists():
    """返回 {playlist_id: playlist_dict} 的原始映射（已补齐默认字段）。"""
    config = load_global_config()
    result = {}
    for pid, entry in config.get("playlists", {}).items():
        result[pid] = deep_merge(DEFAULT_PLAYLIST, entry if isinstance(entry, dict) else {})
    return result


def playlist_ids():
    return list(get_playlists().keys())


def get_playlist(playlist_id):
    return get_playlists().get(playlist_id)


def playlist_name(playlist_id):
    entry = get_playlist(playlist_id)
    if entry and entry.get("name"):
        return entry["name"]
    return playlist_id


def register_playlist(playlist_id, name, description=""):
    """新建或覆盖一个歌单注册项（不影响其数据文件）。"""
    config = load_global_config()
    playlists = config.setdefault("playlists", {})
    existing = playlists.get(playlist_id)
    entry = deep_merge(
        DEFAULT_PLAYLIST,
        existing if isinstance(existing, dict) else {},
    )
    entry["name"] = name
    entry["description"] = description or entry.get("description") or f"{name} 歌单"
    if not entry.get("created_at"):
        entry["created_at"] = datetime.datetime.now().strftime("%Y/%m/%d")
    playlists[playlist_id] = entry
    save_global_config(config)
    return entry


def update_playlist_fields(playlist_id, **fields):
    """更新歌单注册项的若干字段。"""
    config = load_global_config()
    playlists = config.setdefault("playlists", {})
    entry = deep_merge(DEFAULT_PLAYLIST, playlists.get(playlist_id) or {})
    entry.update(fields)
    playlists[playlist_id] = entry
    save_global_config(config)
    return entry


def delete_playlist_entry(playlist_id):
    config = load_global_config()
    playlists = config.setdefault("playlists", {})
    if playlist_id in playlists:
        del playlists[playlist_id]
        if config.get("current_playlist") == playlist_id:
            config["current_playlist"] = next(iter(playlists), None)
        save_global_config(config)
        return True
    return False


def update_song_count(playlist_id, count):
    config = load_global_config()
    playlists = config.setdefault("playlists", {})
    if playlist_id not in playlists:
        return
    entry = deep_merge(DEFAULT_PLAYLIST, playlists[playlist_id])
    entry["song_count"] = count
    playlists[playlist_id] = entry
    save_global_config(config)


# ---------------------------------------------------------------------------
# 当前歌单
# ---------------------------------------------------------------------------

def get_current_playlist_id():
    config = load_global_config()
    current = config.get("current_playlist")
    playlists = config.get("playlists", {})
    if current in playlists:
        return current
    if playlists:
        fallback = next(iter(playlists))
        config["current_playlist"] = fallback
        save_global_config(config)
        return fallback
    return None


def set_current_playlist(playlist_id):
    config = load_global_config()
    if playlist_id not in config.get("playlists", {}):
        return False
    config["current_playlist"] = playlist_id
    save_global_config(config)
    return True


# ---------------------------------------------------------------------------
# 子配置块
# ---------------------------------------------------------------------------

def get_auto_jump_config():
    return load_global_config().get("auto_jump", dict(DEFAULT_AUTO_JUMP))


def save_auto_jump_config(auto_jump):
    config = load_global_config()
    config["auto_jump"] = deep_merge(DEFAULT_AUTO_JUMP, auto_jump)
    save_global_config(config)
    return True


def get_qq_sync_config():
    return load_global_config().get("qq_sync", dict(DEFAULT_QQ_SYNC))


def save_qq_sync_config(qq_sync):
    config = load_global_config()
    config["qq_sync"] = deep_merge(DEFAULT_QQ_SYNC, qq_sync)
    save_global_config(config)
    return True


# ---------------------------------------------------------------------------
# 防重复设置（挂在歌单上）
# ---------------------------------------------------------------------------

def get_prevention(playlist_id):
    entry = get_playlist(playlist_id)
    if not entry:
        return copy.deepcopy(DEFAULT_PREVENTION)
    return deep_merge(DEFAULT_PREVENTION, entry.get("duplicate_prevention") or {})


def save_prevention(playlist_id, prevention):
    update_playlist_fields(playlist_id, duplicate_prevention=prevention)
    return True
