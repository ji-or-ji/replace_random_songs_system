import json
import os
import time
import webbrowser
from config_manager import load_auto_jump_config, save_auto_jump_config
from history_manager import record_history

def enable_auto_jump():
    """启用自动跳转"""
    config = load_auto_jump_config()
    config['auto_jump_enabled'] = True
    
    if save_auto_jump_config(config):
        record_history("启用自动跳转", "", "成功")
        print("✅ 已启用自动跳转")
    else:
        record_history("启用自动跳转", "", "失败")
        print("❌ 启用自动跳转失败")

def disable_auto_jump():
    """关闭自动跳转"""
    config = load_auto_jump_config()
    config['auto_jump_enabled'] = False
    
    if save_auto_jump_config(config):
        record_history("关闭自动跳转", "", "成功")
        print("✅ 已关闭自动跳转")
    else:
        record_history("关闭自动跳转", "", "失败")
        print("❌ 关闭自动跳转失败")

def set_jump_mode():
    """设置跳转模式"""
    config = load_auto_jump_config()
    
    print("\n🌐 跳转模式设置 🌐")
    print("=" * 30)
    print("1. 🔍 搜索跳转模式")
    print("2. 🔗 自定义URL跳转模式")
    
    try:
        choice = input("请选择跳转模式: ").strip()
        
        if choice == '1':
            config['jump_mode'] = 'search'
            if save_auto_jump_config(config):
                record_history("设置跳转模式", "搜索跳转模式", "成功")
                print("✅ 已设置为搜索跳转模式")
            else:
                record_history("设置跳转模式", "搜索跳转模式", "失败")
                print("❌ 设置跳转模式失败")
        elif choice == '2':
            custom_url = input("请输入自定义URL (例如: https://www.bilibili.com): ").strip()
            if custom_url:
                config['jump_mode'] = 'custom'
                config['custom_url'] = custom_url
                if save_auto_jump_config(config):
                    record_history("设置跳转模式", f"自定义URL跳转模式: {custom_url}", "成功")
                    print(f"✅ 已设置为自定义URL跳转模式: {custom_url}")
                else:
                    record_history("设置跳转模式", f"自定义URL跳转模式: {custom_url}", "失败")
                    print("❌ 设置跳转模式失败")
            else:
                print("❌ 自定义URL不能为空")
        else:
            print("❌ 无效的选择")
    except Exception as e:
        print(f"❌ 设置跳转模式失败: {e}")

def set_jump_delay():
    """设置跳转延时"""
    config = load_auto_jump_config()
    
    print("\n⏰ 设置跳转延时 ⏰")
    print("=" * 30)
    print(f"当前延时: {config['jump_delay']}秒")
    
    try:
        delay = int(input("请输入跳转延时 (1-60秒): ").strip())
        if 1 <= delay <= 60:
            config['jump_delay'] = delay
            if save_auto_jump_config(config):
                record_history("设置跳转延时", f"{delay}秒", "成功")
                print(f"✅ 已设置跳转延时为 {delay}秒")
            else:
                record_history("设置跳转延时", f"{delay}秒", "失败")
                print("❌ 设置跳转延时失败")
        else:
            print("❌ 延时必须在1-60秒之间")
    except ValueError:
        print("❌ 请输入有效的数字")

def auto_jump(song_info):
    """自动跳转功能"""
    config = load_auto_jump_config()
    
    if not config['auto_jump_enabled']:
        return
    
    print(f"\n⏰ 将在 {config['jump_delay']} 秒后自动跳转...")
    time.sleep(config['jump_delay'])
    
    # 优先使用歌曲的URL
    song_url = song_info.get('url_list', '').strip()
    if song_url:
        try:
            webbrowser.open(song_url)
            record_history("自动跳转", f"歌曲URL: {song_url}", "成功")
            print(f"✅ 已跳转到歌曲URL: {song_url}")
            return
        except Exception as e:
            print(f"❌ 跳转到歌曲URL失败: {e}")
    
    # 如果没有歌曲URL，根据配置跳转
    if config['jump_mode'] == 'search':
        # B站搜索跳转
        song_name = song_info.get('song_name', '').strip()
        artist = song_info.get('artist', '').strip()
        
        if song_name:
            search_query = f"{song_name} {artist}".strip()
            bilibili_search_url = f"https://search.bilibili.com/all?keyword={search_query}"
            try:
                webbrowser.open(bilibili_search_url)
                record_history("自动跳转", f"B站搜索: {search_query}", "成功")
                print(f"✅ 已跳转到B站搜索: {search_query}")
            except Exception as e:
                print(f"❌ 跳转到B站搜索失败: {e}")
    
    elif config['jump_mode'] == 'custom' and config['custom_url']:
        # 自定义URL跳转
        try:
            webbrowser.open(config['custom_url'])
            record_history("自动跳转", f"自定义URL: {config['custom_url']}", "成功")
            print(f"✅ 已跳转到自定义URL: {config['custom_url']}")
        except Exception as e:
            print(f"❌ 跳转到自定义URL失败: {e}")

def view_auto_jump_settings():
    """查看自动跳转设置"""
    config = load_auto_jump_config()
    
    print("\n🌐 自动网页跳转设置 🌐")
    print("=" * 40)
    
    status = "✅ 启用" if config['auto_jump_enabled'] else "❌ 禁用"
    mode_text = "🔍 搜索跳转" if config['jump_mode'] == 'search' else f"🔗 自定义URL: {config['custom_url']}"
    
    print(f"当前状态: {status}")
    print(f"跳转模式: {mode_text}")
    print(f"跳转延时: {config['jump_delay']}秒")
    print("=" * 40)

def auto_jump_menu():
    """自动跳转设置菜单"""
    while True:
        config = load_auto_jump_config()
        status = "✅ 启用" if config['auto_jump_enabled'] else "❌ 禁用"
        
        print(f"\n🌐 自动网页跳转设置 🌐 (当前状态: {status})")
        print("=" * 40)
        print("1. 启用自动跳转")
        print("2. 关闭自动跳转")
        print("3. 跳转模式设置")
        print("4. 设置跳转延时")
        print("5. 查看当前设置")
        print("6. 返回设置菜单")
        
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            enable_auto_jump()
        elif choice == '2':
            disable_auto_jump()
        elif choice == '3':
            set_jump_mode()
        elif choice == '4':
            set_jump_delay()
        elif choice == '5':
            view_auto_jump_settings()
        elif choice == '6':
            break
        else:
            print("❌ 无效的选择，请重新输入")
