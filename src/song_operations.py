"""
歌曲管理菜单：增 / 改 / 删 / 查。
"""

from config_manager import get_current_playlist_id, playlist_name
from history_manager import record_operation
from requester_manager import get_requester_names
from song_manager import (
    filter_valid_songs,
    load_songs,
    new_song_id,
    save_songs,
)


def _now_str():
    import datetime

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def add_song():
    pid = get_current_playlist_id()
    songs = load_songs(pid)
    requesters = get_requester_names(pid)
    print(f"\n🎵 添加歌曲（歌单: {playlist_name(pid)}）")
    print("=" * 40)

    while True:
        song_name = input("请输入歌曲名称: ").strip()
        if song_name:
            break
        print("歌曲名称不能为空，请重新输入")
    artist = input("请输入歌手名称（可留空）: ").strip()
    url = input("请输入歌曲链接（可留空）: ").strip()

    requested_by = "未知"
    if requesters:
        print("\n👥 请选择点歌人:")
        print("0. 未知")
        for index, requester in enumerate(requesters, 1):
            print(f"{index}. {requester}")
        try:
            choice = int(input("请选择点歌人编号: ").strip() or "0")
            if 0 < choice <= len(requesters):
                requested_by = requesters[choice - 1]
        except ValueError:
            print("❌ 输入无效，将记为「未知」")
    else:
        requested_by = input("请输入点歌人姓名（可留空）: ").strip() or "未知"

    now = _now_str()
    song = {
        "id": new_song_id(),
        "song_name": song_name,
        "artist": artist,
        "url": url,
        "requested_by": requested_by,
        "created_at": now,
        "last_modified": now,
    }
    songs.append(song)
    if save_songs(songs, pid):
        record_operation(
            "添加歌曲",
            f"歌曲: {song_name} - 歌手: {artist} - 点歌人: {requested_by}",
            playlist_id=pid,
        )
        print(f"✅ 已添加歌曲: {song_name}")
    else:
        record_operation("添加歌曲", f"歌曲: {song_name}", result="失败", playlist_id=pid)
        print("❌ 添加歌曲失败")


def modify_song():
    pid = get_current_playlist_id()
    songs = load_songs(pid)
    valid_songs = filter_valid_songs(songs)
    if not valid_songs:
        print("❌ 当前没有有效歌曲")
        return

    print(f"\n🎵 修改歌曲（歌单: {playlist_name(pid)}）")
    print("=" * 40)
    for index, song in enumerate(valid_songs, 1):
        print(f"{index}. {song['song_name']} - {song.get('artist') or '未知'}（点歌人: {song.get('requested_by') or '未知'}）")
    try:
        choice = int(input("\n请选择要修改的歌曲编号: ").strip())
    except ValueError:
        print("❌ 请输入有效的数字")
        return
    if not (1 <= choice <= len(valid_songs)):
        print("❌ 无效的选择")
        return

    target = valid_songs[choice - 1]
    original_name = target["song_name"]
    print(f"\n正在修改: {original_name}（直接回车表示不修改）")

    new_name = input(f"新的歌曲名称（原: {target['song_name']}）: ").strip()
    if new_name:
        target["song_name"] = new_name
    new_artist = input(f"新的歌手（原: {target.get('artist') or '空'}）: ").strip()
    if new_artist:
        target["artist"] = new_artist
    new_url = input(f"新的链接（原: {target.get('url') or '空'}）: ").strip()
    if new_url:
        target["url"] = new_url

    requesters = get_requester_names(pid)
    if requesters:
        print(f"\n0. 保持原值: {target.get('requested_by') or '未知'}")
        for index, requester in enumerate(requesters, 1):
            print(f"{index}. {requester}")
        try:
            requester_choice = int(input("请选择点歌人编号: ").strip() or "0")
            if 0 < requester_choice <= len(requesters):
                target["requested_by"] = requesters[requester_choice - 1]
        except ValueError:
            print("❌ 输入无效，保持原值")

    target["last_modified"] = _now_str()
    if save_songs(songs, pid):
        record_operation(
            "修改歌曲", f"歌曲: {original_name} -> {target['song_name']}", playlist_id=pid
        )
        print(f"✅ 已修改歌曲: {original_name} -> {target['song_name']}")
    else:
        record_operation("修改歌曲", f"歌曲: {original_name}", result="失败", playlist_id=pid)
        print("❌ 修改歌曲失败")


def delete_song():
    pid = get_current_playlist_id()
    songs = load_songs(pid)
    valid_songs = filter_valid_songs(songs)
    if not valid_songs:
        print("❌ 当前没有有效歌曲")
        return

    print(f"\n🎵 删除歌曲（歌单: {playlist_name(pid)}）")
    print("=" * 40)
    for index, song in enumerate(valid_songs, 1):
        print(f"{index}. {song['song_name']} - {song.get('artist') or '未知'}（点歌人: {song.get('requested_by') or '未知'}）")
    try:
        choice = int(input("\n请选择要删除的歌曲编号: ").strip())
    except ValueError:
        print("❌ 请输入有效的数字")
        return
    if not (1 <= choice <= len(valid_songs)):
        print("❌ 无效的选择")
        return

    target = valid_songs[choice - 1]
    if input(f"确定删除歌曲 '{target['song_name']}' 吗？(y/N): ").strip().lower() != "y":
        print("取消删除")
        return

    songs = [song for song in songs if song.get("id") != target.get("id")]
    if save_songs(songs, pid):
        record_operation("删除歌曲", f"歌曲: {target['song_name']}", playlist_id=pid)
        print(f"✅ 已删除歌曲: {target['song_name']}")
    else:
        record_operation("删除歌曲", f"歌曲: {target['song_name']}", result="失败", playlist_id=pid)
        print("❌ 删除歌曲失败")


def view_all_songs():
    pid = get_current_playlist_id()
    songs = filter_valid_songs(load_songs(pid))
    print(f"\n🎵 所有歌曲列表（歌单: {playlist_name(pid)}）")
    print("=" * 60)
    if not songs:
        print("暂无歌曲")
    else:
        for index, song in enumerate(songs, 1):
            print(f"{index}. {song['song_name']}")
            print(f"   歌手: {song.get('artist') or '未知'}")
            print(f"   点歌人: {song.get('requested_by') or '未知'}")
            print(f"   链接: {song.get('url') or '无'}")
            print("-" * 40)
    print(f"\n📊 共 {len(songs)} 首有效歌曲")
    print("=" * 60)


def song_management_menu():
    while True:
        pid = get_current_playlist_id()
        print(f"\n🎵 歌曲管理（当前歌单: {playlist_name(pid)}）")
        print("=" * 30)
        print("1. 添加歌曲")
        print("2. 修改歌曲")
        print("3. 删除歌曲")
        print("4. 查看所有歌曲")
        print("5. 返回主菜单")
        choice = input("请选择操作: ").strip()
        if choice == "1":
            add_song()
        elif choice == "2":
            modify_song()
        elif choice == "3":
            delete_song()
        elif choice == "4":
            view_all_songs()
        elif choice == "5":
            break
        else:
            print("❌ 无效的选择，请重新输入")
