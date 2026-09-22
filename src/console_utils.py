"""
控制台编码兼容处理。

Windows 默认控制台代码页（936/GBK）无法编码 emoji 与部分中文标点，
直接 print 会抛 UnicodeEncodeError 导致程序崩溃。这里把标准流切到 UTF-8，
并把控制台输出代码页设为 65001（配合 chcp 65001 或 run.bat 使用）。
"""

import os
import sys


def setup_console():
    """尽力让控制台支持 UTF-8，失败也不影响主流程。"""
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass

    for stream_name in ("stdout", "stderr", "stdin"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
