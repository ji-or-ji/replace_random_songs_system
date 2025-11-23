#!/usr/bin/env python3
"""
测试运行脚本
用于运行随机点歌系统的单元测试
"""

import unittest
import sys
import os

def run_tests():
    """运行所有测试"""
    # 添加当前目录到Python路径
    sys.path.insert(0, os.path.dirname(__file__))
    
    # 发现并运行测试
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()

if __name__ == '__main__':
    print("🎵 随机点歌系统 - 单元测试 🎵")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败！")
        sys.exit(1)
