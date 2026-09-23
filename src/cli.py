"""
命令行入口：便于与 ClassIsland 等定时/联动工具配合。

约定：
  * 不带任何参数、或只带 --silent 时 —— 静默抽歌：按当前状态随机抽一首，
    只输出结果，不显示主窗口、不等待输入。
  * 带 --gui 时 —— 打开交互式主菜单（run.bat 默认走这个）。

其余参数可覆盖歌单、数量、跳转设置、记录行为与输出格式。
退出码：0 成功；1 参数/环境错误；2 没有可用歌曲。
"""

import argparse
import datetime
import json
import sys

from console_utils import setup_console

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NO_SONG = 2


def build_parser():
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="随机点歌系统命令行入口（默认静默抽歌，不显示主窗口）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python run.py                      静默抽一首（当前歌单）\n"
            "  python run.py --json               静默抽一首并以 JSON 输出\n"
            "  python run.py -p 默认歌单 -n 3      从指定歌单抽 3 首\n"
            "  python run.py --jump --jump-delay 2  抽完 2 秒后打开网页\n"
            '  python run.py --jump --prefer-search  忽略歌曲链接，一律走搜索/自定义\n'
            '  python run.py --jump --url "https://search.bilibili.com/all?keyword={query}"  跳 B 站搜歌\n'
            "  python run.py --no-save            预览，不写记录/不改防重复状态\n"
            "  python run.py --gui                打开交互式主菜单\n"
        ),
    )
    parser.add_argument("--version", action="version", version="随机点歌系统 v2.1")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--silent", "-s", action="store_true", help="静默抽歌（默认模式）")
    mode.add_argument("--gui", "--menu", dest="gui", action="store_true", help="打开交互式主菜单")

    parser.add_argument("-p", "--playlist", metavar="歌单", help="指定歌单（ID 或名称），默认当前歌单")
    parser.add_argument("-n", "--count", type=int, default=1, metavar="N", help="抽取数量，默认 1")

    jump = parser.add_argument_group("跳转相关")
    onoff = jump.add_mutually_exclusive_group()
    onoff.add_argument("--jump", action="store_true", help="本次强制开启自动跳转")
    onoff.add_argument("--no-jump", action="store_true", help="本次不自动跳转")
    jump.add_argument("--jump-mode", choices=["search", "custom"], help="覆盖跳转模式")
    jump.add_argument("--url", metavar="URL", help="自定义跳转 URL（隐含 custom 模式，支持 {query}/{song}/{artist} 占位符）")
    jump.add_argument("--jump-delay", type=int, metavar="秒", help="覆盖跳转延时")
    prefer = jump.add_mutually_exclusive_group()
    prefer.add_argument("--prefer-search", action="store_true", help="忽略歌曲自带链接，一律走模式（搜索/自定义）")
    prefer.add_argument("--no-prefer-search", action="store_true", help="有自带链接时优先打开链接（默认）")

    record = parser.add_argument_group("记录相关")
    record.add_argument("--no-save", action="store_true", help="不写播放记录、不更新防重复状态")
    record.add_argument("--reset-before", action="store_true", help="抽歌前先重置防重复记录")

    output = parser.add_argument_group("输出相关")
    output.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    output.add_argument("--quiet", "-q", action="store_true", help="仅输出歌曲名")
    output.add_argument("--list-playlists", action="store_true", help="列出所有歌单后退出")

    parser.add_argument("--qq-sync", action="store_true", help="抽歌前先同步 QQ 歌单（默认不联网）")
    return parser


def resolve_playlist(token):
    """把歌单 ID 或名称解析为 ID；为空取当前歌单；找不到返回 None。"""
    from config_manager import get_current_playlist_id, get_playlists

    playlists = get_playlists()
    if not token:
        return get_current_playlist_id()
    if token in playlists:
        return token
    for playlist_id, entry in playlists.items():
        if entry.get("name") == token:
            return playlist_id
    return None


