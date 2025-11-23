import json
import datetime
import os

def record_history(action_type, action_details, playlist_id=None, result="成功"):
    """记录操作历史到文件"""
    history_record = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action_type,
        "details": action_details,
        "result": result
    }
    
    # 确定目标歌单ID
    target_playlist_id = playlist_id if playlist_id else get_current_playlist_id()
    
    # 构建历史记录文件路径
    history_file_path = f"main_data/{target_playlist_id}/history_records.log"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(history_file_path), exist_ok=True)
    
    try:
        # 尝试读取现有历史记录
        with open(history_file_path, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
            history_data.append(history_record)
            
            # 保存更新后的历史记录
            with open(history_file_path, 'w', encoding='utf-8') as f_out:
                json.dump(history_data, f_out, ensure_ascii=False, indent=2)
            return True
    except FileNotFoundError:
        # 文件不存在，创建新文件
        try:
            with open(history_file_path, 'w', encoding='utf-8') as f_out:
                json.dump([history_record], f_out, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"创建历史记录文件失败: {e}")
            return False
    except json.JSONDecodeError:
        # 文件存在但格式错误，重新创建
        try:
            with open(history_file_path, 'w', encoding='utf-8') as f_out:
                json.dump([history_record], f_out, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"修复历史记录文件失败: {e}")
            return False
    except Exception as e:
        print(f"记录历史失败: {e}")
        return False

def view_history(playlist_id=None):
    """查看历史记录"""
    # 确定目标歌单ID
    target_playlist_id = playlist_id if playlist_id else get_current_playlist_id()
    
    # 构建历史记录文件路径
    history_file_path = f"main_data/{target_playlist_id}/history_records.log"
    
    try:
        with open(history_file_path, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
            
            if not history_data:
                print("暂无历史记录")
                return
            
            print(f"\n📜 歌单 '{target_playlist_id}' 操作历史记录 📜")
            print("=" * 60)
            for i, record in enumerate(history_data, 1):
                print(f"{i}. [{record['timestamp']}] {record['action']}")
                print(f"   详情: {record['details']}")
                print(f"   结果: {record['result']}")
                print("-" * 40)
    except FileNotFoundError:
        print("暂无历史记录")
    except json.JSONDecodeError:
        print(f"历史记录文件已损坏: {history_file_path}")
    except Exception as e:
        print(f"读取历史记录失败: {e}")

def get_current_playlist_id():
    """获取当前歌单ID"""
    try:
        from config_manager import load_playlist_config
        config = load_playlist_config()
        return config.get("current_playlist", "play_list_1")
    except ImportError:
        return "play_list_1"  # 默认歌单ID
