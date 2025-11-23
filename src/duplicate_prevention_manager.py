import json
import datetime
from config_manager import load_playlist_config, save_playlist_config
from history_manager import record_history

def toggle_duplicate_prevention():
    """切换防重复功能状态"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    prevention_config = config['playlists'][current_playlist_id]['duplicate_prevention']
    
    current_status = prevention_config['enabled']
    new_status = not current_status
    
    prevention_config['enabled'] = new_status
    
    if save_playlist_config(config):
        status_text = "启用" if new_status else "禁用"
        record_history("切换防重复功能", f"歌单: {playlist_name}, 状态: {status_text}", "成功")
        print(f"✅ 已{'启用' if new_status else '禁用'}防重复功能")
    else:
        record_history("切换防重复功能", f"歌单: {playlist_name}", "失败")
        print("❌ 切换防重复功能失败")

def set_prevention_mode():
    """设置防重复模式"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    prevention_config = config['playlists'][current_playlist_id]['duplicate_prevention']
    
    print("\n🔄 防重复模式设置 🔄")
    print("=" * 30)
    print("1. ⏰ 时间窗口模式")
    print("2. 🎲 随机模式")
    
    try:
        choice = input("请选择防重复模式: ").strip()
        
        if choice == '1':
            prevention_config['mode'] = 'time_window'
            if save_playlist_config(config):
                record_history("设置防重复模式", f"歌单: {playlist_name}, 模式: 时间窗口", "成功")
                print("✅ 已设置为时间窗口模式")
            else:
                record_history("设置防重复模式", f"歌单: {playlist_name}, 模式: 时间窗口", "失败")
                print("❌ 设置防重复模式失败")
        elif choice == '2':
            prevention_config['mode'] = 'random'
            if save_playlist_config(config):
                record_history("设置防重复模式", f"歌单: {playlist_name}, 模式: 随机", "成功")
                print("✅ 已设置为随机模式")
            else:
                record_history("设置防重复模式", f"歌单: {playlist_name}, 模式: 随机", "失败")
                print("❌ 设置防重复模式失败")
        else:
            print("❌ 无效的选择")
    except Exception as e:
        print(f"❌ 设置防重复模式失败: {e}")

def set_time_window():
    """设置时间窗口"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    prevention_config = config['playlists'][current_playlist_id]['duplicate_prevention']
    
    print("\n⏰ 设置时间窗口 ⏰")
    print("=" * 30)
    print(f"当前时间窗口: {prevention_config['time_window_hours']}小时{prevention_config['time_window_minutes']}分钟")
    
    try:
        hours = int(input("请输入小时数 (0-24): ").strip())
        minutes = int(input("请输入分钟数 (0-59): ").strip())
        
        if 0 <= hours <= 24 and 0 <= minutes <= 59:
            prevention_config['time_window_hours'] = hours
            prevention_config['time_window_minutes'] = minutes
            
            if save_playlist_config(config):
                record_history("设置时间窗口", f"歌单: {playlist_name}, 时间: {hours}小时{minutes}分钟", "成功")
                print(f"✅ 已设置时间窗口为 {hours}小时{minutes}分钟")
            else:
                record_history("设置时间窗口", f"歌单: {playlist_name}, 时间: {hours}小时{minutes}分钟", "失败")
                print("❌ 设置时间窗口失败")
        else:
            print("❌ 时间范围无效")
    except ValueError:
        print("❌ 请输入有效的数字")

def toggle_reset_on_all_played():
    """切换所有歌曲播放后重置功能"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    prevention_config = config['playlists'][current_playlist_id]['duplicate_prevention']
    
    current_status = prevention_config['reset_on_all_played']
    new_status = not current_status
    
    prevention_config['reset_on_all_played'] = new_status
    
    if save_playlist_config(config):
        status_text = "启用" if new_status else "禁用"
        record_history("切换播放后重置", f"歌单: {playlist_name}, 状态: {status_text}", "成功")
        print(f"✅ 已{'启用' if new_status else '禁用'}所有歌曲播放后重置功能")
    else:
        record_history("切换播放后重置", f"歌单: {playlist_name}", "失败")
        print("❌ 切换播放后重置功能失败")

