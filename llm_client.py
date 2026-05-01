import os
import json
from typing import Dict, Any, Optional, List, Callable
import openai
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    """通用大模型API客户端，支持多种大模型提供商、JSON格式输出和Tool Calling"""
    
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
            import httpx
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=httpx.Timeout(timeout=600.0, connect=30.0)
            )
        else:
            raise ValueError(f"不支持的提供商: {provider}")
    
    def chat_completion(self, 
                       messages: list[Dict[str, str]], 
                       temperature: float = 0.7,
                       max_tokens: int = 2000,
                       response_format: Optional[str] = None,
                       tools: Optional[List[Dict]] = None,
                       tool_choice: Optional[str] = None) -> str:
        """
        调用聊天补全API
        :param messages: 对话消息列表
        :param temperature: 温度参数，控制随机性
        :param max_tokens: 最大生成token数
        :param response_format: 响应格式，可选"json"
        :param tools: 工具定义列表（Tool Calling）
        :param tool_choice: 工具选择策略（"auto"/"required"/"none"）
        :return: 模型返回的内容
        """
        extra_params = {}
        if response_format == "json":
            extra_params["response_format"] = {"type": "json_object"}
        
        if tools:
            extra_params["tools"] = tools
            if tool_choice:
                extra_params["tool_choice"] = tool_choice
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **extra_params
        )
        
        return response.choices[0].message.content.strip()
    
    def chat_completion_with_tools(self,
                                   messages: list[Dict[str, str]],
                                   tools: List[Dict],
                                   tool_functions: Dict[str, Callable],
                                   temperature: float = 0.7,
                                   max_tokens: int = 2000,
                                   response_format: Optional[str] = None) -> str:
        """
        调用聊天补全API并支持Tool Calling循环
        支持两种模式：
        1. 原生Tool Calling（OpenAI兼容API）
        2. JSON格式模拟Tool Calling（模型返回JSON表示要调用工具）
        
        注意：当使用 tools 时，不使用 response_format=json_object，
        因为两者同时使用会导致模型混淆，把工具调用作为JSON文本返回。
        最终输出时再要求JSON格式。
        
        :param messages: 对话消息列表
        :param tools: 工具定义列表
        :param tool_functions: 工具名称到函数的映射
        :param temperature: 温度参数
        :param max_tokens: 最大生成token数
        :param response_format: 响应格式（仅在最终输出时生效）
        :return: 模型最终返回的内容
        """
        extra_params = {}
        extra_params["tools"] = tools
        extra_params["tool_choice"] = "auto"
        
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params
            )
            
            choice = response.choices[0].message
            
            # 模式1：原生Tool Calling
            if choice.tool_calls:
                messages.append(choice)
                
                for tool_call in choice.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if function_name in tool_functions:
                        result = tool_functions[function_name](**function_args)
                    else:
                        result = f"Error: Unknown function '{function_name}'"
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False) if isinstance(result, dict) else str(result)
                    })
                
                extra_params.pop("tool_choice", None)
                continue
            
            # 模式2：JSON格式模拟Tool Calling
            if choice.content:
                content = choice.content.strip()
                try:
                    parsed = json.loads(content)
                    
                    # 格式1: {"type": "tool_call", "tool_name": "...", "arguments": {...}}
                    if parsed.get("type") == "tool_call" and "tool_name" in parsed:
                        function_name = parsed["tool_name"]
                        function_args = parsed.get("arguments", {})
                    
                    # 格式2: {"tool_calls": [{"name": "...", "arguments": {...}}]}
                    elif "tool_calls" in parsed and isinstance(parsed["tool_calls"], list) and len(parsed["tool_calls"]) > 0:
                        tc = parsed["tool_calls"][0]
                        function_name = tc.get("name", "")
                        function_args = tc.get("arguments", {})
                    
                    else:
                        # 不是工具调用，是最终输出
                        # 如果要求JSON格式，尝试解析
                        if response_format == "json":
                            return content
                        return content
                    
                    # 执行工具调用
                    if function_name in tool_functions:
                        result = tool_functions[function_name](**function_args)
                    else:
                        result = f"Error: Unknown function '{function_name}'"
                    
                    # 将工具调用和结果添加到消息历史
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": f"Tool '{function_name}' executed successfully. Result:\n{json.dumps(result, ensure_ascii=False) if isinstance(result, dict) else str(result)}\n\nNow continue with your original task using this information."
                    })
                    
                    # 工具调用后，移除tools，让模型直接输出最终结果
                    extra_params.pop("tool_choice", None)
                    extra_params.pop("tools", None)
                    
                    # 如果要求JSON格式，现在加上
                    if response_format == "json":
                        extra_params["response_format"] = {"type": "json_object"}
                        # 添加提示
                        messages.append({
                            "role": "user",
                            "content": "Please output your final result in valid JSON format."
                        })
                    
                    continue
                except json.JSONDecodeError:
                    pass
                
                # 不是JSON，直接返回
                return content
        
        return ""
    
    def chat_completion_json(self,
                           messages: list[Dict[str, str]],
                           temperature: float = 0.7,
                           max_tokens: int = 2000,
                           tools: Optional[List[Dict]] = None,
                           tool_functions: Optional[Dict[str, Callable]] = None) -> Dict[str, Any]:
        """
        调用聊天补全API并返回JSON格式结果
        :param messages: 对话消息列表
        :param temperature: 温度参数，控制随机性
        :param max_tokens: 最大生成token数
        :param tools: 工具定义列表（可选）
        :param tool_functions: 工具函数映射（可选）
        :return: 解析后的JSON对象
        """
        if tools and tool_functions:
            content = self.chat_completion_with_tools(
                messages=messages,
                tools=tools,
                tool_functions=tool_functions,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format="json"
            )
        else:
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
