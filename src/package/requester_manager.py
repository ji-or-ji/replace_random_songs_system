import json
import os
from package.config_manager import load_playlist_config, save_playlist_config
from package.history_manager import record_history

def load_requesters(playlist_id=None):
    """加载点歌人列表文件"""
    config = load_playlist_config()
    
    if playlist_id:
        # 加载指定歌单的点歌人
        if playlist_id in config['playlists']:
            playlist = config['playlists'][playlist_id]
            # 根据歌单ID构建点歌人文件路径
            file_path = f'main_data/{playlist_id}/requester_list.json'
            target_playlist_id = playlist_id
        else:
            print(f'歌单不存在: {playlist_id}')
            return []
    else:
        # 加载当前歌单的点歌人
        current_playlist_id = config['current_playlist']
        playlist = config['playlists'][current_playlist_id]
        # 根据歌单ID构建点歌人文件路径
        file_path = f'main_data/{current_playlist_id}/requester_list.json'
        target_playlist_id = current_playlist_id
    
    # 在多个可能的位置查找点歌人文件
    possible_paths = [
        file_path,  # 当前目录
        f'../{file_path}',  # 父目录
        f'./{file_path}',  # 当前目录
        f'main_data/{target_playlist_id}/requester_list.json'  # 直接路径
    ]
    
    for json_path in possible_paths:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                requesters = json.load(f)
                print(f'成功加载点歌人列表: {json_path}')
                return requesters
        except FileNotFoundError:
            continue
        except json.JSONDecodeError:
            print(f'点歌人列表文件已损坏，请检查文件格式: {json_path}')
            return []
    
    print('点歌人列表文件不存在，将创建新文件')
    return []

def save_requesters(requesters, playlist_id=None):
    """保存点歌人列表到文件"""
    config = load_playlist_config()
    
    if playlist_id:
        # 保存到指定歌单
        if playlist_id in config['playlists']:
            file_path = f'main_data/{playlist_id}/requester_list.json'
        else:
            print(f'歌单不存在: {playlist_id}')
            return False
    else:
        # 保存到当前歌单
        current_playlist_id = config['current_playlist']
        file_path = f'main_data/{current_playlist_id}/requester_list.json'
    
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(requesters, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f'保存点歌人文件失败: {e}')
        return False

def add_requester():
    """添加点歌人"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    
    requesters = load_requesters()
    
    print("\n🎤 添加点歌人 🎤")
    print("=" * 30)
    
    while True:
        requester_name = input("请输入点歌人姓名: ").strip()
        if not requester_name:
            print("点歌人姓名不能为空，请重新输入")
            continue
        
        # 检查是否已存在
        if requester_name in requesters:
            print(f"点歌人 '{requester_name}' 已存在，请使用其他姓名")
            continue
        
        break
    
    requesters.append(requester_name)
    
    if save_requesters(requesters):
        record_history("添加点歌人", f"点歌人: {requester_name}", "成功")
        print(f"✅ 成功添加点歌人: {requester_name}")
    else:
        record_history("添加点歌人", f"点歌人: {requester_name}", "失败")
        print("❌ 添加点歌人失败")

def delete_requester():
    """删除点歌人"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    
    requesters = load_requesters()
    
    if not requesters:
        print("❌ 当前没有点歌人")
        return
    
    print("\n🎤 删除点歌人 🎤")
    print("=" * 30)
    print("当前点歌人列表:")
    for i, requester in enumerate(requesters, 1):
        print(f"{i}. {requester}")
    
    try:
        choice = int(input("\n请选择要删除的点歌人编号: "))
        if 1 <= choice <= len(requesters):
            requester_to_delete = requesters[choice - 1]
            
            # 确认删除
            confirm = input(f"确定要删除点歌人 '{requester_to_delete}' 吗? (y/N): ").strip().lower()
            if confirm == 'y':
                requesters.remove(requester_to_delete)
                
                if save_requesters(requesters):
                    record_history("删除点歌人", f"点歌人: {requester_to_delete}", "成功")
                    print(f"✅ 成功删除点歌人: {requester_to_delete}")
                else:
                    record_history("删除点歌人", f"点歌人: {requester_to_delete}", "失败")
                    print("❌ 删除点歌人失败")
            else:
                print("取消删除")
        else:
            print("❌ 无效的选择")
    except ValueError:
        print("❌ 请输入有效的数字")

def modify_requester():
    """修改点歌人姓名"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    
    requesters = load_requesters()
    
    if not requesters:
        print("❌ 当前没有点歌人")
        return
    
    print("\n🎤 修改点歌人 🎤")
    print("=" * 30)
    print("当前点歌人列表:")
    for i, requester in enumerate(requesters, 1):
        print(f"{i}. {requester}")
    
    try:
        choice = int(input("\n请选择要修改的点歌人编号: "))
        if 1 <= choice <= len(requesters):
            old_name = requesters[choice - 1]
            
            while True:
                new_name = input(f"请输入新的点歌人姓名 (原姓名: {old_name}): ").strip()
                if not new_name:
                    print("点歌人姓名不能为空，请重新输入")
                    continue
                
                if new_name in requesters and new_name != old_name:
                    print(f"点歌人 '{new_name}' 已存在，请使用其他姓名")
                    continue
                
                break
            
            requesters[choice - 1] = new_name
            
            if save_requesters(requesters):
                record_history("修改点歌人", f"原姓名: {old_name} -> 新姓名: {new_name}", "成功")
                print(f"✅ 成功修改点歌人: {old_name} -> {new_name}")
            else:
                record_history("修改点歌人", f"原姓名: {old_name} -> 新姓名: {new_name}", "失败")
                print("❌ 修改点歌人失败")
        else:
            print("❌ 无效的选择")
    except ValueError:
        print("❌ 请输入有效的数字")

def view_requesters():
    """查看点歌人列表"""
    config = load_playlist_config()
    current_playlist_id = config['current_playlist']
    playlist_name = config['playlists'][current_playlist_id]['name']
    
    requesters = load_requesters()
    
    print(f"\n🎤 点歌人列表 (歌单: {playlist_name}) 🎤")
    print("=" * 40)
    
    if not requesters:
        print("暂无点歌人")
    else:
        for i, requester in enumerate(requesters, 1):
            print(f"{i}. {requester}")
    
    print("=" * 40)

def get_requester_list():
    """获取点歌人列表（供其他模块使用）"""
    return load_requesters()

def requester_menu():
    """点歌人管理菜单"""
    while True:
        print("\n🎤 点歌人管理 🎤")
        print("=" * 20)
        print("1. 增加点歌人")
        print("2. 删除点歌人")
        print("3. 修改点歌人")
        print("4. 查看点歌人列表")
        print("5. 返回主菜单")
        
        choice = input("请选择操作: ").strip()
        
        if choice == '1':
            add_requester()
        elif choice == '2':
            delete_requester()
        elif choice == '3':
            modify_requester()
        elif choice == '4':
            view_requesters()
        elif choice == '5':
            break
        else:
            print("❌ 无效的选择，请重新输入")
