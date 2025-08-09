import streamlit as st
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if project_root not in sys.path:
    sys.path.append(project_root)

from modules.utils.state import create_initial_state, reset_state
from modules.utils.models import get_model_config_ui, create_llm_from_config
from modules.utils.image import decode_base64_image
from modules.agents.htp_agent import create_htp_agent
from modules.ui.chat import render_chat_interface, format_assistant_message
from modules.ui.components import (
    render_progress_sidebar,
    render_session_statistics,
    render_category_status,
    render_debug_panel,
    render_export_buttons,
    render_file_upload,
    render_model_status,
)
from modules.surveys.dass21 import DASS21Survey

st.set_page_config(page_title="HTP 分析", page_icon="🤖", layout="wide")

st.title("🤖 HTP 心理分析系统")

# 初始化状态
if "htp_state" not in st.session_state:
    st.session_state.htp_state = create_initial_state()

# 初始化 DASS-21 问卷
if "dass21_survey" not in st.session_state:
    st.session_state.dass21_survey = DASS21Survey()

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 系统设置")

    # 模型配置
    with st.expander("🤖 模型配置", expanded=False):
        model_config = get_model_config_ui()

    # 创建 LLM 模型
    llm = create_llm_from_config(model_config)

    st.markdown("---")

    # 问答策略配置
    with st.expander("💬 问答策略设置", expanded=False):
        cfg = st.session_state.htp_state.get("qa_config", {})
        col1, col2 = st.columns(2)
        with col1:
            max_per_cat = st.number_input(
                "每个类别最多问题数",
                min_value=1,
                max_value=10,
                value=int(cfg.get("max_questions_per_category", 2)),
                step=1,
                help="防止在某一类别无限追问",
            )
        with col2:
            max_total = st.number_input(
                "全局最多问题数",
                min_value=4,
                max_value=50,
                value=int(cfg.get("max_total_questions", 8)),
                step=1,
                help="限制整个会话的总问答轮次",
            )

        enable_smart = st.checkbox(
            "启用智能覆盖度评估（自动判断是否充分覆盖该类别要点）",
            value=bool(cfg.get("enable_smart_coverage", True)),
        )
        coverage_threshold = st.slider(
            "覆盖度阈值（越高越严格）",
            0.5,
            0.95,
            float(cfg.get("coverage_threshold", 0.7)),
            0.05,
        )
        dedupe_threshold = st.slider(
            "去重相似度阈值（越高越严格）",
            0.70,
            0.98,
            float(cfg.get("dedupe_similarity_threshold", 0.88)),
            0.01,
            help="新问题与历史问题的相似度超过该阈值会重试或更换角度",
        )

        # 保存配置
        st.session_state.htp_state["qa_config"] = {
            "max_questions_per_category": int(max_per_cat),
            "max_total_questions": int(max_total),
            "enable_smart_coverage": bool(enable_smart),
            "coverage_threshold": float(coverage_threshold),
            "dedupe_similarity_threshold": float(dedupe_threshold),
        }

    # 进度显示
    render_progress_sidebar(st.session_state.htp_state)

    st.markdown("---")

    # 会话统计
    render_session_statistics(st.session_state.htp_state)

    st.markdown("---")

    # 类别状态
    render_category_status(st.session_state.htp_state)

    st.markdown("---")

    # Debug 模式
    debug_mode = st.checkbox("🔧 Debug 模式", help="显示调试信息")
    if debug_mode:
        render_debug_panel(st.session_state.htp_state)

    st.markdown("---")

    # 重置按钮
    if st.button("🔄 重新开始分析", use_container_width=True):
        st.session_state.htp_state = reset_state(st.session_state.htp_state)
        if "htp_agent" in st.session_state:
            del st.session_state.htp_agent
        st.rerun()

# 主界面标签页
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🖼️ 图像上传", "💬 智能对话", "📊 分析结果", "📝 DASS-21 量表", "📋 完整报告"]
)

# 模型状态指示
render_model_status(llm is not None)

# 检查是否有可用的 prompts
prompts_path = os.path.join(project_root, "prompts")
if not os.path.exists(prompts_path):
    st.error(f"❌ 未找到 prompts 目录: {prompts_path}")
    st.info("请确保 prompts 文件夹已正确放置在项目根目录")
    st.stop()

