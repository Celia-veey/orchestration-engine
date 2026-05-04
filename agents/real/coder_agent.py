from typing import Dict, Any, Optional, List
from pathlib import Path
import re

from .. import CoderBaseAgent
from llm_client import LLMClient


class CoderAgent(CoderBaseAgent):
    """Coder 真实 Agent：通过 LLM 分批生成代码并直接写入文件"""

    def __init__(self, llm_client: LLMClient, agents_dir: str = "Multi-Agents/agents"):
        self.llm = llm_client
        self._system_prompt = self._load_skill_prompt(agents_dir, "Coder")

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    @staticmethod
    def _load_skill_prompt(agents_dir: str, agent_name: str) -> str:
        import re
        skill_path = Path(agents_dir) / agent_name / "SKILL.md"
        if not skill_path.exists():
            raise FileNotFoundError(f"找不到 Agent 技能文件: {skill_path}")

        content = skill_path.read_text(encoding="utf-8")
        prompt = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL).strip()
        return prompt

    def _extract_code_files(self, content: str) -> List[Dict[str, Any]]:
        """
        从 Markdown 中提取代码文件
        格式：## 文件: path/to/file.py\n```language\ncode\n```
        """
        files = []
        pattern = r'##\s+(?:文件|File):\s*(.+?)\n```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for file_path, language, code in matches:
            file_path = file_path.strip()
            files.append({
                "file_path": file_path,
                "content": code.strip(),
                "change_type": "new",
                "language": language or "text"
            })
        
        return files

    def _parse_file_list(self, tech_plan: str) -> List[str]:
        """从 plan.md 中提取文件变更列表"""
        file_paths = []
        
        # 尝试匹配表格格式的文件列表
        table_pattern = r'\|\s*(`?[^\s|]+\.[a-zA-Z0-9]+`?)\s*\|\s*(new|modify|delete)'
        matches = re.findall(table_pattern, tech_plan)
        for file_path, _ in matches:
            file_paths.append(file_path.strip('`'))
        
        return file_paths

    def _build_batch_prompt(self, tech_plan: str, file_batch: List[str], batch_num: int, total_batches: int) -> str:
        """构建单个批次的生成提示"""
        files_str = "\n".join([f"- {f}" for f in file_batch])
        
        # 提取相关的 API 设计
        api_section = ""
        if "API 设计" in tech_plan:
            start = tech_plan.find("## 7. API 设计")
            end = tech_plan.find("## 8.", start) if "## 8." in tech_plan else len(tech_plan)
            api_section = tech_plan[start:end]
        
        # 提取数据库设计
        db_section = ""
        if "数据库设计" in tech_plan:
            start = tech_plan.find("## 8. 数据库设计")
            end = tech_plan.find("## 9.", start) if "## 9." in tech_plan else len(tech_plan)
            db_section = tech_plan[start:end]
        
        return f"""请生成以下 {len(file_batch)} 个代码文件（批次 {batch_num}/{total_batches}）：

## 需要生成的文件
{files_str}

## 技术栈
- 后端：Next.js + TypeScript
- 数据库：PostgreSQL
- 认证：JWT + Session Cookie

## API 设计参考
{api_section[:2000] if api_section else "无"}

## 数据库设计参考
{db_section[:2000] if db_section else "无"}

**重要**：
1. 必须生成所有 {len(file_batch)} 个文件的完整代码
2. 每个文件使用 `## 文件: path/to/file` 格式开头
3. 代码必须是完整可运行的，不要省略号或占位符
4. 严格按照 Markdown 格式输出
"""

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def run(
        self,
        tech_plan: str,
        codebase_context: Optional[Dict[str, Any]] = None,
        fix_hint: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        fix_info = ""
        if fix_hint:
            fix_info = f"\n\n修复提示（来自测试失败或代码评审）：\n{fix_hint}"

        context_info = ""
        if codebase_context:
            context_info = f"\n\n代码库上下文：\n{codebase_context}"

        # 从 plan.md 中提取文件列表
        all_files = self._parse_file_list(tech_plan)
        if not all_files:
            # 如果无法提取，回退到使用完整 plan
            print("⚠️  无法从 plan.md 中提取文件列表，使用完整方案生成")
            messages = [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": f"请根据以下技术方案生成代码：\n\n{tech_plan}{context_info}{fix_info}"}
            ]
            if chat_history:
                messages.extend(chat_history)
            
            print("⏳ 正在生成代码，这可能需要几分钟...")
            content = self.llm.chat_completion_text(messages=messages, max_tokens=16384)
            code_files = self._extract_code_files(content)
            return {
                "type": "code_generation",
                "content": content,
                "code_files": code_files
            }

        # 分批生成，每批 5-8 个文件
        batch_size = 6
        batches = [all_files[i:i+batch_size] for i in range(0, len(all_files), batch_size)]
        
        print(f"📋 计划生成 {len(all_files)} 个文件，分 {len(batches)} 批生成（每批 {batch_size} 个）")
        
        all_code_files = []
        all_content = []
        
        for batch_num, file_batch in enumerate(batches, 1):
            print(f"\n🔄 正在生成第 {batch_num}/{len(batches)} 批代码 ({len(file_batch)} 个文件)...")
            
            batch_prompt = self._build_batch_prompt(tech_plan, file_batch, batch_num, len(batches))
            
            messages = [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": batch_prompt + context_info + fix_info}
            ]
            
            if chat_history:
                messages.extend(chat_history)
            
            try:
                batch_content = self.llm.chat_completion_text(messages=messages, max_tokens=8192)
                batch_files = self._extract_code_files(batch_content)
                
                print(f"✅ 第 {batch_num} 批完成，生成 {len(batch_files)} 个文件")
                for f in batch_files:
                    print(f"  - {f['file_path']}")
                
                all_code_files.extend(batch_files)
                all_content.append(batch_content)
            except Exception as e:
                print(f"❌ 第 {batch_num} 批生成失败: {str(e)}")
        
        return {
            "type": "code_generation",
            "content": "\n\n".join(all_content),
            "code_files": all_code_files
        }
