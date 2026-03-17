# create_design

在 TestBuddy 中创建一个测试设计，并返回链接。用于用户在 **chat 模式下需要创建测试设计**时调用。

---

## 前置检查：认证信息

调用前检查 session 中是否同时存在 `token` 和 `username`。

如果两者都缺失，**停止后续步骤**，向用户说明：

```
需要您的 token 和 username 才能创建测试设计。
请前往 https://testbuddy.woa.com/tencent/personal/account 获取，并告知我。
```

等用户提供后，再继续执行步骤 1。

---

## 步骤 1：调用 design.py 创建测试设计

```shell
python3 <script_dir>/scripts/design.py create_design --name "测试设计-{当前日期}"
# 有 namespace 时加上：--namespace my_project
```

| 参数          | 必填 | 说明                                                   |
| ------------- | ---- | ------------------------------------------------------ |
| `name`        | ✅   | 从对话上下文中提取需求标题，兜底用 `"测试设计-{日期}"` |
| `description` | 可选 | 需求摘要                                               |
| `namespace`   | 可选 | 智研项目 ID，用户提供时带上                            |

**返回值示例**：

```json
{
  "status": "success",
  "data": {
    "uid": "design-24wGi2ej3N",
    "name": "测试设计-20260316",
    "url": "https://testbuddy.woa.com/tencent/tb/workbench#/testx/jeriezhang/design/design-24wGi2ej3N"
  }
}
```

提取 `data.url` 作为最终展示给用户的链接。

---

## 步骤 2：返回链接

提取 `data.url` 和 `data.name`，返回给调用方使用。

---

## 错误处理

| 错误场景                 | 处理方式                                                                            |
| ------------------------ | ----------------------------------------------------------------------------------- |
| `create_design` 调用失败 | 提示用户手动访问 http://testbuddy.woa.com/                                          |
| 返回值中 `data.url` 为空 | 根据 `data.uid` 拼接：`https://testbuddy.woa.com/tencent/tb/workbench#/testx/{uid}` |

---

## 注意事项

1. **`data.url` 使用返回值**，不要手动拼接
2. 此工具仅负责创建测试设计，若用户意图是**打开 TestBuddy 页面**，请使用 `open_design` 工具
