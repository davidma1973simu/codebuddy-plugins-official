---
description: Spec工作流
alwaysApply: false
enabled: true
updatedAt: 2026-02-02
provider:
---

# Spec工作流

**触发关键词**：`生成测试用例`、`生成用例`、`根据测试点生成用例`、`根据需求生成用例`

**Spec工作流简介**：基于需求分析和参考节点，生成全面的测试用例（包括正常、异常、边界等场景）

**Spec工作流约束**：

- 禁止调用`analyze`、`generate`、`生成节点`、`recall`工具
- 必须严格按照 查询需求 -> 需求分析 -> 测试点设计 -> 用例生成 Spec工作流进行
- 输出中禁止出现分割线
- 保留分析过程

## 执行清单规划

在开始执行前，Spec工作流需要：

1. 使用 `todo_write` 工具创建执行清单，将下述执行步骤转化为 TODO 列表
2. 每完成一个步骤后，立即更新对应 TODO 的状态为 `completed`
3. 开始新步骤时，将对应 TODO 状态更新为 `in_progress`
4. 如遇到错误需跳过某步骤，将对应 TODO 状态更新为 `cancelled`

**标准 TODO 清单模板**：

**无知识库场景**（检测到 `<attached_files>` 区域无知识库时使用）：

```json
[
  { "id": "1", "status": "pending", "content": "确认参考节点" },
  { "id": "2", "status": "pending", "content": "查找关联需求" },
  { "id": "3", "status": "pending", "content": "需求分析" },
  { "id": "4", "status": "pending", "content": "测试点设计" },
  { "id": "5", "status": "pending", "content": "生成测试用例" },
  { "id": "6", "status": "pending", "content": "渲染结果" }
]
```

**有知识库场景**（检测到 `<attached_files>` 区域有知识库时使用）：

```json
[
  { "id": "1", "status": "pending", "content": "确认参考节点" },
  { "id": "2", "status": "pending", "content": "查找关联需求" },
  { "id": "3", "status": "pending", "content": "需求分析" },
  { "id": "4", "status": "pending", "content": "检索需求知识库" },
  { "id": "5", "status": "pending", "content": "检索用例知识库" },
  { "id": "6", "status": "pending", "content": "测试点设计" },
  { "id": "7", "status": "pending", "content": "生成测试用例" },
  { "id": "8", "status": "pending", "content": "渲染结果" }
]
```

## 执行流程

**步骤 1：确认参考节点**

- **方式一**：从 `.testbuddy/env/session.json` 文件获取参考节点信息
- **方式二**：使用 `search_node` 工具（位于 `references/tools/search_node`）从脑图节点中查询参考节点信息
- 读取节点信息（包含 uid, name, kind）
- 如未找到节点信息或信息不完整，提示用户并终止流程
- **禁止**：从其他文件中获取参考节点

**步骤 2：查找关联需求**

- **方式一**：从 `.testbuddy/env/session.json` 文件获取关联需求信息
- **方式二**：使用 `search_node` 工具（位于 `references/tools/search_node`）从脑图节点中查询 STORY 或 BUG 类型的需求节点
- 如未找到需求节点信息，提示用户并终止
- **禁止**：从其他文件中获取需求信息

**步骤 2.5：确保 STORY/BUG 节点存在**

脑图的节点层级结构为：**DESIGN → STORY/BUG → FEATURE/SCENE/TEST_POINT/CASE**。框架等子节点必须挂在 STORY/BUG 节点下才能正确渲染。因此在生成框架前，必须先确保脑图中存在 STORY/BUG 节点作为父节点。

- **判断条件**：步骤 1-2 中未找到 STORY 或 BUG 类型的节点（无论是 chat 模式还是 mindmap 模式，只要脑图中不存在 STORY/BUG 节点就需要创建）
- **执行逻辑**：
  1. 根据需求信息构造一个 STORY（或 BUG）节点，格式如下：
     ```json
     [
       {
         "uid": "story-{10位随机字符}",
         "name": "{需求标题}",
         "description": "{需求描述摘要}",
         "kind": "STORY",
         "parent_uid": "{design_uid}",
         "instance": {
           "workspace": "{TAPD工作空间ID}",
           "issue_id": "{TAPD需求ID}"
         }
       }
     ]
     ```
  2. 将 STORY 节点写入临时文件，使用 `validate_nodes` 校验后通过 `add_nodes` 添加到脑图
  3. **记录此 STORY 节点的 uid**，后续生成的所有框架节点的 `parent_uid` 必须指向这个 STORY 节点的 uid
- **如果已存在 STORY/BUG 节点**：跳过创建，直接使用已有节点的 uid 作为后续子节点的 parent_uid
- **关键约束**：
  - STORY 节点的 `parent_uid` 必须是 `design_uid`（测试设计的 uid）
  - STORY 节点的 `instance` 必须包含 `workspace`（TAPD工作空间ID）和 `issue_id`（需求ID）
  - 如果是 BUG 类型需求，将 `kind` 设为 `"BUG"`

**步骤 3：需求分析**

- **使用工具**：`select_rule`（位于 `references/tools/select_rule`），传入关键词"spec需求分析"
- **根据返回结果**：
  - 如果返回自定义规则名称：使用 `read_rules` 读取规则内容
  - 如果返回默认Generator路径：使用 `read_file` 读取 Generator 内容
- 如果返回空：使用默认 `references/generators/spec/spec-issue-generator.md`
- **执行方式**：按获取到的规则/Generator定义执行需求分析
- **标准输入参数**
  ```python
  {
    "issue_uid": "{需求节点的uid}",
    "issue_kind": "STORY 或 BUG",
    "raw_issue": "{需求详情内容或文件路径 @file:xxx}"
  }
  ```
