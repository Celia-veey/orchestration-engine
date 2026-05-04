from typing import Dict, Any, List
from . import DeliveryBaseAgent
from models import FileChange

class DeliveryMockAgent(DeliveryBaseAgent):
    """Delivery智能体Mock实现，返回固定模拟数据"""
    
    def run(
        self,
        code_changes: List[FileChange],
        test_result: Dict[str, Any],
        review_score: float,
        requirement: str
    ) -> Dict[str, Any]:
        import uuid
        pipeline_id = str(uuid.uuid4())[:8]
        
        return {
            "branch_operation": {
                "branch_name": f"feature/auto-generated-{pipeline_id}",
                "base_branch": "main",
                "commit_message": f"feat: 自动生成代码 - {requirement[:30]}...",
                "commit_hash": "a1b2c3d4e5f6g7h8i9j0"
            },
            "pr_info": {
                "pr_title": f"自动生成：{requirement}",
                "pr_template_md": f"""# PR Description
## 🎯 需求
{requirement}

## 📋 变更内容
- 🆕 新增代码文件：{len(code_changes)}个
- 🧪 新增测试用例：{test_result.get('total_tests', 0)}个
- 📊 测试覆盖率：{test_result.get('total_coverage', 0)}%
- 🔍 代码质量评分：{review_score}/10

## ✅ 检查清单
- [x] 代码符合编码规范
- [x] 所有测试用例通过
- [x] 代码评审通过
- [x] 文档完整

## 📝 生成说明
本PR由DevFlow Engine自动生成，所有代码经过AI评审和测试验证。
""",
                "pr_url": f"https://github.com/your-org/your-repo/pull/12345",
                "reviewers": ["engineer-a", "engineer-b"]
            },
            "execution_result": {
                "status": "success",
                "message": "PR创建成功",
                "duration": "1.2s"
            }
        }
