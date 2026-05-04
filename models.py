import uuid
import json
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

class PipelineStateEnum(str, Enum):
    """流水线状态枚举"""
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

    def get_state_display(self) -> str:
        """获取状态的中文显示名称"""
        state_display_map = {
            PipelineStateEnum.INIT: "初始化",
            PipelineStateEnum.REQUIREMENT_ANALYSIS: "需求分析",
            PipelineStateEnum.ARCHITECTURE_DESIGN: "架构设计",
            PipelineStateEnum.HUMAN_APPROVAL_1: "方案审批",
            PipelineStateEnum.CODE_GENERATION: "代码生成",
            PipelineStateEnum.TEST_GENERATION: "测试生成",
            PipelineStateEnum.CODE_REVIEW: "代码评审",
            PipelineStateEnum.HUMAN_APPROVAL_2: "代码审批",
            PipelineStateEnum.DELIVERY: "交付集成",
            PipelineStateEnum.COMPLETED: "已完成",
            PipelineStateEnum.FAILED: "失败"
        }
        return state_display_map.get(self, self.value)

class FileChange(BaseModel):
    """文件变更模型"""
    file_path: str = Field(description="文件路径（相对代码库根目录）")
    content: str = Field(description="完整的文件内容")
    change_type: str = Field(description="变更类型：new/modify/delete")
    language: Optional[str] = Field(default=None, description="编程语言")

    @field_validator('change_type')
    def validate_change_type(cls, v):
        allowed_types = {'new', 'modify', 'delete'}
        if v not in allowed_types:
            raise ValueError(f"变更类型必须是{allowed_types}之一，当前值：{v}")
        return v

class TestCase(BaseModel):
    """测试用例模型"""
    test_file_path: str = Field(description="测试文件路径")
    test_content: str = Field(description="完整的测试代码内容")
    test_type: str = Field(description="测试类型：unit/integration/e2e")
    coverage: Optional[float] = Field(default=None, ge=0, le=100, description="测试覆盖率百分比")

    @field_validator('test_type')
    def validate_test_type(cls, v):
        allowed_types = {'unit', 'integration', 'e2e'}
        if v not in allowed_types:
            raise ValueError(f"测试类型必须是{allowed_types}之一，当前值：{v}")
        return v

class ProblemItem(BaseModel):
    """评审问题模型"""
    problem_id: int = Field(ge=1, description="问题唯一ID")
    severity: str = Field(description="严重程度：critical/major/minor/suggestion")
    problem_description: str = Field(description="问题详细描述")
    file_path: Optional[str] = Field(default=None, description="问题所在文件路径")
    line_range: Optional[str] = Field(default=None, description="问题所在行范围，格式：L1-L10")
    repair_suggestion: str = Field(description="具体的修复建议")

    @field_validator('severity')
    def validate_severity(cls, v):
        allowed_severities = {'critical', 'major', 'minor', 'suggestion'}
        if v not in allowed_severities:
            raise ValueError(f"严重程度必须是{allowed_severities}之一，当前值：{v}")
        return v

class PipelineContext(BaseModel):
    """统一上下文数据模型 - 整个流水线的"数据宪法" """
    # 基础信息
    pipeline_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="流水线唯一ID")
    user_query: str = Field(description="用户原始需求")
    state: PipelineStateEnum = Field(default=PipelineStateEnum.INIT, description="当前流水线状态")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")
    
    # 阶段1：需求分析输出
    pm_result: Optional[Dict[str, Any]] = Field(default=None, description="PM智能体原始输出")
    template_report_md: Optional[str] = Field(default=None, description="结构化需求文档内容")
    template_report_path: Optional[str] = Field(default=None, description="需求文档存储路径")
    
    # 阶段2：架构设计输出
    architect_result: Optional[Dict[str, Any]] = Field(default=None, description="架构师原始输出")
    plan_md: Optional[str] = Field(default=None, description="技术方案文档内容")
    plan_md_path: Optional[str] = Field(default=None, description="技术方案存储路径")
    file_change_list: Optional[List[Dict[str, Any]]] = Field(default=None, description="文件变更清单")
    api_design: Optional[List[Dict[str, Any]]] = Field(default=None, description="API设计列表")
    
    # 人工检查点1
    approval_1_status: Optional[str] = Field(default=None, description="检查点1状态：pending/approved/rejected")
    approval_1_reason: Optional[str] = Field(default=None, description="检查点1审批/拒绝理由")
    
    # 阶段3：代码生成输出
    coder_result: Optional[Dict[str, Any]] = Field(default=None, description="Coder原始输出")
    code_changes: Optional[List[FileChange]] = Field(default=None, description="代码变更集")
    
    # 阶段4：测试生成输出
    qa_result: Optional[Dict[str, Any]] = Field(default=None, description="QA智能体原始输出")
    test_cases: Optional[List[TestCase]] = Field(default=None, description="测试用例列表")
    test_result: Optional[Dict[str, Any]] = Field(default=None, description="测试执行结果")
    retry_count: int = Field(default=0, ge=0, description="代码修复重试次数")
    max_retries: int = Field(default=3, ge=1, le=10, description="最大重试次数")
    
    # 阶段5：代码评审输出
    reviewer_result: Optional[Dict[str, Any]] = Field(default=None, description="评审专家原始输出")
    eval_report_md: Optional[str] = Field(default=None, description="评审报告内容")
    eval_report_path: Optional[str] = Field(default=None, description="评审报告存储路径")
    problem_list: Optional[List[ProblemItem]] = Field(default=None, description="问题列表")
    overall_score: Optional[float] = Field(default=None, ge=0, le=10, description="代码质量总分 0-10")
    
    # 人工检查点2
    approval_2_status: Optional[str] = Field(default=None, description="检查点2状态：pending/approved/rejected")
    approval_2_reason: Optional[str] = Field(default=None, description="检查点2审批/拒绝理由")
    
    # 阶段6：交付集成输出
    delivery_result: Optional[Dict[str, Any]] = Field(default=None, description="交付智能体原始输出")
    pr_template_md: Optional[str] = Field(default=None, description="PR模板内容")
    pr_template_path: Optional[str] = Field(default=None, description="PR模板存储路径")
    branch_name: Optional[str] = Field(default=None, description="创建的分支名称")
    pr_url: Optional[str] = Field(default=None, description="PR链接")
    
    # 配置信息
    output_dir: str = Field(description="产物输出目录")
    codebase_dir: str = Field(default=".", description="目标代码库目录")

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "allow"  # 允许额外字段，方便扩展
    }

    def update(self, **kwargs) -> None:
        """更新上下文字段，自动更新updated_at时间"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now().isoformat()

    def to_json(self, indent: int = 2, ensure_ascii: bool = False) -> str:
        """序列化为JSON字符串"""
        return self.model_dump_json(indent=indent, ensure_ascii=ensure_ascii)

    @classmethod
    def from_json(cls, json_str: str) -> "PipelineContext":
        """从JSON字符串反序列化"""
        return cls.model_validate_json(json_str)

    def save_to_file(self, file_path: str) -> None:
        """保存上下文到JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def load_from_file(cls, file_path: str) -> "PipelineContext":
        """从JSON文件加载上下文"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())
