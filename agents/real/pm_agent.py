from typing import Dict, Any, Optional, List
from pathlib import Path

from .. import PMBaseAgent
from llm_client import LLMClient


class PMAgent(PMBaseAgent):
    """PM 真实 Agent：通过 LLM 分析需求并输出结构化 PRD"""

    def __init__(self, llm_client: LLMClient, agents_dir: str = "Multi-Agents/agents"):
        self.llm = llm_client
        self._system_prompt = self._load_skill_prompt(agents_dir, "PM")

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    @staticmethod
    def _load_skill_prompt(agents_dir: str, agent_name: str) -> str:
        """读取 SKILL.md，去掉 YAML front-matter，返回正文作为 system prompt"""
        skill_path = Path(agents_dir) / agent_name / "SKILL.md"
        if not skill_path.exists():
            raise FileNotFoundError(f"找不到 Agent 技能文件: {skill_path}")

        content = skill_path.read_text(encoding="utf-8")
        # 去掉 YAML 头部
        import re
        prompt = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL).strip()
        return prompt

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def run(
        self,
        user_query: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": user_query}
        ]

        if chat_history:
            messages.extend(chat_history)

        result = self.llm.chat_completion_text(
            messages=messages,
            max_tokens=4096
        )

        return {"type": "solution", "content": result}
