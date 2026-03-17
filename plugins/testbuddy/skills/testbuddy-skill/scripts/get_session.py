#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys

# 强制使用 Python 3
if sys.version_info[0] < 3:
    print("错误：此脚本需要 Python 3，请使用 python3 运行", file=sys.stderr)
    sys.exit(1)

# 固定路径
SESSION_FILE = os.path.join(os.getcwd(), ".testbuddy/env/session.json")


def load_session():
    """加载 session.json 文件，并自动补全默认值"""
    if not os.path.exists(SESSION_FILE):
        return {"mode": "chat", "env": "codebuddy"}

    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 自动判断模式：如果存在 design_uid 且非空，则为脑图模式；否则为 chat 模式
    if "mode" not in data:
        if data.get("design_uid"):
            data["mode"] = "mindmap"
        else:
            data["mode"] = "chat"

    # env 字段表示 IDE 场景（codebuddy/openclaw），默认为 codebuddy
    if "env" not in data or not isinstance(data["env"], str):
        data["env"] = "codebuddy"

    return data


def save_session(data):
    """回写数据到 session.json"""
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def merge_session(existing, new_data):
    """
    合并新数据到现有 session：
    - dict 类型字段：key 级别合并（有则更新，无则添加）
    - 其他类型字段：直接覆盖更新
    """
    for key, value in new_data.items():
        if isinstance(value, dict):
            # dict 字段做 key 级别合并
            if key not in existing or not isinstance(existing[key], dict):
                existing[key] = {}
            existing[key].update(value)
        else:
            existing[key] = value
    return existing


if __name__ == "__main__":
    # 支持两种用法：
    # 1. python3 get_session.py          → 读取并输出 session
    # 2. python3 get_session.py --write   → 从 stdin 读取 JSON 并回写到 session.json
    if len(sys.argv) > 1 and sys.argv[1] == "--write":
        try:
            input_data = json.loads(sys.stdin.read())
            # 加载现有数据并合并
            existing = load_session()
            merged = merge_session(existing, input_data)
            save_session(merged)
            print(json.dumps(merged, ensure_ascii=False, indent=2))
        except Exception as e:
            print(json.dumps({"status": "error", "msg": str(e)}, ensure_ascii=False))
            sys.exit(1)
    else:
        data = load_session()
        print(json.dumps(data, ensure_ascii=False, indent=2))