with tab1:
    st.subheader("🖼️ 图像上传与分析")

    # 检查是否有全局图像
    if "global_image" in st.session_state and st.session_state["global_image"]:
        # 显示全局图像
        try:
            image = decode_base64_image(st.session_state["global_image"])

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(image, caption="您的 HTP 绘画作品", use_container_width=True)

            # 更新状态
            if not st.session_state.htp_state["uploaded_image"]:
                st.session_state.htp_state["uploaded_image"] = st.session_state[
                    "global_image"
                ].split(",")[1]

            st.success("✅ 图像已加载")

        except Exception as e:
            st.error(f"图像加载失败: {str(e)}")
    else:
        # 文件上传选项
        uploaded_file = render_file_upload()

        if uploaded_file:
            try:
                from modules.utils.image import encode_image
                from PIL import Image

                # 显示上传的图像
                image = Image.open(uploaded_file)
                # image = decode_base64_image(uploaded_file)

                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.image(
                        image, caption="您的 HTP 绘画作品", use_container_width=True
                    )

                # 编码图像
                uploaded_file.seek(0)
                base64_image, _ = encode_image(uploaded_file)
                st.session_state.htp_state["uploaded_image"] = base64_image

                st.success("✅ 图像上传成功")

            except Exception as e:
                st.error(f"图像处理失败: {str(e)}")

    # 开始分析
    if st.session_state.htp_state["uploaded_image"] and llm:
        if not st.session_state.htp_state["stage_progress"]["image_analysis"]:
            if st.button("🚀 开始 HTP 分析", use_container_width=True, type="primary"):
                with st.spinner("🔄 初始化分析系统..."):
                    try:
                        # 创建 HTP 代理
                        if "htp_agent" not in st.session_state:
                            st.session_state.htp_agent = create_htp_agent(llm)

                        # 运行图像分析
                        st.session_state.htp_state = (
                            st.session_state.htp_agent.analyze_image(
                                st.session_state.htp_state
                            )
                        )

                        st.success("✅ 分析系统初始化完成！")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ 初始化失败: {str(e)}")
        else:
            st.success("✅ 分析系统已初始化")
            if st.session_state.htp_state["image_analysis"]:
                st.markdown("**图像分析结果:**")
                with st.container():
                    st.markdown(st.session_state.htp_state["image_analysis"])
    else:
        if not st.session_state.htp_state["uploaded_image"]:
            st.info("👆 请先上传图像")
        if not llm:
            st.warning("⚠️ 请先配置 AWS 凭据")

with tab2:
    st.subheader("💬 智能对话界面")

    if not st.session_state.htp_state["stage_progress"]["image_analysis"]:
        st.info("ℹ️ 请先完成图像上传和分析")
    else:
        # 确保有 HTP 代理
        if "htp_agent" not in st.session_state and llm:
            st.session_state.htp_agent = create_htp_agent(llm)

        # 显示聊天界面
        if not st.session_state.htp_state["is_qa_complete"]:
            # 检查是否需要生成新问题
            if (
                not st.session_state.htp_state["waiting_for_user_input"]
                and not st.session_state.htp_state["current_question"]
                and "htp_agent" in st.session_state
            ):
                # 决定下一个类别并生成问题
                next_action = st.session_state.htp_agent.decide_next_category(
                    st.session_state.htp_state
                )
                if next_action == "generate_question":
                    st.session_state.htp_state = (
                        st.session_state.htp_agent.generate_question(
                            st.session_state.htp_state
                        )
                    )
                    st.rerun()
                elif next_action == "category_analysis":
                    st.session_state.htp_state["is_qa_complete"] = True
                    st.session_state.htp_state["stage_progress"]["qa_loop"] = True
                    st.rerun()

            # 聊天界面
            user_input = render_chat_interface(
                st.session_state.htp_state["chat_messages"],
                show_input=st.session_state.htp_state["waiting_for_user_input"],
            )

            if user_input and "htp_agent" in st.session_state:
                # 处理用户回答
                st.session_state.htp_state = (
                    st.session_state.htp_agent.process_user_response(
                        st.session_state.htp_state, user_input
                    )
                )
                st.rerun()

        else:
            # 显示聊天历史
            render_chat_interface(
                st.session_state.htp_state["chat_messages"], show_input=False
            )

            st.success("✅ 问答阶段已完成！")

            # 开始深度分析
            if not st.session_state.htp_state["stage_progress"]["category_analysis"]:
                if (
                    st.button("🚀 开始深度分析", use_container_width=True)
                    and "htp_agent" in st.session_state
                ):
                    st.session_state.htp_state = (
                        st.session_state.htp_agent.analyze_categories(
                            st.session_state.htp_state
                        )
                    )
                    st.session_state.htp_state = (
                        st.session_state.htp_agent.comprehensive_analysis(
                            st.session_state.htp_state
                        )
                    )
                    st.rerun()

