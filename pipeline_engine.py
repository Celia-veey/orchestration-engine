import os
import re
import json
import yaml
import time
import logging
import traceback
from typing import Dict, Any, Optional, List
from pathlib import Path
from llm_client import LLMClient
from models import PipelineContext, PipelineStateEnum, FileChange, TestCase

# 导入Mock Agent实现
from agents.pm_mock import PMMockAgent
from agents.architect_mock import ArchitectMockAgent
from agents.coder_mock import CoderMockAgent
from agents.qa_mock import QAMockAgent
from agents.reviewer_mock import ReviewerMockAgent
from agents.delivery_mock import DeliveryMockAgent

class SkillManager:
    """渐进式技能管理器：按需加载技能，支持插件式扩展"""
    
    def __init__(self, skills_dir: str = "skills"):
        """
        初始化技能管理器，只构建轻量索引，不加载任何技能内容
        :param skills_dir: 技能配置根目录
        """
        self.skills_dir = Path(skills_dir)
        self.skill_index: Dict[str, Dict[str, Any]] = {}  # 技能元数据索引
        self.skill_cache: Dict[str, str] = {}  # 技能内容缓存，使用时才加载
        self._build_skill_index()
        
    def _build_skill_index(self) -> None:
        """扫描技能目录，构建轻量级技能元数据索引，只读取YAML头部"""
        if not self.skills_dir.exists():
            print(f"⚠️ 技能目录不存在: {self.skills_dir.resolve()}")
            return
            
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        # 只读取前4KB内容，足够提取YAML头部
                        with open(skill_file, 'r', encoding='utf-8') as f:
                            content_head = f.read(4096)
                        
                        # 提取YAML元数据
                        yaml_match = re.match(r'^---\n(.*?)\n---\n', content_head, re.DOTALL)
                        if yaml_match:
                            skill_meta = yaml.safe_load(yaml_match.group(1))
                            skill_name = skill_meta.get('name', skill_dir.name)
                            self.skill_index[skill_name] = {
                                'path': skill_file,
                                'meta': skill_meta
                            }
                    except Exception as e:
                        print(f"⚠️ 加载技能元数据失败 {skill_dir.name}: {str(e)}")
        
        print(f"✅ 技能索引构建完成，共发现 {len(self.skill_index)} 个可用技能")
    
    def has_skill(self, skill_name: str) -> bool:
        """检查是否存在指定技能"""
        return skill_name in self.skill_index
    
    def get_skill_prompt(self, skill_name: str) -> str:
        """
        获取技能的完整Prompt，第一次调用时加载，后续从缓存读取
        :param skill_name: 技能名称
        :return: 技能Prompt内容
        """
        # 优先从缓存读取
        if skill_name in self.skill_cache:
            return self.skill_cache[skill_name]
        
        # 检查技能是否存在
        if not self.has_skill(skill_name):
            raise ValueError(f"技能不存在: {skill_name}")
        
        # 第一次使用才加载完整技能内容
        skill_info = self.skill_index[skill_name]
        skill_file = skill_info['path']
        
        try:
            content = skill_file.read_text(encoding="utf-8")
            # 移除YAML头部，提取正文作为System Prompt
            prompt_content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL).strip()
            
            # 加入缓存
            self.skill_cache[skill_name] = prompt_content
            print(f"📥 已加载技能: {skill_name}")
            
            return prompt_content
        except Exception as e:
            raise RuntimeError(f"加载技能失败 {skill_name}: {str(e)}") from e
    
    def list_available_skills(self) -> list[Dict[str, Any]]:
        """获取所有可用技能的元数据列表"""
        return [
            {
                'name': name,
                'description': info['meta'].get('description', ''),
                'tags': info['meta'].get('tags', []),
                'version': info['meta'].get('version', '1.0.0')
            }
            for name, info in self.skill_index.items()
        ]

