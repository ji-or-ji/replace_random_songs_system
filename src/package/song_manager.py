import json
import random
import datetime
from package.config_manager import load_playlist_config, save_playlist_config

def load_songs(playlist_id=None):
    """加载歌曲列表文件"""
    config = load_playlist_config()
    
    if playlist_id:
        # 加载指定歌单
        if playlist_id in config['playlists']:
            playlist = config['playlists'][playlist_id]
            target_playlist_id = playlist_id
        else:
            print(f'歌单不存在: {playlist_id}')
            return []
    else:
        # 加载当前歌单
        current_playlist_id = config['current_playlist']
        playlist = config['playlists'][current_playlist_id]
        target_playlist_id = current_playlist_id
    
    # 构建歌曲文件路径
    songs_file_path = f"main_data/{target_playlist_id}/songs_list.json"
    
    try:
        with open(songs_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            songs = data.get('songs', [])
            
            # 更新歌单统计信息
            config['playlists'][target_playlist_id]['song_count'] = len(songs)
            save_playlist_config(config)
            
            print(f'成功加载歌曲列表: {songs_file_path} (歌单: {playlist["name"]})')
            return songs
    except FileNotFoundError:
        print(f'歌曲列表文件不存在: {songs_file_path}')
        return []
    except json.JSONDecodeError:
        print(f'歌曲列表文件已损坏，请检查文件格式: {songs_file_path}')
        return []

def save_songs(songs, playlist_id=None):
    """保存歌曲列表到文件"""
    config = load_playlist_config()
    
    if playlist_id:
        # 保存到指定歌单
        if playlist_id in config['playlists']:
            target_playlist_id = playlist_id
        else:
            print(f'歌单不存在: {playlist_id}')
            return False
    else:
        # 保存到当前歌单
        current_playlist_id = config['current_playlist']
        target_playlist_id = current_playlist_id
    
    # 构建歌曲文件路径
    songs_file_path = f"main_data/{target_playlist_id}/songs_list.json"
    
    try:
        with open(songs_file_path, 'w', encoding='utf-8') as f:
            json.dump({'songs': songs}, f, ensure_ascii=False, indent=2)
        
        # 更新歌单统计信息
        config['playlists'][target_playlist_id]['song_count'] = len(songs)
        save_playlist_config(config)
        
        return True
    except Exception as e:
        print(f'保存文件失败: {e}')
        return False

def filter_valid_songs(songs):
    """过滤有效的歌曲（去除空歌名和空歌手名的歌曲）"""
    valid_songs = []
    for song in songs:
        song_name = song.get('song_name', '').strip()
        artist = song.get('artist', '').strip()
        # 只有当歌名不为空时才认为是有效歌曲
        if song_name:
            valid_songs.append(song)
    return valid_songs

def get_random_song_with_prevention(songs, playlist_id=None):
    """带防重复功能的随机选择歌曲"""
    if not songs:
        return None
    
    valid_songs = filter_valid_songs(songs)
    if not valid_songs:
        return None
    
    # 获取当前歌单的防重复配置
    config = load_playlist_config()
    if playlist_id:
        playlist_config = config['playlists'].get(playlist_id)
    else:
        playlist_config = config['playlists'].get(config['current_playlist'])
    
    if not playlist_config or not playlist_config['duplicate_prevention']['enabled']:
        # 防重复功能未启用，直接随机选择
        return random.choice(valid_songs)
    
    prevention_config = playlist_config['duplicate_prevention']
    
    # 检查是否需要重置播放记录
    if prevention_config['reset_on_all_played']:
        current_time = datetime.datetime.now()
        last_reset_time = prevention_config.get('last_reset_time')
        
        # 如果所有歌曲都已播放过，或者从未重置过，则重置
        played_count = len(prevention_config['played_songs'])
        total_songs = len(valid_songs)
        
        if played_count >= total_songs or last_reset_time is None:
            prevention_config['played_songs'] = []
            prevention_config['last_reset_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
            save_playlist_config(config)
    
    # 获取时间窗口内的已播放歌曲
    played_songs_in_window = []
    if prevention_config['mode'] == 'time_window':
        time_window_hours = prevention_config['time_window_hours']
        time_window_minutes = prevention_config['time_window_minutes']
        time_window_seconds = time_window_hours * 3600 + time_window_minutes * 60
        
        current_time = datetime.datetime.now()
        for song_info in prevention_config['played_songs']:
            play_time = datetime.datetime.strptime(song_info['play_time'], "%Y-%m-%d %H:%M:%S")
            time_diff = (current_time - play_time).total_seconds()
            
            if time_diff <= time_window_seconds:
                played_songs_in_window.append(song_info['song_id'])
    
    # 过滤出未在时间窗口内播放过的歌曲
    available_songs = [song for song in valid_songs 
                      if song.get('id') not in played_songs_in_window]
    
    if not available_songs:
        # 所有歌曲都在时间窗口内播放过，根据配置决定是否重置
        if prevention_config['reset_on_all_played']:
            prevention_config['played_songs'] = []
            prevention_config['last_reset_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_playlist_config(config)
            available_songs = valid_songs
        else:
            # 不重置，返回None表示无可用歌曲
            return None
    
    # 随机选择一首歌曲
    selected_song = random.choice(available_songs)
    
    # 记录播放历史
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prevention_config['played_songs'].append({
        'song_id': selected_song.get('id'),
        'song_name': selected_song.get('song_name', '未知'),
        'play_time': current_time
    })
    
    save_playlist_config(config)
    
    return selected_song

def get_random_song(songs):
    """随机选择一首歌曲（兼容旧版本）"""
    return get_random_song_with_prevention(songs)

def get_next_song_id(songs):
    """获取下一个可用的歌曲ID"""
    if not songs:
        return 1
    max_id = max(song.get('id', 0) for song in songs)
    return max_id + 1

def get_songs_statistics(songs):
    """获取歌曲统计信息"""
    valid_songs = filter_valid_songs(songs)
    total_songs = len(songs)
    valid_count = len(valid_songs)
    invalid_count = total_songs - valid_count
    
    # 统计点歌人
    requesters = {}
    for song in valid_songs:
        requester = song.get('requested_by', '未知')
        requesters[requester] = requesters.get(requester, 0) + 1
    
    return {
        'total_songs': total_songs,
        'valid_songs': valid_count,
        'invalid_songs': invalid_count,
        'requesters': requesters
    }

def display_statistics(statistics):
    """显示统计信息"""
    print("\n📊 歌曲统计信息 📊")
    print("=" * 40)
    print(f"总歌曲数: {statistics['total_songs']}")
    print(f"有效歌曲: {statistics['valid_songs']}")
    print(f"无效歌曲: {statistics['invalid_songs']}")
    print("\n👥 点歌人统计:")
    for requester, count in statistics['requesters'].items():
        print(f"  {requester}: {count}首")
    print("=" * 40)
