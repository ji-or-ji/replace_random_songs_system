"""
随机点歌系统 · 主入口。

首次运行时自动初始化 main_data/ 结构并写入一个含示例歌曲的默认歌单，
之后所有数据都以 YAML 形式存放在 main_data/ 下。
"""

import datetime
import os
import sys

import paths
from console_utils import setup_console
from storage import save_yaml

# 示例数据统一使用虚构点歌人，避免出现真实姓名
EXAMPLE_REQUESTERS = ["阿澈", "小满", "林深", "白露"]
EXAMPLE_SONGS = [
    ("夜曲", "周杰伦", "阿澈"),
    ("晴天", "周杰伦", "小满"),
    ("平凡之路", "朴树", "林深"),
    ("起风了", "买辣椒也用券", "白露"),
    ("稻香", "周杰伦", "阿澈"),
]


def _now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _write_templates():
    paths.ensure_dir(paths.TEMPLATE_DIR)
    templates = {
        "playlist_template.yaml": "name: 新歌单\ndescription: 歌单说明\n",
        "song_template.yaml": (
            "id: \"自动生成的UUID\"\n"
            "song_name: 歌名\n"
            "artist: 歌手\n"
            "url: \"\"\n"
            "requested_by: 点歌人\n"
            "created_at: \"2026/01/01 00:00:00\"\n"
            "last_modified: \"2026/01/01 00:00:00\"\n"
        ),
        "requester_template.yaml": "name: 点歌人\nemail: \"\"\nnotes: \"\"\n",
    }
    for filename, content in templates.items():
        path = os.path.join(paths.TEMPLATE_DIR, filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)


def _seed_default_playlist():
    """创建默认歌单并写入示例歌曲。"""
    from playlist_manager import ensure_playlist_files
    from requester_manager import save_requesters
    from song_manager import normalize_song

    from config_manager import register_playlist, set_current_playlist

    requesters = [{"name": name, "email": "", "notes": ""} for name in EXAMPLE_REQUESTERS]
    now = _now_str()
    songs = []
    for song_name, artist, requester in EXAMPLE_SONGS:
        song, _ = normalize_song(
            {
                "song_name": song_name,
                "artist": artist,
                "url": "",
                "requested_by": requester,
                "created_at": now,
                "last_modified": now,
            }
        )
        songs.append(song)

    register_playlist("default", "默认歌单", "主歌单（含示例歌曲）")
    ensure_playlist_files("default", songs=songs, requesters=requesters)
    set_current_playlist("default")
    return songs


def initialize_system(quiet=False):
    """幂等初始化：建目录、写模板、必要时创建默认歌单。"""
    for directory in (paths.MAIN_DATA_DIR, paths.GLOBAL_DIR, paths.PLAYLIST_ROOT, paths.TEMPLATE_DIR):
        paths.ensure_dir(directory)

    _write_templates()

    from config_manager import config_exists, load_global_config

    config = load_global_config()
    if not config_exists() or not config.get("playlists"):
        if not quiet:
            print("📦 首次运行，正在创建默认歌单与示例数据...")
        _seed_default_playlist()

    if not os.path.exists(paths.SYSTEM_STATS_FILE):
        save_yaml(paths.SYSTEM_STATS_FILE, {"total_plays": 0, "last_play_time": None})

    from config_manager import get_current_playlist_id, save_global_config

    config = load_global_config()
    if not config.get("initialized_at"):
        config["initialized_at"] = _now_str()
        save_global_config(config)
    get_current_playlist_id()  # 修正非法的当前歌单


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def display_song_info(song):
    from auto_jump_manager import auto_jump, try_local_playback
    from history_manager import record_play

    if not song:
        print("\n⚠️ 当前没有可供点播的歌曲（可能都在防重复窗口内，或歌单为空）")
        return
    print("\n🎵 随机点歌结果 🎵")
    print("=" * 30)
    print(f"歌曲名: {song.get('song_name', '未知')}")
    print(f"歌手: {song.get('artist') or '未知'}")
    print(f"点歌人: {song.get('requested_by') or '未知'}")
    if song.get("url"):
        print(f"链接: {song['url']}")
    print("=" * 30)
    record_play(song)
    if not try_local_playback(song):
        auto_jump(song)


