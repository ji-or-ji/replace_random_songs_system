#!/usr/bin/env python3
"""
数据备份脚本：把 main_data/ 打包成一个带时间戳的 zip，放到 backups/ 下。

用法:
    python scripts/backup_data.py
"""

import datetime
import os
import sys
import zipfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_ROOT, "main_data")
_BACKUP_DIR = os.path.join(_ROOT, "backups")


def main():
    if not os.path.isdir(_DATA_DIR):
        print(f"未找到数据目录: {_DATA_DIR}")
        return 1

    os.makedirs(_BACKUP_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = os.path.join(_BACKUP_DIR, f"main_data_{stamp}.zip")

    count = 0
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(_DATA_DIR):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, _DATA_DIR)
                zf.write(full, os.path.join("main_data", rel))
                count += 1

    print(f"✅ 已备份 {count} 个文件到: {archive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
