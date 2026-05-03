from typing import Dict, Any, Optional
from . import ArchitectBaseAgent

class ArchitectMockAgent(ArchitectBaseAgent):
    """架构师智能体Mock实现，返回固定模拟数据"""
    
    def run(
        self,
        requirement_doc: str,
        codebase_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {
            "file_change_list": [
                {
                    "file_path": "src/main.py",
                    "change_type": "new",
                    "description": "主程序入口文件"
                },
                {
                    "file_path": "src/api.py",
                    "change_type": "new",
                    "description": "API接口定义"
                },
                {
                    "file_path": "src/models.py",
                    "change_type": "new",
                    "description": "数据模型定义"
                },
                {
                    "file_path": "src/utils.py",
                    "change_type": "new",
                    "description": "工具函数库"
                }
            ],
            "api_design": [
                {
                    "method": "GET",
                    "path": "/api/v1/health",
                    "description": "健康检查接口"
                },
                {
                    "method": "POST",
                    "path": "/api/v1/data",
                    "description": "提交数据接口"
                }
            ],
            "plan_md": """# 技术方案设计
## 🏗️ 系统架构
采用分层架构设计，分为以下几层：
1. **表现层**：提供RESTful API接口
2. **业务层**：实现核心业务逻辑
3. **数据层**：负责数据持久化和访问

## 📁 目录结构
```
src/
├── main.py          # 主程序入口
├── api.py           # API接口定义
├── models.py        # 数据模型定义
├── utils.py         # 工具函数库
└── config.py        # 配置文件
```

## 🔌 API设计
### 1. 健康检查接口
- `GET /api/v1/health`
- 返回系统运行状态

### 2. 数据提交接口
- `POST /api/v1/data`
- 接收并处理用户提交的数据

## 🛠️ 技术栈
- Python 3.10+
- FastAPI (Web框架)
- Pydantic (数据验证)
- SQLAlchemy (ORM)
- SQLite (数据库)
"""
        }
