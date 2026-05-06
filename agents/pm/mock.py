from typing import Dict, Any, Optional, List
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agents import PMBaseAgent

class PMMockAgent(PMBaseAgent):
    """PM智能体Mock实现，返回固定模拟数据"""
    
    def run(
        self,
        user_query: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        return {
            "type": "solution",
            "plan_md": f"""# 需求分析报告
## 📋 需求描述
{user_query}

## ✅ 验收标准
1. 核心功能完全符合用户需求
2. 系统运行稳定，无明显性能问题
3. 代码质量达到可上线标准
4. 包含完整的测试用例和文档

## 🎯 功能清单
- [x] 功能模块1：核心业务逻辑
- [x] 功能模块2：用户交互界面
- [x] 功能模块3：数据存储与管理
- [x] 功能模块4：API接口设计
""",
            "feature_list": ["功能1", "功能2", "功能3", "功能4"],
            "estimated_workload": "3人日"
        }