def list_playlists(as_json=False):
    from config_manager import get_current_playlist_id, get_playlists

    current = get_current_playlist_id()
    items = []
    for playlist_id, entry in get_playlists().items():
        items.append(
            {
                "id": playlist_id,
                "name": entry.get("name"),
                "song_count": entry.get("song_count", 0),
                "current": playlist_id == current,
            }
        )
    if as_json:
        print(json.dumps(items, ensure_ascii=False))
    else:
        for item in items:
            mark = " *当前" if item["current"] else ""
            print(f"{item['id']}\t{item['name']}\t{item['song_count']}首{mark}")
    return EXIT_OK


def _build_jump_config(args):
    from config_manager import get_auto_jump_config

    config = get_auto_jump_config()
    if args.jump:
        config["enabled"] = True
    if args.no_jump:
        config["enabled"] = False
    if args.jump_mode:
        config["mode"] = args.jump_mode
    if args.url:
        config["mode"] = "custom"
        config["custom_url"] = args.url
    if args.jump_delay is not None:
        config["delay"] = max(0, args.jump_delay)
    if getattr(args, "prefer_search", False):
        config["prefer_search"] = True
    if getattr(args, "no_prefer_search", False):
        config["prefer_search"] = False
    if config.get("mode") == "custom" and not config.get("custom_url"):
        config["enabled"] = False
    return config


def _json_song(song):
    return {
        "id": song.get("id"),
        "song_name": song.get("song_name", ""),
        "artist": song.get("artist", ""),
        "url": song.get("url", ""),
        "requested_by": song.get("requested_by", ""),
    }


def _emit(results, args, playlist_id):
    if args.json:
        from config_manager import playlist_name

        print(
            json.dumps(
                {
                    "ok": True,
                    "playlist": playlist_id,
                    "playlist_name": playlist_name(playlist_id),
                    "count": len(results),
                    "songs": [_json_song(song) for song in results],
                },
                ensure_ascii=False,
            )
        )
        return
    if args.quiet:
        for song in results:
            print(song.get("song_name", ""))
        return
    for song in results:
        print(
            f"{song.get('song_name', '')} - {song.get('artist') or '未知'}"
            f"（点歌人: {song.get('requested_by') or '未知'}）"
        )
        if song.get("url"):
            print(f"  链接: {song['url']}")


def run_headless(args):
    """静默抽歌：不显示菜单、不等待输入，按参数抽完即退出。"""
    from duplicate_prevention_manager import get_prevention, pick_song, save_prevention
    from history_manager import record_play
    from main import initialize_system
    from song_manager import load_songs

    initialize_system(quiet=True)

    playlist_id = resolve_playlist(args.playlist)
    if playlist_id is None:
        print(f"错误：找不到歌单 '{args.playlist}'（可用 --list-playlists 查看）", file=sys.stderr)
        return EXIT_ERROR

    if args.qq_sync:
        try:
            from qq_importer import sync_qq_playlist

            sync_qq_playlist(target_playlist_id=playlist_id, verbose=False)
        except Exception as exc:  # noqa: BLE001 - 离线/网络异常不该中断抽歌
            print(f"警告：QQ 同步失败（已跳过）：{exc}", file=sys.stderr)

    if args.reset_before:
        config = get_prevention(playlist_id)
        config["played_songs"] = []
        config["last_reset_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_prevention(playlist_id, config)

    songs = load_songs(playlist_id)
    jump_config = _build_jump_config(args)

    results = []
    for _ in range(max(0, args.count)):
        song = pick_song(playlist_id, songs, persist=not args.no_save)
        if song is None:
            break
        results.append(song)
        if not args.no_save:
            record_play(song, playlist_id)

        from auto_jump_manager import auto_jump, try_local_playback

        played_local = try_local_playback(song, verbose=False)
        if not played_local and jump_config.get("enabled"):
            auto_jump(song, jump_config, verbose=False)

    if not results:
        print(
            "没有可用的歌曲（歌单为空，或都在防重复窗口内且未开启自动重置）",
            file=sys.stderr,
        )
        return EXIT_NO_SONG

    _emit(results, args, playlist_id)
    return EXIT_OK


def main(argv=None):
    setup_console()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_playlists:
        return list_playlists(args.json)

    if args.gui:
        import main as app_main

        app_main.cli()
        return EXIT_OK

    return run_headless(args)


if __name__ == "__main__":
    sys.exit(main())
