"""
QQ 音乐歌单拉取与同步。

数据源为 QQ 音乐的公开接口（c.y.qq.com），输入歌单分享链接或歌单 ID 即可。
没有网络 / 未装 requests 时不会让主程序崩溃，只会给出提示。
"""

import re
import urllib.parse

from config_manager import (
    get_current_playlist_id,
    get_qq_sync_config,
    playlist_name,
    save_qq_sync_config,
)
from history_manager import record_operation
from song_manager import load_songs, new_song_id, save_songs
from playlist_manager import ensure_playlist_files, register_playlist, unique_playlist_id

QQ_API = "https://c.y.qq.com/v8/fcg-bin/fcg_v8_playlist_cp.fcg"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://y.qq.com/",
}
QQ_IMPORT_REQUESTER = "QQ歌单导入"


def requests_available():
    try:
        import requests  # noqa: F401

        return True
    except ImportError:
        return False


def _requests():
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - 环境相关
        raise RuntimeError(
            "缺少 requests 库，无法拉取 QQ 歌单。请运行 install_offline.bat 安装依赖。"
        ) from exc
    return requests


def extract_playlist_id(url_or_id):
    """从分享链接 / 纯 ID 中提取 QQ 歌单 ID。"""
    text = (url_or_id or "").strip()
    if text.isdigit():
        return text
    match = re.search(r"/playlist/(\d+)", text)
    if match:
        return match.group(1)
    # 短链：跟随重定向
    requests = _requests()
    resp = requests.get(text, allow_redirects=True, timeout=15, headers=HEADERS)
    match = re.search(r"/playlist/(\d+)", resp.url)
    if match:
        return match.group(1)
    raise ValueError(f"无法从链接中提取歌单 ID: {url_or_id}")


def fetch_qq_playlist(playlist_id, timeout=15):
    """调用公开接口获取歌单歌曲，返回 [{song_name, artist, url}]。"""
    requests = _requests()
    params = {
        "g_tk": "5381",
        "loginUin": "0",
        "hostUin": "0",
        "format": "json",
        "inCharset": "utf8",
        "outCharset": "utf-8",
        "notice": "0",
        "platform": "yqq.json",
        "needNewCode": "0",
        "ct": "24",
        "cid": "205360838",
        "id": str(playlist_id),
    }
    resp = requests.get(QQ_API, params=params, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"QQ 接口返回错误: code={data.get('code')}")

    cdlist = (data.get("data") or {}).get("cdlist") or []
    if not cdlist:
        raise RuntimeError("歌单为空或不存在")
    raw_songs = cdlist[0].get("songlist") or []

    songs = []
    for item in raw_songs:
        song_name = (item.get("songname") or "").strip()
        if not song_name:
            continue
        singers = item.get("singer") or []
        artist = "、".join(s.get("name", "") for s in singers if s.get("name"))
        song_mid = item.get("songmid") or ""
        url = f"https://y.qq.com/n/ryqq/songDetail/{song_mid}" if song_mid else ""
        songs.append({"song_name": song_name, "artist": artist, "url": url})
    return songs


def _dedup_key(song):
    return (
        str(song.get("song_name", "")).strip().lower(),
        str(song.get("artist", "")).strip().lower(),
    )


def _to_song_dict(item, now):
    return {
        "id": new_song_id(),
        "song_name": item["song_name"],
        "artist": item.get("artist", ""),
        "url": item.get("url", ""),
        "requested_by": QQ_IMPORT_REQUESTER,
        "created_at": now,
        "last_modified": now,
    }


def _now_str():
    import datetime

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def import_qq_playlist(url_or_id, new_playlist_name=None, target_playlist_id=None):
    """
    拉取 QQ 歌单并写入。
    - target_playlist_id 不为空：合并进该歌单（按 歌名+歌手 去重）；
    - 否则新建歌单（用 new_playlist_name）。
    返回 (playlist_id, 新增数量) 或抛出异常。
    """
    qq_id = extract_playlist_id(url_or_id)
    fetched = fetch_qq_playlist(qq_id)
    if not fetched:
        raise RuntimeError("该歌单没有可用歌曲")

    now = _now_str()

    if target_playlist_id:
        pid = target_playlist_id
        songs = load_songs(pid)
        existing = {_dedup_key(song) for song in songs}
        added = 0
        for item in fetched:
            if _dedup_key(item) in existing:
                continue
            songs.append(_to_song_dict(item, now))
            existing.add(_dedup_key(item))
            added += 1
        save_songs(songs, pid)
        return pid, added

    if not new_playlist_name:
        new_playlist_name = f"QQ歌单_{qq_id}"
    pid = unique_playlist_id(new_playlist_name)
    register_playlist(pid, new_playlist_name, f"从 QQ 音乐歌单 {qq_id} 导入")
    songs = [_to_song_dict(item, now) for item in fetched]
    ensure_playlist_files(pid, songs=songs)
    return pid, len(songs)


