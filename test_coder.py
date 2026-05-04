#!/usr/bin/env python3
"""测试 Coder Agent 生成完整项目"""

import json
import os
import shutil
from pathlib import Path
from llm_client import LLMClient
from agents.real.coder_agent import CoderAgent

# 简单的技术方案
SIMPLE_PLAN = """
# 技术方案：待办事项列表

## 技术栈
- 后端：Python FastAPI
- 前端：HTML + JavaScript（单页面）

## 文件结构
```
todo_app/
├── main.py          # FastAPI 主入口
├── models.py        # 数据模型
├── database.py      # 数据库连接
└── index.html       # 前端页面
```

## API 设计
- GET /todos - 获取所有待办
- POST /todos - 创建待办
- PUT /todos/{id} - 更新待办
- DELETE /todos/{id} - 删除待办

## 数据模型
Todo:
- id: int
- title: str
- completed: bool
"""

def main():
    print("=" * 80)
    print("🧪 测试 Coder Agent 生成完整项目")
    print("=" * 80)
    
    # 创建临时测试目录
    test_dir = Path("test_coder_output")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # 初始化 Coder
    llm = LLMClient()
    coder = CoderAgent(llm)
    
    print("\n🔄 正在调用 Coder Agent...")
    print(f"📝 输入技术方案：\n{SIMPLE_PLAN[:200]}...\n")
    
    # 调用 Coder
    result = coder.run(SIMPLE_PLAN)
    
    print("\n📤 Coder 返回结果：")
    print(f"类型: {result.get('type')}")
    print(f"代码文件数: {len(result.get('code_files', []))}")
    print(f"测试文件数: {len(result.get('test_cases', []))}")
    
    # 打印代码文件列表
    print("\n📁 生成的代码文件：")
    for file_info in result.get("code_files", []):
        print(f"  - {file_info.get('file_path')} ({len(file_info.get('content', ''))} 字符)")
    
    # 如果没有提取到文件，打印原始内容的前 1000 字符
    if not result.get("code_files"):
        print("\n⚠️  未提取到代码文件，原始内容前 1000 字符：")
        print(result.get("content", "")[:1000])
    
    # 写入文件
    print("\n📝 正在写入文件...")
    for file_info in result.get("code_files", []):
        file_path = test_dir / file_info["file_path"]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file_info["content"], encoding="utf-8")
        print(f"  ✅ {file_path}")
    
    # 列出所有生成的文件
    print("\n📂 生成的文件列表：")
    for root, dirs, files in os.walk(test_dir):
        level = root.replace(str(test_dir), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            print(f'{subindent}{file} ({size} bytes)')
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print(f"📂 输出目录: {test_dir.resolve()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