def view_played_songs():
    """查看播放记录"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    prevention_config = config['playlists'][current_playlist_id]['duplicate_prevention']
    
    played_songs = prevention_config['played_songs']
    
    print(f"\n📜 播放记录 (歌单: {playlist_name}) 📜")
    print("=" * 60)
    
    if not played_songs:
        print("暂无播放记录")
    else:
        for i, song_info in enumerate(played_songs, 1):
            song_name = song_info.get('song_name', '未知')
            play_time = song_info.get('play_time', '未知时间')
            print(f"{i}. {song_name}")
            print(f"   播放时间: {play_time}")
            print("-" * 40)
    
    print(f"\n📊 统计: 共 {len(played_songs)} 首歌曲播放记录")
    print("=" * 60)

def reset_played_songs():
    """手动重置播放记录"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    prevention_config = config['playlists'][current_playlist_id]['duplicate_prevention']
    
    played_count = len(prevention_config['played_songs'])
    
    if played_count == 0:
        print("❌ 当前没有播放记录需要重置")
        return
    
    # 确认重置
    confirm = input(f"确定要重置播放记录吗? 这将清除 {played_count} 条播放记录 (y/N): ").strip().lower()
    if confirm == 'y':
        prevention_config['played_songs'] = []
        prevention_config['last_reset_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if save_playlist_config(config):
            record_history("重置播放记录", f"歌单: {playlist_name}, 清除记录: {played_count}条", "成功")
            print(f"✅ 已重置播放记录，清除了 {played_count} 条记录")
        else:
            record_history("重置播放记录", f"歌单: {playlist_name}", "失败")
            print("❌ 重置播放记录失败")
    else:
        print("取消重置")

def view_duplicate_prevention_settings():
    """查看防重复功能设置"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    prevention_config = config['playlists'][current_playlist_id]['duplicate_prevention']
    
    print(f"\n🔄 防重复功能设置 🔄 (当前歌单: {playlist_name})")
    print("=" * 50)
    
    status = "✅ 启用" if prevention_config['enabled'] else "❌ 禁用"
    mode = "⏰ 时间窗口模式" if prevention_config['mode'] == 'time_window' else "🎲 随机模式"
    reset = "✅ 是" if prevention_config['reset_on_all_played'] else "❌ 否"
    
    print(f"1. 功能状态: {status}")
    print(f"2. 模式: {mode}")
    
    if prevention_config['mode'] == 'time_window':
        print(f"3. 时间窗口: {prevention_config['time_window_hours']}小时{prevention_config['time_window_minutes']}分钟")
    
    print(f"4. 所有歌曲播放后重置: {reset}")
    print(f"5. 当前已播放歌曲: {len(prevention_config['played_songs'])}首")
    
    if prevention_config['last_reset_time']:
        print(f"6. 上次重置时间: {prevention_config['last_reset_time']}")
    
    print("=" * 50)

def duplicate_prevention_menu():
    """防重复功能设置菜单"""
    while True:
        config = load_playlist_config()
        current_playlist_id = config['current_playlist']
        playlist_name = config['playlists'][current_playlist_id]['name']
        prevention_config = config['playlists'][current_playlist_id]['duplicate_prevention']
        
        status = "✅ 启用" if prevention_config['enabled'] else "❌ 禁用"
        
        print(f"\n🔄 防重复功能设置 🔄 (当前歌单: {playlist_name}, 状态: {status})")
        print("=" * 50)
        print("1. 启用/关闭防重复功能")
        print("2. 设置防重复模式")
        
        if prevention_config['mode'] == 'time_window':
            print("3. 设置时间窗口")
        
        print("4. 启用/关闭播放后重置")
        print("5. 查看播放记录")
        print("6. 手动重置播放记录")
        print("7. 查看当前设置")
        print("8. 返回设置菜单")
        
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            toggle_duplicate_prevention()
        elif choice == '2':
            set_prevention_mode()
        elif choice == '3' and prevention_config['mode'] == 'time_window':
            set_time_window()
        elif choice == '4':
            toggle_reset_on_all_played()
        elif choice == '5':
            view_played_songs()
        elif choice == '6':
            reset_played_songs()
        elif choice == '7':
            view_duplicate_prevention_settings()
        elif choice == '8':
            break
        else:
            print("❌ 无效的选择，请重新输入")
