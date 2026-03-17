# get_session

初始化当前测试会话，一次性完成：加载 session 参数、判断运行模式、补充缺失上下文。

## 使用方式

```shell
python3 <skills_dir>/scripts/get_session.py
```

**注意**：执行脚本前**不要切换目录（不要 cd）**，确保在工作区根目录执行。

---

## 步骤 1：执行脚本，读取 session

```shell
python3 <skills_dir>/scripts/get_session.py
```

脚本自动判断运行模式：

| mode 值   | 含义     | 判断条件                  |
| --------- | -------- | ------------------------- |
| `mindmap` | 脑图模式 | `design_uid` 存在且非空   |
| `chat`    | 会话模式 | `design_uid` 不存在或为空 |

---

## 步骤 2：根据 mode 完成初始化

### 脑图模式（mindmap）

session.json 已由画布自动填充完整上下文，**无需额外补充**，直接进入后续工作流。

**输出示例**：

```json
{
  "mode": "mindmap",
  "design_uid": "design-Az7SsiL3Ui",
  "namespace": "...",
  "select_node": {
    "uid": "test_point-X0krRg3bP2",
    "kind": "TEST_POINT",
    "name": "搜索结果展示"
  },
  "story_node": {
    "instance": {
      "WorkspaceUid": "69995517"
    }
  }
}
```

**关键字段说明**：

| 字段                               | 类型   | 说明                                                  |
| ---------------------------------- | ------ | ----------------------------------------------------- |
| `mode`                             | string | 固定为 `mindmap`                                      |
| `design_uid`                       | string | 测试设计 UID，后续操作必需                            |
| `namespace`                        | string | 智研项目 ID                                           |
| `select_node`                      | object | 用户在画布上选中的节点信息                            |
| `select_node.uid`                  | string | 选中节点的 UID                                        |
| `select_node.kind`                 | string | 选中节点的类型（STORY/FEATURE/SCENE/TEST_POINT/CASE） |
| `select_node.name`                 | string | 选中节点的名称                                        |
| `story_node`                       | object | 需求节点信息（如有）                                  |
| `story_node.instance.WorkspaceUid` | string | TAPD 工作空间 ID                                      |

---

### 会话模式（chat）

session.json 中缺少脑图上下文，需要 Agent 通过对话补充，再回写到 session.json。

**初始输出示例**：

```json
{
  "mode": "chat",
  "token": "user_token_string",
  "knowledge_uids": ["knowledge_uid_1"]
}
```

**关键字段说明**：

| 字段             | 类型   | 说明                            |
| ---------------- | ------ | ------------------------------- |
| `mode`           | string | 固定为 `chat`                   |
| `token`          | string | 用户认证令牌，后续 MCP 调用必需 |
| `knowledge_uids` | array  | 关联的知识库 UID 列表           |

**Agent 需要做的事**：

#### 1. 理解用户意图

理解用户想做什么（生成测试框架/用例等）

#### 2. 补充必要上下文

通过对话获取以下信息（视意图而定）：

- 需求链接（TAPD 链接等）或需求描述
- 目标模块/功能名称
- 其他必要的业务上下文

#### 3. 将补充的上下文回写到 session.json

```shell
echo '{"user_requirement": "用户描述的需求内容", "target_name": "目标名称"}' | python3 <skills_dir>/scripts/get_session.py --write
```

**成功输出**：

```json
{ "status": "success", "msg": "session.json 已更新" }
```

> **`env` 字段特殊处理**：`--write` 时 `env` 字段按 key 级别合并，有则更新、无则添加，不会整体覆盖。

#### 4. 继续后续工作流

上下文补充完成后，进入后续工作流（如 `select_workflow`、`add_nodes` 等）。

---

## 注意事项

- `<skills_dir>` 是脚本所在路径的前缀
- **脚本依赖当前工作目录，执行前不要 cd 切换目录**
- `--write` 回写操作是**合并写入**，不会覆盖已有字段；`env` 字段做 key 级别合并
