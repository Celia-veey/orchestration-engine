"""
文件操作工具 - 供 Coder Agent 直接写入代码文件
"""
import os
from pathlib import Path
from typing import Dict, Any, List

def write_file(file_path: str, content: str, codebase_dir: str = ".") -> Dict[str, Any]:
    """
    写入文件到指定路径
    
    :param file_path: 文件路径（相对 codebase_dir）
    :param content: 文件内容
    :param codebase_dir: 代码库根目录
    :return: 写入结果
    """
    try:
        abs_path = Path(codebase_dir) / file_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        
        return {
            "status": "success",
            "file_path": str(abs_path),
            "message": f"文件已写入: {abs_path}"
        }
    except Exception as e:
        return {
            "status": "error",
            "file_path": file_path,
            "message": f"写入文件失败: {str(e)}"
        }

def write_files(files: List[Dict[str, str]], codebase_dir: str = ".") -> List[Dict[str, Any]]:
    """
    批量写入文件
    
    :param files: 文件列表，每个元素包含 {"file_path": "...", "content": "..."}
    :param codebase_dir: 代码库根目录
    :return: 每个文件的写入结果
    """
    results = []
    for file_info in files:
        result = write_file(
            file_path=file_info["file_path"],
            content=file_info["content"],
            codebase_dir=codebase_dir
        )
        results.append(result)
    return results
