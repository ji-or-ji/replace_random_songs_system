import json
import datetime

def load_playlist_config():
    """加载歌单配置文件"""
    config_paths = [
        'main_data/play_list_1/play_lists_config.json',
        './main_data/play_list_1/play_lists_config.json',
        '../main_data/play_list_1/play_lists_config.json',
        'playlists_config.json',
        '../playlists_config.json'
    ]
    
    for config_path in config_paths:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            continue
        except json.JSONDecodeError:
            print(f'歌单配置文件已损坏: {config_path}')
            # 创建默认配置
            return {
                "current_playlist": "default",
                "playlists": {
                    "default": {
                        "name": "默认歌单",
                        "description": "主歌单",
                        "file_path": "songs_list.json",
                        "created_at": datetime.datetime.now().strftime("%Y/%m/%d"),
                        "song_count": 0,
                        "duplicate_prevention": {
                            "enabled": True,
                            "mode": "time_window",
                            "time_window_hours": 1,
                            "time_window_minutes": 0,
                            "reset_on_all_played": True,
                            "last_reset_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "played_songs": []
                        }
                    }
                }
            }
    
    # 如果配置文件不存在，创建默认配置
    default_config = {
        "current_playlist": "default",
        "playlists": {
            "default": {
                "name": "默认歌单",
                "description": "主歌单",
                "file_path": "songs_list.json",
                "created_at": datetime.datetime.now().strftime("%Y/%m/%d"),
                "song_count": 0,
                "duplicate_prevention": {
                    "enabled": True,
                    "mode": "time_window",
                    "time_window_hours": 1,
                    "time_window_minutes": 0,
                    "reset_on_all_played": True,
                    "last_reset_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "played_songs": []
                }
            }
        }
    }
    save_playlist_config(default_config)
    return default_config

def save_playlist_config(config):
    """保存歌单配置文件"""
    # 使用与load_playlist_config相同的路径解析逻辑
    config_paths = [
        'main_data/play_list_1/play_lists_config.json',
        './main_data/play_list_1/play_lists_config.json',
        '../main_data/play_list_1/play_lists_config.json',
        'playlists_config.json',
        '../playlists_config.json'
    ]
    
    # 尝试在所有可能的路径中保存
    for config_path in config_paths:
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            # 如果这个路径失败，继续尝试下一个
            continue
    
    # 如果所有路径都失败，尝试在当前目录创建
    try:
        with open('playlists_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f'保存歌单配置失败: {e}')
        return False

def load_auto_jump_config():
    """加载自动跳转配置文件"""
    config_paths = [
        'main_data/auto_jump_config.json',
        './main_data/auto_jump_config.json',
        '../main_data/auto_jump_config.json',
        'auto_jump_config.json',
        '../auto_jump_config.json'
    ]
    
    for config_path in config_paths:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            continue
        except json.JSONDecodeError:
            print(f'自动跳转配置文件已损坏: {config_path}')
            # 创建默认配置
            return {
                "auto_jump_enabled": False,
                "jump_mode": "search",
                "custom_url": "",
                "jump_delay": 3
            }
    
    # 如果配置文件不存在，创建默认配置
    default_config = {
        "auto_jump_enabled": False,
        "jump_mode": "search",
        "custom_url": "",
        "jump_delay": 3
    }
    save_auto_jump_config(default_config)
    return default_config

def save_auto_jump_config(config):
    """保存自动跳转配置文件"""
    config_path = 'main_data/auto_jump_config.json'
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f'保存自动跳转配置失败: {e}')
        return False
