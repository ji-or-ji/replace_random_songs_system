#!/usr/bin/env python3
"""便捷入口：从项目根目录直接运行（python run.py）。"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from main import cli  # noqa: E402

if __name__ == "__main__":
    cli()
