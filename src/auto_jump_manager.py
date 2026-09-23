"""
自动网页跳转：随机点歌后自动打开歌曲链接或搜索页。

跳转优先级：
  1. 歌曲自带链接（url）—— 除非开启了 prefer_search（优先搜索）；
  2. 按模式：
     - search：用「歌名 歌手」在 B 站搜索；
     - custom：打开自定义 URL，支持占位符 {query} / {song} / {artist}。
"""

import os
import time
import webbrowser
from urllib.parse import quote

from config_manager import get_auto_jump_config, save_auto_jump_config
from history_manager import record_operation


def expand_url(template, song_info):
    """展开自定义 URL 中的占位符：{query}/{song}/{artist}（自动 URL 编码）。"""
    if not template:
        return template
    song = (song_info.get("song_name") or "").strip()
    artist = (song_info.get("artist") or "").strip()
    query = f"{song} {artist}".strip()
    url = template
    for key, value in (
        ("{query}", quote(query)),
        ("{song}", quote(song)),
        ("{artist}", quote(artist)),
    ):
        url = url.replace(key, value)
    return url


def _update(**fields):
    config = get_auto_jump_config()
    config.update(fields)
    save_auto_jump_config(config)
    return config


def enable_auto_jump():
    _update(enabled=True)
    record_operation("启用自动跳转", "")
    print("✅ 已启用自动跳转")


def disable_auto_jump():
    _update(enabled=False)
    record_operation("关闭自动跳转", "")
    print("✅ 已关闭自动跳转")


def toggle_prefer_search():
    config = get_auto_jump_config()
    config["prefer_search"] = not config.get("prefer_search", False)
    save_auto_jump_config(config)
    if config["prefer_search"]:
        record_operation("切换优先搜索", "状态: 开启")
        print("✅ 已开启「优先搜索」：忽略歌曲自带链接，一律按模式跳转")
    else:
        record_operation("切换优先搜索", "状态: 关闭")
        print("✅ 已关闭「优先搜索」：有自带链接时优先打开链接")


def try_local_playback(song, verbose=True):
    """本地播放模式：启用且歌曲带本地文件（且存在）时播放它；返回是否已处理。"""
    try:
        from config_manager import get_local_playback

        config = get_local_playback()
    except Exception:
        return False
    if not config.get("enabled"):
        return False

    path = (song or {}).get("local_path") or ""
    if not path or not os.path.exists(path):
        return False

    try:
        if hasattr(os, "startfile"):
            os.startfile(path)  # Windows
        else:
            import subprocess
            import sys

            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.Popen([opener, path])
        record_operation("本地播放", f"文件: {path}")
        if verbose:
            print(f"▶ 已调用本地播放器: {path}")
        return True
    except Exception as exc:  # noqa: BLE001
        if verbose:
            print(f"⚠️ 本地播放失败: {exc}")
        return False


def set_jump_mode():
    print("\n🌐 跳转模式设置")
    print("=" * 30)
    print("1. 🔍 搜索跳转（用歌名在 B 站搜索）")
    print("2. 🔗 自定义 URL（支持 {query}/{song}/{artist} 占位符）")
    choice = input("请选择跳转模式: ").strip()
    if choice == "1":
        _update(mode="search")
        record_operation("设置跳转模式", "搜索跳转模式")
        print("✅ 已设为搜索跳转模式")
    elif choice == "2":
        print("示例: https://search.bilibili.com/all?keyword={query}")
        custom_url = input("请输入自定义 URL（可含占位符）: ").strip()
        if not custom_url:
            print("❌ URL 不能为空")
            return
        _update(mode="custom", custom_url=custom_url)
        record_operation("设置跳转模式", f"自定义URL: {custom_url}")
        print(f"✅ 已设为自定义 URL: {custom_url}")
    else:
        print("❌ 无效的选择")


def set_jump_delay():
    config = get_auto_jump_config()
    print("\n⏰ 设置跳转延时")
    print("=" * 30)
    print(f"当前延时: {config['delay']} 秒")
    try:
        delay = int(input("请输入跳转延时 (0-60 秒): ").strip())
    except ValueError:
        print("❌ 请输入有效的数字")
        return
    if not (0 <= delay <= 60):
        print("❌ 延时必须在 0-60 秒之间")
        return
    _update(delay=delay)
    record_operation("设置跳转延时", f"{delay}秒")
    print(f"✅ 已设置跳转延时为 {delay} 秒")


