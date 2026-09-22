"""
统一路径解析。

所有数据路径都基于本文件位置推导出的项目根目录，不再依赖"当前工作目录"。
这样无论从哪个目录、用哪个方式启动，都能找到同一份 main_data/。
"""

import os

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_SRC_DIR)

MAIN_DATA_DIR = os.path.join(PROJECT_ROOT, "main_data")
GLOBAL_DIR = os.path.join(MAIN_DATA_DIR, "global")
PLAYLIST_ROOT = os.path.join(MAIN_DATA_DIR, "play_list")
TEMPLATE_DIR = os.path.join(MAIN_DATA_DIR, "templates")

GLOBAL_CONFIG_FILE = os.path.join(GLOBAL_DIR, "global_config.yaml")
SYSTEM_STATS_FILE = os.path.join(GLOBAL_DIR, "system_stats.yaml")
GLOBAL_PLAY_HISTORY_FILE = os.path.join(GLOBAL_DIR, "global_play_history.log")
GLOBAL_OPERATE_HISTORY_FILE = os.path.join(GLOBAL_DIR, "global_operate_history.log")


def playlist_dir(playlist_id):
    return os.path.join(PLAYLIST_ROOT, playlist_id)


def playlist_songs_file(playlist_id):
    return os.path.join(playlist_dir(playlist_id), "songs.yaml")


def playlist_requesters_file(playlist_id):
    return os.path.join(playlist_dir(playlist_id), "requesters.yaml")


def playlist_play_history_file(playlist_id):
    return os.path.join(playlist_dir(playlist_id), "play_history.log")


def playlist_operate_history_file(playlist_id):
    return os.path.join(playlist_dir(playlist_id), "operate_history.log")


def playlist_music_dir(playlist_id):
    return os.path.join(playlist_dir(playlist_id), "music_files")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def set_data_root(root):
    """重定位数据根目录（供测试或自定义部署使用）。"""
    global MAIN_DATA_DIR, GLOBAL_DIR, PLAYLIST_ROOT, TEMPLATE_DIR
    global GLOBAL_CONFIG_FILE, SYSTEM_STATS_FILE, GLOBAL_PLAY_HISTORY_FILE, GLOBAL_OPERATE_HISTORY_FILE
    MAIN_DATA_DIR = root
    GLOBAL_DIR = os.path.join(root, "global")
    PLAYLIST_ROOT = os.path.join(root, "play_list")
    TEMPLATE_DIR = os.path.join(root, "templates")
    GLOBAL_CONFIG_FILE = os.path.join(GLOBAL_DIR, "global_config.yaml")
    SYSTEM_STATS_FILE = os.path.join(GLOBAL_DIR, "system_stats.yaml")
    GLOBAL_PLAY_HISTORY_FILE = os.path.join(GLOBAL_DIR, "global_play_history.log")
    GLOBAL_OPERATE_HISTORY_FILE = os.path.join(GLOBAL_DIR, "global_operate_history.log")
    return MAIN_DATA_DIR
