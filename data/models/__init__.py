"""
数据模型模块
"""
from .department import Department
from .employee import Employee
from .ai_config import AIModelConfig, ChatMessage, ChatSession
from .group_chat import GroupChatSession, GroupChatParticipant, GroupChatMessage

__all__ = [
    "Department", "Employee",
    "AIModelConfig", "ChatMessage", "ChatSession",
    "GroupChatSession", "GroupChatParticipant", "GroupChatMessage"
]
