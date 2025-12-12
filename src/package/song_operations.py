import json
from package.song_manager import load_songs, save_songs, get_next_song_id, filter_valid_songs
from package.requester_manager import get_requester_list
from package.history_manager import record_history
from package.config_manager import load_playlist_config

def add_song():
    """添加歌曲"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    
    songs = load_songs()
    requesters = get_requester_list()
    
    print(f"\n🎵 添加歌曲 (歌单: {playlist_name}) 🎵")
    print("=" * 40)
    
    # 获取歌曲信息
    while True:
        song_name = input("请输入歌曲名称: ").strip()
        if not song_name:
            print("歌曲名称不能为空，请重新输入")
            continue
        break
    
    artist = input("请输入歌手名称 (可选): ").strip()
    url_list = input("请输入歌曲链接 (可选): ").strip()
    
    # 选择点歌人
    requested_by = "未知"
    if requesters:
        print("\n👥 请选择点歌人:")
        print("0. 未知")
        for i, requester in enumerate(requesters, 1):
            print(f"{i}. {requester}")
        
        try:
            choice = int(input("请选择点歌人编号: ").strip())
            if choice == 0:
                requested_by = "未知"
            elif 1 <= choice <= len(requesters):
                requested_by = requesters[choice - 1]
            else:
                print("❌ 无效的选择，将使用'未知'")
        except ValueError:
            print("❌ 请输入有效的数字，将使用'未知'")
    else:
        requested_by = input("请输入点歌人姓名 (可选): ").strip() or "未知"
    
    # 创建新歌曲
    new_song = {
        "id": get_next_song_id(songs),
        "song_name": song_name,
        "artist": artist,
        "url_list": url_list,
        "requested_by": requested_by
    }
    
    songs.append(new_song)
    
    if save_songs(songs):
        record_history("添加歌曲", f"歌曲: {song_name} - 歌手: {artist} - 点歌人: {requested_by}", "成功")
        print(f"✅ 成功添加歌曲: {song_name}")
    else:
        record_history("添加歌曲", f"歌曲: {song_name} - 歌手: {artist} - 点歌人: {requested_by}", "失败")
        print("❌ 添加歌曲失败")

def modify_song():
    """修改歌曲"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    
    songs = load_songs()
    valid_songs = filter_valid_songs(songs)
    
    if not valid_songs:
        print("❌ 当前没有有效歌曲")
        return
    
    print(f"\n🎵 修改歌曲 (歌单: {playlist_name}) 🎵")
    print("=" * 40)
    print("当前歌曲列表:")
    
    for i, song in enumerate(valid_songs, 1):
        artist = song.get('artist', '未知')
        requester = song.get('requested_by', '未知')
        print(f"{i}. {song['song_name']} - {artist} (点歌人: {requester})")
    
    try:
        choice = int(input("\n请选择要修改的歌曲编号: "))
        if 1 <= choice <= len(valid_songs):
            song_to_modify = valid_songs[choice - 1]
            original_song_name = song_to_modify['song_name']
            
            print(f"\n正在修改歌曲: {original_song_name}")
            print("=" * 30)
            
            # 获取新的歌曲信息
            new_song_name = input(f"请输入新的歌曲名称 (原: {song_to_modify['song_name']}): ").strip()
            if new_song_name:
                song_to_modify['song_name'] = new_song_name
            
            new_artist = input(f"请输入新的歌手名称 (原: {song_to_modify.get('artist', '')}): ").strip()
            song_to_modify['artist'] = new_artist
            
            new_url = input(f"请输入新的歌曲链接 (原: {song_to_modify.get('url_list', '')}): ").strip()
            song_to_modify['url_list'] = new_url
            
            # 选择新的点歌人
            requesters = get_requester_list()
            if requesters:
                print("\n👥 请选择新的点歌人:")
                print(f"0. 保持原值: {song_to_modify.get('requested_by', '未知')}")
                for i, requester in enumerate(requesters, 1):
                    print(f"{i}. {requester}")
                
                try:
                    requester_choice = int(input("请选择点歌人编号: ").strip())
                    if requester_choice != 0 and 1 <= requester_choice <= len(requesters):
                        song_to_modify['requested_by'] = requesters[requester_choice - 1]
                except ValueError:
                    print("❌ 请输入有效的数字，将保持原值")
            
            if save_songs(songs):
                record_history("修改歌曲", f"歌曲: {original_song_name} -> {new_song_name}", "成功")
                print(f"✅ 成功修改歌曲: {original_song_name} -> {new_song_name}")
            else:
                record_history("修改歌曲", f"歌曲: {original_song_name} -> {new_song_name}", "失败")
                print("❌ 修改歌曲失败")
        else:
            print("❌ 无效的选择")
    except ValueError:
        print("❌ 请输入有效的数字")

