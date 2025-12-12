import json
import os
import datetime
from package.config_manager import load_playlist_config, save_playlist_config
from package.history_manager import record_history

def create_playlist():
    """创建空白歌单"""
    config = load_playlist_config()
    
    print("\n🎵 创建歌单 🎵")
    print("=" * 30)
    
    # 获取歌单名称
    while True:
        playlist_name = input("请输入歌单名称: ").strip()
        if not playlist_name:
            print("歌单名称不能为空，请重新输入")
            continue
        break
    
    # 获取歌单描述
    description = input("请输入歌单描述 (可选): ").strip()
    if not description:
        description = f"{playlist_name} 歌单"
    
    # 生成歌单ID
    playlist_id = playlist_name.lower().replace(' ', '_')
    
    # 检查是否已存在
    if playlist_id in config['playlists']:
        print(f"❌ 歌单 '{playlist_name}' 已存在")
        return
    
    # 创建歌单目录结构
    playlist_dir = f"main_data/play_list_{len(config['playlists']) + 1}"
    songs_file = f"{playlist_dir}/songs_list.json"
    requester_file = f"{playlist_dir}/requester_list.json"
    history_file = f"{playlist_dir}/history_records.log"
    
    # 创建目录
    try:
        os.makedirs(playlist_dir, exist_ok=True)
        
        # 创建歌曲文件
        with open(songs_file, 'w', encoding='utf-8') as f:
            json.dump({"songs": []}, f, ensure_ascii=False, indent=2)
        
        # 创建点歌人文件
        with open(requester_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        
        # 创建历史记录文件
        with open(history_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        # 更新配置
        config['playlists'][playlist_id] = {
            "name": playlist_name,
            "description": description,
            "file_path": songs_file,
            "requester_file_path": requester_file,
            "history_file_path": history_file,
            "created_at": datetime.datetime.now().strftime("%Y/%m/%d"),
            "song_count": 0,
            "duplicate_prevention": {
                "enabled": True,
                "mode": "time_window",
                "time_window_hours": 1,
                "time_window_minutes": 0,
                "reset_on_all_played": True,
                "last_reset_time": None,
                "played_songs": []
            }
        }
        
        if save_playlist_config(config):
            record_history("创建歌单", f"歌单: {playlist_name}", "成功")
            print(f"✅ 成功创建歌单: {playlist_name}")
            print(f"📁 歌单目录: {playlist_dir}")
        else:
            record_history("创建歌单", f"歌单: {playlist_name}", "失败")
            print("❌ 创建歌单失败")
            
    except Exception as e:
        record_history("创建歌单", f"歌单: {playlist_name}", f"失败: {e}")
        print(f"❌ 创建歌单失败: {e}")

def delete_playlist():
    """删除歌单"""
    config = load_playlist_config()
    
    if len(config['playlists']) <= 1:
        print("❌ 至少需要保留一个歌单")
        return
    
    print("\n🎵 删除歌单 🎵")
    print("=" * 30)
    print("当前歌单列表:")
    
    playlists = list(config['playlists'].items())
    for i, (playlist_id, playlist_info) in enumerate(playlists, 1):
        current_marker = " (当前)" if playlist_id == config['current_playlist'] else ""
        print(f"{i}. {playlist_info['name']} - {playlist_info['song_count']}首歌曲{current_marker}")
    
    try:
        choice = int(input("\n请选择要删除的歌单编号: "))
        if 1 <= choice <= len(playlists):
            playlist_id_to_delete, playlist_info = playlists[choice - 1]
            
            # 不能删除当前歌单
            if playlist_id_to_delete == config['current_playlist']:
                print("❌ 不能删除当前正在使用的歌单，请先切换到其他歌单")
                return
            
            # 确认删除
            confirm = input(f"确定要删除歌单 '{playlist_info['name']}' 吗? 此操作不可恢复! (y/N): ").strip().lower()
            if confirm == 'y':
                # 删除歌单配置
                del config['playlists'][playlist_id_to_delete]
                
                if save_playlist_config(config):
                    record_history("删除歌单", f"歌单: {playlist_info['name']}", "成功")
                    print(f"✅ 成功删除歌单: {playlist_info['name']}")
                else:
                    record_history("删除歌单", f"歌单: {playlist_info['name']}", "失败")
                    print("❌ 删除歌单失败")
            else:
                print("取消删除")
        else:
            print("❌ 无效的选择")
    except ValueError:
        print("❌ 请输入有效的数字")

def switch_playlist():
    """切换歌单"""
    config = load_playlist_config()
    
    if len(config['playlists']) <= 1:
        print("❌ 只有一个歌单，无需切换")
        return
    
    print("\n🎵 切换歌单 🎵")
    print("=" * 30)
    print("当前歌单列表:")
    
    playlists = list(config['playlists'].items())
    for i, (playlist_id, playlist_info) in enumerate(playlists, 1):
        current_marker = " (当前)" if playlist_id == config['current_playlist'] else ""
        print(f"{i}. {playlist_info['name']} - {playlist_info['song_count']}首歌曲{current_marker}")
    
    try:
        choice = int(input("\n请选择要切换到的歌单编号: "))
        if 1 <= choice <= len(playlists):
            playlist_id_to_switch, playlist_info = playlists[choice - 1]
            
            if playlist_id_to_switch == config['current_playlist']:
                print("❌ 已经是当前歌单")
                return
            
            old_playlist_name = config['playlists'][config['current_playlist']]['name']
            config['current_playlist'] = playlist_id_to_switch
            
            if save_playlist_config(config):
                record_history("切换歌单", f"从 '{old_playlist_name}' 切换到 '{playlist_info['name']}'", "成功")
                print(f"✅ 成功切换到歌单: {playlist_info['name']}")
            else:
                record_history("切换歌单", f"从 '{old_playlist_name}' 切换到 '{playlist_info['name']}'", "失败")
                print("❌ 切换歌单失败")
        else:
            print("❌ 无效的选择")
    except ValueError:
        print("❌ 请输入有效的数字")

def view_all_playlists():
    """查看所有歌单信息"""
    config = load_playlist_config()
    
    print("\n🎵 歌单信息 🎵")
    print("=" * 50)
    
    for playlist_id, playlist_info in config['playlists'].items():
        current_marker = "🎯 当前歌单" if playlist_id == config['current_playlist'] else ""
        print(f"📁 歌单名称: {playlist_info['name']} {current_marker}")
        print(f"📝 描述: {playlist_info['description']}")
        print(f"📊 歌曲数量: {playlist_info['song_count']}")
        print(f"📅 创建时间: {playlist_info['created_at']}")
        
        # 防重复功能状态
        prevention = playlist_info['duplicate_prevention']
        status = "✅ 启用" if prevention['enabled'] else "❌ 禁用"
        mode = "⏰ 时间窗口" if prevention['mode'] == 'time_window' else "🎲 随机"
        reset = "✅ 是" if prevention['reset_on_all_played'] else "❌ 否"
        
        print(f"🔄 防重复: {status}")
        if prevention['enabled']:
            print(f"  模式: {mode}")
            print(f"  时间窗口: {prevention['time_window_hours']}小时{prevention['time_window_minutes']}分钟")
            print(f"  播放后重置: {reset}")
            print(f"  已播放歌曲: {len(prevention['played_songs'])}首")
        
        print("-" * 50)

def import_external_playlist():
    """从外部JSON文件导入歌单"""
    config = load_playlist_config()
    
    print("\n🎵 从外部导入歌单 🎵")
    print("=" * 40)
    
    # 获取外部文件路径
    external_file = input("请输入外部JSON文件路径: ").strip()
    if not external_file:
        print("❌ 文件路径不能为空")
        return
    
    # 获取歌单名称
    while True:
        playlist_name = input("请输入新歌单名称: ").strip()
        if not playlist_name:
            print("歌单名称不能为空，请重新输入")
            continue
        break
    
    # 生成歌单ID
    playlist_id = playlist_name.lower().replace(' ', '_')
    
    # 检查是否已存在
    if playlist_id in config['playlists']:
        print(f"❌ 歌单 '{playlist_name}' 已存在")
        return
    
    try:
        # 读取外部文件
        with open(external_file, 'r', encoding='utf-8') as f:
            external_data = json.load(f)
        
        # 验证文件格式
        if 'songs' not in external_data:
            print("❌ 文件格式不正确，缺少 'songs' 字段")
            return
        
        # 创建歌单目录结构
        playlist_dir = f"main_data/play_list_{len(config['playlists']) + 1}"
        songs_file = f"{playlist_dir}/songs_list.json"
        requester_file = f"{playlist_dir}/requester_list.json"
        history_file = f"{playlist_dir}/history_records.log"
        
        # 创建目录
        os.makedirs(playlist_dir, exist_ok=True)
        
        # 保存歌曲数据
        with open(songs_file, 'w', encoding='utf-8') as f:
            json.dump(external_data, f, ensure_ascii=False, indent=2)
        
        # 创建点歌人文件
        with open(requester_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        
        # 创建历史记录文件
        with open(history_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        # 统计歌曲数量
        song_count = len(external_data['songs'])
        
        # 更新配置
        config['playlists'][playlist_id] = {
            "name": playlist_name,
            "description": f"从外部导入的歌单: {playlist_name}",
            "file_path": songs_file,
            "requester_file_path": requester_file,
            "history_file_path": history_file,
            "created_at": datetime.datetime.now().strftime("%Y/%m/%d"),
            "song_count": song_count,
            "duplicate_prevention": {
                "enabled": True,
                "mode": "time_window",
                "time_window_hours": 1,
                "time_window_minutes": 0,
                "reset_on_all_played": True,
                "last_reset_time": None,
                "played_songs": []
            }
        }
        
        if save_playlist_config(config):
            record_history("导入外部歌单", f"歌单: {playlist_name}, 歌曲数: {song_count}", "成功")
            print(f"✅ 成功导入歌单: {playlist_name}")
            print(f"📁 歌单目录: {playlist_dir}")
            print(f"🎵 导入歌曲: {song_count}首")
        else:
            record_history("导入外部歌单", f"歌单: {playlist_name}", "失败")
            print("❌ 导入歌单失败")
            
    except FileNotFoundError:
        print(f"❌ 文件不存在: {external_file}")
    except json.JSONDecodeError:
        print(f"❌ 文件格式错误，不是有效的JSON文件: {external_file}")
    except Exception as e:
        print(f"❌ 导入失败: {e}")

def playlist_menu():
    """歌单管理菜单"""
    while True:
        config = load_playlist_config()
        current_playlist_name = config['playlists'][config['current_playlist']]['name']
        
        print(f"\n🎵 歌单管理 🎵 (当前歌单: {current_playlist_name})")
        print("=" * 40)
        print("1. 从外部已有歌单导入")
        print("2. 创建空白歌单")
        print("3. 删除歌单")
        print("4. 切换歌单")
        print("5. 查看所有歌单")
        print("6. 返回设置菜单")
        
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            import_external_playlist()
        elif choice == '2':
            create_playlist()
        elif choice == '3':
            delete_playlist()
        elif choice == '4':
            switch_playlist()
        elif choice == '5':
            view_all_playlists()
        elif choice == '6':
            break
        else:
            print("❌ 无效的选择，请重新输入")
