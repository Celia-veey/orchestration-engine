import asyncio
import uuid
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from pathlib import Path
import json

# 导入流水线引擎
from pipeline_engine import PipelineEngine
from models import PipelineStateEnum, PipelineContext

# 初始化FastAPI应用
app = FastAPI(
    title="DevFlow Engine API",
    description="AI驱动的需求交付流程引擎RESTful API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 请求/响应模型定义
class PipelineTriggerRequest(BaseModel):
    requirement: str = Field(description="用户需求描述", examples=["开发一个用户管理系统"])
    codebase_dir: Optional[str] = Field(default=".", description="目标代码库目录")
    output_dir: Optional[str] = Field(default="output", description="产物输出目录")

class PipelineTriggerResponse(BaseModel):
    pipeline_id: str = Field(description="流水线唯一ID")
    status: str = Field(description="状态")
    message: str = Field(description="响应消息")

class ApprovalRequest(BaseModel):
    action: str = Field(description="审批动作：approve/reject", examples=["approve"])
    reason: Optional[str] = Field(default="", description="拒绝理由（reject时必填）")

class PipelineStatusResponse(BaseModel):
    pipeline_id: str = Field(description="流水线唯一ID")
    state: str = Field(description="当前状态")
    state_display: str = Field(description="状态中文显示")
    created_at: str = Field(description="创建时间")
    updated_at: str = Field(description="更新时间")
    user_query: str = Field(description="用户原始需求")
    context: Optional[Dict[str, Any]] = Field(description="完整上下文数据（可选）")
    current_step: Optional[str] = Field(description="当前步骤说明")

class PipelineListItem(BaseModel):
    pipeline_id: str = Field(description="流水线唯一ID")
    state: str = Field(description="当前状态")
    state_display: str = Field(description="状态中文显示")
    created_at: str = Field(description="创建时间")
    user_query: str = Field(description="用户需求摘要")

class PipelineListResponse(BaseModel):
    total: int = Field(description="总数量")
    pipelines: List[PipelineListItem] = Field(description="流水线列表")

# 审批事件同步原语
class ApprovalEvent:
    def __init__(self):
        self.event = asyncio.Event()
        self.action: Optional[str] = None
        self.reason: Optional[str] = None
    
    def set_approval(self, action: str, reason: str = ""):
        self.action = action
        self.reason = reason
        self.event.set()
    
    async def wait(self):
        await self.event.wait()
        return self.action, self.reason

# 流水线实例管理器
class PipelineManager:
    def __init__(self):
        self.pipelines: Dict[str, PipelineEngine] = {}
        self.approval_events: Dict[str, ApprovalEvent] = {}
        self.pipeline_contexts: Dict[str, PipelineContext] = {}
    
    def create_pipeline(self, requirement: str, codebase_dir: str = ".", output_dir: str = "output") -> str:
        """创建新的流水线实例"""
        engine = PipelineEngine(codebase_dir=codebase_dir, output_dir=output_dir)
        pipeline_id = str(uuid.uuid4())
        self.pipelines[pipeline_id] = engine
        return pipeline_id
    
    def get_pipeline(self, pipeline_id: str) -> Optional[PipelineEngine]:
        """获取流水线实例"""
        return self.pipelines.get(pipeline_id)
    
    def get_context(self, pipeline_id: str) -> Optional[PipelineContext]:
        """获取流水线上下文"""
        return self.pipeline_contexts.get(pipeline_id)
    
    def update_context(self, pipeline_id: str, context: PipelineContext):
        """更新流水线上下文"""
        self.pipeline_contexts[pipeline_id] = context
    
    def create_approval_event(self, pipeline_id: str) -> ApprovalEvent:
        """创建审批等待事件"""
        event = ApprovalEvent()
        self.approval_events[pipeline_id] = event
        return event
    
    def get_approval_event(self, pipeline_id: str) -> Optional[ApprovalEvent]:
        """获取审批事件"""
        return self.approval_events.get(pipeline_id)
    
    def remove_approval_event(self, pipeline_id: str):
        """移除审批事件"""
        if pipeline_id in self.approval_events:
            del self.approval_events[pipeline_id]
    
    def list_pipelines(self) -> List[Dict[str, Any]]:
        """获取所有流水线列表"""
        result = []
        for pipeline_id, context in self.pipeline_contexts.items():
            result.append({
                "pipeline_id": pipeline_id,
                "state": context.state.value,
                "state_display": context.state.get_state_display(),
                "created_at": context.created_at,
                "user_query": context.user_query[:100] + "..." if len(context.user_query) > 100 else context.user_query
            })
        return result

# 全局管理器实例
pipeline_manager = PipelineManager()

# 改造流水线引擎，支持异步审批
async def run_pipeline_async(pipeline_id: str, requirement: str):
    """异步运行流水线"""
    engine = pipeline_manager.get_pipeline(pipeline_id)
    if not engine:
        return
    
    try:
        # 初始化上下文
        engine.context = PipelineContext(
            user_query=requirement,
            output_dir=str(engine.output_dir.resolve()),
            codebase_dir=str(engine.codebase_dir.resolve()),
            state=PipelineStateEnum.INIT
        )
        engine.context.save_to_file(engine.output_dir / "context.json")
        pipeline_manager.update_context(pipeline_id, engine.context)
        
        # 阶段1：需求分析
        engine.set_state(PipelineStateEnum.REQUIREMENT_ANALYSIS)
        if not engine.run_requirement_analysis(requirement):
            engine.set_state(PipelineStateEnum.FAILED)
            pipeline_manager.update_context(pipeline_id, engine.context)
            return
        pipeline_manager.update_context(pipeline_id, engine.context)
        
        # 阶段2：方案设计 + 人工检查点1
        while True:
            engine.set_state(PipelineStateEnum.ARCHITECTURE_DESIGN)
            if not engine.run_architecture_design():
                engine.set_state(PipelineStateEnum.FAILED)
                pipeline_manager.update_context(pipeline_id, engine.context)
                return
            pipeline_manager.update_context(pipeline_id, engine.context)
            
            # 等待审批
            engine.set_state(PipelineStateEnum.HUMAN_APPROVAL_1)
            pipeline_manager.update_context(pipeline_id, engine.context)
            
            approval_event = pipeline_manager.create_approval_event(pipeline_id)
            action, reason = await approval_event.wait()
            pipeline_manager.remove_approval_event(pipeline_id)
            
            if action == 'approve':
                engine.context.update(approval_1_status='approved')
                break
            elif action == 'reject':
                engine.context.update(
                    approval_1_status='rejected',
                    approval_1_reason=reason,
                    architect_result=None,
                    plan_md=None,
                    plan_md_path=None,
                    file_change_list=None,
                    api_design=None
                )
                # 重新运行需求分析
                if not engine.run_requirement_analysis(requirement):
                    engine.set_state(PipelineStateEnum.FAILED)
                    pipeline_manager.update_context(pipeline_id, engine.context)
                    return
                pipeline_manager.update_context(pipeline_id, engine.context)
        
        # 阶段3：代码生成
        engine.set_state(PipelineStateEnum.CODE_GENERATION)
        if not engine.run_code_generation():
            engine.set_state(PipelineStateEnum.FAILED)
            pipeline_manager.update_context(pipeline_id, engine.context)
            return
        pipeline_manager.update_context(pipeline_id, engine.context)
        
        # 阶段4：测试生产
        engine.set_state(PipelineStateEnum.TEST_GENERATION)
        if not engine.run_test_generation():
            engine.set_state(PipelineStateEnum.FAILED)
            pipeline_manager.update_context(pipeline_id, engine.context)
            return
        pipeline_manager.update_context(pipeline_id, engine.context)
        
        # 阶段5：代码评审 + 人工检查点2
        while True:
            engine.set_state(PipelineStateEnum.CODE_REVIEW)
            if not engine.run_code_review():
                engine.set_state(PipelineStateEnum.FAILED)
                pipeline_manager.update_context(pipeline_id, engine.context)
                return
            pipeline_manager.update_context(pipeline_id, engine.context)
            
            # 等待审批
            engine.set_state(PipelineStateEnum.HUMAN_APPROVAL_2)
            pipeline_manager.update_context(pipeline_id, engine.context)
            
            approval_event = pipeline_manager.create_approval_event(pipeline_id)
            action, reason = await approval_event.wait()
            pipeline_manager.remove_approval_event(pipeline_id)
            
            if action == 'approve':
                engine.context.update(approval_2_status='approved')
                break
            elif action == 'reject':
                engine.context.update(
                    approval_2_status='rejected',
                    approval_2_reason=reason,
                    reviewer_result=None,
                    eval_report_path=None,
                    eval_report_md=None,
                    qa_result=None,
                    test_cases=None,
                    test_result=None
                )
                # 重新运行代码生成
                if not engine.run_code_generation():
                    engine.set_state(PipelineStateEnum.FAILED)
                    pipeline_manager.update_context(pipeline_id, engine.context)
                    return
                pipeline_manager.update_context(pipeline_id, engine.context)
                
                # 重新运行测试生成
                if not engine.run_test_generation():
                    engine.set_state(PipelineStateEnum.FAILED)
                    pipeline_manager.update_context(pipeline_id, engine.context)
                    return
                pipeline_manager.update_context(pipeline_id, engine.context)
        
        # 阶段6：交付集成
        engine.set_state(PipelineStateEnum.DELIVERY)
        if not engine.run_delivery():
            engine.set_state(PipelineStateEnum.FAILED)
            pipeline_manager.update_context(pipeline_id, engine.context)
            return
        pipeline_manager.update_context(pipeline_id, engine.context)
        
        # 保存所有输出
        engine.save_outputs(engine.context.pm_result, engine.context.coder_result)
        
        engine.set_state(PipelineStateEnum.COMPLETED)
        pipeline_manager.update_context(pipeline_id, engine.context)
        
    except Exception as e:
        if engine.context:
            engine.set_state(PipelineStateEnum.FAILED)
            pipeline_manager.update_context(pipeline_id, engine.context)
        print(f"流水线 {pipeline_id} 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()

# API接口实现
@app.post("/pipeline/trigger", response_model=PipelineTriggerResponse, summary="触发新流水线")
async def trigger_pipeline(request: PipelineTriggerRequest, background_tasks: BackgroundTasks):
    """
    触发新的AI需求交付流水线
    - **requirement**: 用户需求描述（必填）
    - **codebase_dir**: 目标代码库目录（可选，默认当前目录）
    - **output_dir**: 产物输出目录（可选，默认output目录）
    """
    pipeline_id = pipeline_manager.create_pipeline(
        requirement=request.requirement,
        codebase_dir=request.codebase_dir,
        output_dir=request.output_dir
    )
    
    # 后台异步运行流水线
    background_tasks.add_task(run_pipeline_async, pipeline_id, request.requirement)
    
    return PipelineTriggerResponse(
        pipeline_id=pipeline_id,
        status="running",
        message="流水线已成功触发，正在后台运行"
    )

@app.get("/pipeline/{pipeline_id}/status", response_model=PipelineStatusResponse, summary="查询流水线状态")
async def get_pipeline_status(pipeline_id: str, include_context: bool = False):
    """
    查询指定流水线的运行状态和上下文
    - **pipeline_id**: 流水线唯一ID（必填）
    - **include_context**: 是否返回完整上下文数据（可选，默认false）
    """
    context = pipeline_manager.get_context(pipeline_id)
    if not context:
        raise HTTPException(status_code=404, detail=f"流水线 {pipeline_id} 不存在")
    
    # 确定当前步骤说明
    step_map = {
        PipelineStateEnum.INIT: "初始化中",
        PipelineStateEnum.REQUIREMENT_ANALYSIS: "需求分析中",
        PipelineStateEnum.ARCHITECTURE_DESIGN: "架构设计中",
        PipelineStateEnum.HUMAN_APPROVAL_1: "等待技术方案审批",
        PipelineStateEnum.CODE_GENERATION: "代码生成中",
        PipelineStateEnum.TEST_GENERATION: "测试生成中",
        PipelineStateEnum.CODE_REVIEW: "代码评审中",
        PipelineStateEnum.HUMAN_APPROVAL_2: "等待代码评审结果审批",
        PipelineStateEnum.DELIVERY: "交付集成中",
        PipelineStateEnum.COMPLETED: "执行完成",
        PipelineStateEnum.FAILED: "执行失败"
    }
    
    response = PipelineStatusResponse(
        pipeline_id=pipeline_id,
        state=context.state.value,
        state_display=context.state.get_state_display(),
        created_at=context.created_at,
        updated_at=context.updated_at,
        user_query=context.user_query,
        current_step=step_map.get(context.state, "未知状态")
    )
    
    if include_context:
        response.context = json.loads(context.to_json())
    
    return response

@app.post("/pipeline/{pipeline_id}/approve", summary="提交审批结果")
async def submit_approval(pipeline_id: str, request: ApprovalRequest):
    """
    提交人工审批结果
    - **pipeline_id**: 流水线唯一ID（必填）
    - **action**: 审批动作，可选值：approve（通过）/ reject（打回）（必填）
    - **reason**: 拒绝理由，action为reject时必填
    """
    event = pipeline_manager.get_approval_event(pipeline_id)
    if not event:
        # 检查流水线是否存在
        context = pipeline_manager.get_context(pipeline_id)
        if not context:
            raise HTTPException(status_code=404, detail=f"流水线 {pipeline_id} 不存在")
        # 检查是否处于审批状态
        if context.state not in [PipelineStateEnum.HUMAN_APPROVAL_1, PipelineStateEnum.HUMAN_APPROVAL_2]:
            raise HTTPException(status_code=400, detail=f"流水线 {pipeline_id} 当前不处于审批状态")
        raise HTTPException(status_code=400, detail=f"流水线 {pipeline_id} 没有待处理的审批请求")
    
    if request.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="action参数只能是approve或reject")
    
    if request.action == "reject" and not request.reason:
        raise HTTPException(status_code=400, detail="拒绝时必须填写reason参数")
    
    event.set_approval(request.action, request.reason)
    
    return {
        "status": "success",
        "message": f"审批结果已提交：{'通过' if request.action == 'approve' else '打回'}"
    }

@app.get("/pipeline/list", response_model=PipelineListResponse, summary="查询流水线列表")
async def list_pipelines():
    """获取所有流水线的简要信息列表"""
    pipelines = pipeline_manager.list_pipelines()
    return PipelineListResponse(
        total=len(pipelines),
        pipelines=[PipelineListItem(**p) for p in pipelines]
    )

@app.get("/", summary="API根路径")
async def root():
    return {
        "name": "DevFlow Engine API",
        "version": "1.0.0",
        "description": "AI驱动的需求交付流程引擎",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
