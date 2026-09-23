#!/usr/bin/env python3
"""
从备份 zip 恢复数据（与 GUI 版同逻辑）。

用法:
    python scripts/restore_data.py <备份.zip>            # 自动识别类型，交互确认
    python scripts/restore_data.py <备份.zip> --force    # 跳过确认

说明:
  * 整库备份（条目以 main_data/ 开头）→ 覆盖整个 main_data；恢复前会自动再做一次安全备份。
  * 单歌单备份 → 覆盖对应歌单目录；覆盖前会自动再备份一次该歌单。
"""

import datetime
import os
import shutil
import sys
import tempfile
import zipfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA = os.path.join(_ROOT, "main_data")
_BACKUPS = os.path.join(_ROOT, "backups")


def _stamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _unique(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    index = 2
    while os.path.exists(f"{base}_{index}{ext}"):
        index += 1
    return f"{base}_{index}{ext}"


def _zip_dir(zip_path, source_dir, prefix):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(source_dir):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, source_dir).replace(os.sep, "/")
                zf.write(full, f"{prefix}/{rel}")


def backup_all(suffix=None):
    os.makedirs(_BACKUPS, exist_ok=True)
    name = "main_data_" + _stamp() + (f"_{suffix}" if suffix else "")
    path = _unique(os.path.join(_BACKUPS, name + ".zip"))
    _zip_dir(path, _DATA, "main_data")
    return path


def backup_playlist(playlist_id):
    dest = os.path.join(_DATA, "play_list", playlist_id)
    if not os.path.isdir(dest):
        return None
    os.makedirs(_BACKUPS, exist_ok=True)
    path = _unique(os.path.join(_BACKUPS, f"playlist_{playlist_id}_{_stamp()}.zip"))
    _zip_dir(path, dest, playlist_id)
    return path


def inspect(zip_path):
    """返回 (类型, 文件数, 歌单ID)。类型: full / playlist / unknown。"""
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
    normalized = [n.replace("\\", "/") for n in names]
    if any(n.startswith("main_data/") for n in normalized):
        return ("full", len(names), "")
    tops = {n.split("/")[0] for n in normalized if "/" in n}
    if len(tops) == 1:
        return ("playlist", len(names), tops.pop())
    return ("unknown", len(names), "")


def restore_all(zip_path):
    safety = backup_all("pre-restore")
    temp = os.path.join(tempfile.gettempdir(), "rss_restore_" + os.urandom(8).hex())
    os.makedirs(temp, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(temp)
        extracted = os.path.join(temp, "main_data")
        if not os.path.isdir(extracted):
            raise RuntimeError("备份里没有找到 main_data 目录")

        aside = _unique(_DATA + ".replaced-" + _stamp())
        if os.path.isdir(_DATA):
            os.rename(_DATA, aside)
        try:
            os.rename(extracted, _DATA)
        except Exception:
            if os.path.isdir(_DATA):
                shutil.rmtree(_DATA, ignore_errors=True)
            if os.path.isdir(aside):
                os.rename(aside, _DATA)
            raise
        shutil.rmtree(aside, ignore_errors=True)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    return safety


def restore_playlist(zip_path, playlist_id):
    backup_playlist(playlist_id)  # 覆盖前的安全备份

    dest = os.path.join(_DATA, "play_list", playlist_id)
    if os.path.isdir(dest):
        shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest, exist_ok=True)

    prefix = playlist_id + "/"
    count = 0
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            normalized = name.replace("\\", "/")
            relative = normalized[len(prefix):] if normalized.startswith(prefix) else normalized
            if not relative:
                continue
            out_path = os.path.join(dest, *relative.split("/"))
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with zf.open(name) as src, open(out_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            count += 1

    # 若歌单未在配置里注册，补上
    sys.path.insert(0, os.path.join(_ROOT, "src"))
    from config_manager import get_playlists, register_playlist

    if playlist_id not in get_playlists():
        register_playlist(playlist_id, playlist_id, "从备份恢复")
    return count


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    if not args:
        print(__doc__)
        return 1

    zip_path = args[0]
    if not os.path.isfile(zip_path):
        print(f"文件不存在: {zip_path}")
        return 1

    kind, count, playlist_id = inspect(zip_path)
    if kind == "unknown":
        print("无法识别的备份文件（既不是整库备份，也不是单歌单备份）")
        return 1

    if kind == "full":
        print(f"整库备份（{count} 个文件）→ 将覆盖整个 main_data")
        if not force and input("确定恢复? (y/N): ").strip().lower() != "y":
            print("已取消")
            return 0
        safety = restore_all(zip_path)
        print(f"✅ 已恢复整库。恢复前的数据已备份到: {safety}")
    else:
        print(f"单歌单备份（歌单 ID: {playlist_id}，{count} 个文件）→ 将覆盖该歌单")
        if not force and input("确定恢复? (y/N): ").strip().lower() != "y":
            print("已取消")
            return 0
        files = restore_playlist(zip_path, playlist_id)
        print(f"✅ 已恢复歌单「{playlist_id}」：{files} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