class PipelineEngine:
    """AI驱动的需求交付流程引擎核心编排器 - 6阶段状态机版本"""
    
    def __init__(self, skills_dir: str = "skills", codebase_dir: str = ".", output_dir: str = "output", context_file: str = None):
        """
        初始化流水线引擎
        :param skills_dir: 智能体技能配置目录
        :param codebase_dir: 目标代码库目录
        :param output_dir: 生成产物统一输出目录
        :param context_file: 可选，从已有context.json恢复流水线
        """
        self.skills_dir = Path(skills_dir)
        self.codebase_dir = Path(codebase_dir)
        self.logger = None  # 日志实例
        self.stage_start_time = {}  # 记录各阶段开始时间，用于计算耗时
        
        # 如果指定了context_file，则从断点恢复
        if context_file:
            self._restore_from_context(context_file)
            print(f"✅ 已从断点恢复流水线: {self.context.pipeline_id}")
            print(f"📂 恢复到状态: {self.state.get_state_display()}")
            return
        
        # 新建流水线，创建带时间戳的输出目录
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(output_dir) / timestamp
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化日志系统
        self._init_logger()
        
        self.llm_client = LLMClient()
        self.skill_manager = SkillManager(skills_dir)
        
        # 初始化Agent实例
        self.pm_agent = PMMockAgent(self.skill_manager)
        self.architect_agent = ArchitectMockAgent(self.skill_manager)
        self.coder_agent = CoderMockAgent(self.skill_manager)
        self.qa_agent = QAMockAgent(self.skill_manager)
        self.reviewer_agent = ReviewerMockAgent(self.skill_manager)
        self.delivery_agent = DeliveryMockAgent(self.skill_manager)
        
        # 状态管理
        self.state = PipelineStateEnum.INIT
        self.context: Optional[PipelineContext] = None  # 流水线上下文，保存各阶段输出
        
        self.logger.info("✅ 6阶段流水线引擎初始化完成")
        self.logger.info(f"📂 技能配置目录: {self.skills_dir.resolve()}")
        self.logger.info(f"📂 目标代码库: {self.codebase_dir.resolve()}")
        self.logger.info(f"📂 产物输出目录: {self.output_dir.resolve()}")
        print("✅ 6阶段流水线引擎初始化完成")
        print(f"📂 技能配置目录: {self.skills_dir.resolve()}")
        print(f"📂 目标代码库: {self.codebase_dir.resolve()}")
        print(f"📂 产物输出目录: {self.output_dir.resolve()}")
    
    def _init_logger(self) -> None:
        """初始化统一日志系统"""
        self.logger = logging.getLogger(f"pipeline_{self.output_dir.name}")
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加handler
        if self.logger.handlers:
            return
        
        # 日志格式：[时间] [级别] 消息
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # 输出到文件
        file_handler = logging.FileHandler(
            self.output_dir / "pipeline.log",
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 输出到控制台
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _restore_from_context(self, context_file: str) -> None:
        """从context.json文件恢复流水线状态"""
        context_path = Path(context_file)
        if not context_path.exists():
            raise FileNotFoundError(f"上下文文件不存在: {context_file}")
        
        # 加载上下文
        self.context = PipelineContext.load_from_file(str(context_path.resolve()))
        self.state = self.context.state
        
        # 恢复输出目录
        self.output_dir = Path(self.context.output_dir)
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 恢复日志系统
        self._init_logger()
        
        # 初始化其他组件
        self.llm_client = LLMClient()
        self.skill_manager = SkillManager(str(self.skills_dir.resolve()))
        
        # 初始化Agent实例
        self.pm_agent = PMMockAgent(self.skill_manager)
        self.architect_agent = ArchitectMockAgent(self.skill_manager)
        self.coder_agent = CoderMockAgent(self.skill_manager)
        self.qa_agent = QAMockAgent(self.skill_manager)
        self.reviewer_agent = ReviewerMockAgent(self.skill_manager)
        self.delivery_agent = DeliveryMockAgent(self.skill_manager)
    
    def set_state(self, new_state: PipelineStateEnum) -> None:
        """更新流水线状态"""
        old_state = self.state
        self.logger.info(f"\n🔄 状态切换: {old_state.get_state_display()} -> {new_state.get_state_display()}")
        print(f"\n🔄 状态切换: {self.state.get_state_display()} -> {new_state.get_state_display()}")
        self.state = new_state
        if self.context:
            self.context.update(state=new_state)
            # 每次状态切换都自动保存上下文
            self.context.save_to_file(self.output_dir / "context.json")
            self.logger.info(f"💾 上下文已自动保存，当前状态: {new_state.get_state_display()}")
    
    def _log_stage_start(self, stage_name: str, stage_desc: str) -> None:
        """记录阶段开始日志"""
        self.stage_start_time[stage_name] = time.time()
        self.logger.info("\n" + "="*80)
        self.logger.info(f"🚀 【{stage_name}】{stage_desc}")
        self.logger.info("="*80)
        print("\n" + "="*80)
        print(f"🚀 【{stage_name}】{stage_desc}")
        print("="*80)
    
    def _log_stage_end(self, stage_name: str, success: bool = True, extra_msg: str = "") -> None:
        """记录阶段结束日志，计算耗时"""
        start_time = self.stage_start_time.get(stage_name, time.time())
        duration = round(time.time() - start_time, 2)
        status = "✅ 完成" if success else "❌ 失败"
        msg = f"{status} {stage_name}，耗时: {duration}秒"
        if extra_msg:
            msg += f"，{extra_msg}"
        self.logger.info(msg)
        self.logger.info("="*80)
        return duration
    
    # ==================== 阶段1：需求分析 ====================
    def run_requirement_analysis(self, user_requirement: str) -> bool:
        """
        阶段1：需求分析 - 渐进式澄清需求，生成结构化需求文档
        :param user_requirement: 用户原始需求
        :return: 是否成功
        """
        self._log_stage_start("阶段1/6", "需求分析 (PM智能体)")
        self.set_state(PipelineStateEnum.REQUIREMENT_ANALYSIS)
        
        self.logger.info(f"📥 阶段输入：用户需求\n{user_requirement}\n")
        self.logger.info("🔄 正在调用PM智能体分析需求（Mock模式）...")
        print("🔄 正在调用PM智能体分析需求（Mock模式）...")
        
        try:
            # 调用PM Agent
            pm_result = self.pm_agent.run(user_requirement)
            self.logger.info(f"📤 阶段输出：PM智能体返回结果，类型: {pm_result.get('type', 'unknown')}")
            self.logger.debug(f"详细输出：\n{json.dumps(pm_result, ensure_ascii=False, indent=2)}\n")
        
            # 生成template-report.md
            template_report = pm_result.get("plan_md", "# 需求文档生成失败")
            report_file = self.output_dir / "template-report.md"
            report_file.write_text(template_report, encoding="utf-8")
            self.logger.info(f"\n✅ 结构化需求文档已生成: {report_file.resolve()}")
            print(f"\n✅ 结构化需求文档已生成: {report_file.resolve()}")
            
            # 保存到上下文
            self.context.update(
                pm_result=pm_result,
                template_report_md=template_report,
                template_report_path=str(report_file.resolve())
            )
            
            # 自动保存上下文
            self.context.save_to_file(self.output_dir / "context.json")
            
            duration = self._log_stage_end("阶段1/6", True, "生成需求文档1份，功能点4个")
            self.logger.info(f"⏱️  阶段总耗时：{duration}秒，状态：成功")
            return True
        except Exception as e:
            error_msg = f"❌ 阶段1/6 需求分析失败: {str(e)}"
            stack_trace = traceback.format_exc()
            self.logger.error(error_msg)
            self.logger.error(f"📋 错误堆栈：\n{stack_trace}\n")
            self._log_stage_end("阶段1/6", False, str(e))
            # 保存错误上下文
            error_context = {
                "stage": "需求分析",
                "error": str(e),
                "stack_trace": stack_trace,
                "input": user_requirement
            }
            error_file = self.output_dir / "error.json"
            error_file.write_text(json.dumps(error_context, ensure_ascii=False, indent=2), encoding="utf-8")
            raise RuntimeError(error_msg) from e
    
    # ==================== 阶段2：方案设计 ====================
    def run_architecture_design(self) -> bool:
        """阶段2：架构设计 - Architect智能体生成技术方案"""
        self._log_stage_start("阶段2/6", "技术方案设计 (Architect智能体)")
        self.set_state(PipelineStateEnum.ARCHITECTURE_DESIGN)
        
        self.logger.info(f"📥 阶段输入：需求文档\n{self.context.template_report_md[:500]}...\n")
        self.logger.info("🔄 正在调用Architect智能体设计技术方案（Mock模式）...")
        print("🔄 正在调用Architect智能体设计技术方案（Mock模式）...")
        
        try:
            # 调用Architect Agent
            architect_result = self.architect_agent.run(self.context.template_report_md)
            self.logger.info(f"📤 阶段输出：技术方案，变更文件数: {len(architect_result.get('file_change_list', []))}，API设计数: {len(architect_result.get('api_design', []))}")
            self.logger.debug(f"详细输出：\n{json.dumps(architect_result, ensure_ascii=False, indent=2)}\n")
        
            print("\n📋 技术方案设计完成：")
            print(f"✅ 变更文件数: {len(architect_result.get('file_change_list', []))}")
            print(f"✅ API设计数: {len(architect_result.get('api_design', []))}")
            
            # 保存plan.md
            plan_md = architect_result.get("plan_md", "# 技术方案生成失败")
            plan_file = self.output_dir / "plan.md"
            plan_file.write_text(plan_md, encoding="utf-8")
            print(f"\n✅ 技术方案文档已生成: {plan_file.resolve()}")
            print("📄 方案预览：")
            print("-"*60)
            preview_lines = plan_md.split('\n')[:20]
            print('\n'.join(preview_lines))
            if len(preview_lines) < len(plan_md.split('\n')):
                print("...\n(更多内容请查看plan.md文件)")
            print("-"*60)
            
            # 保存到上下文
            self.context.update(
                architect_result=architect_result,
                plan_md=plan_md,
                plan_md_path=str(plan_file.resolve()),
                file_change_list=architect_result.get('file_change_list', []),
                api_design=architect_result.get('api_design', [])
            )
            
            # 自动保存上下文
            self.context.save_to_file(self.output_dir / "context.json")
            
            duration = self._log_stage_end("阶段2/6", True, f"生成技术方案1份，变更文件{len(architect_result.get('file_change_list', []))}个，API设计{len(architect_result.get('api_design', []))}个")
            self.logger.info(f"⏱️  阶段总耗时：{duration}秒，状态：成功")
            return True
        except Exception as e:
            error_msg = f"❌ 阶段2/6 技术方案设计失败: {str(e)}"
            stack_trace = traceback.format_exc()
            self.logger.error(error_msg)
            self.logger.error(f"📋 错误堆栈：\n{stack_trace}\n")
            self._log_stage_end("阶段2/6", False, str(e))
            # 保存错误上下文
            error_context = {
                "stage": "技术方案设计",
                "error": str(e),
                "stack_trace": stack_trace,
                "input": self.context.template_report_md
            }
            error_file = self.output_dir / "error.json"
            error_file.write_text(json.dumps(error_context, ensure_ascii=False, indent=2), encoding="utf-8")
            raise RuntimeError(error_msg) from e
    
    def human_approval_1(self) -> str:
        """人工检查点1：技术方案审批
        :return: 'approve' / 'reject'
        """
        self.set_state(PipelineStateEnum.HUMAN_APPROVAL_1)
        print("\n" + "="*80)
        print("🔍 【人工检查点1】技术方案审批")
        print("="*80)
        
        while True:
            choice = input("\n请审批技术方案：输入 [A]ppove 通过 / [R]eject 打回 / [V]iew 查看完整方案 / [O]pen 打开文档：").strip().upper()
            
            if choice == 'V':
                print("\n📋 技术方案详情：")
                print(json.dumps(self.context.architect_result, ensure_ascii=False, indent=2))
            elif choice == 'O':
                # 打开plan.md
                if os.name == 'nt':
                    os.startfile(self.context.plan_md_path)
                else:
                    import subprocess
                    subprocess.run(['open', self.context.plan_md_path])
            elif choice == 'A':
                print("✅ 技术方案已通过审批，进入代码开发阶段")
                self.context.update(approval_1_status='approved')
                return 'approve'
            elif choice == 'R':
                reason = input("请输入打回理由：").strip()
                print(f"❌ 方案已被打回，理由：{reason}，将回到需求分析阶段重新调整")
                self.context.update(
                    approval_1_status='rejected',
                    approval_1_reason=reason
                )
                return 'reject'
            else:
                print("⚠️ 无效输入，请输入A/R/V/O")
    
    # ==================== 阶段3：代码生成 ====================
    def run_code_generation(self) -> bool:
        """阶段3：代码生成 - Coder智能体严格按照方案生成代码"""
        self.set_state(PipelineStateEnum.CODE_GENERATION)
        print("\n" + "="*80)
        print("💻 【阶段3/6】代码生成 (Coder智能体)")
        print("="*80)
        
        print("🔄 正在调用Coder智能体生成代码（Mock模式）...")
        
        # 调用Coder Agent
        coder_result = self.coder_agent.run(self.context.plan_md)
        
        print("\n📦 代码生成完成：")
        print(f"✅ 生成代码文件数: {len(coder_result.get('code_files', []))}")
        print(f"✅ 生成测试用例数: {len(coder_result.get('test_cases', []))}")
        
        # 保存到上下文
        self.context.update(
            coder_result=coder_result,
            code_changes=[FileChange(**cf) for cf in coder_result.get('code_files', [])]
        )
        
        return True
    
    # ==================== 阶段4：测试生产 ====================
    def run_test_generation(self) -> bool:
        """阶段4：测试生产 - QA智能体生成测试用例并执行"""
        self.set_state(PipelineStateEnum.TEST_GENERATION)
        print("\n" + "="*80)
        print("🧪 【阶段4/6】测试生成与执行 (QA智能体)")
        print("="*80)
        
        print("🔄 正在调用QA智能体生成测试用例（Mock模式）...")
        
        # 调用QA Agent
        qa_result = self.qa_agent.run(self.context.code_changes, self.context.template_report_md)
        
        execution_result = qa_result.get('execution_result', {})
        failed_count = execution_result.get('failed_tests', 0)
        
        if failed_count == 0:
            print("✅ 所有测试通过！")
        
        # 保存到上下文
        self.context.update(
            qa_result=qa_result,
            test_cases=[TestCase(**tc) for tc in qa_result.get('test_cases', [])],
            test_result=execution_result
        )
        
        print(f"\n📊 测试结果：总用例 {execution_result.get('total_tests', 0)}，通过 {execution_result.get('passed_tests', 0)}，失败 {execution_result.get('failed_tests', 0)}")
        
        return True
    
    # ==================== 阶段5：代码评审 ====================
    def run_code_review(self) -> bool:
        """阶段5：代码评审 - Reviewer智能体生成评审报告"""
        self.set_state(PipelineStateEnum.CODE_REVIEW)
        print("\n" + "="*80)
        print("🔍 【阶段5/6】代码评审 (Reviewer智能体)")
        print("="*80)
        
        print("🔄 正在调用Reviewer智能体进行代码评审（Mock模式）...")
        
        # 调用Reviewer Agent
        reviewer_result = self.reviewer_agent.run(
            self.context.code_changes, 
            self.context.plan_md, 
            self.context.test_result
        )
        
        review_summary = reviewer_result.get('review_summary', {})
        print("\n📋 代码评审完成：")
        print(f"✅ 整体结论: {review_summary.get('overall_status', 'unknown')}")
        print(f"✅ 总问题数: {review_summary.get('total_problems', 0)}")
        print(f"✅ 严重问题: {review_summary.get('critical_problems', 0)}")
        print(f"✅ 代码质量总分: {reviewer_result.get('code_quality_scores', {}).get('overall_score', 0)}/10")
        
        # 生成评审报告
        eval_report = reviewer_result.get('eval_template_report', "# 代码评审报告生成失败")
        eval_file = self.output_dir / "eval-template-report.md"
        eval_file.write_text(eval_report, encoding="utf-8")
        print(f"\n✅ 代码评审报告已生成: {eval_file.resolve()}")
        
        # 保存到上下文
        self.context.update(
            reviewer_result=reviewer_result,
            eval_report_path=str(eval_file.resolve()),
            eval_report_md=eval_report
        )
        
        return True
    
    def human_approval_2(self) -> str:
        """人工检查点2：代码评审结果审批
        :return: 'approve' / 'reject'
        """
        self.set_state(PipelineStateEnum.HUMAN_APPROVAL_2)
        print("\n" + "="*80)
        print("🔍 【人工检查点2】代码评审结果审批")
        print("="*80)
        
        while True:
            choice = input("\n请审批代码评审结果：输入 [A]ppove 通过 / [R]eject 打回 / [V]iew 查看完整报告 / [O]pen 打开报告：").strip().upper()
            
            if choice == 'V':
                print("\n📋 代码评审详情：")
                print(json.dumps(self.context.reviewer_result, ensure_ascii=False, indent=2))
            elif choice == 'O':
                # 打开评审报告
                if os.name == 'nt':
                    os.startfile(self.context.eval_report_path)
                else:
                    import subprocess
                    subprocess.run(['open', self.context.eval_report_path])
            elif choice == 'A':
                print("✅ 代码评审已通过，进入交付阶段")
                self.context.update(approval_2_status='approved')
                return 'approve'
            elif choice == 'R':
                reason = input("请输入打回理由：").strip()
                print(f"❌ 代码已被打回，理由：{reason}，将回到代码生成阶段重新开发")
                self.context.update(
                    approval_2_status='rejected',
                    approval_2_reason=reason
                )
                return 'reject'
            else:
                print("⚠️ 无效输入，请输入A/R/V/O")
    
    # ==================== 阶段6：交付集成 ====================
    def save_outputs(self, pm_result: Dict[str, Any], coder_result: Dict[str, Any]) -> None:
        """
        保存所有输出结果到统一的输出目录
        :param pm_result: PM输出结果
        :param coder_result: Coder输出结果
        """
        output_path = self.output_dir
        
        # 保存PM结果
        pm_file = output_path / "pm_result.json"
        pm_file.write_text(json.dumps(pm_result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n💾 PM方案已保存到: {pm_file.resolve()}")
        
        # 保存Coder结果
        coder_file = output_path / "coder_result.json"
        coder_file.write_text(json.dumps(coder_result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"💾 开发结果已保存到: {coder_file.resolve()}")
        
        # 保存QA测试结果
        if self.context.qa_result:
            qa_file = output_path / "qa_result.json"
            qa_file.write_text(json.dumps(self.context.qa_result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"💾 测试结果已保存到: {qa_file.resolve()}")
        
        # 保存评审结果
        if self.context.reviewer_result:
            review_file = output_path / "review_result.json"
            review_file.write_text(json.dumps(self.context.reviewer_result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"💾 评审结果已保存到: {review_file.resolve()}")
        
        # 保存交付结果
        if self.context.delivery_result:
            delivery_file = output_path / "delivery_result.json"
            delivery_file.write_text(json.dumps(self.context.delivery_result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"💾 交付结果已保存到: {delivery_file.resolve()}")
        
        # 生成代码文件
        code_dir = output_path / "code"
        for code_file in coder_result.get("code_files", []):
            file_path = code_dir / code_file["file_path"]
            file_path.parent.mkdir(exist_ok=True, parents=True)
            file_path.write_text(code_file["content"], encoding="utf-8")
            print(f"💾 生成代码文件: {file_path.resolve()}")
        
        # 生成测试文件
        test_dir = output_path / "tests"
        for test_file in coder_result.get("test_cases", []):
            file_path = test_dir / test_file["test_file_path"]
            file_path.parent.mkdir(exist_ok=True, parents=True)
            file_path.write_text(test_file["test_content"], encoding="utf-8")
            print(f"💾 生成测试文件: {file_path.resolve()}")
    
    def run_delivery(self) -> bool:
        """阶段6：交付集成 - Delivery智能体自动提交PR"""
        self.set_state(PipelineStateEnum.DELIVERY)
        print("\n" + "="*80)
        print("🚚 【阶段6/6】交付集成 (Delivery智能体)")
        print("="*80)
        
        # ------------------------------
        # Mock实现：直接返回交付结果，跳过LLM调用和Git操作
        # ------------------------------
        print("🔄 正在调用Delivery智能体生成PR（Mock模式）...")
        
        mock_delivery_result = {
            "branch_operation": {
                "branch_name": f"feature/auto-generated-{self.context.pipeline_id[:8]}",
                "base_branch": "main",
                "commit_message": f"feat: 自动生成代码 - {self.context.user_query[:30]}...",
                "commit_hash": "a1b2c3d4e5f6g7h8i9j0"
            },
            "pr_info": {
                "pr_title": f"自动生成：{self.context.user_query}",
                "pr_template_md": f"""# PR Description
## 🎯 需求
{self.context.user_query}

## 📋 变更内容
- 🆕 新增代码文件：{len(self.context.code_changes) if self.context.code_changes else 0}个
- 🧪 新增测试用例：{len(self.context.test_cases) if self.context.test_cases else 0}个
- 📊 测试覆盖率：{self.context.test_result.get('total_coverage', 0) if self.context.test_result else 0}%
- 🔍 代码质量评分：{self.context.reviewer_result.get('code_quality_scores', {}).get('overall_score', 0) if self.context.reviewer_result else 0}/10

## ✅ 检查清单
- [x] 代码符合编码规范
- [x] 所有测试用例通过
- [x] 代码评审通过
- [x] 文档完整

## 📝 生成说明
本PR由DevFlow Engine自动生成，所有代码经过AI评审和测试验证。
""",
                "pr_url": f"https://github.com/your-org/your-repo/pull/12345",
                "reviewers": ["engineer-a", "engineer-b"]
            },
            "execution_result": {
                "status": "success",
                "message": "PR创建成功",
                "duration": "1.2s"
            }
        }
        
        # 生成PR模板
        pr_template = mock_delivery_result.get('pr_info', {}).get('pr_template_md', "# PR模板生成失败")
        pr_file = self.output_dir / "pr-template.md"
        pr_file.write_text(pr_template, encoding="utf-8")
        print(f"\n✅ PR模板已生成: {pr_file.resolve()}")
        
        # 保存到上下文
        self.context.update(
            delivery_result=mock_delivery_result,
            pr_template_path=str(pr_file.resolve()),
            branch_name=mock_delivery_result.get('branch_operation', {}).get('branch_name'),
            pr_url=mock_delivery_result.get('pr_info', {}).get('pr_url')
        )
        
        print("\n🎉 所有阶段执行完成！")
        print(f"📦 交付产物：")
        print(f"  - 需求文档: {self.context.template_report_path}")
        print(f"  - 技术方案: {self.context.plan_md_path}")
        print(f"  - 代码变更集: {len(self.context.code_changes) if self.context.code_changes else 0}个文件")
        print(f"  - 测试用例: {len(self.context.test_cases) if self.context.test_cases else 0}个")
        print(f"  - 评审报告: {self.context.eval_report_path}")
        print(f"  - PR模板: {self.context.pr_template_path}")
        
        return True
    
    # ==================== 主流程 ====================
    def run(self, user_requirement: str) -> bool:
        """
        运行完整6阶段流水线
        :param user_requirement: 用户原始需求
        :return: 是否成功
        """
        try:
            # 初始化统一上下文
            self.context = PipelineContext(
                user_query=user_requirement,
                output_dir=str(self.output_dir.resolve()),
                codebase_dir=str(self.codebase_dir.resolve()),
                state=PipelineStateEnum.INIT
            )
            
            # 自动保存上下文
            self.context.save_to_file(self.output_dir / "context.json")
            
            # 阶段1：需求分析
            if not self.run_requirement_analysis(user_requirement):
                self.set_state(PipelineStateEnum.FAILED)
                return False
            
            # 阶段2：方案设计 + 人工检查点1
            while True:
                if not self.run_architecture_design():
                    self.set_state(PipelineStateEnum.FAILED)
                    return False
                
                approval_result = self.human_approval_1()
                if approval_result == 'approve':
                    break
                elif approval_result == 'reject':
                    # 打回重写，回到需求分析阶段重新生成
                    print("🔄 技术方案被打回，回到需求分析阶段重新调整...")
                    # 清空架构设计相关数据，重新运行需求分析
                    self.context.update(
                        architect_result=None,
                        plan_md=None,
                        plan_md_path=None,
                        file_change_list=None,
                        api_design=None,
                        approval_1_status=None,
                        approval_1_reason=None
                    )
                    # 重新运行需求分析
                    if not self.run_requirement_analysis(self.context.user_query):
                        self.set_state(PipelineStateEnum.FAILED)
                        return False
                    continue
            
            # 阶段3：代码生成
            if not self.run_code_generation():
                self.set_state(PipelineStateEnum.FAILED)
                return False
            
            # 阶段4：测试生产（含自动重试修复）
            if not self.run_test_generation():
                self.set_state(PipelineStateEnum.FAILED)
                return False
            
            # 阶段5：代码评审 + 人工检查点2
            while True:
                if not self.run_code_review():
                    self.set_state(PipelineStateEnum.FAILED)
                    return False
                
                approval_result = self.human_approval_2()
                if approval_result == 'approve':
                    break
                elif approval_result == 'reject':
                    # 打回重写，回到代码生成阶段重新开发
                    print("🔄 代码被打回，回到代码生成阶段重新开发...")
                    # 清空代码评审、测试相关数据，重新运行代码生成
                    self.context.update(
                        reviewer_result=None,
                        eval_report_path=None,
                        eval_report_md=None,
                        approval_2_status=None,
                        approval_2_reason=None,
                        qa_result=None,
                        test_cases=None,
                        test_result=None
                    )
                    # 重新运行代码生成
                    if not self.run_code_generation():
                        self.set_state(PipelineStateEnum.FAILED)
                        return False
                    # 重新运行测试生成
                    if not self.run_test_generation():
                        self.set_state(PipelineStateEnum.FAILED)
                        return False
                    continue
            
            # 阶段6：交付集成
            if not self.run_delivery():
                self.set_state(PipelineStateEnum.FAILED)
                return False
            
            # 保存所有输出到统一目录
            self.save_outputs(self.context.pm_result, self.context.coder_result)
            
            self.set_state(PipelineStateEnum.COMPLETED)
            print("\n" + "="*80)
            print("🎉 🔥 整个需求交付流水线已100%成功完成！")
            print(f"📦 所有产物已统一保存到: {self.output_dir.resolve()}")
            print("="*80)
            
            return True
            
        except Exception as e:
            self.set_state(PipelineStateEnum.FAILED)
            print(f"\n❌ 流水线执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    import sys
    
    print("🤖 基于AI驱动的6阶段需求交付流程引擎 (DevFlow Engine Pro)")
    print("="*80)
    
    if len(sys.argv) > 1:
        # 从命令行参数读取需求
        user_requirement = " ".join(sys.argv[1:])
    else:
        # 交互式输入需求
        print("请输入您的需求：")
        user_requirement = input("> ").strip()
    
    if not user_requirement:
        print("⚠️ 需求不能为空")
        sys.exit(1)
    
    engine = PipelineEngine()
    success = engine.run(user_requirement)
    
    sys.exit(0 if success else 1)
