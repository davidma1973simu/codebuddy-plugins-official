---
description: 加载 tcase-codegen 和 alb-autotest-codegen 两个 skill，生成 ALB 测试用例代码
allowed-tools: Read,Write,Bash,Search
---

根据用户提供的 uuid / text_case / node 生成 ALB 测试用例代码。

## 强制执行流程

两个 skill **必须按顺序显式加载**，缺一不可，不可跳过任何一步：

### 步骤1: 加载 `tcase-codegen` skill
- 执行环境准备（获取 user_id、user_repo、user_branch）
- 参数组装与校验
- 调用 TCase MCP 工具获取初始生成代码
- **本步骤完成的标志**：MCP 返回 code 字段

### 步骤2: 加载 `alb-autotest-codegen` skill
- **必须在步骤1完成后立即加载，不要先自行搜索代码**
- 按照该 skill 定义的完整工作流（识别产品线 → 获取源码 → 分析接口类型 → 检索 API → 搜索类似实现 → 生成代码 → 验证）补全和完善代码
- 消除所有 TODO 占位符
- **本步骤完成的标志**：生成完整可执行的测试代码文件

### 输出
- 完整的测试代码文件（无 TODO）
- 可直接执行的测试命令