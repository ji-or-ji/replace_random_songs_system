

# 导入模块
import json
import os
import random
import datetime
import time
import webbrowser

# 导入自定义模块
from history_manager import record_history, view_history
from config_manager import load_playlist_config, save_playlist_config, load_auto_jump_config, save_auto_jump_config
from song_manager import load_songs, save_songs, filter_valid_songs, get_random_song_with_prevention, get_songs_statistics, display_statistics
from requester_manager import requester_menu, get_requester_list
from song_operations import song_management_menu
from playlist_manager import playlist_menu
from auto_jump_manager import auto_jump, auto_jump_menu
from duplicate_prevention_manager import duplicate_prevention_menu

def initialize_system():
    """初始化系统，检查并创建必要的文件和目录"""
    
    # 创建主数据目录
    main_data_dirs = [
        'main_data',
        'main_data/global',
        'main_data/global/history',
        'main_data/play_list_1',
        'main_data/play_list_1/songs'
    ]
    
    for dir_path in main_data_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"📁 创建目录: {dir_path}")
    
    # 检查并创建全局配置文件
    global_config_path = 'main_data/global/global_config.json'
    if not os.path.exists(global_config_path):
        global_config = {
            "system_version": "1.0.0",
            "initialized_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_playlists": 1
        }
        with open(global_config_path, 'w', encoding='utf-8') as f:
            json.dump(global_config, f, ensure_ascii=False, indent=2)
        print("✅ 创建全局配置文件")
    
    # 检查并创建歌单配置文件
    playlist_config_path = 'main_data/play_list_main/config.json'
    if not os.path.exists(playlist_config_path):
        playlist_config = {
            "current_playlist": "play_list_main",
            "playlists": {
                "play_list_main": {
                    "name": "默认歌单",
                    "description": "主歌单",
                    "file_path": "main_data/play_list_main/songs_list.json",
                    "requester_file_path": "main_data/play_list_1/requester_list.json",
                    "history_file_path": "main_data/play_list_1/history_records.log",
                    "created_at": datetime.datetime.now().strftime("%Y/%m/%d"),
                    "song_count": 5,  # 更新为5首示例歌曲
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
            }
        }
        with open(playlist_config_path, 'w', encoding='utf-8') as f:
            json.dump(playlist_config, f, ensure_ascii=False, indent=2)
        print("✅ 创建歌单配置文件")
    
    # 检查并创建歌曲列表文件
    songs_list_path = 'main_data/play_list_1/songs_list.json'
    if not os.path.exists(songs_list_path):
        # 添加一些示例歌曲，让新用户第一次使用时就有可用的歌曲
        songs_list = {
            "songs": [
                {
                    "song_name": "夜曲",
                    "artist": "周杰伦",
                    "requested_by": "系统",
                    "url_list": ["https://music.163.com/#/song?id=185809"],
                    "added_time": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                },
                {
                    "song_name": "晴天",
                    "artist": "周杰伦",
                    "requested_by": "系统",
                    "url_list": ["https://music.163.com/#/song?id=186016"],
                    "added_time": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                },
                {
                    "song_name": "七里香",
                    "artist": "周杰伦",
                    "requested_by": "系统",
                    "url_list": ["https://music.163.com/#/song?id=185923"],
                    "added_time": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                },
                {
                    "song_name": "稻香",
                    "artist": "周杰伦",
                    "requested_by": "系统",
                    "url_list": ["https://music.163.com/#/song?id=287035"],
                    "added_time": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                },
                {
                    "song_name": "青花瓷",
                    "artist": "周杰伦",
                    "requested_by": "系统",
                    "url_list": ["https://music.163.com/#/song?id=185951"],
                    "added_time": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                }
            ]
        }
        with open(songs_list_path, 'w', encoding='utf-8') as f:
            json.dump(songs_list, f, ensure_ascii=False, indent=2)
        print("✅ 创建歌曲列表文件（包含5首示例歌曲）")
    
    # 检查并创建点歌人列表文件
    requester_list_path = 'main_data/play_list_1/requester_list.json'
    if not os.path.exists(requester_list_path):
        # 添加示例歌曲对应的点歌人
        requester_list = ["系统"]
        with open(requester_list_path, 'w', encoding='utf-8') as f:
            json.dump(requester_list, f, ensure_ascii=False, indent=2)
        print("✅ 创建点歌人列表文件（包含示例点歌人）")
    
    # 检查并创建历史记录文件
    history_path = 'main_data/play_list_1/history_records.log'
    if not os.path.exists(history_path):
        with open(history_path, 'w', encoding='utf-8') as f:
            f.write(f"系统初始化于: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("✅ 创建历史记录文件")
    
    # 检查并创建自动跳转配置文件
    auto_jump_config_path = 'main_data/auto_jump_config.json'
    if not os.path.exists(auto_jump_config_path):
        auto_jump_config = {
            "auto_jump_enabled": False,
            "jump_mode": "search",
            "custom_url": "",
            "jump_delay": 3
        }
        with open(auto_jump_config_path, 'w', encoding='utf-8') as f:
            json.dump(auto_jump_config, f, ensure_ascii=False, indent=2)
        print("✅ 创建自动跳转配置文件")
    
    # 检查并创建全局历史记录文件
    global_history_path = 'main_data/global/history/global_play_history.log'
    if not os.path.exists(global_history_path):
        with open(global_history_path, 'w', encoding='utf-8') as f:
            f.write(f"全局历史记录初始化于: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("✅ 创建全局播放历史文件")
    
    global_operate_history_path = 'main_data/global/history/global_operate_history.log'
    if not os.path.exists(global_operate_history_path):
        with open(global_operate_history_path, 'w', encoding='utf-8') as f:
            f.write(f"全局操作历史初始化于: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("✅ 创建全局操作历史文件")
    
    print("🎉 系统初始化完成！")

def get_random_song(songs):
    """随机选择一首歌曲（兼容旧版本）"""
    return get_random_song_with_prevention(songs)

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
    print("🎵 随机点歌系统 🎵")
    print("正在初始化系统...")
    
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
