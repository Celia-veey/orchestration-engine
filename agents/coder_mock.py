from typing import Dict, Any, Optional, List
from . import CoderBaseAgent
from models import FileChange

class CoderMockAgent(CoderBaseAgent):
    """Coder智能体Mock实现，返回通用前后端模板代码"""
    
    def run(
        self,
        tech_plan: str,
        codebase_context: Optional[Dict[str, Any]] = None,
        fix_hint: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        return {
            "code_files": [
                {
                    "file_path": "backend/main.py",
                    "content": """from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api import router as api_router
import os

app = FastAPI(title="Project API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix="/api/v1")

# 挂载静态文件（前端页面）
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

@app.get("/")
async def root():
    return {"message": "Welcome to Project API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
                    "change_type": "new",
                    "language": "python"
                },
                {
                    "file_path": "backend/api.py",
                    "content": """from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter()

# 内存存储（Mock用，实际应该用数据库）
db: List[dict] = []

class ItemCreate(BaseModel):
    name: str = Field(description="名称")
    description: Optional[str] = Field(default="", description="描述")

class ItemResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: str

@router.get("/items", response_model=List[ItemResponse])
async def list_items():
    \"\"\"获取所有记录\"\"\"
    return sorted(db, key=lambda x: x["created_at"], reverse=True)

@router.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    \"\"\"新增记录\"\"\"
    record = {
        "id": str(uuid.uuid4())[:8],
        "name": item.name,
        "description": item.description,
        "created_at": datetime.now().isoformat()
    }
    db.append(record)
    return record

@router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    \"\"\"删除记录\"\"\"
    for i, e in enumerate(db):
        if e["id"] == item_id:
            return db.pop(i)
    raise HTTPException(status_code=404, detail="记录不存在")
""",
                    "change_type": "new",
                    "language": "python"
                },
                {
                    "file_path": "backend/requirements.txt",
                    "content": """fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
""",
                    "change_type": "new",
                    "language": "text"
                },
                {
                    "file_path": "frontend/index.html",
                    "content": """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project App</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Project App</h1>
        </header>

        <!-- 新增表单 -->
        <div class="form-section">
            <h2>新增记录</h2>
            <form id="item-form">
                <input type="text" id="name" placeholder="名称" required>
                <input type="text" id="description" placeholder="描述">
                <button type="submit">添加</button>
            </form>
        </div>

        <!-- 列表 -->
        <div class="list-section">
            <h2>记录列表</h2>
            <div id="item-list"></div>
        </div>
    </div>

    <script src="app.js"></script>
</body>
</html>
""",
                    "change_type": "new",
                    "language": "html"
                },
                {
                    "file_path": "frontend/style.css",
                    "content": """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f5f7fa;
    color: #333;
    line-height: 1.6;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    padding: 20px 0;
}

header h1 {
    font-size: 28px;
    color: #2c3e50;
}

.form-section {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.form-section h2 {
    font-size: 18px;
    margin-bottom: 16px;
    color: #2c3e50;
}

input {
    width: 100%;
    padding: 10px 14px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 14px;
    margin-bottom: 12px;
}

input:focus {
    outline: none;
    border-color: #3498db;
}

button {
    width: 100%;
    padding: 12px;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
}

button:hover {
    background: #2980b9;
}

.list-section {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.item-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #eee;
}

.item-item:last-child {
    border-bottom: none;
}

.delete-btn {
    width: auto;
    padding: 6px 12px;
    background: #e74c3c;
    font-size: 12px;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}

.empty-state {
    text-align: center;
    padding: 40px;
    color: #999;
}
""",
                    "change_type": "new",
                    "language": "css"
                },
                {
                    "file_path": "frontend/app.js",
                    "content": """const API_BASE = '/api/v1';

document.addEventListener('DOMContentLoaded', () => {
    loadItems();
    
    document.getElementById('item-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await addItem();
    });
});

async function loadItems() {
    const res = await fetch(`${API_BASE}/items`);
    const items = await res.json();
    
    const listEl = document.getElementById('item-list');
    if (items.length === 0) {
        listEl.innerHTML = '<div class="empty-state">暂无记录</div>';
        return;
    }
    
    listEl.innerHTML = items.map(e => `
        <div class="item-item">
            <div>
                <strong>${e.name}</strong>
                <p>${e.description}</p>
            </div>
            <button class="delete-btn" onclick="deleteItem('${e.id}')">删除</button>
        </div>
    `).join('');
}

async function addItem() {
    const data = {
        name: document.getElementById('name').value,
        description: document.getElementById('description').value
    };
    
    const res = await fetch(`${API_BASE}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    if (res.ok) {
        document.getElementById('item-form').reset();
        loadItems();
    }
}

async function deleteItem(id) {
    const res = await fetch(`${API_BASE}/items/${id}`, { method: 'DELETE' });
    if (res.ok) loadItems();
}
""",
                    "change_type": "new",
                    "language": "javascript"
                }
            ],
            "test_cases": []
        }
