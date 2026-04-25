import os
import re
import json
from typing import Dict, Any
from pathlib import Path
from llm_client import LLMClient

class PipelineEngine:
    """AI驱动的需求交付流程引擎核心编排器"""
    
    def __init__(self, skills_dir: str = ".agents/skills"):
        """
        初始化流水线引擎
        :param skills_dir: 智能体技能配置目录
        """
        self.skills_dir = Path(skills_dir)
        self.llm_client = LLMClient()
        self.pm_system_prompt = self._load_skill_prompt("PM")
        self.coder_system_prompt = self._load_skill_prompt("Coder")
        
        print("✅ 流程引擎初始化完成")
        print(f"📂 技能配置目录: {self.skills_dir.resolve()}")
    
    def _load_skill_prompt(self, skill_name: str) -> str:
        """
        加载指定智能体的技能配置文件作为System Prompt
        :param skill_name: 技能名称(PM/Coder)
        :return: 处理后的System Prompt内容
        """
        skill_file = self.skills_dir / skill_name / "SKILL.md"
        
        if not skill_file.exists():
            raise FileNotFoundError(f"技能配置文件不存在: {skill_file}")
        
        content = skill_file.read_text(encoding="utf-8")
        # 移除YAML头部，只保留Markdown正文部分
        yaml_pattern = r'^---\n.*?\n---\n'
        prompt_content = re.sub(yaml_pattern, '', content, flags=re.DOTALL)
        
        return prompt_content.strip()
    
    def run_pm_phase(self, user_requirement: str) -> Dict[str, Any]:
        """
        执行PM阶段：分析需求并输出结构化方案
        :param user_requirement: 用户原始需求
        :return: PM输出的结构化方案
        """
        print("\n" + "="*60)
        print("🚀 开始执行PM阶段：需求分析与方案设计")
        print("="*60)
        
        messages = [
            {"role": "system", "content": self.pm_system_prompt},
            {"role": "user", "content": f"用户需求：\n{user_requirement}"}
        ]
        
        print("🔄 正在调用PM智能体分析需求...")
        pm_result = self.llm_client.chat_completion_json(messages, temperature=0.3, max_tokens=4000)
        
        print("\n📋 PM智能体输出方案：")
        print(json.dumps(pm_result, ensure_ascii=False, indent=2))
        
        return pm_result
    
    def human_approval(self, pm_result: Dict[str, Any]) -> bool:
        """
        人工确认环节：等待用户审批PM方案
        :param pm_result: PM输出的方案
        :return: 是否通过审批
        """
        print("\n" + "="*60)
        print("🔍 人工审批环节")
        print("="*60)
        
        while True:
            choice = input("\n请审批PM方案：输入 [A]ppove 通过 / [R]eject 拒绝 / [V]iew 查看详细方案：").strip().upper()
            
            if choice == 'V':
                print("\n📋 PM方案详情：")
                print(json.dumps(pm_result, ensure_ascii=False, indent=2))
            elif choice == 'A':
                print("✅ 方案已通过审批，进入开发阶段")
                return True
            elif choice == 'R':
                print("❌ 方案已被拒绝，流程终止")
                return False
            else:
                print("⚠️ 无效输入，请输入A/R/V")
    
    def run_coder_phase(self, pm_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Coder阶段：根据PM方案编写代码和测试
        :param pm_result: PM输出的结构化方案
        :return: Coder输出的代码结果
        """
        print("\n" + "="*60)
        print("💻 开始执行Coder阶段：代码开发与测试")
        print("="*60)
        
        messages = [
            {"role": "system", "content": self.coder_system_prompt},
            {"role": "user", "content": f"PM方案：\n{json.dumps(pm_result, ensure_ascii=False)}"}
        ]
        
        print("🔄 正在调用Coder智能体生成代码...")
        # qwen3.6-plus支持32k上下文，设置更大的max_tokens支持完整项目生成
        coder_result = self.llm_client.chat_completion_json(messages, temperature=0.2, max_tokens=30000)
        
        print("\n📦 Coder智能体输出结果：")
        print(f"✅ 生成代码文件数: {len(coder_result.get('code_files', []))}")
        print(f"✅ 生成测试用例数: {len(coder_result.get('test_cases', []))}")
        
        return coder_result
    
    def save_outputs(self, pm_result: Dict[str, Any], coder_result: Dict[str, Any], output_dir: str = "output"):
        """
        保存所有输出结果到文件
        :param pm_result: PM输出结果
        :param coder_result: Coder输出结果
        :param output_dir: 输出目录
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 保存PM结果
        pm_file = output_path / "pm_result.json"
        pm_file.write_text(json.dumps(pm_result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n💾 PM方案已保存到: {pm_file.resolve()}")
        
        # 保存Coder结果
        coder_file = output_path / "coder_result.json"
        coder_file.write_text(json.dumps(coder_result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"💾 开发结果已保存到: {coder_file.resolve()}")
        
        # 生成代码文件
        for code_file in coder_result.get("code_files", []):
            file_path = output_path / code_file["file_path"]
            file_path.parent.mkdir(exist_ok=True, parents=True)
            file_path.write_text(code_file["content"], encoding="utf-8")
            print(f"💾 生成代码文件: {file_path.resolve()}")
        
        # 生成测试文件
        for test_file in coder_result.get("test_cases", []):
            file_path = output_path / test_file["test_file_path"]
            file_path.parent.mkdir(exist_ok=True, parents=True)
            file_path.write_text(test_file["test_content"], encoding="utf-8")
            print(f"💾 生成测试文件: {file_path.resolve()}")
    
    def run(self, user_requirement: str) -> bool:
        """
        运行完整流水线
        :param user_requirement: 用户原始需求
        :return: 流程是否成功完成
        """
        try:
            # 1. PM阶段
            pm_result = self.run_pm_phase(user_requirement)
            
            # 2. 人工审批
            if not self.human_approval(pm_result):
                return False
            
            # 3. Coder阶段
            coder_result = self.run_coder_phase(pm_result)
            
            # 4. 保存输出
            self.save_outputs(pm_result, coder_result)
            
            print("\n" + "="*60)
            print("🎉 整个需求交付流程已成功完成！")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ 流程执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    import sys
    
    print("🤖 基于AI驱动的需求交付流程引擎 (DevFlow Engine)")
    print("="*60)
    
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
