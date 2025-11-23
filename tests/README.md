# 随机点歌系统 - 单元测试

这个目录包含了随机点歌系统的单元测试。

## 测试结构

- `test_main.py` - 测试 main.py 的主要功能
- `run_tests.py` - 测试运行脚本

## 测试覆盖的功能

### main.py 测试覆盖

1. **系统初始化测试**
   - 测试目录创建
   - 测试配置文件创建
   - 测试配置文件内容正确性

2. **核心功能测试**
   - `get_random_song()` - 随机选歌功能
   - `display_song_info()` - 显示歌曲信息
   - `settings_menu()` - 设置菜单功能

3. **主函数测试**
   - 正常退出流程
   - 无歌曲时的退出流程

## 运行测试

### 方法1：使用测试运行脚本
```bash
python run_tests.py
```

### 方法2：直接使用 unittest
```bash
python -m unittest discover tests
```

### 方法3：运行特定测试文件
```bash
python -m unittest tests.test_main
```

### 方法4：运行特定测试方法
```bash
python -m unittest tests.test_main.TestMain.test_initialize_system_creates_directories
```

## 测试设计原则

1. **隔离性**：每个测试都在临时目录中运行，不影响实际数据
2. **模拟依赖**：使用 unittest.mock 模拟外部依赖
3. **全面覆盖**：测试正常流程和边界情况
4. **中文描述**：测试用例和方法名使用中文，便于理解

## 测试依赖

测试需要以下 Python 标准库：
- `unittest` - 测试框架
- `unittest.mock` - 模拟对象
- `tempfile` - 临时目录管理
- `shutil` - 文件操作
- `json` - JSON 处理
- `os`, `sys` - 系统操作

## 添加新测试

当添加新功能到 main.py 时，请相应地在 `test_main.py` 中添加测试用例：

1. 在 `TestMain` 类中添加新的测试方法
2. 方法名以 `test_` 开头
3. 使用适当的模拟来隔离外部依赖
4. 测试正常情况和异常情况

## 测试最佳实践

- 每个测试方法应该只测试一个功能
- 使用 `setUp()` 和 `tearDown()` 进行测试准备和清理
- 使用描述性的测试方法名
- 验证函数的输入和输出
- 测试边界条件和错误情况
