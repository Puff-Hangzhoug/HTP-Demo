import streamlit as st
import sys
import os
import base64
import io
from PIL import Image

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if project_root not in sys.path:
    sys.path.append(project_root)

# 尝试导入 streamlit_tldraw，如果没有则显示提示
try:
    from streamlit_tldraw import st_tldraw

    TLDRAW_AVAILABLE = True
except ImportError:
    TLDRAW_AVAILABLE = False

from modules.utils.state import create_initial_state
from modules.utils.image import encode_image

st.set_page_config(
    page_title="绘画画布",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("🖼️ HTP 绘画画布")

# 初始化状态
if "htp_state" not in st.session_state:
    st.session_state.htp_state = create_initial_state()

# 全局图片显示区域
if "global_image" in st.session_state and st.session_state["global_image"]:
    with st.container():
        st.subheader("📸 当前作品")
        # 从base64解码并显示图片
        try:
            img_data = base64.b64decode(st.session_state["global_image"].split(",")[1])
            img = Image.open(io.BytesIO(img_data))

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(img, caption="您的 HTP 绘画作品", use_container_width=True)

            # 更新到 HTP 状态
            st.session_state.htp_state["uploaded_image"] = st.session_state[
                "global_image"
            ].split(",")[1]

            # 操作按钮
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 重新绘制", use_container_width=True):
                    if "global_image" in st.session_state:
                        del st.session_state["global_image"]
                    st.rerun()

            with col2:
                if st.button("🤖 开始分析", use_container_width=True, type="primary"):
                    st.switch_page("pages/2_HTP_Analysis.py")

            with col3:
                # 下载图像
                st.download_button(
                    label="💾 下载图像",
                    data=img_data,
                    file_name="htp_drawing.png",
                    mime="image/png",
                    use_container_width=True,
                )

        except Exception as e:
            st.error(f"图像显示失败: {str(e)}")
            if "global_image" in st.session_state:
                del st.session_state["global_image"]

else:
    st.info("🎨 请在下方画布中创作您的房-树-人绘画作品")

st.divider()

# 绘画区域
if TLDRAW_AVAILABLE:
    st.subheader("🎨 绘画区域")

    # 使用说明
    with st.expander("📋 使用说明", expanded=False):
        st.markdown(
            """
        ### HTP 绘画指导
        
        **房-树-人（HTP）绘画测试** 是一种经典的心理投射测试，请按以下步骤创作：
        
        1. **🏠 画一间房子** - 可以是任何风格的房屋
        2. **🌳 画一棵树** - 任何种类的树都可以
        3. **👤 画一个人** - 可以是任何年龄、性别的人物
        
        ### 🖌️ 绘画提示
        - **自由创作**：没有标准答案，请按您的想法绘制
        - **细节表达**：可以添加您觉得重要的细节
        - **色彩使用**：可以使用颜色，也可以只用线条
        - **构图安排**：三个元素的位置和大小由您决定
        
        ### 🎯 完成后
        - 点击 "🌐 更新为当前作品" 保存您的绘画
        - 然后可以进入分析阶段开始心理测试
        """
        )

    # tldraw 画布
    payload = st_tldraw(key="htp_canvas", height=600, dark_mode=False, show_ui=True)

    # 处理画布数据
    if payload:
        snapshot = payload["snapshot"]
        st.session_state["tldraw_doc"] = snapshot

        # 获取 PNG 图像
        png_b64 = payload.get("png")
        if png_b64:
            # 预览图像
            try:
                img = Image.open(io.BytesIO(base64.b64decode(png_b64.split(",")[1])))

                with st.container():
                    st.subheader("🔍 预览")
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.image(img, caption="当前绘画预览", use_container_width=True)

                # 保存按钮
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(
                        "🌐 更新为当前作品", use_container_width=True, type="primary"
                    ):
                        st.session_state["global_image"] = png_b64
                        st.session_state["tldraw_png"] = png_b64
                        st.success("✅ 作品已保存！")
                        st.rerun()

                with col2:
                    if st.button("🗑️ 清空画布", use_container_width=True):
                        # 注意：这只是UI提示，实际清空需要重新加载组件
                        st.info("请使用画布上的清空工具或刷新页面")

            except Exception as e:
                st.error(f"图像处理失败: {str(e)}")

else:
    # 如果没有 streamlit_tldraw，提供文件上传选项
    st.warning("⚠️ 未安装 streamlit_tldraw 组件，请使用文件上传功能")

    st.subheader("📤 上传绘画作品")

    uploaded_file = st.file_uploader(
        "选择您的 HTP 绘画文件",
        type=["png", "jpg", "jpeg"],
        help="请上传您的房-树-人绘画作品",
    )

    if uploaded_file:
        try:
            # 显示上传的图像
            image = Image.open(uploaded_file)

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(image, caption="您的 HTP 绘画作品", use_container_width=True)

            # 编码图像
            uploaded_file.seek(0)
            base64_image, _ = encode_image(uploaded_file)

            # 保存到全局状态
            if st.button("💾 保存作品", use_container_width=True, type="primary"):
                st.session_state["global_image"] = (
                    f"data:image/png;base64,{base64_image}"
                )
                st.session_state.htp_state["uploaded_image"] = base64_image
                st.success("✅ 作品已保存！")
                st.rerun()

        except Exception as e:
            st.error(f"文件处理失败: {str(e)}")

# 页脚信息
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        HTP 绘画画布 | 完成创作后请进入分析页面开始心理测试
    </div>
    """,
    unsafe_allow_html=True,
)
