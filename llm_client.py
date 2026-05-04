import os
import json
from typing import Dict, Any, Optional, List, Callable
import openai
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    """通用大模型API客户端，支持多种大模型提供商和JSON格式输出"""
    
    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        """
        初始化LLM客户端
        :param provider: 大模型提供商，目前支持openai
        :param model: 使用的模型名称，不传则从环境变量MODEL_NAME读取，默认gpt-3.5-turbo
        """
        self.provider = provider
        self.model = model or os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        self.api_key = os.getenv(f"{provider.upper()}_API_KEY")
        self.base_url = os.getenv(f"{provider.upper()}_BASE_URL")
        
        if not self.api_key:
            raise ValueError(f"环境变量 {provider.upper()}_API_KEY 未设置")
        
        if provider == "openai":
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=300.0  # 5分钟超时，支持长代码生成
            )
        else:
            raise ValueError(f"不支持的提供商: {provider}")
    
    def chat_completion(self, 
                       messages: list[Dict[str, str]], 
                       temperature: float = 0.7,
                       max_tokens: int = 2000,
                       response_format: Optional[str] = None) -> str:
        """
        调用聊天补全API
        :param messages: 对话消息列表
        :param temperature: 温度参数，控制随机性
        :param max_tokens: 最大生成token数
        :param response_format: 响应格式，可选"json"
        :return: 模型返回的内容
        """
        try:
            extra_params = {}
            if response_format == "json":
                extra_params["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_type = type(e).__name__
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                raise TimeoutError(f"LLM API 请求超时（5分钟），请检查：\n1. API 服务是否正常\n2. max_tokens={max_tokens} 是否过大\n3. 网络连接是否稳定") from e
            raise RuntimeError(f"LLM API 请求失败 ({error_type}): {str(e)}") from e
    
    def chat_completion_text(self,
                           messages: list[Dict[str, str]],
                           temperature: float = 0.7,
                           max_tokens: int = 2000) -> str:
        """
        调用聊天补全API并返回纯文本结果
        :param messages: 对话消息列表
        :param temperature: 温度参数，控制随机性
        :param max_tokens: 最大生成token数
        :return: 模型返回的纯文本内容
        """
        return self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def chat_completion_json(self,
                           messages: list[Dict[str, str]],
                           temperature: float = 0.7,
                           max_tokens: int = 2000) -> Dict[str, Any]:
        """
        调用聊天补全API并返回JSON格式结果
        :param messages: 对话消息列表
        :param temperature: 温度参数，控制随机性
        :param max_tokens: 最大生成token数
        :return: 解析后的JSON对象
        """
        # 构建强制 JSON 输出指令（同时加到 system 和 user message）
        json_instruction = """

IMPORTANT OUTPUT RULES:
1. You MUST wrap your ENTIRE response inside <json_output>...</json_output> tags
2. DO NOT output any text, diagrams, explanations, or markdown outside these tags
3. The content inside the tags MUST be valid JSON only
4. Violating these rules will cause system failure"""
        
        modified_messages = []
        for i, msg in enumerate(messages):
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                # System prompt: 追加指令
                modified_messages.append({"role": "system", "content": content + json_instruction})
            elif role == "user" and i == len(messages) - 1:
                # 最后一个 user message: 也追加指令（双重约束）
                modified_messages.append({"role": "user", "content": content + "\n\nRemember: Output ONLY valid JSON wrapped in <json_output>...</json_output> tags."})
            else:
                modified_messages.append(msg)
        
        content = self.chat_completion(
            messages=modified_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format="json"
        )
        
        # 提取 <json_output> 标签内的内容
        import re
        json_match = re.search(r'<json_output>\s*(.*?)\s*</json_output>', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        else:
            # 兜底1：尝试提取 markdown 代码块
            code_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if code_match:
                content = code_match.group(1)
            else:
                # 兜底2：尝试直接查找第一个 { 到最后一个 } 之间的内容
                brace_match = re.search(r'\{.*\}', content, re.DOTALL)
                if brace_match:
                    content = brace_match.group(0)
        
        try:
            result = json.loads(content)
            if not isinstance(result, dict):
                raise ValueError(f"模型返回的JSON不是字典类型，而是: {type(result).__name__}\n返回内容前500字符: {content[:500]}")
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"模型返回的JSON格式解析失败: {str(e)}\n返回内容前500字符: {content[:500]}") from e
