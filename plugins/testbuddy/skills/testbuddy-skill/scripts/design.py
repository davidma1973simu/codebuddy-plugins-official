#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# design.py：testx design 相关工具的内置脚本封装
#
# 用法：
#   python3 design.py create_design   --name "测试设计名称" [--namespace xxx] [--description xxx]
#
# 所有命令均从 session.json 自动读取 token / namespace（命令行参数优先）

import argparse
import json
import os
import sys

if sys.version_info[0] < 3:
    print("错误：此脚本需要 Python 3，请使用 python3 运行", file=sys.stderr)
    sys.exit(1)

try:
    import ssl
    import urllib.error as urllib_error
    import urllib.request as urllib_request
except ImportError:
    print(json.dumps({"status": "error", "msg": "urllib 不可用，请使用 Python 3"}))
    sys.exit(1)

# 内网环境跳过 SSL 证书验证
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# ──────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────
BASE_URL = "https://testbuddy.woa.com"
SESSION_FILE = os.path.join(os.getcwd(), ".testbuddy/env/session.json")


# ──────────────────────────────────────────────
# Session 工具
# ──────────────────────────────────────────────
def load_session():
    """从 session.json 读取 token / namespace 等信息"""
    if not os.path.exists(SESSION_FILE):
        return {}
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────
# HTTP 工具
# ──────────────────────────────────────────────
def _request(method, path, token, body=None):
    """发送 HTTP 请求，返回解析后的 JSON 响应"""
    url = BASE_URL + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Authorization": "token {}".format(token),
        "Content-Type": "application/json",
        "x-testbuddy-origin": "testbuddy-skill",
    }
    req = urllib_request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib_request.urlopen(req, timeout=30, context=SSL_CONTEXT) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib_error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {"Error": {"Code": str(e.code), "Message": raw}}
    except Exception as e:
        return {"Error": {"Code": "NetworkError", "Message": str(e)}}


def _get(path, token):
    return _request("GET", path, token)


def _post(path, token, body):
    return _request("POST", path, token, body)


def _put(path, token, body):
    return _request("PUT", path, token, body)


# ──────────────────────────────────────────────
# 命令实现
# ──────────────────────────────────────────────
def cmd_create_design(args, session):
    """
    创建测试设计
    POST /api/testx/design/v2/namespaces/{namespace}/designs
    """
    token = args.token or session.get("token", "")
    username = args.username or session.get("username", "")
    namespace = args.namespace or session.get("namespace") or username
    name = args.name
    description = args.description or ""

    if not token and not username:
        return {
            "status": "need_input",
            "fields": ["token", "username"],
            "msg": "需要 token 和 username 才能继续，请向用户索取后重试。\n"
            "可前往 https://testbuddy.woa.com/tencent/personal/account 获取。",
        }
    if not name:
        return {"status": "error", "msg": "缺少 --name 参数"}

    body = {
        "Meta": {"Name": name},
        "Spec": {"Description": description, "Stories": [], "Bugs": []},
    }
    path = "/api/testx/design/v2/namespaces/{}/designs".format(namespace)

    resp = _post(path, token, body)

    err = resp.get("Error")
    if err and err.get("Code"):
        return {"status": "error", "msg": err.get("Message", str(err))}

    data = resp.get("Data", {})
    meta = data.get("Meta", {})
    uid = meta.get("Uid", "")
    url = data.get("Url") or data.get("url", "")

    # 兼容 MCP 返回格式
    return {
        "status": "success",
        "message": "测试设计创建成功",
        "data": {
            "uid": uid,
            "name": name,
            "description": description,
            "url": url or "{}/tencent/tb/workbench#/testx/{}/design/{}".format(BASE_URL, namespace, uid),
        },
    }


# def cmd_batch_create(args, session):
#     """
#     批量创建节点（暂不实现）
#     """
#     pass


# def cmd_batch_update(args, session):
#     """
#     批量更新节点（暂不实现）
#     """
#     pass


# def cmd_batch_delete(args, session):
#     """
#     批量删除节点（暂不实现）
#     """
#     pass


# def cmd_get_nodes(args, session):
#     """
#     获取设计节点树（暂不实现）
#     """
#     pass


# ──────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────
COMMANDS = {
    "create_design": cmd_create_design,
    # "batch_create": cmd_batch_create,   # 暂不实现
    # "batch_update": cmd_batch_update,   # 暂不实现
    # "batch_delete": cmd_batch_delete,   # 暂不实现
    # "get_nodes": cmd_get_nodes,         # 暂不实现
}

USAGE = """
用法：python3 design.py <command> [options]

命令：
  create_design   创建测试设计

通用选项（所有命令均支持，优先级高于 session.json）：
  --token TOKEN           用户认证令牌
  --namespace NAMESPACE   智研项目 ID（不填则使用个人空间）

create_design 选项：
  --name NAME             测试设计名称（必填）
  --description DESC      测试设计描述

示例：
  python3 design.py create_design --name "登录功能测试设计"
  python3 design.py create_design --name "登录功能测试设计" --namespace my_project
"""


if __name__ == "__main__":
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0)

    command = sys.argv[1]
    if command not in COMMANDS:
        print(
            json.dumps(
                {"status": "error", "msg": "未知命令: {}，支持的命令: {}".format(command, ", ".join(COMMANDS.keys()))},
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    # 解析参数
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("cmd")
    parser.add_argument("--token", default=None)
    parser.add_argument("--username", default=None)
    parser.add_argument("--namespace", default=None)
    # parser.add_argument("--design_uid", default=None)  # 暂不实现
    parser.add_argument("--name", default=None)
    parser.add_argument("--description", default=None)
    # parser.add_argument("--resources", default=None)  # 暂不实现
    # parser.add_argument("--nodes", default=None)      # 暂不实现
    # parser.add_argument("--uids", default=None)       # 暂不实现

    try:
        args = parser.parse_args()
    except SystemExit:
        print(json.dumps({"status": "error", "msg": "参数解析失败，请检查参数格式"}, ensure_ascii=False))
        sys.exit(1)

    session = load_session()

    try:
        result = COMMANDS[command](args, session)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("status") == "success" else 1)
    except Exception as e:
        print(json.dumps({"status": "error", "msg": "脚本执行异常: {}".format(str(e))}, ensure_ascii=False, indent=2))
        sys.exit(1)
