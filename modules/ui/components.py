"""
通用 UI 组件模块
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
from modules.utils.state import (
    HTPState,
    get_stage_display_name,
    get_category_display_name,
)


def render_progress_sidebar(state: HTPState):
    """
    渲染进度侧边栏

    Args:
        state: HTP 状态
    """
    st.header("📊 分析进度")

    stages = {
        "image_analysis": "🔍 图像分析",
        "qa_loop": "💬 问答阶段",
        "category_analysis": "📝 类别分析",
        "comprehensive": "🧠 综合分析",
        "dass21": "📝 DASS-21 量表",
        "final_report": "📊 完整报告",
    }

    for stage_key, stage_name in stages.items():
        status = "✅" if state["stage_progress"].get(stage_key, False) else "⏳"
        current = "👉" if state["current_stage"] == stage_key else ""
        st.write(f"{status} {current} {stage_name}")


def render_session_statistics(state: HTPState):
    """
    渲染会话统计信息

    Args:
        state: HTP 状态
    """
    st.subheader("📈 会话统计")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("问答轮次", state.get("total_questions_asked", 0))
        st.metric("已完成类别", len(state.get("categories_covered", [])))

    with col2:
        chat_messages = len(state.get("chat_messages", []))
        st.metric("聊天消息", chat_messages)

        if state.get("analysis_timestamp"):
            timestamp = datetime.fromisoformat(state["analysis_timestamp"])
            st.metric("最后更新", timestamp.strftime("%H:%M"))


def render_category_status(state: HTPState):
    """
    渲染类别完成状态

    Args:
        state: HTP 状态
    """
    st.subheader("📋 类别状态")

    categories = ["person", "house", "tree", "overall"]
    categories_covered = state.get("categories_covered", [])
    current_category = state.get("current_category")

    for category in categories:
        category_display = get_category_display_name(category)

        if category in categories_covered:
            status = "✅ 已完成"
        elif category == current_category:
            status = "🔄 进行中"
        else:
            status = "⏳ 待处理"

        st.write(f"{category_display}: {status}")


def render_debug_panel(state: HTPState):
    """
    渲染调试面板

    Args:
        state: HTP 状态
    """
    st.subheader("🐛 Debug 信息")

    with st.expander("状态详情", expanded=False):
        st.json(dict(state), expanded=False)

    # 快速操作
    st.subheader("⚡ 快速操作")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("清空聊天记录", use_container_width=True):
            state["chat_messages"] = []
            st.rerun()

    with col2:
        if st.button("重置问答进度", use_container_width=True):
            state["categories_covered"] = []
            state["current_category"] = None
            state["is_qa_complete"] = False
            state["current_question"] = None
            st.rerun()


def render_file_upload(
    label: str = "选择图像文件", types: List[str] = None, help_text: str = None
) -> Optional[Any]:
    """
    渲染文件上传组件

    Args:
        label: 上传标签
        types: 允许的文件类型
        help_text: 帮助文本

    Returns:
        上传的文件对象或 None
    """
    if types is None:
        types = ["png", "jpg", "jpeg"]

    if help_text is None:
        help_text = "请上传您的房-树-人绘画作品"

    return st.file_uploader(label, type=types, help=help_text)


def render_model_status(llm_available: bool):
    """
    渲染模型状态指示器

    Args:
        llm_available: LLM 是否可用
    """
    if llm_available:
        st.success("🤖 模型已就绪")
    else:
        st.warning("⚠️ 请先配置 AWS 凭据")


def render_stage_header(stage: str):
    """
    渲染阶段标题

    Args:
        stage: 当前阶段
    """
    stage_display = get_stage_display_name(stage)
    st.header(stage_display)


def render_export_buttons(
    state: HTPState, show_chat: bool = True, show_report: bool = True
):
    """
    渲染导出按钮

    Args:
        state: HTP 状态
        show_chat: 是否显示聊天导出
        show_report: 是否显示报告导出
    """
    if not show_chat and not show_report:
        return

    st.subheader("💾 导出选项")

    col1, col2 = st.columns(2)

    if show_chat and col1:
        # 导出聊天记录
        chat_messages = state.get("chat_messages", [])
        if chat_messages:
            chat_text = "HTP 对话记录\n" + "=" * 50 + "\n\n"

            for i, message in enumerate(chat_messages, 1):
                role_display = "用户" if message["role"] == "user" else "助手"
                chat_text += f"{i}. {role_display}：\n{message['content']}\n\n"

            col1.download_button(
                label="💬 下载对话记录",
                data=chat_text,
                file_name=f"HTP_Chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

    if show_report and col2:
        # 导出完整报告
        final_report = state.get("final_report")
        if final_report:
            report_text = f"""
HTP 心理测试完整报告
生成时间: {state.get("analysis_timestamp", "未知")}
总问答轮次: {state.get("total_questions_asked", 0)}

=== 图像分析 ===
{state.get("image_analysis", "未完成")}

=== 综合分析 ===
{state.get("comprehensive_analysis", "未完成")}

=== 最终评估报告 ===
{final_report}
"""

            col2.download_button(
                label="📄 下载完整报告",
                data=report_text,
                file_name=f"HTP_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )


def render_warning_box(message: str, warning_type: str = "warning"):
    """
    渲染警告框

    Args:
        message: 警告消息
        warning_type: 警告类型 ('warning', 'error', 'info', 'success')
    """
    if warning_type == "warning":
        st.warning(message)
    elif warning_type == "error":
        st.error(message)
    elif warning_type == "info":
        st.info(message)
    elif warning_type == "success":
        st.success(message)
    else:
        st.write(message)
