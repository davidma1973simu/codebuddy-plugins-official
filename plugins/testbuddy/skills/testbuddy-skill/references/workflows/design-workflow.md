# 测试设计生成工作流

**触发关键词**：`生成测试设计`、`帮我做测试设计`、`测试设计`

**工作流简介**：基于需求分析，分两阶段完成完整的测试设计——先生成测试框架（模块/场景/测试点），再基于框架生成测试用例。

## 执行清单规划

在开始执行前，工作流需要：

1. 使用 `todo_write` 工具创建执行清单，将下述执行步骤转化为 TODO 列表
2. 执行应该按照列表的顺序进行执行，禁止跳过步骤
3. 每完成一个步骤后，需检查步骤是否执行，检查通过后更新对应 TODO 的状态为 `completed`
4. 开始新步骤时，将对应 TODO 状态更新为 `in_progress`

**标准 TODO 清单模板**：

Demo:

```json
[
  { "id": "1", "status": "pending", "content": "确认参考节点列表" },
  { "id": "2", "status": "pending", "content": "查找关联需求" },
  { "id": "3", "status": "pending", "content": "需求分析" },
  { "id": "4", "status": "pending", "content": "检索需求知识库" },
  { "id": "5", "status": "pending", "content": "生成测试框架" },
  { "id": "6", "status": "pending", "content": "添加框架节点" },
  { "id": "7", "status": "pending", "content": "基于框架生成测试用例" },
  { "id": "8", "status": "pending", "content": "添加用例节点" }
]
```

## 执行流程

---

### 第一阶段：生成测试框架

**步骤 1：确认参考节点列表**
需根据实际用户的意图选择合适的方式

- **方式一**：从对话上下文中读取（SKILL加载时已执行 get_session，结果在上下文中）
- **方式二**：使用 `get_session` 工具（位于 `references/tools/get_session.md`）读取会话信息
- **方式三**：使用 `search_nodes` 工具（位于 `references/tools/search_nodes.md`）从脑图节点中查询
- 节点信息包含：uid, name, kind, instance
- 如未找到节点信息或信息不完整，提示用户并终止流程
- 参考节点可能是单个、也可能是多个
- **禁止**：从其他文件中获取参考节点列表

**步骤 2：查找关联需求**
需根据实际用户的意图选择合适的方式

- **方式一**：从对话上下文中读取（SKILL加载时已执行 get_session，结果在上下文中）
- **方式二**：使用 `get_session` 工具（位于 `references/tools/get_session.md`）读取会话信息
- **方式三**：使用 `search_nodes` 工具（位于 `references/tools/search_nodes.md`）从脑图查询 STORY 或 BUG 类型节点
- 节点信息包含：uid, name, kind, instance（包含 IssueUid, IssueName 等需求详情）
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

- **使用工具**：`select_rule`（位于 `references/tools/select_rule`），传入关键词"需求分析"
- **根据返回结果**：
  - 如果返回自定义规则路径（`.codebuddy/rules/xxx`）：使用 `read_rules` 读取规则内容
  - 如果返回默认Generator路径（`references/generators/xxx`）：使用 `read_file` 读取 Generator 内容
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

**步骤 4：检索需求知识库**

- **使用工具**：`RAG_search`（位于 `references/tools/rag_search.md`）
- **检索目标**：从需求分析结果中提取关键词进行检索
  - **关键词提取方法**：
    - 从步骤3的需求分析结果中识别核心功能模块（如"用户登录"、"数据导出"）
    - 提取关键业务术语和专业词汇（如"会话管理"、"权限控制"）
    - 识别技术要点（如"接口设计"、"数据格式"）
    - 建议提取 3-5 个最具代表性的关键词
  - **检索策略**：
    - **优先策略**：使用 2-3 个核心关键词组合检索（如"用户登录 会话管理"），获取高相关性内容
    - **补充策略**：如组合检索结果不足，可针对单个重要关键词补充检索
    - 检索历史需求描述、业务规则、技术规范等相关文档
  - **结果合并**：将检索到的知识库内容与步骤3的需求分析结果合并
    - 在需求分析文档末尾追加 "## 知识库参考信息" 章节
    - 整理检索内容，标注来源和关联性
    - 合并后的完整文档作为后续框架生成的输入
- **说明**：工具内部会自动判断是否有可用的知识库，无需手动判断

