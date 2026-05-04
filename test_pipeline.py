#!/usr/bin/env python3
"""端到端测试：生成前后端代码并启动服务"""

import subprocess
import sys
import os
from pipeline_engine import PipelineEngine
from models import PipelineContext, PipelineStateEnum

REQUIREMENT = "开发一个个人记账系统，包含前端界面和后端API。前端支持新增支出记录（标题、金额、分类、日期、备注）、按分类筛选、查看统计卡片（总支出、记录数）；后端提供RESTful API，支持增删改查和统计接口"

print("=" * 80)
print("🧪 端到端测试：个人记账系统（前后端）")
print(f"📝 需求: {REQUIREMENT[:60]}...")
print("=" * 80)

engine = PipelineEngine(
    skills_dir="skills",
    codebase_dir=".",
    output_dir="output"
)

engine.context = PipelineContext(
    user_query=REQUIREMENT,
    output_dir=str(engine.output_dir.resolve()),
    codebase_dir=str(engine.codebase_dir.resolve()),
    state=PipelineStateEnum.INIT
)

# 阶段1: 需求分析
engine.set_state(PipelineStateEnum.REQUIREMENT_ANALYSIS)
engine.run_requirement_analysis(REQUIREMENT)

# 阶段2: 架构设计
engine.set_state(PipelineStateEnum.ARCHITECTURE_DESIGN)
engine.run_architecture_design()

# 阶段3: 代码生成
engine.set_state(PipelineStateEnum.CODE_GENERATION)
engine.run_code_generation()

# 跳过阶段4（测试生成）和阶段5（代码评审），直接交付
print("\n⏭️  跳过测试生成和代码评审阶段")

# 阶段6: 交付集成
engine.set_state(PipelineStateEnum.DELIVERY)
engine.run_delivery()

# 保存所有产物
engine.save_outputs(engine.context.pm_result, engine.context.coder_result)

engine.set_state(PipelineStateEnum.COMPLETED)

print("\n" + "=" * 80)
print("🎉 代码生成完成！")
print(f"📂 产物目录: {engine.output_dir.resolve()}")
print("=" * 80)

# 列出产物
code_dir = engine.output_dir / "code"
print("\n📁 生成的代码文件:")
for root, dirs, files in os.walk(code_dir):
    for f in files:
        path = os.path.join(root, f)
        rel = os.path.relpath(path, code_dir)
        size = os.path.getsize(path)
        print(f"   {rel} ({size} bytes)")

# 启动后端
print("\n" + "=" * 80)
print("🚀 正在启动后端服务...")
print("=" * 80)

backend_main = code_dir / "backend" / "main.py"
if backend_main.exists():
    print(f"📍 服务地址: http://localhost:8000")
    print(f"📍 API文档: http://localhost:8000/docs")
    print(f"📍 前端页面: http://localhost:8000/")
    print("\n按 Ctrl+C 停止服务\n")
    
    subprocess.run([sys.executable, str(backend_main)])
else:
    print(f"❌ 找不到后端入口: {backend_main}")
