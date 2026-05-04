#!/usr/bin/env python3
"""
Debug test: Check full conversation flow with tool calling
"""

import json
from pipeline_engine import PipelineEngine
from reference_tools import read_reference_doc

template_report = """# Todo List API - Requirement Document

## Core Features
1. User Authentication - Registration with email/password, JWT login
2. Todo CRUD - Create, read, update, delete todos
3. Authorization - Users can only access their own todos
"""

print('='*80)
print('🔍 Debug: Full Conversation Flow')
print('='*80)

engine = PipelineEngine()

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_reference_doc",
            "description": "读取架构设计规范文档",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": ["api-design", "db-schema", "auth-flow", "tech-selection", "environment-management", "testing-strategy", "django-best-practices", "release-checklist"],
                        "description": "规范文档主题"
                    }
                },
                "required": ["topic"]
            }
        }
    }
]

api_designer_prompt = engine.skill_manager.get_skill_prompt("architect-api-designer")
messages = [
    {"role": "system", "content": api_designer_prompt},
    {"role": "user", "content": f"需求文档：\n{template_report}"}
]

print('\n📡 Calling API Designer with tool support...')
result = engine.llm_client.chat_completion_with_tools(
    messages=messages,
    tools=tools,
    tool_functions={"read_reference_doc": read_reference_doc},
    temperature=0.2,
    max_tokens=8000,
    response_format="json"
)

print(f'\n✅ Final response length: {len(result)} chars')
print(f'✅ Final response preview: {result[:1000]}...')

# Try to parse as JSON
try:
    parsed = json.loads(result)
    print(f'\n✅ JSON parsed successfully!')
    print(f'Keys: {list(parsed.keys())}')
    print(f'API endpoints: {len(parsed.get("api_endpoints", []))}')
    if parsed.get("api_endpoints"):
        for ep in parsed["api_endpoints"][:5]:
            print(f'  {ep.get("method", "?")} {ep.get("path", "?")} - {ep.get("description", "?")}')
    else:
        print(f'\n⚠️ Full JSON output:\n{json.dumps(parsed, indent=2, ensure_ascii=False)[:2000]}')
except json.JSONDecodeError as e:
    print(f'\n❌ JSON parse error: {e}')

# Show conversation history
print(f'\n📜 Conversation history ({len(messages)} messages):')
for i, msg in enumerate(messages):
    role = msg.get("role", "?")
    content_preview = str(msg.get("content", ""))[:150]
    print(f'  [{i}] {role}: {content_preview}...')

print('\n' + '='*80)
