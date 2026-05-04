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
                base_url=self.base_url
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
        content = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format="json"
        )
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"模型返回的JSON格式解析失败: {str(e)}\n返回内容: {content}") from e
