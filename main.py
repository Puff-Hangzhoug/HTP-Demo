import streamlit as st
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

st.set_page_config(
    page_title="HTP 心理分析系统",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧠 HTP 心理分析系统")

st.markdown(
    """
    ## 🎨 房-树-人（HTP）心理投射测试完整流程系统
    
    欢迎使用基于现代 AI 技术的 HTP 心理分析系统。本系统提供完整的测试流程：
    
    ### 📋 系统功能
    
    1. **🖼️ 绘画创作** - 使用高级画布工具进行 HTP 绘画
    2. **🤖 智能分析** - 基于 LangGraph + YAML Prompts 的多阶段分析
    3. **📊 心理评估** - 结合 DASS-21 量表的综合心理状态评估
    4. **🔧 系统管理** - Prompt 模板管理和系统配置
    
    ### 🚀 使用流程
    
    1. **绘画阶段**: 在绘画画布中创作您的房-树-人作品
    2. **分析阶段**: 上传绘画，通过聊天界面进行深度问答
    3. **评估阶段**: 完成 DASS-21 量表，获得完整心理评估报告
    
    ### 🔬 技术特性
    
    - **模块化设计**: 清晰的代码架构，便于维护和扩展
    - **现代化 UI**: 流畅的聊天界面和直观的用户体验
    - **专业分析**: 基于心理学理论的多维度分析框架
    - **数据安全**: 所有数据仅在会话期间存储，保护隐私
    
    ---
    
    👈 **请从左侧菜单选择功能页面开始使用**
    
    """
)

# 系统状态概览
if st.session_state:
    with st.expander("📊 当前会话状态", expanded=False):
        # 统计会话状态信息
        htp_state = st.session_state.get("htp_state", {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "图像分析",
                "✅ 完成" if htp_state.get("image_analysis") else "⏳ 待处理",
            )

        with col2:
            qa_complete = htp_state.get("is_qa_complete", False)
            st.metric("问答阶段", "✅ 完成" if qa_complete else "⏳ 进行中")

        with col3:
            dass21_complete = htp_state.get("is_dass21_complete", False)
            st.metric("DASS-21 评估", "✅ 完成" if dass21_complete else "⏳ 待评估")

        with col4:
            final_report = htp_state.get("final_report")
            st.metric("完整报告", "✅ 已生成" if final_report else "⏳ 待生成")

# 快速操作
st.markdown("### 🎯 快速操作")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🖼️ 开始绘画", use_container_width=True):
        st.switch_page("pages/1_Drawing_Canvas.py")

with col2:
    if st.button("🤖 开始分析", use_container_width=True):
        st.switch_page("pages/2_HTP_Analysis.py")

with col3:
    if st.button("🔧 管理设置", use_container_width=True):
        st.switch_page("pages/3_Prompt_Management.py")

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        HTP 心理分析系统 | 基于 LangGraph + YAML Prompts + 模块化架构
    </div>
    """,
    unsafe_allow_html=True,
)
