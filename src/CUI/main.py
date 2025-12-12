

# 导入模块

# 导入自定义包
from package.initialize import initialize_system                 # 初始化函数
from package.history_manager import record_history, view_history
from package.config_manager import load_playlist_config, save_playlist_config, load_auto_jump_config, save_auto_jump_config
from package.song_manager import load_songs, save_songs, filter_valid_songs, get_random_song_with_prevention, get_songs_statistics, display_statistics
from package.requester_manager import requester_menu, get_requester_list
from package.song_operations import song_management_menu
from package.playlist_manager import playlist_menu
from package.auto_jump_manager import auto_jump, auto_jump_menu
from package.duplicate_prevention_manager import duplicate_prevention_menu

def display_song_info(song):
    """显示歌曲信息"""
    if not song:
        print("没有找到有效的歌曲")
        return
    
    print("\n🎵 随机点歌结果 🎵")
    print("=" * 30)
    print(f"歌曲名: {song.get('song_name', '未知')}")
    print(f"歌手: {song.get('artist', '未知') or '未知'}")
    print(f"点歌人: {song.get('requested_by', '未知')}")
    if song.get('url_list'):
        print(f"链接: {song.get('url_list')}")
    print("=" * 30)
    
    # 记录历史
    record_history("随机点歌", f"歌曲: {song.get('song_name', '未知')} - 歌手: {song.get('artist', '未知')}")
    
    # 执行自动网页跳转
    auto_jump(song)

def settings_menu():
    """设置菜单"""
    while True:
        config = load_playlist_config()
        current_playlist = config['playlists'][config['current_playlist']]['name']
        
        print(f"\n⚙️ 设置菜单 ⚙️ (当前歌单: {current_playlist})")
        print("=" * 30)
        print("1. 歌单管理")
        print("2. 自动网页跳转开关")
        print("3. 防重复功能设置")
        print("4. 返回主菜单")
        
        choice = input("请输入选项 (1-4): ").strip()
        
        if choice == '1':
            new_songs = playlist_menu()
            if new_songs is not None:
                # 返回新的歌曲列表给调用者
                return new_songs
        elif choice == '2':
            auto_jump_menu()
        elif choice == '3':
            duplicate_prevention_menu()
        elif choice == '4':
            break
        else:
            print("无效选项，请重新选择!")
    
    return None

def main():
    """主函数"""
    print("    __                           __                _ __  __       ________  ______")
    print("   / /   ____ ___  ______  _____/ /_     _      __(_) /_/ /_     / ____/ / / /  _/")
    print("  / /   / __ `/ / / / __ \\/ ___/ __ \\   | | /| / / / __/ __ \\   / /   / / / // /  ")
    print(" / /___/ /_/ / /_/ / / / / /__/ / / /   | |/ |/ / / /_/ / / /  / /___/ /_/ // /   ")
    print("/_____/\\__,_/\\__,_/_/ /_/\\___/_/ /_/    |__/|__/_/\\__/_/ /_/   \\____/\\____/___/   ")
    print("                                                                                  ")
    print("    ____                  __                   _____                           _____            __               ")
    print("   / __ \\____ _____  ____/ /___  ____ ___     / ___/____  ____  ____ ______   / ___/__  _______/ /____  ____ ___ ")
    print("  / /_/ / __ `/ __ \\/ __  / __ \\/ __ `__ \\    \\__ \\/ __ \\/ __ \\/ __ `/ ___/   \\__ \\/ / / / ___/ __/ _ \\/ __ `__ \\")
    print(" / _, _/ /_/ / / / / /_/ / /_/ / / / / / /   ___/ / /_/ / / / / /_/ (__  )   ___/ / /_/ (__  ) /_/  __/ / / / / /")
    print("/_/ |_|\\__,_/_/ /_/\\__,_/\\____/_/ /_/ /_/   /____/\\____/_/ /_/\\__, /____/   /____/\\__, /____/\\__/\\___/_/ /_/ /_/ ")
    print("                                                             /____/              /____/                          ")

    
    # 初始化系统，检查并创建必要的文件和目录
    initialize_system()
    
    print("正在加载歌曲列表...")
    songs = load_songs()
    if not songs:
        print("没有找到任何歌曲，程序退出")
        return
    
    # 显示统计信息
    stats = get_songs_statistics(songs)
    display_statistics(stats)
    
    while True:
        print("\n请选择操作:")
        print("1. 随机点歌")
        print("2. 重新加载歌曲列表")
        print("3. 查看统计信息")
        print("4. 点歌人管理")
        print("5. 歌曲管理")
        print("6. 查看历史记录")
        print("7. 设置")
        print("8. 退出")
        
        choice = input("请输入选项 (1-8): ").strip()
        
        if choice == '1':
            random_song = get_random_song(songs)
            display_song_info(random_song)
            
        elif choice == '2':
            songs = load_songs()
            if songs:
                print("歌曲列表重新加载成功!")
                stats = get_songs_statistics(songs)
                display_statistics(stats)
            else:
                print("重新加载失败!")
                
        elif choice == '3':
            stats = get_songs_statistics(songs)
            display_statistics(stats)
            
        elif choice == '4':
            requester_menu()
            
        elif choice == '5':
            song_management_menu()
            
        elif choice == '6':
            view_history()
            
        elif choice == '7':
            new_songs = settings_menu()
            if new_songs is not None:
                songs = new_songs
                print("歌单已切换，歌曲列表已更新!")
                stats = get_songs_statistics(songs)
                display_statistics(stats)
            
        elif choice == '8':
            print("天空属于哈夫克~！")
            break
            
        else:
            print("无效选项，请重新选择!")

if __name__ == "__main__":
    main()
    input("\n按回车键退出程序...")
