from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from models import FileChange, TestCase

class BaseAgent(ABC):
    """所有Agent的抽象基类"""
    
    def __init__(self, skill_manager=None):
        self.skill_manager = skill_manager

class PMBaseAgent(BaseAgent):
    """PM智能体抽象基类"""
    
    @abstractmethod
    def run(
        self,
        user_query: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        需求分析与澄清
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
        pass

class ArchitectBaseAgent(BaseAgent):
    """架构师智能体抽象基类"""
    
    @abstractmethod
    def run(
        self,
        requirement_doc: str,
        codebase_context: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        技术方案设计
        :param requirement_doc: 需求文档内容（template-report.md）
        :param codebase_context: 代码库上下文（文件树、依赖信息等）
        :param chat_history: 历史对话记录（工具调用时使用）
        :return:
            {
                "type": "tech_solution",
                "file_change_list": [...],
                "api_design": [...],
                "plan_md": "...",
                ...
            }
        """
        pass

class CoderBaseAgent(BaseAgent):
    """开发工程师智能体抽象基类"""
    
    @abstractmethod
    def run(
        self,
        tech_plan: str,
        codebase_context: Optional[Dict[str, Any]] = None,
        fix_hint: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        代码生成
        :param tech_plan: 技术方案内容（plan.md）
        :param codebase_context: 代码库上下文
        :param fix_hint: 修复提示（测试失败或评审不通过时使用）
        :param chat_history: 历史对话记录（工具调用时使用）
        :return:
            {
                "type": "code_generation",
                "code_files": [FileChange, ...],
                "test_cases": [TestCase, ...],
                ...
            }
        """
        pass

class QABaseAgent(BaseAgent):
    """测试工程师智能体抽象基类"""
    
    @abstractmethod
    def run(
        self,
        code_changes: List[FileChange],
        requirement_doc: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        生成测试用例并执行
        :param code_changes: 代码变更集
        :param requirement_doc: 需求文档
        :param chat_history: 历史对话记录（工具调用时使用）
        :return:
            {
                "type": "test_generation",
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
        pass

class ReviewerBaseAgent(BaseAgent):
    """代码评审专家智能体抽象基类"""
    
    @abstractmethod
    def run(
        self,
        code_changes: List[FileChange],
        tech_plan: str,
        test_result: Dict[str, Any],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        代码质量审查
        :param code_changes: 代码变更集
        :param tech_plan: 技术方案
        :param test_result: 测试执行结果
        :param chat_history: 历史对话记录（工具调用时使用）
        :return:
            {
                "type": "code_review",
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
        pass

class DeliveryBaseAgent(BaseAgent):
    """交付工程师智能体抽象基类"""
    
    @abstractmethod
    def run(
        self,
        code_changes: List[FileChange],
        test_result: Dict[str, Any],
        review_score: float,
        requirement: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        代码集成与PR生成
        :param code_changes: 代码变更集
        :param test_result: 测试结果
        :param review_score: 代码评审得分
        :param requirement: 原始需求
        :param chat_history: 历史对话记录（工具调用时使用）
        :return:
            {
                "type": "delivery",
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
        pass
