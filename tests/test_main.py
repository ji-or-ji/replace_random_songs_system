import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from CLI.main import initialize_system, get_random_song, display_song_info, settings_menu, main


class TestMain(unittest.TestCase):
    """测试main.py的主要功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # 创建必要的目录结构
        os.makedirs('main_data/global/history', exist_ok=True)
        os.makedirs('main_data/play_list_1/songs', exist_ok=True)
    
    def tearDown(self):
        """测试后的清理工作"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_initialize_system_creates_directories(self):
        """测试系统初始化创建必要的目录"""
        # 删除已创建的目录
        shutil.rmtree('main_data')
        
        # 执行初始化
        initialize_system()
        
        # 验证目录是否创建
        expected_dirs = [
            'main_data',
            'main_data/global',
            'main_data/global/history',
            'main_data/play_list_1',
            'main_data/play_list_1/songs'
        ]
        
        for dir_path in expected_dirs:
            self.assertTrue(os.path.exists(dir_path), f"目录 {dir_path} 应该被创建")
    
    def test_initialize_system_creates_config_files(self):
        """测试系统初始化创建配置文件"""
        # 删除已创建的目录
        shutil.rmtree('main_data')
        
        # 执行初始化
        initialize_system()
        
        # 验证配置文件是否创建
        expected_files = [
            'main_data/global/global_config.json',
            'main_data/play_list_1/play_lists_config.json',
            'main_data/play_list_1/songs_list.json',
            'main_data/play_list_1/requester_list.json',
            'main_data/play_list_1/history_records.log',
            'main_data/auto_jump_config.json',
            'main_data/global/history/global_play_history.log',
            'main_data/global/history/global_operate_history.log'
        ]
        
        for file_path in expected_files:
            self.assertTrue(os.path.exists(file_path), f"文件 {file_path} 应该被创建")
    
    def test_initialize_system_global_config_content(self):
        """测试全局配置文件内容"""
        # 删除已创建的目录
        shutil.rmtree('main_data')
        
        # 执行初始化
        initialize_system()
        
        # 验证全局配置文件内容
        with open('main_data/global/global_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.assertIn('system_version', config)
        self.assertIn('initialized_at', config)
        self.assertIn('total_playlists', config)
        self.assertEqual(config['total_playlists'], 1)
    
    def test_initialize_system_songs_list_content(self):
        """测试歌曲列表文件内容"""
        # 删除已创建的目录
        shutil.rmtree('main_data')
        
        # 执行初始化
        initialize_system()
        
        # 验证歌曲列表文件内容
        with open('main_data/play_list_1/songs_list.json', 'r', encoding='utf-8') as f:
            songs_data = json.load(f)
        
        self.assertIn('songs', songs_data)
        self.assertIsInstance(songs_data['songs'], list)
        self.assertEqual(len(songs_data['songs']), 5)  # 应该有5首示例歌曲
        
        # 验证第一首歌曲的结构
        first_song = songs_data['songs'][0]
        expected_keys = ['song_name', 'artist', 'requested_by', 'url_list', 'added_time']
        for key in expected_keys:
            self.assertIn(key, first_song)
    
    @patch('main.get_random_song_with_prevention')
    def test_get_random_song_calls_prevention_function(self, mock_get_random):
        """测试get_random_song函数调用防重复函数"""
        # 设置模拟返回值
        mock_song = {
            'song_name': '测试歌曲',
            'artist': '测试歌手',
            'requested_by': '测试点歌人'
        }
        mock_get_random.return_value = mock_song
        
        # 测试歌曲列表
        test_songs = [mock_song]
        
        # 调用函数
        result = get_random_song(test_songs)
        
        # 验证函数调用和返回值
        mock_get_random.assert_called_once_with(test_songs)
        self.assertEqual(result, mock_song)
    
    @patch('main.record_history')
    @patch('main.auto_jump')
    def test_display_song_info_with_valid_song(self, mock_auto_jump, mock_record_history):
        """测试显示有效歌曲信息"""
        test_song = {
            'song_name': '测试歌曲',
            'artist': '测试歌手',
            'requested_by': '测试点歌人',
            'url_list': ['https://example.com/song1']
        }
        
        # 使用patch捕获print输出
        with patch('builtins.print') as mock_print:
            display_song_info(test_song)
            
            # 验证print被调用
            self.assertTrue(mock_print.called)
            
            # 验证历史记录被调用
            mock_record_history.assert_called_once()
            
            # 验证自动跳转被调用
            mock_auto_jump.assert_called_once_with(test_song)
    
    @patch('builtins.print')
    def test_display_song_info_with_none_song(self, mock_print):
        """测试显示None歌曲信息"""
        display_song_info(None)
        
        # 验证显示"没有找到有效的歌曲"
        mock_print.assert_called_with("没有找到有效的歌曲")
    
    @patch('main.load_playlist_config')
    @patch('main.playlist_menu')
    @patch('builtins.input')
    def test_settings_menu_playlist_management(self, mock_input, mock_playlist_menu, mock_load_config):
        """测试设置菜单中的歌单管理功能"""
        # 设置模拟返回值
        mock_load_config.return_value = {
            'current_playlist': 'play_list_1',
            'playlists': {
                'play_list_1': {'name': '默认歌单'}
            }
        }
        mock_playlist_menu.return_value = ['new_song1', 'new_song2']
        mock_input.side_effect = ['1', '4']  # 选择歌单管理，然后返回
        
        # 调用函数
        result = settings_menu()
        
        # 验证函数调用和返回值
        mock_playlist_menu.assert_called_once()
        self.assertEqual(result, ['new_song1', 'new_song2'])
    
    @patch('main.load_playlist_config')
    @patch('main.auto_jump_menu')
    @patch('builtins.input')
    def test_settings_menu_auto_jump(self, mock_input, mock_auto_jump_menu, mock_load_config):
        """测试设置菜单中的自动跳转功能"""
        # 设置模拟返回值
        mock_load_config.return_value = {
            'current_playlist': 'play_list_1',
            'playlists': {
                'play_list_1': {'name': '默认歌单'}
            }
        }
        mock_input.side_effect = ['2', '4']  # 选择自动跳转，然后返回
        
        # 调用函数
        result = settings_menu()
        
        # 验证函数调用
        mock_auto_jump_menu.assert_called_once()
        self.assertIsNone(result)  # 没有返回新的歌曲列表
    
    @patch('main.load_playlist_config')
    @patch('main.duplicate_prevention_menu')
    @patch('builtins.input')
    def test_settings_menu_duplicate_prevention(self, mock_input, mock_duplicate_menu, mock_load_config):
        """测试设置菜单中的防重复功能"""
        # 设置模拟返回值
        mock_load_config.return_value = {
            'current_playlist': 'play_list_1',
            'playlists': {
                'play_list_1': {'name': '默认歌单'}
            }
        }
        mock_input.side_effect = ['3', '4']  # 选择防重复功能，然后返回
        
        # 调用函数
        result = settings_menu()
        
        # 验证函数调用
        mock_duplicate_menu.assert_called_once()
        self.assertIsNone(result)  # 没有返回新的歌曲列表
    
    @patch('main.load_playlist_config')
    @patch('builtins.input')
    def test_settings_menu_invalid_choice(self, mock_input, mock_load_config):
        """测试设置菜单中的无效选项"""
        # 设置模拟返回值
        mock_load_config.return_value = {
            'current_playlist': 'play_list_1',
            'playlists': {
                'play_list_1': {'name': '默认歌单'}
            }
        }
        mock_input.side_effect = ['99', '4']  # 无效选项，然后返回
        
        # 使用patch捕获print输出
        with patch('builtins.print') as mock_print:
            result = settings_menu()
            
            # 验证显示错误信息 - 检查是否包含错误消息
            error_calls = [call for call in mock_print.call_args_list 
                          if call[0] and "无效选项" in call[0][0]]
            self.assertTrue(len(error_calls) > 0, "应该显示无效选项错误消息")
            self.assertIsNone(result)
    
    @patch('main.initialize_system')
    @patch('main.load_songs')
    @patch('main.get_songs_statistics')
    @patch('main.display_statistics')
    @patch('builtins.input')
    def test_main_function_exit_option(self, mock_input, mock_display_stats, mock_get_stats, mock_load_songs, mock_init_system):
        """测试主函数退出选项"""
        # 设置模拟返回值
        mock_load_songs.return_value = ['song1', 'song2']
        mock_get_stats.return_value = {'total': 2}
        mock_input.side_effect = ['8']  # 直接选择退出
        
        # 调用主函数
        main()
        
        # 验证初始化函数被调用
        mock_init_system.assert_called_once()
        
        # 验证加载歌曲函数被调用
        mock_load_songs.assert_called_once()
        
        # 验证统计函数被调用
        mock_get_stats.assert_called_once_with(['song1', 'song2'])
        mock_display_stats.assert_called_once_with({'total': 2})
    
    @patch('main.initialize_system')
    @patch('main.load_songs')
    @patch('main.get_songs_statistics')
    @patch('main.display_statistics')
    @patch('builtins.input')
    def test_main_function_no_songs_exit(self, mock_input, mock_display_stats, mock_get_stats, mock_load_songs, mock_init_system):
        """测试主函数在没有歌曲时退出"""
        # 设置模拟返回值 - 没有歌曲
        mock_load_songs.return_value = []
        
        # 调用主函数
        main()
        
        # 验证初始化函数被调用
        mock_init_system.assert_called_once()
        
        # 验证加载歌曲函数被调用
        mock_load_songs.assert_called_once()
        
        # 验证统计函数没有被调用（因为没有歌曲）
        mock_get_stats.assert_not_called()
        mock_display_stats.assert_not_called()


if __name__ == '__main__':
    unittest.main()
