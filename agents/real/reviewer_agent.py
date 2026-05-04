from typing import Dict, Any, List, Optional
from pathlib import Path

from .. import ReviewerBaseAgent
from llm_client import LLMClient


class ReviewerAgent(ReviewerBaseAgent):
    """Reviewer 真实 Agent：通过 LLM 进行代码质量审查"""

    def __init__(self, llm_client: LLMClient, agents_dir: str = "Multi-Agents/agents"):
        self.llm = llm_client
        self._system_prompt = self._load_skill_prompt(agents_dir, "Reviewer")

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
        code_changes: List[Any],
        tech_plan: str,
        test_result: Dict[str, Any],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": f"请对以下代码变更进行质量审查：\n\n代码变更：\n{code_changes}\n\n技术方案：\n{tech_plan}\n\n测试结果：\n{test_result}"}
        ]

        if chat_history:
            messages.extend(chat_history)

        result = self.llm.chat_completion_text(
            messages=messages,
            max_tokens=4096
        )

        return {"type": "code_review", "content": result}
