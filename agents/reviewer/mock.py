from typing import Dict, Any, Optional, List
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agents import ReviewerBaseAgent
from models import FileChange

class ReviewerMockAgent(ReviewerBaseAgent):
    """Reviewer智能体Mock实现，返回固定模拟数据"""
    
    def run(
        self,
        code_changes: List[FileChange],
        tech_plan: str,
        test_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "review_summary": {
                "overall_status": "pass",
                "total_problems": 2,
                "critical_problems": 0,
                "major_problems": 0,
                "minor_problems": 1,
                "suggestion_problems": 1,
                "review_summary": "代码质量良好，符合编码规范，可以通过评审"
            },
            "problem_list": [
                {
                    "problem_id": 1,
                    "severity": "minor",
                    "problem_description": "main.py中缺少错误处理的统一中间件",
                    "file_path": "src/main.py",
                    "line_range": "L1-L20",
                    "repair_suggestion": "建议添加全局异常处理中间件，统一返回错误格式"
                },
                {
                    "problem_id": 2,
                    "severity": "suggestion",
                    "problem_description": "utils.py中的函数缺少类型注解",
                    "file_path": "src/utils.py",
                    "line_range": "L1-L30",
                    "repair_suggestion": "建议为所有函数添加完整的类型注解，提高代码可读性"
                }
            ],
            "code_quality_scores": {
                "overall_score": 92,
                "readability": 95,
                "maintainability": 90,
                "performance": 95,
                "security": 90
            },
            "eval_template_report": """# 代码评审报告
## 📊 评审概览
- 整体结论：✅ 通过
- 代码质量总分：92/100
- 问题总数：2个（无严重问题）

## 📝 详细评审结果
### 1. 优点
- 代码结构清晰，分层架构合理
- API设计符合RESTful规范
- 测试用例覆盖率达到96.2%
- 命名规范，注释完整

### 2. 待改进项
| 问题ID | 严重程度 | 问题描述 | 修复建议 |
|--------|----------|----------|----------|
| 1 | 次要 | main.py中缺少错误处理的统一中间件 | 建议添加全局异常处理中间件，统一返回错误格式 |
| 2 | 建议 | utils.py中的函数缺少类型注解 | 建议为所有函数添加完整的类型注解，提高代码可读性 |

## ✅ 评审结论
代码质量良好，符合上线标准，可以进入下一阶段。
"""
        }