**步骤 5：生成测试框架**

- **使用工具**：`select_rule`（位于 `references/tools/select_rule`），传入关键词"框架生成"
- **根据返回结果**：
  - 如果返回自定义规则路径（`.codebuddy/rules/xxx`）：使用 `read_rules` 读取规则内容
  - 如果返回默认Generator路径（`references/generators/xxx`）：使用 `read_file` 读取 Generator 内容
- **执行方式**：按获取到的规则/Generator定义执行框架生成
- **标准输入参数**：
  ```python
  {
    "ref_node": {  # 参考节点信息
      "uid": "story_123",
      "name": "用户登录需求",
      "kind": "STORY"
    },
    "issue_txt": "{步骤3生成的需求分析文档完整内容（已包含步骤4合并的知识库参考信息，如有）或文件路径 @file:xxx}",
    "knowledge_context": "{步骤4检索到的历史框架结构参考（如有）}"
  }
  ```
- **输出要求**：
  - ✅ **必须输出标准JSON数组格式**（参考 `references/generators/framework-generator.md`）
  - ✅ 每个框架节点必须包含完整字段：`uid`, `name`, `description`, `kind`, `parent_uid`, `instance`
  - ✅ 所有字符串必须正确转义特殊字符（引号、换行符等）
  - ❌ 禁止使用YAML格式
  - ❌ 禁止在JSON中添加注释

**步骤 6：添加框架节点**

- **使用工具**：`add_nodes`(位于`references/tools/add_nodes.md`)
- **说明**：将生成的框架节点（FEATURE/SCENE/TEST_POINT）添加到脑图或远程设计
- **⚠️ 关键**：添加成功后，**记录所有已创建节点的真实 uid 和层级关系**，用于第二阶段的用例生成

---

### 第二阶段：基于框架生成测试用例

> 本阶段复用第一阶段的需求分析结果（步骤 3+4），不重复执行。

**步骤 7：基于框架生成测试用例**

- **使用工具**：`select_rule`（位于 `references/tools/select_rule`），传入关键词"用例生成"
- **根据返回结果**：
  - 如果返回自定义规则路径（`.codebuddy/rules/xxx`）：使用 `read_rules` 读取规则内容
  - 如果返回默认Generator路径（`references/generators/xxx`）：使用 `read_file` 读取 Generator 内容
- **执行方式**：按获取到的规则/Generator定义执行用例生成
- **参考节点**：使用**步骤 5 生成的框架节点**（FEATURE/SCENE/TEST_POINT）作为参考节点，而不是原始的 STORY/BUG 节点
- **标准输入参数**：
  ```python
  {
    "ref_nodes": [  # 步骤5生成的框架节点（优先使用最细粒度的节点）
      {
        "uid": "testpoint_001",
        "name": "账号密码登录验证",
        "kind": "TEST_POINT"
      },
      {
        "uid": "testpoint_002",
        "name": "手机验证码登录验证",
        "kind": "TEST_POINT"
      }
    ],
    "issue_analysis": "{步骤3生成的需求分析文档完整内容（已包含步骤4合并的知识库参考信息，如有）}",
    "knowledge_context": "{步骤4检索到的历史用例参考（如有）}"
  }
  ```
- **参考节点选取策略**：
  - 如果框架中有 TEST_POINT 节点 → 以 TEST_POINT 为参考节点生成 CASE
  - 如果框架只到 SCENE 层级 → 以 SCENE 为参考节点生成 CASE
  - 如果框架只到 FEATURE 层级 → 以 FEATURE 为参考节点生成 CASE
- **输出要求**：
  - ✅ **必须输出标准JSON数组格式**（参考 `references/generators/case-generator.md`）
  - ✅ 每个用例节点必须包含完整字段：`uid`, `name`, `description`, `kind`, `parent_uid`, `instance`
  - ✅ `parent_uid` 必须是步骤 5/6 中已创建的框架节点的真实 uid
  - ✅ 所有字符串必须正确转义特殊字符（引号、换行符等）
  - ❌ 禁止使用YAML格式
  - ❌ 禁止在JSON中添加注释

**步骤 8：添加用例节点**

- **使用工具**：`add_nodes`(位于`references/tools/add_nodes.md`)
- **说明**：将生成的测试用例节点（CASE）添加到脑图或远程设计，挂在对应的框架节点下
