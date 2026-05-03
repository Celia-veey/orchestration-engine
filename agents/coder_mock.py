from typing import Dict, Any, Optional
from . import CoderBaseAgent
from models import FileChange

class CoderMockAgent(CoderBaseAgent):
    """Coder智能体Mock实现，返回固定模拟数据"""
    
    def run(
        self,
        tech_plan: str,
        codebase_context: Optional[Dict[str, Any]] = None,
        fix_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "code_files": [
                {
                    "file_path": "src/main.py",
                    "content": """from fastapi import FastAPI
from api import router as api_router

app = FastAPI(title="DevFlow API", version="1.0.0")

# 注册路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to DevFlow API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
                    "change_type": "new",
                    "language": "python"
                },
                {
                    "file_path": "src/api.py",
                    "content": """from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

class DataSubmission(BaseModel):
    data: Dict[str, Any]
    timestamp: str

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@router.post("/data")
async def submit_data(data: DataSubmission):
    try:
        # 这里是业务逻辑处理
        return {"status": "success", "message": "Data received successfully", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
""",
                    "change_type": "new",
                    "language": "python"
                },
                {
                    "file_path": "src/models.py",
                    "content": """from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class BaseResponse(BaseModel):
    status: str = Field(description="响应状态：success/error")
    message: str = Field(description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")

class DataModel(BaseModel):
    id: str = Field(description="数据唯一ID")
    content: Dict[str, Any] = Field(description="数据内容")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
""",
                    "change_type": "new",
                    "language": "python"
                },
                {
                    "file_path": "src/utils.py",
                    "content": """import json
from datetime import datetime
from typing import Any

def serialize_json(obj: Any) -> str:
    '序列化对象为JSON字符串'
    if isinstance(obj, datetime):
        return obj.isoformat()
    return json.dumps(obj, ensure_ascii=False)

def generate_unique_id() -> str:
    '生成唯一ID'
    return datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

def validate_input(data: dict, required_fields: list) -> bool:
    '验证输入是否包含所有必填字段'
    return all(field in data for field in required_fields)
""",
                    "change_type": "new",
                    "language": "python"
                }
            ],
            "test_cases": [
                {
                    "test_file_path": "tests/test_api.py",
                    "test_content": """from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_submit_data():
    test_data = {
        "data": {"key": "value"},
        "timestamp": "2024-01-01T00:00:00Z"
    }
    response = client.post("/api/v1/data", json=test_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
""",
                    "test_type": "unit",
                    "coverage": 85.0
                }
            ]
        }
