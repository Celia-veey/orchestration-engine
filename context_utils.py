"""
上下文摘要工具 - 防止对话历史无限增长
"""
from typing import List, Dict, Any, Optional

MAX_HISTORY_MESSAGES = 10
SUMMARY_TOKEN_ESTIMATE = 150

def summarize_history(
    messages: List[Dict[str, str]],
    max_messages: int = MAX_HISTORY_MESSAGES,
    llm_client=None
) -> List[Dict[str, str]]:
    """
    压缩对话历史，保留最近的消息
    
    :param messages: 原始消息列表
    :param max_messages: 保留的最大消息数
    :param llm_client: 可选，用于生成摘要的LLM客户端
    :return: 压缩后的消息列表
    """
    if len(messages) <= max_messages:
        return messages
    
    overflow = messages[:-max_messages]
    recent = messages[-max_messages:]
    
    summary_text = _extract_key_info(overflow)
    
    summary_message = {
        "role": "system",
        "content": f"[历史摘要] 之前的对话摘要：{summary_text}"
    }
    
    return [summary_message] + recent

def _extract_key_info(messages: List[Dict[str, str]]) -> str:
    """从消息列表提取关键信息"""
    key_points = []
    
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        if role == "user":
            if len(content) > 100:
                key_points.append(f"用户: {content[:100]}...")
            else:
                key_points.append(f"用户: {content}")
        elif role == "assistant":
            if len(content) > 150:
                key_points.append(f"助手: {content[:150]}...")
            else:
                key_points.append(f"助手: {content}")
    
    return " | ".join(key_points)

def truncate_message(content: str, max_length: int = 2000) -> str:
    """截断超长消息"""
    if len(content) <= max_length:
        return content
    return content[:max_length] + "\n...(已截断)"

def estimate_token_count(text: str) -> int:
    """估算文本的token数量（粗略估算）"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    english_words = len(text.split())
    return int(chinese_chars * 1.5 + english_words * 1.3)