def delete_song():
    """删除歌曲"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    
    songs = load_songs()
    valid_songs = filter_valid_songs(songs)
    
    if not valid_songs:
        print("❌ 当前没有有效歌曲")
        return
    
    print(f"\n🎵 删除歌曲 (歌单: {playlist_name}) 🎵")
    print("=" * 40)
    print("当前歌曲列表:")
    
    for i, song in enumerate(valid_songs, 1):
        artist = song.get('artist', '未知')
        requester = song.get('requested_by', '未知')
        print(f"{i}. {song['song_name']} - {artist} (点歌人: {requester})")
    
    try:
        choice = int(input("\n请选择要删除的歌曲编号: "))
        if 1 <= choice <= len(valid_songs):
            song_to_delete = valid_songs[choice - 1]
            
            # 确认删除
            confirm = input(f"确定要删除歌曲 '{song_to_delete['song_name']}' 吗? (y/N): ").strip().lower()
            if confirm == 'y':
                # 从原列表中删除
                songs = [song for song in songs if song.get('id') != song_to_delete.get('id')]
                
                if save_songs(songs):
                    record_history("删除歌曲", f"歌曲: {song_to_delete['song_name']}", "成功")
                    print(f"✅ 成功删除歌曲: {song_to_delete['song_name']}")
                else:
                    record_history("删除歌曲", f"歌曲: {song_to_delete['song_name']}", "失败")
                    print("❌ 删除歌曲失败")
            else:
                print("取消删除")
        else:
            print("❌ 无效的选择")
    except ValueError:
        print("❌ 请输入有效的数字")

def view_all_songs():
    """查看所有歌曲"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    
    songs = load_songs()
    valid_songs = filter_valid_songs(songs)
    
    print(f"\n🎵 所有歌曲列表 (歌单: {playlist_name}) 🎵")
    print("=" * 60)
    
    if not valid_songs:
        print("暂无歌曲")
    else:
        for i, song in enumerate(valid_songs, 1):
            artist = song.get('artist', '未知')
            requester = song.get('requested_by', '未知')
            url = song.get('url_list', '无')
            
            print(f"{i}. {song['song_name']}")
            print(f"   歌手: {artist}")
            print(f"   点歌人: {requester}")
            print(f"   链接: {url}")
            print("-" * 40)
    
    print(f"\n📊 统计: 共 {len(valid_songs)} 首有效歌曲")
    print("=" * 60)

def song_management_menu():
    """歌曲管理菜单"""
    while True:
        config = load_playlist_config()
        current_playlist_id = config['current_playlist']
        playlist_name = config['playlists'][current_playlist_id]['name']
        
        print(f"\n🎵 歌曲管理 🎵 (当前歌单: {playlist_name})")
        print("=" * 30)
        print("1. 添加歌曲")
        print("2. 修改歌曲")
        print("3. 删除歌曲")
        print("4. 查看所有歌曲")
        print("5. 返回主菜单")
        
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            add_song()
        elif choice == '2':
            modify_song()
        elif choice == '3':
            delete_song()
        elif choice == '4':
            view_all_songs()
        elif choice == '5':
            break
        else:
            print("❌ 无效的选择，请重新输入")
