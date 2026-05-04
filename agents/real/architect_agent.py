from typing import Dict, Any, Optional, List
from pathlib import Path

from .. import ArchitectBaseAgent
from llm_client import LLMClient


class ArchitectAgent(ArchitectBaseAgent):
    """Architect 真实 Agent：通过 LLM 进行技术方案设计"""

    def __init__(self, llm_client: LLMClient, agents_dir: str = "Multi-Agents/agents"):
        self.llm = llm_client
        self._system_prompt = self._load_skill_prompt(agents_dir, "Architect")

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

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def run(
        self,
        requirement_doc: str,
        codebase_context: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        context_info = ""
        if codebase_context:
            context_info = f"\n\n代码库上下文信息：\n{codebase_context}"

        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": f"请根据以下需求文档进行技术方案设计：\n\n{requirement_doc}{context_info}"}
        ]

        if chat_history:
            messages.extend(chat_history)

        result = self.llm.chat_completion_text(
            messages=messages,
            max_tokens=8192
        )

        return {"type": "tech_solution", "plan_md": result}
