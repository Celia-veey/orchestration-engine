from typing import Dict, Any, List
from . import QABaseAgent
from models import FileChange, TestCase

class QAMockAgent(QABaseAgent):
    """QA智能体Mock实现，返回固定模拟数据"""
    
    def run(
        self,
        code_changes: List[FileChange],
        requirement_doc: str
    ) -> Dict[str, Any]:
        return {
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

def test_submit_invalid_data():
    test_data = {
        "timestamp": "2024-01-01T00:00:00Z"
    }
    response = client.post("/api/v1/data", json=test_data)
    assert response.status_code == 422
""",
                    "test_type": "unit",
                    "coverage": 92.5
                },
                {
                    "test_file_path": "tests/test_utils.py",
                    "test_content": """from src.utils import generate_unique_id, validate_input, serialize_json
from datetime import datetime

def test_generate_unique_id():
    id1 = generate_unique_id()
    id2 = generate_unique_id()
    assert len(id1) == 17  # 格式：YYYYMMDDHHMMSSmmm
    assert id1 != id2

def test_validate_input():
    data = {"name": "test", "age": 20}
    assert validate_input(data, ["name", "age"]) == True
    assert validate_input(data, ["name", "email"]) == False

def test_serialize_json():
    now = datetime.now()
    result = serialize_json(now)
    assert isinstance(result, str)
    assert len(result) > 0
""",
                    "test_type": "unit",
                    "coverage": 100.0
                }
            ],
            "execution_result": {
                "total_tests": 5,
                "passed_tests": 5,
                "failed_tests": 0,
                "skipped_tests": 0,
                "total_coverage": 96.2,
                "execution_time": "0.2s"
            },
            "failed_test_details": []
        }
