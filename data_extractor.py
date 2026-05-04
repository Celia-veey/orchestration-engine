import re
import json
from typing import Dict, Any, List, Optional

def extract_json_from_markdown(text: str, field_name: str) -> Optional[Any]:
    """
    从 Markdown 文本中提取指定字段的 JSON 值
    
    支持的格式：
    1. ```json
       {"field_name": ...}
       ```
    2. <json_output>{"field_name": ...}</json_output>
    3. "field_name": value (在 JSON 块中)
    
    :param text: Markdown 文本
    :param field_name: 要提取的字段名
    :return: 提取的值，如果未找到则返回 None
    """
    # 尝试从 JSON 代码块中提取
    json_blocks = re.findall(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    
    for block in json_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, dict) and field_name in data:
                return data[field_name]
        except json.JSONDecodeError:
            continue
    
    # 尝试从 <json_output> 标签中提取
    json_output_blocks = re.findall(r'<json_output>\s*(.*?)\s*</json_output>', text, re.DOTALL)
    
    for block in json_output_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, dict) and field_name in data:
                return data[field_name]
        except json.JSONDecodeError:
            continue
    
    # 尝试从整个文本中提取 JSON 对象
    try:
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            data = json.loads(brace_match.group(0))
            if isinstance(data, dict) and field_name in data:
                return data[field_name]
    except json.JSONDecodeError:
        pass
    
    return None

def extract_all_json_fields(text: str) -> Dict[str, Any]:
    """
    从 Markdown 文本中提取所有 JSON 字段
    
    :param text: Markdown 文本
    :return: 包含所有提取字段的字典
    """
    result = {}
    
    # 尝试解析整个 JSON 块
    json_blocks = re.findall(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    
    for block in json_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, dict):
                result.update(data)
        except json.JSONDecodeError:
            continue
    
    # 尝试从 <json_output> 标签中提取
    json_output_blocks = re.findall(r'<json_output>\s*(.*?)\s*</json_output>', text, re.DOTALL)
    
    for block in json_output_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, dict):
                result.update(data)
        except json.JSONDecodeError:
            continue
    
    return result

def extract_list_from_markdown(text: str, field_name: str) -> List[Any]:
    """
    从 Markdown 文本中提取列表字段
    
    :param text: Markdown 文本
    :param field_name: 要提取的字段名
    :return: 提取的列表，如果未找到则返回空列表
    """
    value = extract_json_from_markdown(text, field_name)
    if isinstance(value, list):
        return value
    return []
