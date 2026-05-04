from typing import Dict, Any, List, Optional
from pathlib import Path

from .. import QABaseAgent
from llm_client import LLMClient


class QAAgent(QABaseAgent):
    """QA 真实 Agent：通过 LLM 生成测试用例"""

    def __init__(self, llm_client: LLMClient, agents_dir: str = "Multi-Agents/agents"):
        self.llm = llm_client
        self._system_prompt = self._load_skill_prompt(agents_dir, "QA")

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
        requirement_doc: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": f"请根据以下代码变更和需求文档生成测试用例：\n\n代码变更：\n{code_changes}\n\n需求文档：\n{requirement_doc}"}
        ]

        if chat_history:
            messages.extend(chat_history)

        result = self.llm.chat_completion_text(
            messages=messages,
            max_tokens=4096
        )

        return {"type": "test_generation", "content": result}
