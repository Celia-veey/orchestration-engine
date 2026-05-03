# DevFlow Engine 协作开发指南
## 🎯 项目分工
---
### 👨‍💻 角色 A：引擎架构师 (The Engine Builder)
**负责“修路和建站”，确保系统能稳定流转、能对外提供服务。**
#### 核心任务
1. **核心状态机与控制流**
   - 编写DevFlow的主干循环代码
   - 实现各阶段之间的数据结构传递
   - 定义每个阶段输入输出的JSON Schema/Pydantic Model
2. **API-First改造 (FastAPI)**
   - 提供流水线触发、状态查询的RESTful API
   - 暴露出给前端或命令行调用的接口
3. **Human-in-the-Loop与路由**
   - 实现引擎的“挂起（Suspend）”机制
   - 编写Approve放行和Reject携带理由回滚到上一阶段的代码逻辑
4. **外部工程工具链**
   - 对接Git/GitHub/GitLab的API，实现自动拉分支、提交Diff、创建PR
   - 对接飞书文档MCP（Model Context Protocol）
---
### 🧠 角色 B：AI算法与提示词工程师 (The Agent Whisperer)
**负责“造脑和喂饭”，确保每个Agent够聪明、上下文够精准。**
#### 核心任务
1. **全链路Agent的Prompt工程**
   - 为PM、Architect、Coder、QA、Reviewer编写和调试System Prompt及Skill指令
   - 规范AI的输出格式（确保稳定输出Markdown或JSON，不废话）
2. **代码库精准索引 (Context Engineering)**
   - 编写脚本，提取目标代码库的文件树结构、核心类/函数签名
   - 控制上下文长度，防止Coder和Architect产生幻觉
3. **自动回归闭环 (Auto-Regression)**
   - 编写QA和Coder之间的内部重试逻辑（提取报错log -> 塞给Coder -> 限制重试3次）
4. **质量评估与沙箱运行**
   - 准备测试用例，专门跑Agent的单点能力
   - 打磨AI生成的技术方案(`plan.md`)和评估报告(`eval-template-report.md`)的质量
