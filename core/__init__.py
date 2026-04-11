"""
核心业务模块
"""
from .excel_processor import ExcelProcessor
from .ppt_generator import PPTGenerator
from .model_manager import ModelManager, model_manager, MODEL_PROVIDERS
from .group_chat_manager import GroupChatManager, group_chat_manager, ROLE_TEMPLATES

__all__ = [
    "ExcelProcessor",
    "PPTGenerator",
    "ModelManager",
    "model_manager",
    "MODEL_PROVIDERS",
    "GroupChatManager",
    "group_chat_manager",
    "ROLE_TEMPLATES",
]
