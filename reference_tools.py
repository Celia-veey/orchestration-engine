"""
架构规范工具函数 - 供 Agent 按需读取参考文档
"""
import os
import re
from pathlib import Path

REFERENCES_DIR = Path(__file__).parent / "Multi-Agents" / "agents" / "references"
SKILLS_DIR = Path(__file__).parent / "Multi-Agents" / "skills"
MAX_DOC_LENGTH = 2000  # 截断文档长度，避免消耗过多 token

def read_reference_doc(topic: str, section: str = None) -> str:
    """
    读取参考文档或 Skill 文档（截断版本，避免消耗过多 token）
    
    :param topic: 文档主题或 Skill 名称
    :param section: 可选的章节名称，只返回该章节内容
    :return: 文档内容（截断到 MAX_DOC_LENGTH 字符）
    """
    # 参考文档（无 YAML front matter）
    ref_map = {
        "ears-requirements": "ears-requirements.md",
        "three-layer-architecture": "three-layer-architecture.md",
        "adr-template": "adr-template.md",
        "nfr-checklist": "nfr-checklist.md",
        "git-conventions": "git-conventions.md",
        "api-design": "api-design.md",
        "db-schema": "db-schema.md",
        "auth-flow": "auth-flow.md",
        "tech-selection": "technology-selection.md",
        "environment-management": "environment-management.md",
        "testing-strategy": "testing-strategy.md",
        "django-best-practices": "django-best-practices.md",
        "release-checklist": "release-checklist.md",
    }
    
    # Skill 文档（有 YAML front matter）
    skill_map = {
        # 代码审查与交付
        "code-reviewer": "Multi-Agents/skills/Code_Reviewer/SKILL.md",
        "github-pr-delivery": "Multi-Agents/skills/GitHub_PR_Delivery/SKILL.md",
        # 前端设计
        "frontend-design": "Multi-Agents/skills/frontend-design/SKILL.md",
        # 架构改进
        "improve-codebase-architecture": "Multi-Agents/skills/improve-codebase-architecture/SKILL.md",
    }
    
    all_topics = list(ref_map.keys()) + list(skill_map.keys())
    
    if topic in ref_map:
        doc_path = REFERENCES_DIR / ref_map[topic]
    elif topic in skill_map:
        doc_path = Path(__file__).parent / skill_map[topic]
    else:
        return f"Error: Unknown topic '{topic}'. Available topics: {', '.join(all_topics)}"
    
    if not doc_path.exists():
        return f"Error: Document '{doc_path}' not found"
    
    try:
        content = doc_path.read_text(encoding="utf-8")
        
        # 移除 YAML 头部（仅对 Skill 文档）
        if topic in skill_map:
            content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL).strip()
        
        # 如果指定了 section，只返回该章节
        if section:
            content = _extract_section(content, section)
        
        # 截断到最大长度
        if len(content) > MAX_DOC_LENGTH:
            content = content[:MAX_DOC_LENGTH] + "\n\n... (document truncated, request specific sections if needed)"
        
        return content
    except Exception as e:
        return f"Error reading document: {str(e)}"

def _extract_section(content: str, section: str) -> str:
    """提取文档中的特定章节"""
    lines = content.split('\n')
    in_section = False
    section_lines = []
    current_heading = None
    
    for line in lines:
        if line.startswith('# '):
            current_heading = line[2:].strip().lower()
            if section.lower() in current_heading:
                in_section = True
                section_lines.append(line)
                continue
            elif in_section:
                # 到达下一个顶级章节，结束
                break
            else:
                continue
        
        if in_section:
            section_lines.append(line)
    
    if not section_lines:
        return f"Section '{section}' not found. Available sections:\n" + "\n".join(
            [l[2:] for l in lines if l.startswith('# ')]
        )
    
    return '\n'.join(section_lines)