---
## 📦 统一数据总线 (State Payload)
---
整个流水线流转的上下文数据包，所有阶段共享，字段约定如下：
```python
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

class PipelineStateEnum(str, Enum):
    INIT = "init"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    ARCHITECTURE_DESIGN = "architecture_design"
    HUMAN_APPROVAL_1 = "human_approval_1"
    CODE_GENERATION = "code_generation"
    TEST_GENERATION = "test_generation"
    CODE_REVIEW = "code_review"
    HUMAN_APPROVAL_2 = "human_approval_2"
    DELIVERY = "delivery"
    COMPLETED = "completed"
    FAILED = "failed"

class FileChange(BaseModel):
    """文件变更模型"""
    file_path: str = Field(description="文件路径")
    content: str = Field(description="文件内容")
    change_type: str = Field(description="变更类型：new/modify/delete")
    language: Optional[str] = Field(description="编程语言")

class TestCase(BaseModel):
    """测试用例模型"""
    test_file_path: str = Field(description="测试文件路径")
    test_content: str = Field(description="测试代码内容")
    test_type: str = Field(description="测试类型：unit/integration/e2e")
    coverage: Optional[float] = Field(description="测试覆盖率")

class ProblemItem(BaseModel):
    """评审问题模型"""
    problem_id: int = Field(description="问题ID")
    severity: str = Field(description="严重程度：critical/major/minor/suggestion")
    problem_description: str = Field(description="问题描述")
    file_path: Optional[str] = Field(description="问题所在文件")
    line_range: Optional[str] = Field(description="问题行范围")
    repair_suggestion: str = Field(description="修复建议")

class PipelineContext(BaseModel):
    """统一上下文数据模型"""
    # 基础信息
    pipeline_id: str = Field(description="流水线唯一ID")
    user_query: str = Field(description="用户原始需求")
    state: PipelineStateEnum = Field(description="当前流水线状态")
    created_at: str = Field(description="创建时间")
    updated_at: str = Field(description="更新时间")
    
    # 阶段1：需求分析输出
    pm_result: Optional[Dict[str, Any]] = Field(description="PM智能体原始输出")
    template_report_md: Optional[str] = Field(description="结构化需求文档内容")
    template_report_path: Optional[str] = Field(description="需求文档存储路径")
    
    # 阶段2：架构设计输出
    architect_result: Optional[Dict[str, Any]] = Field(description="架构师原始输出")
    plan_md: Optional[str] = Field(description="技术方案文档内容")
    plan_md_path: Optional[str] = Field(description="技术方案存储路径")
    file_change_list: Optional[List[Dict[str, Any]]] = Field(description="文件变更清单")
    api_design: Optional[List[Dict[str, Any]]] = Field(description="API设计列表")
    
    # 人工检查点1
    approval_1_status: Optional[str] = Field(description="检查点1状态：pending/approved/rejected")
    approval_1_reason: Optional[str] = Field(description="检查点1审批/拒绝理由")
    
    # 阶段3：代码生成输出
    coder_result: Optional[Dict[str, Any]] = Field(description="Coder原始输出")
    code_changes: Optional[List[FileChange]] = Field(description="代码变更集")
    
    # 阶段4：测试生成输出
    qa_result: Optional[Dict[str, Any]] = Field(description="QA智能体原始输出")
    test_cases: Optional[List[TestCase]] = Field(description="测试用例列表")
    test_result: Optional[Dict[str, Any]] = Field(description="测试执行结果")
    retry_count: int = Field(default=0, description="代码修复重试次数")
    max_retries: int = Field(default=3, description="最大重试次数")
    
    # 阶段5：代码评审输出
    reviewer_result: Optional[Dict[str, Any]] = Field(description="评审专家原始输出")
    eval_report_md: Optional[str] = Field(description="评审报告内容")
    eval_report_path: Optional[str] = Field(description="评审报告存储路径")
    problem_list: Optional[List[ProblemItem]] = Field(description="问题列表")
    overall_score: Optional[float] = Field(description="代码质量总分 0-10")
    
    # 人工检查点2
    approval_2_status: Optional[str] = Field(description="检查点2状态：pending/approved/rejected")
    approval_2_reason: Optional[str] = Field(description="检查点2审批/拒绝理由")
    
    # 阶段6：交付集成输出
    delivery_result: Optional[Dict[str, Any]] = Field(description="交付智能体原始输出")
    pr_template_md: Optional[str] = Field(description="PR模板内容")
    pr_template_path: Optional[str] = Field(description="PR模板存储路径")
    branch_name: Optional[str] = Field(description="创建的分支名称")
    pr_url: Optional[str] = Field(description="PR链接")
    
    # 输出配置
    output_dir: str = Field(description="产物输出目录")
    codebase_dir: str = Field(description="目标代码库目录")
```
---
## 🔌 Agent接口标准
---
所有Agent函数的输入输出统一约定，角色A和B独立开发，约定不变互不干扰。
### 1. PM Agent 接口
```python
def run_pm_agent(
    user_query: str,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    PM智能体：需求分析与澄清
    :param user_query: 用户原始需求
    :param chat_history: 历史对话记录（多轮澄清时使用）
    :return: 
        {
            "type": "clarification/solution",
            "questions": [...],  # clarification类型时返回
            "plan_md": "...",     # solution类型时返回
            ...
        }
    """
```
### 2. Architect Agent 接口
```python
def run_architect_agent(
    requirement_doc: str,
    codebase_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    架构师智能体：技术方案设计
    :param requirement_doc: 需求文档内容（template-report.md）
    :param codebase_context: 代码库上下文（文件树、依赖信息等）
    :return:
        {
            "file_change_list": [...],
            "api_design": [...],
            "plan_md": "...",
            ...
        }
    """
```
### 3. Coder Agent 接口
```python
def run_coder_agent(
    tech_plan: str,
    codebase_context: Optional[Dict[str, Any]] = None,
    fix_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    开发工程师智能体：代码生成
    :param tech_plan: 技术方案内容（plan.md）
    :param codebase_context: 代码库上下文
    :param fix_hint: 修复提示（测试失败或评审不通过时使用）
    :return:
        {
            "code_files": [FileChange, ...],
            "test_cases": [TestCase, ...],
            ...
        }
    """
```
### 4. QA Agent 接口
```python
def run_qa_agent(
    code_changes: List[FileChange],
    requirement_doc: str
) -> Dict[str, Any]:
    """
    测试工程师智能体：生成测试用例并执行
    :param code_changes: 代码变更集
    :param requirement_doc: 需求文档
    :return:
        {
            "test_cases": [TestCase, ...],
            "execution_result": {
                "total_tests": 10,
                "passed_tests": 8,
                "failed_tests": 2,
                ...
            },
            "failed_test_details": [...],
            ...
        }
    """
```
### 5. Reviewer Agent 接口
```python
def run_reviewer_agent(
    code_changes: List[FileChange],
    tech_plan: str,
    test_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    代码评审专家智能体：代码质量审查
    :param code_changes: 代码变更集
    :param tech_plan: 技术方案
    :param test_result: 测试执行结果
    :return:
        {
            "review_summary": {
                "overall_status": "pass/reject/need_modify",
                "total_problems": 5,
                ...
            },
            "problem_list": [ProblemItem, ...],
            "code_quality_scores": {...},
            "eval_template_report": "...",
            ...
        }
    """
```
### 6. Delivery Agent 接口
```python
def run_delivery_agent(
    code_changes: List[FileChange],
    test_result: Dict[str, Any],
    review_score: float,
    requirement: str
) -> Dict[str, Any]:
    """
    交付工程师智能体：代码集成与PR生成
    :param code_changes: 代码变更集
    :param test_result: 测试结果
    :param review_score: 代码评审得分
    :param requirement: 原始需求
    :return:
        {
            "branch_operation": {...},
            "pr_info": {
                "pr_title": "...",
                "pr_template_md": "...",
                ...
            },
            "execution_result": {...},
            ...
        }
    """
```
---
## 📋 协作规范
---
### 1. 代码规范
- 所有Python代码遵循PEP8规范
- 函数必须有类型注解和docstring
- 关键逻辑必须有注释
### 2. 提交规范
- 提交信息格式：`[角色][模块] 描述`
  示例：
  - `[A][state-machine] 实现状态机回滚逻辑`
  - `[B][prompt] 优化Coder Agent输出格式`
### 3. 分支规范
- 主分支：`main`
- 开发分支：`feature/[角色]-[功能名]`
  示例：`feature/A-fastapi`、`feature/B-pm-prompt`
### 4. 接口约定
- 所有Agent接口必须严格遵循上述约定，输入输出字段变更必须提前协商
- 新增字段必须添加Optional默认值，保证向后兼容
---
## 🔄 协作流程
1. 角色A先实现状态机流转和Mock数据，跑通主干流程
2. 角色B并行调试各个Agent的Prompt和能力
3. 双方联调，把Agent接入到状态机中
4. 集成测试，跑通完整流水线
