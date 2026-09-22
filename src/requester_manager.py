"""
点歌人管理：读写 requesters.yaml，并维护歌曲里的点歌人引用。
"""

from config_manager import get_current_playlist_id, playlist_name
from history_manager import record_operation
from paths import playlist_requesters_file
from song_manager import load_songs, save_songs
from storage import load_yaml, save_yaml


def _normalize(item):
    if isinstance(item, str):
        return {"name": item.strip(), "email": "", "notes": ""}
    if isinstance(item, dict):
        return {
            "name": str(item.get("name", "")).strip(),
            "email": str(item.get("email", "")),
            "notes": str(item.get("notes", "")),
        }
    return None


def load_requesters(playlist_id=None):
    pid = playlist_id or get_current_playlist_id()
    if not pid:
        return []
    data = load_yaml(playlist_requesters_file(pid), default={})
    raw = data.get("requesters") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        raw = []
    requesters = []
    healed = False
    for item in raw:
        normalized = _normalize(item)
        if normalized is None:
            healed = True
            continue
        if not isinstance(item, dict):
            healed = True
        requesters.append(normalized)
    if healed:
        save_requesters(requesters, pid)
    return requesters


def save_requesters(requesters, playlist_id=None):
    pid = playlist_id or get_current_playlist_id()
    if not pid:
        print("[错误] 没有可用的歌单，无法保存点歌人")
        return False
    try:
        save_yaml(playlist_requesters_file(pid), {"requesters": requesters})
        return True
    except OSError as exc:
        print(f"[错误] 保存点歌人失败: {exc}")
        return False


def get_requester_names(playlist_id=None):
    return [item["name"] for item in load_requesters(playlist_id) if item["name"]]


def add_requester():
    pid = get_current_playlist_id()
    name = playlist_name(pid)
    requesters = load_requesters(pid)
    print(f"\n🎤 添加点歌人（歌单: {name}）")
    print("=" * 30)
    while True:
        requester_name = input("请输入点歌人姓名: ").strip()
        if not requester_name:
            print("姓名不能为空，请重新输入")
            continue
        if requester_name in [item["name"] for item in requesters]:
            print(f"点歌人 '{requester_name}' 已存在")
            continue
        break
    email = input("备注邮箱（可留空）: ").strip()
    notes = input("备注（可留空）: ").strip()
    requesters.append({"name": requester_name, "email": email, "notes": notes})
    if save_requesters(requesters, pid):
        record_operation("添加点歌人", f"点歌人: {requester_name}", playlist_id=pid)
        print(f"✅ 已添加点歌人: {requester_name}")


def delete_requester():
    pid = get_current_playlist_id()
    requesters = load_requesters(pid)
    if not requesters:
        print("❌ 当前没有点歌人")
        return
    print("\n🎤 删除点歌人")
    print("=" * 30)
    for index, item in enumerate(requesters, 1):
        print(f"{index}. {item['name']}")
    try:
        choice = int(input("\n请选择要删除的编号: ").strip())
    except ValueError:
        print("❌ 请输入有效的数字")
        return
    if not (1 <= choice <= len(requesters)):
        print("❌ 无效的选择")
        return
    target = requesters[choice - 1]["name"]
    if input(f"确定删除点歌人 '{target}' 吗？(y/N): ").strip().lower() != "y":
        print("取消删除")
        return
    requesters.pop(choice - 1)
    if save_requesters(requesters, pid):
        record_operation("删除点歌人", f"点歌人: {target}", playlist_id=pid)
        print(f"✅ 已删除点歌人: {target}")


def modify_requester():
    pid = get_current_playlist_id()
    requesters = load_requesters(pid)
    if not requesters:
        print("❌ 当前没有点歌人")
        return
    print("\n🎤 修改点歌人")
    print("=" * 30)
    for index, item in enumerate(requesters, 1):
        print(f"{index}. {item['name']}")
    try:
        choice = int(input("\n请选择要修改的编号: ").strip())
    except ValueError:
        print("❌ 请输入有效的数字")
        return
    if not (1 <= choice <= len(requesters)):
        print("❌ 无效的选择")
        return

    old_name = requesters[choice - 1]["name"]
    names = [item["name"] for item in requesters]
    while True:
        new_name = input(f"新的姓名（原: {old_name}）: ").strip()
        if not new_name:
            print("姓名不能为空")
            continue
        if new_name != old_name and new_name in names:
            print(f"点歌人 '{new_name}' 已存在")
            continue
        break

    requesters[choice - 1]["name"] = new_name
    save_requesters(requesters, pid)

    # 同步更新歌曲里的点歌人引用
    songs = load_songs(pid)
    changed = 0
    for song in songs:
        if song.get("requested_by") == old_name:
            song["requested_by"] = new_name
            changed += 1
    if changed:
        save_songs(songs, pid)

    record_operation(
        "修改点歌人",
        f"原姓名: {old_name} -> 新姓名: {new_name}（同步 {changed} 首歌）",
        playlist_id=pid,
    )
    print(f"✅ 已修改点歌人: {old_name} -> {new_name}（同步 {changed} 首歌）")


def view_requesters():
    pid = get_current_playlist_id()
    requesters = load_requesters(pid)
    print(f"\n🎤 点歌人列表（歌单: {playlist_name(pid)}）")
    print("=" * 40)
    if not requesters:
        print("暂无点歌人")
    else:
        song_counts = {}
        for song in load_songs(pid):
            requester = song.get("requested_by") or "未知"
            song_counts[requester] = song_counts.get(requester, 0) + 1
        for index, item in enumerate(requesters, 1):
            extra = f"（{song_counts.get(item['name'], 0)}首）"
            print(f"{index}. {item['name']} {extra}")
    print("=" * 40)


def requester_menu():
    while True:
        print("\n🎤 点歌人管理")
        print("=" * 20)
        print("1. 增加点歌人")
        print("2. 删除点歌人")
        print("3. 修改点歌人")
        print("4. 查看点歌人列表")
        print("5. 返回主菜单")
        choice = input("请选择操作: ").strip()
        if choice == "1":
            add_requester()
        elif choice == "2":
            delete_requester()
        elif choice == "3":
            modify_requester()
        elif choice == "4":
            view_requesters()
        elif choice == "5":
            break
        else:
            print("❌ 无效的选择，请重新输入")
