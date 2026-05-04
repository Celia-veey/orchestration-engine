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
                    "file_path": "backend/main.py",
                    "content": """from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api import router as api_router
import os

app = FastAPI(title="Expense Tracker API", version="1.0.0")

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
    return {"message": "Welcome to Expense Tracker API"}

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
expenses_db: List[dict] = []

class ExpenseCreate(BaseModel):
    title: str = Field(description="支出标题")
    amount: float = Field(description="金额", gt=0)
    category: str = Field(description="分类：餐饮/交通/购物/娱乐/居住/其他")
    date: Optional[str] = Field(default=None, description="日期，默认今天")
    note: Optional[str] = Field(default="", description="备注")

class ExpenseResponse(BaseModel):
    id: str
    title: str
    amount: float
    category: str
    date: str
    note: str
    created_at: str

@router.get("/expenses", response_model=List[ExpenseResponse])
async def list_expenses(
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    \"\"\"获取所有支出记录，支持筛选\"\"\"
    results = expenses_db[:]
    if category:
        results = [e for e in results if e["category"] == category]
    if start_date:
        results = [e for e in results if e["date"] >= start_date]
    if end_date:
        results = [e for e in results if e["date"] <= end_date]
    return sorted(results, key=lambda x: x["date"], reverse=True)

@router.post("/expenses", response_model=ExpenseResponse)
async def create_expense(expense: ExpenseCreate):
    \"\"\"新增支出记录\"\"\"
    record = {
        "id": str(uuid.uuid4())[:8],
        "title": expense.title,
        "amount": expense.amount,
        "category": expense.category,
        "date": expense.date or datetime.now().strftime("%Y-%m-%d"),
        "note": expense.note,
        "created_at": datetime.now().isoformat()
    }
    expenses_db.append(record)
    return record

@router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    \"\"\"删除支出记录\"\"\"
    for i, e in enumerate(expenses_db):
        if e["id"] == expense_id:
            return expenses_db.pop(i)
    raise HTTPException(status_code=404, detail="记录不存在")

@router.get("/stats")
async def get_stats():
    \"\"\"获取统计信息\"\"\"
    total = sum(e["amount"] for e in expenses_db)
    by_category = {}
    for e in expenses_db:
        by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]
    return {
        "total_expenses": total,
        "count": len(expenses_db),
        "by_category": by_category
    }
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
    <title>个人记账系统</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>💰 个人记账系统</h1>
        </header>

        <!-- 统计卡片 -->
        <div class="stats-cards">
            <div class="card">
                <h3>总支出</h3>
                <p class="amount" id="total-amount">¥0.00</p>
            </div>
            <div class="card">
                <h3>记录数</h3>
                <p class="count" id="total-count">0</p>
            </div>
        </div>

        <!-- 新增表单 -->
        <div class="form-section">
            <h2>新增支出</h2>
            <form id="expense-form">
                <div class="form-row">
                    <input type="text" id="title" placeholder="标题" required>
                    <input type="number" id="amount" placeholder="金额" step="0.01" min="0" required>
                </div>
                <div class="form-row">
                    <select id="category" required>
                        <option value="">选择分类</option>
                        <option value="餐饮">🍜 餐饮</option>
                        <option value="交通">🚗 交通</option>
                        <option value="购物">🛒 购物</option>
                        <option value="娱乐">🎮 娱乐</option>
                        <option value="居住">🏠 居住</option>
                        <option value="其他">📦 其他</option>
                    </select>
                    <input type="date" id="date">
                </div>
                <input type="text" id="note" placeholder="备注（可选）">
                <button type="submit">添加记录</button>
            </form>
        </div>

        <!-- 支出列表 -->
        <div class="list-section">
            <h2>支出记录</h2>
            <div class="filters">
                <select id="filter-category">
                    <option value="">全部分类</option>
                    <option value="餐饮">餐饮</option>
                    <option value="交通">交通</option>
                    <option value="购物">购物</option>
                    <option value="娱乐">娱乐</option>
                    <option value="居住">居住</option>
                    <option value="其他">其他</option>
                </select>
            </div>
            <div id="expense-list"></div>
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

/* 统计卡片 */
.stats-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}

.card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.card h3 {
    font-size: 14px;
    color: #666;
    margin-bottom: 8px;
}

.card .amount {
    font-size: 32px;
    font-weight: bold;
    color: #e74c3c;
}

.card .count {
    font-size: 32px;
    font-weight: bold;
    color: #3498db;
}

/* 表单 */
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

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 12px;
}

input, select {
    width: 100%;
    padding: 10px 14px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.2s;
}

input:focus, select:focus {
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
    transition: background 0.2s;
}

button:hover {
    background: #2980b9;
}

/* 列表 */
.list-section {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.list-section h2 {
    font-size: 18px;
    margin-bottom: 16px;
    color: #2c3e50;
}

.filters {
    margin-bottom: 16px;
}

.filters select {
    max-width: 200px;
}

.expense-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #eee;
}

.expense-item:last-child {
    border-bottom: none;
}

.expense-info h4 {
    font-size: 15px;
    color: #333;
}

.expense-info p {
    font-size: 12px;
    color: #999;
}

.expense-amount {
    font-size: 18px;
    font-weight: bold;
    color: #e74c3c;
}

.delete-btn {
    width: auto;
    padding: 6px 12px;
    background: #e74c3c;
    font-size: 12px;
    margin-left: 12px;
}

.delete-btn:hover {
    background: #c0392b;
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

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    loadExpenses();
    loadStats();
    
    // 表单提交
    document.getElementById('expense-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await addExpense();
    });
    
    // 筛选变化
    document.getElementById('filter-category').addEventListener('change', loadExpenses);
});

// 加载支出列表
async function loadExpenses() {
    const category = document.getElementById('filter-category').value;
    let url = `${API_BASE}/expenses`;
    if (category) url += `?category=${category}`;
    
    const res = await fetch(url);
    const expenses = await res.json();
    
    const listEl = document.getElementById('expense-list');
    if (expenses.length === 0) {
        listEl.innerHTML = '<div class="empty-state">暂无记录</div>';
        return;
    }
    
    listEl.innerHTML = expenses.map(e => `
        <div class="expense-item" data-id="${e.id}">
            <div class="expense-info">
                <h4>${e.title}</h4>
                <p>${e.category} · ${e.date}${e.note ? ' · ' + e.note : ''}</p>
            </div>
            <div style="display:flex;align-items:center;">
                <span class="expense-amount">-¥${e.amount.toFixed(2)}</span>
                <button class="delete-btn" onclick="deleteExpense('${e.id}')">删除</button>
            </div>
        </div>
    `).join('');
}

// 加载统计
async function loadStats() {
    const res = await fetch(`${API_BASE}/stats`);
    const stats = await res.json();
    
    document.getElementById('total-amount').textContent = `¥${stats.total_expenses.toFixed(2)}`;
    document.getElementById('total-count').textContent = stats.count;
}

// 新增支出
async function addExpense() {
    const data = {
        title: document.getElementById('title').value,
        amount: parseFloat(document.getElementById('amount').value),
        category: document.getElementById('category').value,
        date: document.getElementById('date').value || null,
        note: document.getElementById('note').value
    };
    
    const res = await fetch(`${API_BASE}/expenses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    if (res.ok) {
        document.getElementById('expense-form').reset();
        loadExpenses();
        loadStats();
    }
}

// 删除支出
async function deleteExpense(id) {
    if (!confirm('确定删除这条记录吗？')) return;
    
    const res = await fetch(`${API_BASE}/expenses/${id}`, { method: 'DELETE' });
    if (res.ok) {
        loadExpenses();
        loadStats();
    }
}
""",
                    "change_type": "new",
                    "language": "javascript"
                }
            ],
            "test_cases": []
        }
