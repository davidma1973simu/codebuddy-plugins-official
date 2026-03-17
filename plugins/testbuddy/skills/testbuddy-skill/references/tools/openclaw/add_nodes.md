# add_nodes_chat

会话模式（chat）下的**节点添加**工具。通过内置脚本 `design.py` 直接调用 testx HTTP API 写入远程智研平台。

**⚠️ 重要**：执行脚本前**不要切换目录（不要 cd）**，确保在工作区根目录执行。

## 适用条件

- 仅在 `mode == "chat"` 时使用

## 前置条件

- 工作流已完成节点数据生成（框架/模块/场景/测试点/用例等）
- **无需依赖 session.json**，本工具自主完成所有操作

## 核心原则

| 规则                 | 说明                                           |
| -------------------- | ---------------------------------------------- |
| **默认创建测试设计** | 用户没提供 `design_uid` → 直接创建，**不询问** |
| **复用已有设计**     | 用户明确提供了 `design_uid` → 跳过创建         |
| **namespace 可选**   | 用户提供了就带上，没提供就不填（使用个人空间） |
| **禁止阻塞**         | 绝对不要因为缺少任何参数而停下来询问用户       |

---

## 完整操作流程

### 步骤 1：创建测试设计（create_design）

> 默认执行。仅当用户明确提供了 `design_uid` 时跳过。

```shell
python3 <script_dir>/scripts/design.py create_design --name "用户登录功能测试设计" --description "基于用户登录需求的测试设计"
# 有 namespace 时加上：--namespace my_project
```

| 参数          | 必填 | 说明                                                  |
| ------------- | ---- | ----------------------------------------------------- |
| `name`        | ✅   | 从需求标题/对话上下文提取，兜底用 `"测试设计-{日期}"` |
| `description` | 可选 | 需求分析摘要                                          |
| `namespace`   | 可选 | 智研项目ID                                            |

**返回值示例**：

```json
{
  "status": "success",
  "message": "测试设计创建成功",
  "data": {
    "uid": "design-24wGi2ej3N",
    "name": "MCP调用验证测试设计",
    "description": "验证API返回值结构",
    "url": "https://testbuddy.woa.com/tencent/tb/workbench#/testx/jeriezhang/design/design-24wGi2ej3N"
  }
}
```

**提取**：

- `data.uid` → 后续所有步骤的 `design_uid`
- `data.url` → 最终返回给用户的链接

---

### 步骤 1.5：创建 STORY 节点（仅当有 TAPD 需求时）

**判断条件**——满足以下**任一条件**时创建：

- 用户提供了 TAPD 需求链接
- 对话中通过 `get_story` 获取了需求详情
- 上下文中存在 `workspace` + `story_id`

**不满足 → 跳过**，步骤 2 的顶层节点直接挂在 `design_uid` 下。

```shell
python3 <script_dir>/scripts/design.py batch_create \
  --design_uid design-24wGi2ej3N \
  --resources '[{"Target":{"NodeParentUid":"design-24wGi2ej3N","Position":"CHILD"},"Nodes":[{"Meta":{"Name":"会话停止响应延迟过高","Kind":"STORY"},"Spec":{"Instance":{"Workspace":"69995517","IssueId":"106999551700123","IssueSource":"TAPD","IssueUrl":"https://tapd.woa.com/tapd_fe/69995517/story/detail/106999551700123"}}}]}]'
```

**返回值示例**：

```json
{
  "status": "success",
  "message": "成功批量创建 1 个节点",
  "data": {
    "nodes": [
      {
        "uid": "story-yDt63XOVE7",
        "name": "测试需求STORY",
        "kind": "STORY",
        "parent_uid": "design-24wGi2ej3N"
      }
    ],
    "total_count": 1
  }
}
```

**提取**：`data.nodes[0].uid`（如 `story-yDt63XOVE7`），作为步骤 2 中 FEATURE 的父节点。

---

### 步骤 2：逐层批量创建节点（batch_create_design_nodes）

> **逐层创建**：父节点必须先创建拿到真实 uid，才能创建子节点。

#### ⚠️ API 核心数据结构（重要）

`batch_create_design_nodes` 的 `resources` 是一个**容器数组**，每个容器结构如下：

```json
{
  "Target": {
    "NodeParentUid": "父节点的真实uid",
    "Position": "CHILD"
  },
  "Nodes": [
    {
      "Meta": { "Name": "节点名称", "Kind": "FEATURE" },
      "Spec": {}
    }
  ]
}
```

**关键规则**：

1. **`resources` 里的每个元素必须包含 `Nodes` 字段，且 `Nodes` 不能为空**——否则报错 `"每个resource必须包含非空的Nodes字段"`
2. **`Nodes` 里的每个节点必须包含 `Meta` 字段**——否则报错 `"节点必须包含Meta字段"`
3. **不要在 resources 顶层放 `Name`/`Kind`**——它们必须放在 `Nodes[].Meta` 里
4. **API 只创建 `Nodes` 里一层的节点**，不会递归创建嵌套的 `Nodes`
5. **同一个 `Target` 下的多个节点可以放在同一个 `Nodes` 数组中批量创建**

