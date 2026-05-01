"""
架构规范工具函数 - 供 Architect Agent 按需读取参考文档
"""
import os
from pathlib import Path

REFERENCES_DIR = Path(__file__).parent / "skills" / "references"

def read_reference_doc(topic: str) -> str:
    """
    读取架构设计规范文档
    
    :param topic: 文档主题
    :return: 文档内容
    """
    doc_map = {
        "api-design": "api-design.md",
        "db-schema": "db-schema.md",
        "auth-flow": "auth-flow.md",
        "tech-selection": "technology-selection.md",
        "environment-management": "environment-management.md",
        "testing-strategy": "testing-strategy.md",
        "django-best-practices": "django-best-practices.md",
        "release-checklist": "release-checklist.md",
    }
    
    if topic not in doc_map:
        return f"Error: Unknown topic '{topic}'. Available topics: {', '.join(doc_map.keys())}"
    
    doc_path = REFERENCES_DIR / doc_map[topic]
    
    if not doc_path.exists():
        return f"Error: Document '{doc_map[topic]}' not found at {doc_path}"
    
    try:
        return doc_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading document: {str(e)}"
