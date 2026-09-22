"""
自动网页跳转：随机点歌后自动打开歌曲链接或搜索页。
"""

import time
import webbrowser

from config_manager import get_auto_jump_config, save_auto_jump_config
from history_manager import record_operation


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


def set_jump_mode():
    print("\n🌐 跳转模式设置")
    print("=" * 30)
    print("1. 🔍 搜索跳转（用歌名在 B 站搜索）")
    print("2. 🔗 自定义 URL")
    choice = input("请选择跳转模式: ").strip()
    if choice == "1":
        _update(mode="search")
        record_operation("设置跳转模式", "搜索跳转模式")
        print("✅ 已设为搜索跳转模式")
    elif choice == "2":
        custom_url = input("请输入自定义 URL（如 https://www.bilibili.com）: ").strip()
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


def auto_jump(song_info):
    """根据配置打开网页。任何异常都不应中断点歌主流程。"""
    config = get_auto_jump_config()
    if not config.get("enabled"):
        return

    delay = int(config.get("delay", 3))
    if delay > 0:
        print(f"\n⏰ 将在 {delay} 秒后自动跳转...")
        time.sleep(delay)

    song_url = (song_info.get("url") or "").strip()
    if song_url:
        try:
            webbrowser.open(song_url)
            record_operation("自动跳转", f"歌曲URL: {song_url}")
            print(f"✅ 已打开歌曲链接: {song_url}")
            return
        except Exception as exc:  # noqa: BLE001 - 不希望跳转失败影响主流程
            print(f"⚠️ 打开歌曲链接失败: {exc}")

    if config.get("mode") == "search":
        song_name = (song_info.get("song_name") or "").strip()
        artist = (song_info.get("artist") or "").strip()
        if song_name:
            from urllib.parse import quote

            query = f"{song_name} {artist}".strip()
            url = f"https://search.bilibili.com/all?keyword={quote(query)}"
            try:
                webbrowser.open(url)
                record_operation("自动跳转", f"B站搜索: {query}")
                print(f"✅ 已打开 B 站搜索: {query}")
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️ 打开搜索页失败: {exc}")
    elif config.get("mode") == "custom" and config.get("custom_url"):
        try:
            webbrowser.open(config["custom_url"])
            record_operation("自动跳转", f"自定义URL: {config['custom_url']}")
            print(f"✅ 已打开自定义 URL: {config['custom_url']}")
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ 打开自定义 URL 失败: {exc}")


def view_auto_jump_settings():
    config = get_auto_jump_config()
    mode = "🔍 搜索跳转" if config.get("mode") == "search" else f"🔗 自定义 URL: {config.get('custom_url')}"
    print("\n🌐 自动网页跳转设置")
    print("=" * 40)
    print(f"当前状态: {'✅ 启用' if config.get('enabled') else '❌ 关闭'}")
    print(f"跳转模式: {mode}")
    print(f"跳转延时: {config.get('delay', 3)} 秒")
    print("=" * 40)


def auto_jump_menu():
    while True:
        config = get_auto_jump_config()
        state = "✅ 启用" if config.get("enabled") else "❌ 关闭"
        print(f"\n🌐 自动网页跳转设置（当前状态: {state}）")
        print("=" * 40)
        print("1. 启用自动跳转")
        print("2. 关闭自动跳转")
        print("3. 跳转模式设置")
        print("4. 设置跳转延时")
        print("5. 查看当前设置")
        print("6. 返回设置菜单")
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
            view_auto_jump_settings()
        elif choice == "6":
            break
        else:
            print("❌ 无效的选择，请重新输入")
