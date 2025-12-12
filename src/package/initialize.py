

# 导入模块
import yaml
import os
import datetime


def initialize_system():
    """初始化系统，检查并创建必要的文件和目录"""
    print("正在初始化系统...")
    
    # 创建主数据目录
    main_data_dirs = [
        'main_data',
        'main_data/global',
        'main_data/global/history',
        'main_data/play_list_1',
        'main_data/play_list_1/songs'
    ]
    
    # 初始化变量
    create_directory : str = "F"
    
    for dir_path in main_data_dirs:
        if not os.path.exists(dir_path):
            print("似乎主文件目录不见了...正在还原...")
            os.makedirs(dir_path, exist_ok=True)
            print(f"📁 创建目录: {dir_path}")
            create_directory = "T"
    
    # 检查并创建全局配置文件
    global_config_path = 'main_data/global/global_config.yaml'
    if not os.path.exists(global_config_path):
        print("似乎全局配置文件不见了...正在还原...")
        global_config = {
            "system_version": "2.0.1",
            "initialized_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_playlists": 1
        }
        with open(global_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(global_config, f, allow_unicode=True, default_flow_style=False)
        print("✅ 创建全局配置文件\n")
        create_global_configuration_file : str = "T"
    else :
        create_global_configuration_file : str = "F"
    
    # 检查并创建全局历史记录文件
    global_history_path = 'main_data/global/history/global_play_history.log'
    if not os.path.exists(global_history_path):
        print("似乎局历史记录不见了...正在还原...")
        with open(global_history_path, 'w', encoding='utf-8') as f:
            f.write(f"全局历史记录初始化于: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("✅ 创建全局播放历史文件\n")
        create_global_play_history_file : str = "T"
    else :
        create_global_play_history_file : str = "F"
    
    global_operate_history_path = 'main_data/global/history/global_operate_history.log'
    if not os.path.exists(global_operate_history_path):
        with open(global_operate_history_path, 'w', encoding='utf-8') as f:
            f.write(f"全局操作历史初始化于: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("✅ 创建全局操作历史文件\n")
        create_global_operation_history_file : str = "T"
    else :
        create_global_operation_history_file : str = "F"
    
    print("🎉 系统初始化完成！")
    return (create_directory , create_global_configuration_file , create_global_play_history_file , create_global_operation_history_file)


if __name__ == "__main__" :
    input("\n按回车键退出程序...")
