"""
聊天界面组件模块
"""

import streamlit as st
from typing import List, Dict, Optional
from modules.utils.state import HTPState, add_chat_message


def render_chat_interface(
    chat_messages: List[Dict[str, str]],
    height: int = 400,
    show_input: bool = True,
    input_placeholder: str = "请分享您的感受和想法...",
) -> Optional[str]:
    """
    渲染聊天界面

    Args:
        chat_messages: 聊天消息列表
        height: 聊天容器高度
        show_input: 是否显示输入框
        input_placeholder: 输入框占位符文本

    Returns:
        Optional[str]: 用户输入的文本，如果没有输入则返回 None
    """
    # 显示聊天历史
    chat_container = st.container(height=height)

    with chat_container:
        for message in chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 聊天输入
    if show_input:
        user_input = st.chat_input(input_placeholder)
        return user_input

    return None


def add_message_to_chat(state: HTPState, role: str, content: str) -> HTPState:
    """
    添加消息到聊天记录

    Args:
        state: HTP 状态
        role: 角色 ('user' 或 'assistant')
        content: 消息内容

    Returns:
        HTPState: 更新后的状态
    """
    return add_chat_message(state, role, content)


def format_assistant_message(
    message_type: str, content: str, category: str = None
) -> str:
    """
    格式化助手消息

    Args:
        message_type: 消息类型 ('question', 'analysis', 'completion')
        content: 消息内容
        category: 类别（如果适用）

    Returns:
        str: 格式化后的消息
    """
    if message_type == "question" and category:
        category_names = {
            "person": "👤 人物",
            "house": "🏠 房子",
            "tree": "🌳 树木",
            "overall": "🎨 整体感受",
        }
        category_display = category_names.get(category, category)
        return f"**{category_display} 相关问题：**\n\n{content}"

    elif message_type == "analysis":
        return f"✅ 分析完成！\n\n**分析结果：**\n{content}"

    elif message_type == "completion":
        return f"✅ {content}"

    else:
        return content


def show_chat_statistics(chat_messages: List[Dict[str, str]]):
    """
    显示聊天统计信息

    Args:
        chat_messages: 聊天消息列表
    """
    if not chat_messages:
        st.info("暂无聊天记录")
        return

    user_messages = [msg for msg in chat_messages if msg["role"] == "user"]
    assistant_messages = [msg for msg in chat_messages if msg["role"] == "assistant"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("总消息数", len(chat_messages))

    with col2:
        st.metric("用户消息", len(user_messages))

    with col3:
        st.metric("助手消息", len(assistant_messages))


def export_chat_history(chat_messages: List[Dict[str, str]]) -> str:
    """
    导出聊天历史为文本格式

    Args:
        chat_messages: 聊天消息列表

    Returns:
        str: 格式化的聊天历史文本
    """
    if not chat_messages:
        return "暂无聊天记录"

    chat_text = "HTP 对话记录\n" + "=" * 50 + "\n\n"

    for i, message in enumerate(chat_messages, 1):
        role_display = "用户" if message["role"] == "user" else "助手"
        chat_text += f"{i}. {role_display}：\n{message['content']}\n\n"

    return chat_text