#### 支持的 Kind 类型

| Kind         | 说明                        |
| ------------ | --------------------------- |
| `STORY`      | 需求节点（仅步骤 1.5 使用） |
| `FEATURE`    | 功能模块                    |
| `SCENE`      | 测试场景                    |
| `TEST_POINT` | 测试点                      |
| `CASE`       | 测试用例                    |

#### CASE 节点的 Spec 结构

CASE 节点需要通过 `Spec.Instance` 传递优先级、前置条件和步骤：

```json
{
  "Meta": { "Name": "输入正确账号密码成功登录", "Kind": "CASE" },
  "Spec": {
    "Instance": {
      "Priority": "P0",
      "PreConditions": "用户已注册有效账号",
      "Steps": [
        { "Content": "打开登录页面", "ExpectedResult": "页面正常显示" },
        { "Content": "输入正确的账号和密码", "ExpectedResult": "登录成功" }
      ]
    }
  }
}
```

#### 逐层创建流程

**第一层：创建 FEATURE**

```shell
python3 <script_dir>/scripts/design.py batch_create \
  --design_uid design-24wGi2ej3N \
  --resources '[{"Target":{"NodeParentUid":"story-yDt63XOVE7","Position":"CHILD"},"Nodes":[{"Meta":{"Name":"停止按钮响应","Kind":"FEATURE"}},{"Meta":{"Name":"流式输出中断","Kind":"FEATURE"}}]}]'
```

**返回值示例**：

```json
{
  "status": "success",
  "message": "成功批量创建 2 个节点",
  "data": {
    "nodes": [
      {
        "uid": "feature-V93fsvnEeZ",
        "name": "停止按钮响应",
        "kind": "FEATURE",
        "parent_uid": "story-yDt63XOVE7"
      },
      {
        "uid": "feature-HE3gS82uSS",
        "name": "流式输出中断",
        "kind": "FEATURE",
        "parent_uid": "story-yDt63XOVE7"
      }
    ],
    "total_count": 2
  }
}
```

**提取**：通过 `name` 匹配找到对应 `uid`：

- `停止按钮响应 → feature-V93fsvnEeZ`
- `流式输出中断 → feature-HE3gS82uSS`

**第二层：创建 CASE**（使用上一步的真实 uid）

> 不同父节点下的 CASE 可以用**多个 resources 容器**在一次调用中完成。

```shell
python3 <script_dir>/scripts/design.py batch_create \
  --design_uid design-24wGi2ej3N \
  --resources '[{"Target":{"NodeParentUid":"feature-V93fsvnEeZ","Position":"CHILD"},"Nodes":[{"Meta":{"Name":"点击停止后1秒内停止输出","Kind":"CASE"},"Spec":{"Instance":{"Priority":"P0","PreConditions":"会话正在流式输出中","Steps":[{"Content":"点击停止按钮","ExpectedResult":"1秒内停止输出"}]}}},{"Meta":{"Name":"停止后不产生多余内容","Kind":"CASE"},"Spec":{"Instance":{"Priority":"P0","Steps":[{"Content":"点击停止并观察","ExpectedResult":"无多余内容"}]}}}]},{"Target":{"NodeParentUid":"feature-HE3gS82uSS","Position":"CHILD"},"Nodes":[{"Meta":{"Name":"中断后连接正常断开","Kind":"CASE"},"Spec":{"Instance":{"Priority":"P1","Steps":[{"Content":"停止后检查连接","ExpectedResult":"SSE连接关闭"}]}}}]}]'
```

**返回值示例**：

```json
{
  "status": "success",
  "message": "成功批量创建 3 个节点",
  "data": {
    "nodes": [
      {
        "uid": "case-4l4hOWCX7x",
        "name": "点击停止后1秒内停止输出",
        "kind": "CASE",
        "parent_uid": "feature-V93fsvnEeZ"
      },
      {
        "uid": "case-jnh6XCtubO",
        "name": "停止后不产生多余内容",
        "kind": "CASE",
        "parent_uid": "feature-V93fsvnEeZ"
      },
      {
        "uid": "case-CQeBPCccru",
        "name": "中断后连接正常断开",
        "kind": "CASE",
        "parent_uid": "feature-HE3gS82uSS"
      }
    ],
    "total_count": 3
  }
}
```

#### 工作流字段到 API 字段的映射