def sync_qq_playlist(target_playlist_id=None, verbose=True):
    """按配置同步 QQ 歌单到目标歌单（默认当前歌单）。返回 (added, total)。"""
    config = get_qq_sync_config()
    qq_id = (config.get("playlist_id") or "").strip()
    if not qq_id:
        raise RuntimeError("尚未配置 QQ 歌单 ID")

    pid = target_playlist_id or get_current_playlist_id()
    if not pid:
        raise RuntimeError("没有可用的目标歌单")

    if verbose:
        print(f"🔄 正在从 QQ 歌单 {qq_id} 同步到「{playlist_name(pid)}」...")
    _, added = import_qq_playlist(qq_id, target_playlist_id=pid)
    total = len(load_songs(pid))
    record_operation("QQ歌单同步", f"QQ歌单: {qq_id}, 新增: {added}首, 总计: {total}首", playlist_id=pid)
    if verbose:
        print(f"✅ 同步完成：新增 {added} 首，歌单现有 {total} 首")
    return added, total


def auto_sync_on_start():
    """启动时自动同步；任何失败都软着陆，不阻断启动。返回状态文本或 None。"""
    config = get_qq_sync_config()
    if not config.get("enabled") or not config.get("auto_on_start"):
        return None
    if not (config.get("playlist_id") or "").strip():
        return None
    if not requests_available():
        return "跳过 QQ 自动同步：未安装 requests"
    try:
        added, total = sync_qq_playlist(verbose=False)
        return f"QQ 歌单已同步：新增 {added} 首，共 {total} 首"
    except Exception as exc:  # noqa: BLE001 - 离线/网络异常都不该让程序起不来
        return f"QQ 自动同步失败（不影响使用）：{exc}"


# ---------------------------------------------------------------------------
# 菜单
# ---------------------------------------------------------------------------

def import_qq_playlist_interactive():
    if not requests_available():
        print("❌ 未安装 requests，无法拉取 QQ 歌单。请先运行 install_offline.bat")
        return
    print("\n🎵 从 QQ 音乐歌单导入")
    print("=" * 40)
    url = input("请输入 QQ 歌单分享链接或歌单 ID: ").strip().strip('"')
    if not url:
        print("❌ 输入不能为空")
        return
    name = input("新歌单名称（可留空，默认用歌单 ID 命名）: ").strip()
    try:
        pid, count = import_qq_playlist(url, new_playlist_name=name or None)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ 导入失败: {exc}")
        return
    print(f"✅ 导入完成：新增 {count} 首，歌单「{playlist_name(pid)}」")


def qq_sync_menu():
    while True:
        config = get_qq_sync_config()
        state = "✅ 启用" if config.get("enabled") else "❌ 关闭"
        auto = "开" if config.get("auto_on_start") else "关"
        print(f"\n🎵 QQ 歌单同步（总开关: {state}，启动自动同步: {auto}）")
        print("=" * 50)
        print(f"当前 QQ 歌单 ID: {config.get('playlist_id') or '（未设置）'}")
        print("1. 设置 QQ 歌单 ID / 链接")
        print("2. 启用/关闭自动同步")
        print("3. 启用/关闭「启动时自动同步」")
        print("4. 立即同步到当前歌单")
        print("5. 从 QQ 歌单导入为新歌单")
        print("6. 返回设置菜单")
        choice = input("请选择操作: ").strip()

        if choice == "1":
            value = input("请输入 QQ 歌单分享链接或 ID: ").strip().strip('"')
            if not value:
                print("❌ 输入不能为空")
                continue
            config["playlist_id"] = value
            save_qq_sync_config(config)
            record_operation("设置QQ歌单", f"歌单: {value}")
            print("✅ 已保存（将在同步时自动解析为歌单 ID）")
        elif choice == "2":
            config["enabled"] = not config.get("enabled")
            save_qq_sync_config(config)
            print(f"✅ 自动同步已{'启用' if config['enabled'] else '关闭'}")
        elif choice == "3":
            config["auto_on_start"] = not config.get("auto_on_start")
            save_qq_sync_config(config)
            print(f"✅ 启动时自动同步已{'开启' if config['auto_on_start'] else '关闭'}")
        elif choice == "4":
            try:
                sync_qq_playlist()
            except Exception as exc:  # noqa: BLE001
                print(f"❌ 同步失败: {exc}")
        elif choice == "5":
            import_qq_playlist_interactive()
        elif choice == "6":
            break
        else:
            print("❌ 无效的选择，请重新输入")