def auto_jump(song_info, config=None, verbose=True):
    """根据配置打开网页。任何异常都不应中断点歌主流程。

    config 为空时读取全局设置；传入 dict 可覆盖本次行为（命令行参数用）。
    verbose=False 时不向标准输出打印提示（静默模式用，保持 stdout 干净）。
    """
    if config is None:
        config = get_auto_jump_config()
    if not config.get("enabled"):
        return

    def say(message):
        if verbose:
            print(message)

    delay = int(config.get("delay", 3))
    if delay > 0:
        say(f"\n⏰ 将在 {delay} 秒后自动跳转...")
        time.sleep(delay)

    song_url = (song_info.get("url") or "").strip()
    prefer_search = bool(config.get("prefer_search"))

    # 1. 歌曲自带链接优先（除非开启「优先搜索」）
    if song_url and not prefer_search:
        try:
            webbrowser.open(song_url)
            record_operation("自动跳转", f"歌曲URL: {song_url}")
            say(f"✅ 已打开歌曲链接: {song_url}")
            return
        except Exception as exc:  # noqa: BLE001 - 不希望跳转失败影响主流程
            say(f"⚠️ 打开歌曲链接失败: {exc}")

    # 2. 按模式跳转
    mode = config.get("mode")
    if mode == "search":
        song_name = (song_info.get("song_name") or "").strip()
        artist = (song_info.get("artist") or "").strip()
        if song_name:
            query = f"{song_name} {artist}".strip()
            url = f"https://search.bilibili.com/all?keyword={quote(query)}"
            try:
                webbrowser.open(url)
                record_operation("自动跳转", f"B站搜索: {query}")
                say(f"✅ 已打开 B 站搜索: {query}")
            except Exception as exc:  # noqa: BLE001
                say(f"⚠️ 打开搜索页失败: {exc}")
    elif mode == "custom" and config.get("custom_url"):
        url = expand_url(config["custom_url"], song_info)
        try:
            webbrowser.open(url)
            record_operation("自动跳转", f"自定义URL: {url}")
            say(f"✅ 已打开自定义 URL: {url}")
        except Exception as exc:  # noqa: BLE001
            say(f"⚠️ 打开自定义 URL 失败: {exc}")


def view_auto_jump_settings():
    config = get_auto_jump_config()
    if config.get("mode") == "search":
        mode_text = "🔍 搜索跳转（B 站搜索「歌名 歌手」）"
    else:
        mode_text = f"🔗 自定义 URL: {config.get('custom_url')}"
    print("\n🌐 自动网页跳转设置")
    print("=" * 40)
    print(f"当前状态: {'✅ 启用' if config.get('enabled') else '❌ 关闭'}")
    print(f"跳转模式: {mode_text}")
    print(f"跳转延时: {config.get('delay', 3)} 秒")
    print(f"优先搜索: {'✅ 开（忽略歌曲自带链接）' if config.get('prefer_search') else '❌ 关（有链接先开链接）'}")
    print("=" * 40)


def auto_jump_menu():
    while True:
        config = get_auto_jump_config()
        state = "✅ 启用" if config.get("enabled") else "❌ 关闭"
        prefer = "开" if config.get("prefer_search") else "关"
        print(f"\n🌐 自动网页跳转设置（当前状态: {state}，优先搜索: {prefer}）")
        print("=" * 40)
        print("1. 启用自动跳转")
        print("2. 关闭自动跳转")
        print("3. 跳转模式设置")
        print("4. 设置跳转延时")
        print("5. 切换「优先搜索」（忽略歌曲自带链接）")
        print("6. 查看当前设置")
        print("7. 返回设置菜单")
        choice = input("请选择操作: ").strip()
        if choice == "1":
            enable_auto_jump()
        elif choice == "2":
            disable_auto_jump()
        elif choice == "3":
            set_jump_mode()
        elif choice == "4":
            set_jump_delay()
        elif choice == "5":
            toggle_prefer_search()
        elif choice == "6":
            view_auto_jump_settings()
        elif choice == "7":
            break
        else:
            print("❌ 无效的选择，请重新输入")