| 工作流字段                  | API 字段                               | 说明     |
| --------------------------- | -------------------------------------- | -------- |
| `name`                      | `Meta.Name`                            | 节点名称 |
| `kind`                      | `Meta.Kind`                            | 节点类型 |
| `description`               | `Meta.Description`                     | 可选描述 |
| `instance.priority`         | `Spec.Instance.Priority`               | 仅 CASE  |
| `instance.preconditions`    | `Spec.Instance.PreConditions`          | 仅 CASE  |
| `instance.steps[].action`   | `Spec.Instance.Steps[].Content`        | 仅 CASE  |
| `instance.steps[].expected` | `Spec.Instance.Steps[].ExpectedResult` | 仅 CASE  |

**分批策略**：超过 50 个节点时分批，每批不超过 50 个。

---

### 步骤 3：返回结果给用户

```
测试设计创建成功！

设计名称：{name}
测试设计链接：{data.url}

已创建 X 个功能模块、Y 个测试用例。
您可以通过以上链接在智研平台查看和管理测试设计。
```

`data.url` 来自步骤 1 `create_design` 的返回值。

---

## 端到端完整示例

用户为 TAPD 需求生成了 2 个 FEATURE、每个下面 2 个 CASE。

### 第 1 步：create_design → 拿到 design_uid

```shell
python3 <script_dir>/scripts/design.py create_design --name "会话停止响应延迟优化测试设计"
```

→ 返回 `data.uid = "design-001"`，`data.url = "https://..."`

### 第 2 步：创建 STORY → 拿到 story_uid

```shell
python3 <script_dir>/scripts/design.py batch_create \
  --design_uid design-001 \
  --resources '[{"Target":{"NodeParentUid":"design-001","Position":"CHILD"},"Nodes":[{"Meta":{"Name":"会话停止响应延迟过高","Kind":"STORY"},"Spec":{"Instance":{"Workspace":"69995517","IssueId":"106999551700123","IssueSource":"TAPD","IssueUrl":"https://tapd.woa.com/..."}}}]}]'
```

→ 返回 `data.nodes[0].uid = "story-s01"`

### 第 3 步：创建 FEATURE → 拿到 feature_uid

```shell
python3 <script_dir>/scripts/design.py batch_create \
  --design_uid design-001 \
  --resources '[{"Target":{"NodeParentUid":"story-s01","Position":"CHILD"},"Nodes":[{"Meta":{"Name":"停止按钮响应","Kind":"FEATURE"}},{"Meta":{"Name":"流式输出中断","Kind":"FEATURE"}}]}]'
```

→ 返回 `feature-f01`、`feature-f02`

### 第 4 步：创建 CASE（不同父节点的 CASE 用多个 resources 容器，一次调用完成）

```shell
python3 <script_dir>/scripts/design.py batch_create \
  --design_uid design-001 \
  --resources '[{"Target":{"NodeParentUid":"feature-f01","Position":"CHILD"},"Nodes":[{"Meta":{"Name":"用例1","Kind":"CASE"},"Spec":{"Instance":{"Priority":"P0","Steps":[...]}}},{"Meta":{"Name":"用例2","Kind":"CASE"},"Spec":{"Instance":{"Priority":"P0","Steps":[...]}}}]},{"Target":{"NodeParentUid":"feature-f02","Position":"CHILD"},"Nodes":[{"Meta":{"Name":"用例3","Kind":"CASE"},"Spec":{...}},{"Meta":{"Name":"用例4","Kind":"CASE"},"Spec":{...}}]}]'
```

**总计脚本调用**：4 次（create_design → STORY → FEATURE → CASE）。

---

## 错误处理

| 错误信息                              | 原因                                               | 解决方式                                  |
| ------------------------------------- | -------------------------------------------------- | ----------------------------------------- |
| `每个resource必须包含非空的Nodes字段` | resources 中的元素缺少 `Nodes` 或 `Nodes` 为空数组 | 确保每个 resource 都有非空的 `Nodes` 数组 |
| `节点必须包含Meta字段`                | `Nodes` 里的节点缺少 `Meta`                        | 确保每个节点都有 `Meta: {Name, Kind}`     |
| `namespace 不存在`                    | namespace 无效                                     | 去掉 namespace，使用个人空间重试          |
| `design_uid 无效`                     | 步骤 1 失败或 uid 错误                             | 检查 create_design 返回值                 |

---

## 注意事项

1. **默认创建测试设计**，不要因为缺参数而询问用户
2. **resources 结构**：`[{Target: {...}, Nodes: [{Meta: {...}, Spec: {...}}]}]`——不要在顶层放 Name/Kind
3. **逐层创建**：父节点必须先创建拿到 uid，再创建子节点
4. **同一父节点下的多个子节点**放在同一个 `Nodes` 数组中
5. **不同父节点的子节点**用多个 resources 容器，可以一次调用完成
6. **TAPD 需求才创建 STORY**：自由文本需求直接创建 FEATURE 挂在 design_uid 下
7. **返回值路径**：`data.nodes[].uid` 和 `data.nodes[].name`，通过 name 匹配找 uid
8. **design_url 用返回值中的 `data.url`**，不要手动拼接
