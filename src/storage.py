"""
底层存储工具：YAML 读写（原子写入）与文本日志追加。
"""

import os
import tempfile

import yaml


def load_yaml(path, default=None):
    """读取 YAML；文件不存在或损坏时返回 default（不抛异常）。"""
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as exc:
        print(f"[警告] 读取失败，改用默认值: {path} ({exc})")
        return default
    if data is None:
        return default
    return data


def save_yaml(path, data):
    """原子写入 YAML：先写同目录临时文件再替换，避免写一半损坏数据。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=parent or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def append_line(path, line):
    """向文本文件追加一行（自动建目录）。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")


def read_lines(path, limit=None, newest_first=False):
    """读取文本文件所有行；文件不存在返回空列表。"""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]
    except OSError:
        return []
    lines = [line for line in lines if line.strip()]
    if newest_first:
        lines.reverse()
    if limit is not None:
        lines = lines[:limit]
    return lines