def history_menu():
    from history_manager import view_operation_history, view_play_history

    while True:
        print("\n📚 历史记录")
        print("=" * 30)
        print("1. 操作历史")
        print("2. 播放历史")
        print("3. 返回主菜单")
        choice = input("请选择操作: ").strip()
        if choice == "1":
            view_operation_history()
        elif choice == "2":
            view_play_history()
        elif choice == "3":
            break
        else:
            print("❌ 无效的选择，请重新输入")


def settings_menu():
    from auto_jump_manager import auto_jump_menu
    from config_manager import get_current_playlist_id, playlist_name
    from duplicate_prevention_manager import duplicate_prevention_menu
    from playlist_manager import playlist_menu

    while True:
        print(f"\n⚙️ 设置菜单（当前歌单: {playlist_name(get_current_playlist_id())}）")
        print("=" * 30)
        print("1. 歌单管理")
        print("2. 自动网页跳转设置")
        print("3. 防重复功能设置")
        print("4. QQ 歌单同步")
        print("5. 返回主菜单")
        choice = input("请选择操作: ").strip()
        if choice == "1":
            playlist_menu()
        elif choice == "2":
            auto_jump_menu()
        elif choice == "3":
            duplicate_prevention_menu()
        elif choice == "4":
            from qq_importer import qq_sync_menu

            qq_sync_menu()
        elif choice == "5":
            break
        else:
            print("❌ 无效的选择，请重新输入")


def main():
    from config_manager import get_current_playlist_id, playlist_name
    from history_manager import get_play_count
    from qq_importer import auto_sync_on_start
    from song_manager import (
        display_statistics,
        filter_valid_songs,
        get_random_song,
        get_songs_statistics,
        load_songs,
    )

    setup_console()
    print("🎵 随机点歌系统 🎵")
    print("正在初始化系统...")
    initialize_system()

    sync_message = auto_sync_on_start()
    if sync_message:
        print(sync_message)

    songs = load_songs()
    print(f"正在加载歌曲列表（歌单: {playlist_name(get_current_playlist_id())}）...")
    if not filter_valid_songs(songs):
        print("⚠️ 当前歌单没有有效歌曲，可在「歌曲管理」中添加，或导入歌单。")

    while True:
        pid = get_current_playlist_id()
        print(f"\n🎵 主菜单（当前歌单: {playlist_name(pid)}，累计播放 {get_play_count()} 次）")
        print("1. 随机点歌")
        print("2. 重新加载歌曲列表")
        print("3. 查看统计信息")
        print("4. 点歌人管理")
        print("5. 歌曲管理")
        print("6. 查看历史记录")
        print("7. 设置")
        print("8. 退出")
        choice = input("请输入选项 (1-8): ").strip()

        if choice == "1":
            display_song_info(get_random_song())
        elif choice == "2":
            songs = load_songs()
            print(f"✅ 已重新加载，共 {len(filter_valid_songs(songs))} 首有效歌曲")
        elif choice == "3":
            display_statistics(get_songs_statistics(songs), get_current_playlist_id())
        elif choice == "4":
            from requester_manager import requester_menu

            requester_menu()
        elif choice == "5":
            from song_operations import song_management_menu

            song_management_menu()
            songs = load_songs()
        elif choice == "6":
            history_menu()
        elif choice == "7":
            settings_menu()
            songs = load_songs()
        elif choice == "8":
            print("天空属于哈夫克~！")
            break
        else:
            print("❌ 无效选项，请重新选择")


def cli():
    """命令行入口：处理中断与退出暂停。"""
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n已退出")
    finally:
        if sys.stdin is not None and getattr(sys.stdin, "isatty", lambda: False)():
            try:
                input("\n按回车键退出程序...")
            except (KeyboardInterrupt, EOFError):
                pass


if __name__ == "__main__":
    cli()
