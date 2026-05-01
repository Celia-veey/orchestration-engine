import os
import re
import json
import yaml
import time
from enum import Enum
from typing import Dict, Any, Optional, List
from pathlib import Path
from llm_client import LLMClient
from reference_tools import read_reference_doc

class PipelineState(Enum):
    """流水线状态枚举"""
    INIT = "init"
    # 阶段1：需求分析
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    # 阶段2：方案设计
    ARCHITECTURE_DESIGN = "architecture_design"
    HUMAN_APPROVAL_1 = "human_approval_1"
    # 阶段3：代码生成
    CODE_GENERATION = "code_generation"
    # 阶段4：测试生产
    TEST_GENERATION = "test_generation"
    # 阶段5：代码评审
    CODE_REVIEW = "code_review"
    HUMAN_APPROVAL_2 = "human_approval_2"
    # 阶段6：交付集成
    DELIVERY = "delivery"
    COMPLETED = "completed"
    FAILED = "failed"

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
    
    def __init__(self, skills_dir: str = "skills", codebase_dir: str = ".", output_dir: str = "output"):
        """
        初始化流水线引擎
        :param skills_dir: 智能体技能配置目录
        :param codebase_dir: 目标代码库目录
        :param output_dir: 生成产物统一输出目录
        """
        self.skills_dir = Path(skills_dir)
        self.codebase_dir = Path(codebase_dir)
        # 创建带时间戳的输出目录，避免覆盖
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(output_dir) / timestamp
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.llm_client = LLMClient()
        self.skill_manager = SkillManager(skills_dir)
        
        # 状态管理
        self.state = PipelineState.INIT
        self.context: Dict[str, Any] = {}  # 流水线上下文，保存各阶段输出
        
        print("✅ 6阶段流水线引擎初始化完成")
        print(f"📂 技能配置目录: {self.skills_dir.resolve()}")
        print(f"📂 目标代码库: {self.codebase_dir.resolve()}")
        print(f"📂 产物输出目录: {self.output_dir.resolve()}")
    
    def set_state(self, new_state: PipelineState) -> None:
        """更新流水线状态"""
        print(f"\n🔄 状态切换: {self.state.value} -> {new_state.value}")
        self.state = new_state
    
    # ==================== 阶段1：需求分析 ====================
    def run_requirement_analysis(self, user_requirement: str) -> bool:
        """
        阶段1：需求分析 - 渐进式澄清需求，生成结构化需求文档
        :param user_requirement: 用户原始需求
        :return: 是否成功
        """
        self.set_state(PipelineState.REQUIREMENT_ANALYSIS)
        print("\n" + "="*80)
        print("🚀 【阶段1/6】需求分析 (PM智能体)")
        print("="*80)
        
        # 加载PM技能
        pm_system_prompt = self.skill_manager.get_skill_prompt("pm-agent")
        
        # 初始化对话历史
        messages = [
            {"role": "system", "content": pm_system_prompt},
            {"role": "user", "content": f"用户原始需求：\n{user_requirement}"}
        ]
        
        while True:
            print("🔄 正在调用PM智能体分析需求...")
            pm_response = self.llm_client.chat_completion_json(messages, temperature=0.3, max_tokens=8000)
            
            # 检查响应类型
            response_type = pm_response.get("type", "solution")
            
            if response_type == "clarification":
                # 需求不明确，需要提问
                print("\n❓ PM智能体需要您补充以下关键信息（选择题为主，减少输入）：")
                print("="*60)
                questions = pm_response.get("questions", [])
                answers = []
                
                for q in questions:
                    q_id = q['id']
                    question = q['question']
                    q_type = q.get('question_type', 'single_choice')
                    options = q.get('options', [])
                    impact = q.get('impact', '这个信息会影响项目的准确性')
                    default = q.get('default_choice', '')
                    
                    print(f"\n📋 Q{q_id}: {question}")
                    print(f"💡 影响：{impact}")
                    
                    # 显示选项
                    for opt in options:
                        print(f"  [{opt['value']}] {opt['label']}")
                    
                    if default:
                        default_label = next((opt['label'] for opt in options if opt['value'] == default), default)
                        print(f"✨ 默认选项 [{default}]: {default_label}，直接回车使用默认值")
                    
                    # 收集回答
                    while True:
                        prompt = f"\n请选择答案（输入选项字母）"
                        if q_type == 'multi_choice':
                            prompt += "，多选用逗号分隔"
                        prompt += "："
                        
                        user_input = input(prompt).strip()
                        
                        # 使用默认值
                        if not user_input and default:
                            user_input = default
                            print(f"✅ 已选择默认选项: {default}")
                        
                        if not user_input:
                            print("⚠️ 请输入选项")
                            continue
                        
                        # 处理单选
                        if q_type == 'single_choice':
                            selected_opt = next((opt for opt in options if opt['value'].upper() == user_input.upper()), None)
                            if selected_opt:
                                answer = selected_opt['label']
                                if selected_opt['value'] == 'D' and '其他' in selected_opt['label']:
                                    custom_answer = input("请补充说明：").strip()
                                    answer = f"其他：{custom_answer}" if custom_answer else selected_opt['label']
                                answers.append({
                                    "question_id": q_id,
                                    "question": question,
                                    "answer": answer,
                                    "selected_option": user_input.upper()
                                })
                                print(f"✅ 已选择: {answer}")
                                break
                            else:
                                print(f"⚠️ 无效选项，请输入 {','.join([opt['value'] for opt in options])} 中的一个")
                        
                        # 处理多选
                        elif q_type == 'multi_choice':
                            selected_values = [v.strip().upper() for v in user_input.split(',')]
                            selected_opts = [opt for opt in options if opt['value'].upper() in selected_values]
                            if len(selected_opts) == len(selected_values):
                                answer_list = []
                                for opt in selected_opts:
                                    opt_answer = opt['label']
                                    if opt['value'] == 'D' and '其他' in opt['label']:
                                        custom_answer = input("请补充说明其他内容：").strip()
                                        opt_answer = f"其他：{custom_answer}" if custom_answer else opt['label']
                                    answer_list.append(opt_answer)
                                answers.append({
                                    "question_id": q_id,
                                    "question": question,
                                    "answer": "、".join(answer_list),
                                    "selected_options": selected_values
                                })
                                print(f"✅ 已选择: {'、'.join(answer_list)}")
                                break
                            else:
                                print(f"⚠️ 存在无效选项，请输入 {','.join([opt['value'] for opt in options])} 中的值，多选用逗号分隔")
                
                # 二次确认所有答案
                print("\n" + "="*60)
                print("🔍 请确认您的回答：")
                print("-"*60)
                for ans in answers:
                    print(f"Q{ans['question_id']}: {ans['question']}")
                    print(f"    您的回答：{ans['answer']}")
                print("-"*60)
                
                while True:
                    confirm = input("\n确认回答正确？输入 [Y]确认 / [N]修改 / [R]重新回答所有：").strip().upper()
                    if confirm == 'Y':
                        print("✅ 回答已确认，继续分析需求...")
                        break
                    elif confirm == 'R':
                        # 重新回答所有问题
                        print("🔄 重新开始回答问题...")
                        continue
                    elif confirm == 'N':
                        # 选择要修改的问题
                        while True:
                            q_num = input("请输入要修改的问题编号（如1,2,3）：").strip()
                            if not q_num.isdigit():
                                print("⚠️ 请输入有效的数字编号")
                                continue
                            q_id = int(q_num)
                            ans_to_modify = next((a for a in answers if a['question_id'] == q_id), None)
                            if not ans_to_modify:
                                print(f"⚠️ 没有找到编号为{q_id}的问题")
                                continue
                            # 找到对应的问题
                            q_to_modify = next((q for q in questions if q['id'] == q_id), None)
                            if q_to_modify:
                                print(f"\n重新回答Q{q_id}: {q_to_modify['question']}")
                                # 重新显示选项
                                for opt in q_to_modify['options']:
                                    print(f"  [{opt['value']}] {opt['label']}")
                                # 收集新回答
                                while True:
                                    new_input = input("请选择新的答案：").strip()
                                    if not new_input:
                                        print("⚠️ 回答不能为空")
                                        continue
                                    selected_opt = next((opt for opt in q_to_modify['options'] if opt['value'].upper() == new_input.upper()), None)
                                    if selected_opt:
                                        new_answer = selected_opt['label']
                                        if selected_opt['value'] == 'D' and '其他' in selected_opt['label']:
                                            custom_answer = input("请补充说明：").strip()
                                            new_answer = f"其他：{custom_answer}" if custom_answer else selected_opt['label']
                                        ans_to_modify['answer'] = new_answer
                                        ans_to_modify['selected_option'] = new_input.upper()
                                        print(f"✅ Q{q_id} 已修改为: {new_answer}")
                                        break
                                    else:
                                        print(f"⚠️ 无效选项，请输入 {','.join([opt['value'] for opt in q_to_modify['options']])} 中的一个")
                            break
                    else:
                        print("⚠️ 无效输入，请输入Y/N/R")
                
                # 将回答加入对话历史，继续下一轮
                messages.append({"role": "assistant", "content": json.dumps(pm_response, ensure_ascii=False)})
                messages.append({"role": "user", "content": f"用户回答：\n{json.dumps(answers, ensure_ascii=False)}"})
                
            elif response_type == "solution":
                # 需求明确，输出最终方案
                print("\n📋 PM智能体输出最终需求方案：")
                print(json.dumps(pm_response, ensure_ascii=False, indent=2))
                
                # 生成template-report.md
                template_report = pm_response.get("template_report_md", "# 需求文档生成失败")
                report_file = self.output_dir / "template-report.md"
                report_file.write_text(template_report, encoding="utf-8")
                print(f"\n✅ 结构化需求文档已生成: {report_file.resolve()}")
                
                # 保存到上下文
                self.context['user_requirement'] = user_requirement
                self.context['pm_result'] = pm_response
                self.context['template_report_path'] = str(report_file.resolve())
                self.context['template_report_content'] = template_report
                
                return True
            
            else:
                # 未知响应类型，重新生成
                print(f"⚠️ 未知响应类型: {response_type}，重新生成...")
                messages.append({"role": "assistant", "content": json.dumps(pm_response, ensure_ascii=False)})
                messages.append({"role": "user", "content": "返回格式错误，请按照要求返回clarification或solution类型的JSON"})
    
    # ==================== 阶段2：方案设计（多智能体协作） ====================
    def run_architecture_design(self) -> bool:
        """阶段2：架构设计 - 多智能体协作（API Designer + DB Architect + Auth Specialist）"""
        self.set_state(PipelineState.ARCHITECTURE_DESIGN)
        print("\n" + "="*80)
        print("🏗️  【阶段2/6】技术方案设计 (多智能体协作)")
        print("="*80)
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_reference_doc",
                    "description": "读取架构设计规范文档，按需获取特定主题的设计规范",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "enum": ["api-design", "db-schema", "auth-flow", "tech-selection", "environment-management", "testing-strategy", "django-best-practices", "release-checklist"],
                                "description": "规范文档主题"
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]
        
        # Step 1: API Designer 设计 API
        print("\n📡 步骤1/3: API Designer 正在设计 API 规范...")
        api_designer_prompt = self.skill_manager.get_skill_prompt("architect-api-designer")
        api_messages = [
            {"role": "system", "content": api_designer_prompt},
            {"role": "user", "content": f"需求文档：\n{self.context['template_report_content']}"}
        ]
        api_design_result = self.llm_client.chat_completion_json(
            api_messages, temperature=0.2, max_tokens=8000,
            tools=tools, tool_functions={"read_reference_doc": read_reference_doc}
        )
        print(f"✅ API 设计完成: {len(api_design_result.get('api_endpoints', []))} 个端点")
        
        # Step 2: DB Architect 设计数据库
        print("\n🗄️ 步骤2/3: DB Architect 正在设计数据库架构...")
        db_architect_prompt = self.skill_manager.get_skill_prompt("architect-db-architect")
        db_messages = [
            {"role": "system", "content": db_architect_prompt},
            {"role": "user", "content": f"需求文档：\n{self.context['template_report_content']}\n\nAPI 设计：\n{json.dumps(api_design_result, ensure_ascii=False)}"}
        ]
        db_design_result = self.llm_client.chat_completion_json(
            db_messages, temperature=0.2, max_tokens=8000,
            tools=tools, tool_functions={"read_reference_doc": read_reference_doc}
        )
        print(f"✅ 数据库设计完成: {len(db_design_result.get('tables', []))} 个表")
        
        # Step 3: Auth Specialist 设计认证授权
        print("\n🔐 步骤3/3: Auth Specialist 正在设计认证授权方案...")
        auth_specialist_prompt = self.skill_manager.get_skill_prompt("architect-auth-specialist")
        auth_messages = [
            {"role": "system", "content": auth_specialist_prompt},
            {"role": "user", "content": f"需求文档：\n{self.context['template_report_content']}\n\nAPI 设计：\n{json.dumps(api_design_result, ensure_ascii=False)}"}
        ]
        auth_design_result = self.llm_client.chat_completion_json(
            auth_messages, temperature=0.2, max_tokens=8000,
            tools=tools, tool_functions={"read_reference_doc": read_reference_doc}
        )
        print(f"✅ 认证授权设计完成")
        
        # Step 4: 主 Architect 整合所有子智能体输出
        print("\n🔗 正在整合所有子智能体输出...")
        architect_prompt = self.skill_manager.get_skill_prompt("architect-agent")
        codebase_context = "当前代码库架构："
        
        integration_messages = [
            {"role": "system", "content": architect_prompt},
            {"role": "user", "content": f"""需求文档：
{self.context['template_report_content']}

代码库上下文：
{codebase_context}

API 设计方案：
{json.dumps(api_design_result, ensure_ascii=False)}

数据库设计方案：
{json.dumps(db_design_result, ensure_ascii=False)}

认证授权方案：
{json.dumps(auth_design_result, ensure_ascii=False)}

请整合以上所有子智能体的输出，生成完整的技术方案。"""}
        ]
        
        architect_result = self.llm_client.chat_completion_json(
            integration_messages, temperature=0.2, max_tokens=12000,
            tools=tools, tool_functions={"read_reference_doc": read_reference_doc}
        )
        
        print("\n📋 技术方案设计完成：")
        print(f"✅ 变更文件数: {len(architect_result.get('file_change_list', []))}")
        print(f"✅ API设计数: {len(architect_result.get('api_design', []))}")
        
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
        
        self.context['architect_result'] = architect_result
        self.context['api_design_result'] = api_design_result
        self.context['db_design_result'] = db_design_result
        self.context['auth_design_result'] = auth_design_result
        self.context['plan_md_path'] = str(plan_file.resolve())
        self.context['plan_md_content'] = plan_md
        
        return True
    
    def human_approval_1(self) -> bool:
        """人工检查点1：技术方案审批"""
        self.set_state(PipelineState.HUMAN_APPROVAL_1)
        print("\n" + "="*80)
        print("🔍 【人工检查点1】技术方案审批")
        print("="*80)
        
        while True:
            choice = input("\n请审批技术方案：输入 [A]ppove 通过 / [R]eject 打回 / [V]iew 查看完整方案 / [O]pen 打开文档：").strip().upper()
            
            if choice == 'V':
                print("\n📋 技术方案详情：")
                print(json.dumps(self.context['architect_result'], ensure_ascii=False, indent=2))
            elif choice == 'O':
                # 打开plan.md
                if os.name == 'nt':
                    os.startfile(self.context['plan_md_path'])
                else:
                    import subprocess
                    subprocess.run(['open', self.context['plan_md_path']])
            elif choice == 'A':
                print("✅ 技术方案已通过审批，进入代码开发阶段")
                return True
            elif choice == 'R':
                reason = input("请输入打回理由：").strip()
                print(f"❌ 方案已被打回，理由：{reason}")
                self.context['reject_reason_1'] = reason
                return False
            else:
                print("⚠️ 无效输入，请输入A/R/V/O")
    
    # ==================== 阶段3：代码生成（多智能体协作） ====================
    def run_code_generation(self) -> bool:
        """阶段3：代码生成 - 多智能体协作（Backend + Frontend + Database）"""
        self.set_state(PipelineState.CODE_GENERATION)
        print("\n" + "="*80)
        print("💻 【阶段3/6】代码生成 (多智能体协作)")
        print("="*80)
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_reference_doc",
                    "description": "读取编码规范文档，按需获取特定主题的编码规范",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "enum": ["api-design", "db-schema", "auth-flow", "tech-selection", "environment-management", "testing-strategy", "django-best-practices", "release-checklist"],
                                "description": "规范文档主题"
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]
        
        # Step 1: Database Developer 实现数据库层
        print("\n🗄️ 步骤1/3: Database Developer 正在实现数据库层...")
        db_coder_prompt = self.skill_manager.get_skill_prompt("coder-database")
        db_messages = [
            {"role": "system", "content": db_coder_prompt},
            {"role": "user", "content": f"技术方案：\n{self.context['plan_md_content']}\n\n数据库设计：\n{json.dumps(self.context.get('db_design_result', {}), ensure_ascii=False)}"}
        ]
        db_code_result = self.llm_client.chat_completion_json(
            db_messages, temperature=0.2, max_tokens=12000,
            tools=tools, tool_functions={"read_reference_doc": read_reference_doc}
        )
        print(f"✅ 数据库层完成: {len(db_code_result.get('migrations', []))} 个迁移, {len(db_code_result.get('models', []))} 个模型")
        
        # Step 2: Backend Developer 实现后端层
        print("\n🔧 步骤2/3: Backend Developer 正在实现后端层...")
        backend_coder_prompt = self.skill_manager.get_skill_prompt("coder-backend")
        backend_messages = [
            {"role": "system", "content": backend_coder_prompt},
            {"role": "user", "content": f"技术方案：\n{self.context['plan_md_content']}\n\nAPI 设计：\n{json.dumps(self.context.get('api_design_result', {}), ensure_ascii=False)}\n\n数据库代码：\n{json.dumps(db_code_result, ensure_ascii=False)}"}
        ]
        backend_code_result = self.llm_client.chat_completion_json(
            backend_messages, temperature=0.2, max_tokens=15000,
            tools=tools, tool_functions={"read_reference_doc": read_reference_doc}
        )
        print(f"✅ 后端层完成: {len(backend_code_result.get('code_files', []))} 个文件")
        
        # Step 3: Frontend Developer 实现前端层
        print("\n🎨 步骤3/3: Frontend Developer 正在实现前端层...")
        frontend_coder_prompt = self.skill_manager.get_skill_prompt("coder-frontend")
        frontend_messages = [
            {"role": "system", "content": frontend_coder_prompt},
            {"role": "user", "content": f"技术方案：\n{self.context['plan_md_content']}\n\nAPI 设计：\n{json.dumps(self.context.get('api_design_result', {}), ensure_ascii=False)}\n\n后端代码：\n{json.dumps(backend_code_result, ensure_ascii=False)}"}
        ]
        frontend_code_result = self.llm_client.chat_completion_json(
            frontend_messages, temperature=0.2, max_tokens=15000,
            tools=tools, tool_functions={"read_reference_doc": read_reference_doc}
        )
        print(f"✅ 前端层完成: {len(frontend_code_result.get('code_files', []))} 个文件")
        
        # Step 4: 合并所有代码
        print("\n🔗 正在合并所有子智能体生成的代码...")
        all_code_files = []
        all_test_cases = []
        
        for code_file in db_code_result.get('code_files', []):
            all_code_files.append(code_file)
        for code_file in backend_code_result.get('code_files', []):
            all_code_files.append(code_file)
        for code_file in frontend_code_result.get('code_files', []):
            all_code_files.append(code_file)
        
        for test_case in db_code_result.get('test_cases', []):
            all_test_cases.append(test_case)
        for test_case in backend_code_result.get('test_cases', []):
            all_test_cases.append(test_case)
        for test_case in frontend_code_result.get('test_cases', []):
            all_test_cases.append(test_case)
        
        coder_result = {
            'code_files': all_code_files,
            'test_cases': all_test_cases,
            'deployment_guide': backend_code_result.get('deployment_guide', {})
        }
        
        print("\n📦 代码生成完成：")
        print(f"✅ 生成代码文件数: {len(all_code_files)}")
        print(f"✅ 生成测试用例数: {len(all_test_cases)}")
        
        self.context['coder_result'] = coder_result
        self.context['code_changes'] = all_code_files
        self.context['db_code_result'] = db_code_result
        self.context['backend_code_result'] = backend_code_result
        self.context['frontend_code_result'] = frontend_code_result
        
        return True
    
    # ==================== 阶段4：测试生产 ====================
    def run_test_generation(self) -> bool:
        """阶段4：测试生产 - QA智能体生成测试用例并执行"""
        self.set_state(PipelineState.TEST_GENERATION)
        print("\n" + "="*80)
        print("🧪 【阶段4/6】测试生成与执行 (QA智能体)")
        print("="*80)
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_reference_doc",
                    "description": "读取测试规范文档",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "enum": ["api-design", "db-schema", "auth-flow", "tech-selection", "environment-management", "testing-strategy", "django-best-practices", "release-checklist"],
                                "description": "规范文档主题"
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]
        
        qa_prompt = self.skill_manager.get_skill_prompt("qa-agent")
        
        messages = [
            {"role": "system", "content": qa_prompt},
            {"role": "user", "content": f"需求：\n{self.context['template_report_content']}\n\n代码变更集：\n{json.dumps(self.context['code_changes'], ensure_ascii=False)}"}
        ]
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            print(f"🔄 正在调用QA智能体生成测试用例（第{retry_count+1}次尝试）...")
            qa_result = self.llm_client.chat_completion_json(messages, temperature=0.1, max_tokens=12000)
            
            execution_result = qa_result.get('execution_result', {})
            failed_count = execution_result.get('failed_tests', 0)
            
            if failed_count == 0:
                print("✅ 所有测试通过！")
                break
            else:
                retry_count += 1
                print(f"⚠️ 测试失败 {failed_count} 个，尝试自动修复（重试 {retry_count}/{max_retries}）")
                
                repair_messages = [
                    {"role": "system", "content": self.skill_manager.get_skill_prompt("coder-backend")},
                    {"role": "user", "content": f"技术方案：\n{self.context['plan_md_content']}\n\n当前代码：\n{json.dumps(self.context['code_changes'], ensure_ascii=False)}\n\n测试失败信息：\n{json.dumps(qa_result.get('failed_test_details', []), ensure_ascii=False)}\n\n请修复代码中的问题，只返回修复后的代码变更集。"}
                ]
                
                print("🔄 正在调用Backend Developer修复代码问题...")
                fix_result = self.llm_client.chat_completion_json(
                    repair_messages, temperature=0.1, max_tokens=15000,
                    tools=tools, tool_functions={"read_reference_doc": read_reference_doc}
                )
                
                self.context['code_changes'] = fix_result.get('code_files', self.context['code_changes'])
                messages.append({"role": "user", "content": f"修复后的代码：\n{json.dumps(self.context['code_changes'], ensure_ascii=False)}"})
        
        self.context['qa_result'] = qa_result
        self.context['test_cases'] = qa_result.get('test_cases', [])
        self.context['test_result'] = execution_result
        
        print(f"\n📊 测试结果：总用例 {execution_result.get('total_tests', 0)}，通过 {execution_result.get('passed_tests', 0)}，失败 {execution_result.get('failed_tests', 0)}")
        
        return True
    
    # ==================== 阶段5：代码评审 ====================
    def run_code_review(self) -> bool:
        """阶段5：代码评审 - Reviewer智能体生成评审报告"""
        self.set_state(PipelineState.CODE_REVIEW)
        print("\n" + "="*80)
        print("🔍 【阶段5/6】代码评审 (Reviewer智能体)")
        print("="*80)
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_reference_doc",
                    "description": "读取代码评审规范文档",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "enum": ["api-design", "db-schema", "auth-flow", "tech-selection", "environment-management", "testing-strategy", "django-best-practices", "release-checklist"],
                                "description": "规范文档主题"
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]
        
        reviewer_prompt = self.skill_manager.get_skill_prompt("reviewer-agent")
        
        messages = [
            {"role": "system", "content": reviewer_prompt},
            {"role": "user", "content": f"技术方案：\n{self.context['plan_md_content']}\n\n代码变更集：\n{json.dumps(self.context['code_changes'], ensure_ascii=False)}\n\n测试结果：\n{json.dumps(self.context['test_result'], ensure_ascii=False)}"}
        ]
        
        print("🔄 正在调用Reviewer智能体进行代码评审...")
        reviewer_result = self.llm_client.chat_completion_json(
            messages, temperature=0.3, max_tokens=12000,
            tools=tools, tool_functions={"read_reference_doc": read_reference_doc}
        )
        
        review_summary = reviewer_result.get('review_summary', {})
        print("\n📋 代码评审完成：")
        print(f"✅ 整体结论: {review_summary.get('overall_status', 'unknown')}")
        print(f"✅ 总问题数: {review_summary.get('total_problems', 0)}")
        print(f"✅ 严重问题: {review_summary.get('critical_problems', 0)}")
        print(f"✅ 代码质量总分: {reviewer_result.get('code_quality_scores', {}).get('overall_score', 0)}/10")
        
        eval_report = reviewer_result.get('eval_template_report', "# 代码评审报告生成失败")
        eval_file = self.output_dir / "eval-template-report.md"
        eval_file.write_text(eval_report, encoding="utf-8")
        print(f"\n✅ 代码评审报告已生成: {eval_file.resolve()}")
        
        self.context['reviewer_result'] = reviewer_result
        self.context['eval_report_path'] = str(eval_file.resolve())
        self.context['eval_report_content'] = eval_report
        
        return True
    
    def human_approval_2(self) -> bool:
        """人工检查点2：代码评审结果审批"""
        self.set_state(PipelineState.HUMAN_APPROVAL_2)
        print("\n" + "="*80)
        print("🔍 【人工检查点2】代码评审结果审批")
        print("="*80)
        
        while True:
            choice = input("\n请审批代码评审结果：输入 [A]ppove 通过 / [R]eject 打回 / [V]iew 查看完整报告 / [O]pen 打开报告：").strip().upper()
            
            if choice == 'V':
                print("\n📋 代码评审详情：")
                print(json.dumps(self.context['reviewer_result'], ensure_ascii=False, indent=2))
            elif choice == 'O':
                # 打开评审报告
                if os.name == 'nt':
                    os.startfile(self.context['eval_report_path'])
                else:
                    import subprocess
                    subprocess.run(['open', self.context['eval_report_path']])
            elif choice == 'A':
                print("✅ 代码评审已通过，进入交付阶段")
                return True
            elif choice == 'R':
                reason = input("请输入打回理由：").strip()
                print(f"❌ 代码已被打回，理由：{reason}")
                self.context['reject_reason_2'] = reason
                return False
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
        if 'qa_result' in self.context:
            qa_file = output_path / "qa_result.json"
            qa_file.write_text(json.dumps(self.context['qa_result'], ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"💾 测试结果已保存到: {qa_file.resolve()}")
        
        # 保存评审结果
        if 'reviewer_result' in self.context:
            review_file = output_path / "review_result.json"
            review_file.write_text(json.dumps(self.context['reviewer_result'], ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"💾 评审结果已保存到: {review_file.resolve()}")
        
        # 保存交付结果
        if 'delivery_result' in self.context:
            delivery_file = output_path / "delivery_result.json"
            delivery_file.write_text(json.dumps(self.context['delivery_result'], ensure_ascii=False, indent=2), encoding="utf-8")
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
        self.set_state(PipelineState.DELIVERY)
        print("\n" + "="*80)
        print("🚚 【阶段6/6】交付集成 (Delivery智能体)")
        print("="*80)
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_reference_doc",
                    "description": "读取发布清单规范文档",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "enum": ["api-design", "db-schema", "auth-flow", "tech-selection", "environment-management", "testing-strategy", "django-best-practices", "release-checklist"],
                                "description": "规范文档主题"
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]
        
        delivery_prompt = self.skill_manager.get_skill_prompt("delivery-agent")
        
        messages = [
            {"role": "system", "content": delivery_prompt},
            {"role": "user", "content": f"需求：{self.context['user_requirement']}\n\n代码变更集：\n{json.dumps(self.context['code_changes'], ensure_ascii=False)}\n\n测试结果：\n{json.dumps(self.context['test_result'], ensure_ascii=False)}\n\n评审得分：{self.context['reviewer_result'].get('code_quality_scores', {}).get('overall_score', 0)}/10"}
        ]
        
        print("🔄 正在调用Delivery智能体生成PR...")
        delivery_result = self.llm_client.chat_completion_json(
            messages, temperature=0.1, max_tokens=8000,
            tools=tools, tool_functions={"read_reference_doc": read_reference_doc}
        )
        
        pr_template = delivery_result.get('pr_info', {}).get('pr_template_md', "# PR模板生成失败")
        pr_file = self.output_dir / "pr-template.md"
        pr_file.write_text(pr_template, encoding="utf-8")
        print(f"\n✅ PR模板已生成: {pr_file.resolve()}")
        
        self.context['delivery_result'] = delivery_result
        self.context['pr_template_path'] = str(pr_file.resolve())
        
        print("\n🎉 所有阶段执行完成！")
        print(f"📦 交付产物：")
        print(f"  - 需求文档: {self.context['template_report_path']}")
        print(f"  - 技术方案: {self.context['plan_md_path']}")
        print(f"  - 代码变更集: {len(self.context['code_changes'])}个文件")
        print(f"  - 测试用例: {len(self.context['test_cases'])}个")
        print(f"  - 评审报告: {self.context['eval_report_path']}")
        print(f"  - PR模板: {self.context['pr_template_path']}")
        
        return True
    
    # ==================== 主流程 ====================
    def run(self, user_requirement: str) -> bool:
        """
        运行完整6阶段流水线
        :param user_requirement: 用户原始需求
        :return: 是否成功
        """
        try:
            # 阶段1：需求分析
            if not self.run_requirement_analysis(user_requirement):
                self.set_state(PipelineState.FAILED)
                return False
            
            # 阶段2：方案设计 + 人工检查点1
            while True:
                if not self.run_architecture_design():
                    self.set_state(PipelineState.FAILED)
                    return False
                
                if self.human_approval_1():
                    break
                else:
                    # 打回重写，重新生成方案
                    print("🔄 技术方案被打回，重新生成...")
                    continue
            
            # 阶段3：代码生成
            if not self.run_code_generation():
                self.set_state(PipelineState.FAILED)
                return False
            
            # 阶段4：测试生产（含自动重试修复）
            if not self.run_test_generation():
                self.set_state(PipelineState.FAILED)
                return False
            
            # 阶段5：代码评审 + 人工检查点2
            while True:
                if not self.run_code_review():
                    self.set_state(PipelineState.FAILED)
                    return False
                
                if self.human_approval_2():
                    break
                else:
                    # 打回重写，重新生成代码
                    print("🔄 代码被打回，重新生成...")
                    continue
            
            # 阶段6：交付集成
            if not self.run_delivery():
                self.set_state(PipelineState.FAILED)
                return False
            
            # 保存所有输出到统一目录
            self.save_outputs(self.context['pm_result'], self.context['coder_result'])
            
            self.set_state(PipelineState.COMPLETED)
            print("\n" + "="*80)
            print("🎉 🔥 整个需求交付流水线已100%成功完成！")
            print(f"📦 所有产物已统一保存到: {self.output_dir.resolve()}")
            print("="*80)
            
            return True
            
        except Exception as e:
            self.set_state(PipelineState.FAILED)
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