- **输出**：需求分析文档结果
- **复用逻辑**：如该需求已分析过，直接使用历史分析文档
- **用户审批机制**：
  - 更新需求分析内容后，模型必须主动询问用户："需求分析是否正确？如果是，将进入测试点设计阶段。"
  - 如果用户要求更改或未明确批准（如"否"、"需修改"），模型必须修改文档
  - 模型必须在每次编辑后请求明确批准（如"是"、"批准"、"确认"、"go on"）
  - 模型必须在收到明确批准前不得进入下一阶段
  - 模型必须重复反馈-修订循环直至批准

**步骤 4：检索需求知识库（仅在有知识库时执行）**

- **触发条件**：检查 `<attached_files>` 区域中是否包含知识库文件
  - **如无知识库**：跳过步骤4和步骤5，直接进入步骤6
  - **如有知识库**：继续执行本步骤
- **使用工具**：`RAG_search`
- **检索目标**：从需求分析结果中提取关键词进行检索
  - **关键词提取方法**：
    - 从步骤3的需求分析结果中识别核心功能模块（如"用户登录"、"权限管理"、"数据导出"）
    - 提取关键业务术语和专业词汇（如"鉴权"、"加密"、"回滚"）
    - 识别技术要点（如"API接口"、"数据库事务"、"缓存策略"）
    - 建议提取 3-5 个最具代表性的关键词
  - **检索策略**：
    - **优先策略**：使用 2-3 个核心关键词组合检索（如"用户登录 密码验证"），获取高相关性内容
    - **补充策略**：如组合检索结果不足，可针对单个重要关键词补充检索
    - 检索与需求相关的技术规范、业务规则、实现方案
  - **结果合并**：将检索到的知识库内容与步骤3的需求分析结果合并
    - 在需求分析文档末尾追加 "## 知识库参考信息" 章节
    - 整理检索内容，标注来源和关联性
    - 合并后的完整文档作为后续用例生成的输入
- **知识库名称**：从 `<attached_files>` 中提取

**步骤 5：检索用例知识库（仅在有知识库时执行）**

- **触发条件**：检查 `<attached_files>` 区域中是否包含知识库文件
  - **如无知识库**：跳过本步骤，直接进入步骤6
  - **如有知识库**：继续执行本步骤
- **使用工具**：`RAG_search`
- **检索目标**：根据功能关键词检索历史测试用例
  - 从参考节点中提取功能关键词（如"密码验证"、"表单提交"等）
  - 检索历史测试用例和测试策略
  - 用途：复用测试思路，参考历史测试策略
- **知识库名称**：从 `<attached_files>` 中提取

**步骤 6：测试点设计**

- **使用工具**：`select_rule`（位于 `references/tools/select_rule`），传入关键词"spec测试点生成"
- **根据返回结果**：
  - 如果返回自定义规则名称：使用 `read_rules` 读取规则内容
  - 如果返回默认Generator路径：使用 `read_file` 读取 Generator 内容
- 如果返回空：使用默认 `references/generators/spec/spec-tpoint-generator.md`
- **重要说明**：先输出结果，再简要总结
- **用户审批机制**：
  - 更新测试点设计内容后，模型必须主动询问用户："测试点设计是否正确？如果是，我们可以进入用例生成阶段"
  - 如果用户要求更改或未明确批准（如"否"、"需修改"），模型必须修改文档
  - 模型必须在每次编辑后请求明确批准（如"是"、"批准"、"确认"、"go on"）
  - 模型必须在收到明确批准前不得进入下一阶段
  - 模型必须重复反馈-修订循环直至批准

**步骤 7：生成测试用例**

- **使用工具**：`select_rule`（位于 `references/tools/select_rule`），传入关键词"spec用例生成"
- **根据返回结果**：
  - 如果返回自定义规则名称：使用 `read_rules` 读取规则内容
  - 如果返回默认Generator路径：使用 `read_file` 读取 Generator 内容
- 如果返回空：使用默认 `references/generators/spec/spec-case-generator.md`
- **执行方式**：按获取到的规则/Generator定义执行用例生成
- **重要说明**：参考`需求分析`及`测试点设计`内容进行用例生成，先输出结果，再简要总结
- **标准输入参数**（如使用默认Generator）：
  ```python
  {
    "ref_nodes": [  # YAML格式的参考节点数组
      {
        "uid": "node_123",
        "name": "登录功能测试点",
        "kind": "TEST_POINT"
      }
    ],
    "issue_analysis": "{步骤3生成的需求分析文档完整内容（已包含步骤4合并的知识库参考信息，如有）}",
    "test_design": "{步骤6生成的测试点设计文档完整内容}",
    "knowledge_context": "{步骤5检索到的历史用例参考（如有）}"
  }
  ```
- **输出**：测试用例节点已添加到脑图文件
- **用户审批机制**：
  - 模型必须为每个测试用例分配唯一标识符（格式：TC001, TC002等）
  - 更新测试用例文档后，模型必须主动询问用户："用例生成是否完整？如果是，将同步用例到脑图"
  - 如果用户要求更改或未明确批准，模型必须修改文档
  - 如果用户确认或批准后，同步`测试用例`信息到脑图

**步骤 7：添加节点到脑图**

- **使用工具**：`add_nodes`
- **说明**：将生成的模块节点添加到脑图并渲染，参考 `references/tools/add_nodes.md`
