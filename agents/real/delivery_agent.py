from typing import Dict, Any, List, Optional
from pathlib import Path

from .. import DeliveryBaseAgent
from llm_client import LLMClient


class DeliveryAgent(DeliveryBaseAgent):
    """Delivery 真实 Agent：通过 LLM 进行交付集成和 PR 生成"""

    def __init__(self, llm_client: LLMClient, agents_dir: str = "Multi-Agents/agents"):
        self.llm = llm_client
        self._system_prompt = self._load_skill_prompt(agents_dir, "Delivery")

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
        test_result: Dict[str, Any],
        review_score: float,
        requirement: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": f"请根据以下信息生成交付内容：\n\n代码变更：\n{code_changes}\n\n测试结果：\n{test_result}\n\n评审得分：{review_score}\n\n原始需求：\n{requirement}"}
        ]

        if chat_history:
            messages.extend(chat_history)

        result = self.llm.chat_completion_text(
            messages=messages,
            max_tokens=4096
        )

        return {"type": "delivery", "content": result}
