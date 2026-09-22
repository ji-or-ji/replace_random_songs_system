#!/usr/bin/env python3
"""便捷入口：python run.py [参数]。

不带参数时＝静默抽一首（供 ClassIsland 等联动调用）；
需要交互菜单请加 --gui。参数详见 python run.py --help。
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from cli import main as cli_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(cli_main(sys.argv[1:]))