with tab3:
    st.subheader("📊 分析结果")

    if not st.session_state.htp_state["stage_progress"]["qa_loop"]:
        st.info("ℹ️ 请先完成问答阶段")
    else:
        # 显示各类别分析结果
        if st.session_state.htp_state["stage_progress"]["category_analysis"]:
            st.markdown("### 📝 各类别详细分析")

            category_names = {
                "person": "👤 人物部分",
                "house": "🏠 房子部分",
                "tree": "🌳 树木部分",
                "overall": "🎨 整体感受",
            }

            for category, analysis in st.session_state.htp_state[
                "category_analyses"
            ].items():
                if analysis:
                    with st.expander(
                        f"{category_names.get(category, category)} 分析结果"
                    ):
                        st.markdown(analysis)

        # 显示综合分析结果
        if st.session_state.htp_state["comprehensive_analysis"]:
            st.markdown("### 🧠 综合整合分析")
            with st.container():
                st.markdown(st.session_state.htp_state["comprehensive_analysis"])

with tab4:
    st.subheader("📝 DASS-21 抑郁·焦虑·压力量表")

    if not st.session_state.htp_state["stage_progress"]["comprehensive"]:
        st.info("ℹ️ 请先完成综合分析阶段")
    elif st.session_state.htp_state["is_dass21_complete"]:
        # 显示已完成的结果
        scores = st.session_state.htp_state["dass21_scores"]
        levels = st.session_state.htp_state["dass21_levels"]
        st.session_state.dass21_survey.render_results(scores, levels)

        # 继续生成最终报告
        if not st.session_state.htp_state["stage_progress"]["final_report"]:
            if (
                st.button("📊 生成完整报告", use_container_width=True)
                and "htp_agent" in st.session_state
            ):
                st.session_state.htp_state = (
                    st.session_state.htp_agent.generate_final_report(
                        st.session_state.htp_state
                    )
                )
                st.rerun()
    else:
        # 显示问卷表单
        responses = st.session_state.dass21_survey.render_form()

        if responses and "htp_agent" in st.session_state:
            st.session_state.htp_state = st.session_state.htp_agent.process_dass21(
                st.session_state.htp_state, responses
            )
            st.rerun()

with tab5:
    st.subheader("📋 完整心理评估报告")

    if not st.session_state.htp_state["stage_progress"]["dass21"]:
        st.info("ℹ️ 请先完成 DASS-21 量表评估")
    else:
        # 显示最终报告
        if st.session_state.htp_state["final_report"]:
            # 报告头部信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("分析维度", "4大主题")
            with col2:
                st.metric(
                    "问答轮次", st.session_state.htp_state["total_questions_asked"]
                )
            with col3:
                if st.session_state.htp_state["analysis_timestamp"]:
                    from datetime import datetime

                    timestamp = datetime.fromisoformat(
                        st.session_state.htp_state["analysis_timestamp"]
                    )
                    st.metric("完成时间", timestamp.strftime("%H:%M"))

            st.markdown("---")

            # 完整报告内容
            st.markdown("### 📊 多维度心理状态评估报告")
            with st.container():
                st.markdown(st.session_state.htp_state["final_report"])

            # 导出选项
            st.markdown("---")
            render_export_buttons(st.session_state.htp_state)

        else:
            st.info("请等待报告生成完成...")

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        HTP 心理分析系统 | 基于模块化架构的现代化心理测试平台
    </div>
    """,
    unsafe_allow_html=True,
)
