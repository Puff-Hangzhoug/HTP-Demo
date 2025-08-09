import streamlit as st
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if project_root not in sys.path:
    sys.path.append(project_root)

from modules.prompts.manager import get_prompt_manager

st.set_page_config(page_title="Prompt 管理", page_icon="🔧", layout="wide")

st.title("🔧 Prompt 管理系统")

st.markdown(
    """
    ## 基于 LangChain load_prompt 的 Prompt 管理系统
    
    本系统使用 YAML 格式管理所有 HTP 分析流程的 prompt：
    - 🔍 **图像分析**: 客观描述HTP绘画内容
    - 💬 **智能问答**: 四个维度的温和提问
    - 📊 **分析评估**: 各类别及综合心理分析
    - 📋 **完整报告**: 多维度心理状态评估
    
    ---
    """
)

# 获取 Prompt 管理器
try:
    prompt_manager = get_prompt_manager()
except Exception as e:
    st.error(f"Prompt 管理器初始化失败: {str(e)}")
    st.stop()


def display_prompt_info(prompt_info: dict):
    """显示 prompt 详细信息"""
    metadata = prompt_info["metadata"]

    # 基本信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("版本", metadata.get("version", "1.0"))
    with col2:
        st.metric("类别", metadata.get("category", "unknown"))
    with col3:
        if metadata.get("subcategory"):
            st.metric("子类别", metadata.get("subcategory"))

    # 描述
    if metadata.get("description"):
        st.info(f"**描述**: {metadata['description']}")

    # 加载 prompt 内容
    load_result = prompt_manager.load_prompt_with_langchain(prompt_info["filepath"])

    if load_result["success"]:
        st.success(f"✅ 成功加载 {load_result['prompt_type']}")

        # 显示输入变量
        if load_result["input_variables"]:
            st.markdown("**输入变量:**")
            variables_text = ", ".join(
                [f"`{var}`" for var in load_result["input_variables"]]
            )
            st.markdown(variables_text)
        else:
            st.info("无需输入变量")

        # 显示模板内容
        st.markdown("**Prompt 模板:**")
        st.code(load_result["template"], language="markdown")

        # 测试功能
        if load_result["input_variables"]:
            with st.expander("🧪 测试 Prompt", expanded=False):
                test_values = {}

                for var in load_result["input_variables"]:
                    test_values[var] = st.text_area(
                        f"输入 {var}:",
                        height=100,
                        placeholder=f"请输入 {var} 的测试内容...",
                    )

                if st.button("生成测试结果"):
                    try:
                        formatted_prompt = load_result["prompt"].format(**test_values)
                        st.markdown("**生成的 Prompt:**")
                        st.markdown(formatted_prompt)
                    except Exception as e:
                        st.error(f"格式化失败: {str(e)}")
    else:
        st.error(f"❌ 加载失败: {load_result['error']}")


# 侧边栏配置
with st.sidebar:
    st.header("🔧 管理配置")

    # 文件统计
    try:
        prompt_files = prompt_manager.get_all_prompt_files()
    except Exception as e:
        st.error(f"获取 prompt 文件失败: {str(e)}")
        prompt_files = []

    if prompt_files:
        st.metric("Prompt 文件总数", len(prompt_files))

        # 按类别统计
        categories = {}
        for pf in prompt_files:
            cat = pf["category"]
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        st.markdown("**按类别分布:**")
        for cat, count in categories.items():
            st.write(f"- {cat}: {count} 个")
    else:
        st.warning("未找到 prompt 文件")
        st.info(f"请检查 prompts 目录是否存在")

    st.markdown("---")

    # 筛选选项
    st.subheader("🔍 筛选选项")

    if prompt_files:
        # 类别筛选
        all_categories = ["全部"] + list(set(pf["category"] for pf in prompt_files))
        selected_category = st.selectbox("选择类别", all_categories)

        # 子类别筛选
        if selected_category != "全部":
            subcategories = ["全部"] + list(
                set(
                    pf["subcategory"]
                    for pf in prompt_files
                    if pf["category"] == selected_category and pf["subcategory"]
                )
            )
            if len(subcategories) > 1:
                selected_subcategory = st.selectbox("选择子类别", subcategories)
            else:
                selected_subcategory = "全部"
        else:
            selected_subcategory = "全部"
    else:
        selected_category = "全部"
        selected_subcategory = "全部"

    # 刷新按钮
    if st.button("🔄 刷新缓存", use_container_width=True):
        prompt_manager.clear_cache()
        st.rerun()

# 主界面
if not prompt_files:
    st.error("❌ 未找到 prompt 文件，请检查 prompts/ 目录")
    st.info(f"当前查找路径: {prompt_manager.prompts_path}")

    # 提供创建示例的选项
    if st.button("📁 查看项目结构"):
        st.code(
            f"""
项目结构应该是：
{project_root}/
├── prompts/
│   ├── 01_image_analysis.yaml
│   ├── 02_person_question.yaml
│   ├── 03_house_question.yaml
│   └── ... (其他 YAML 文件)
├── modules/
└── pages/
        """
        )
    st.stop()

# 筛选文件
filtered_files = prompt_files
if selected_category != "全部":
    filtered_files = [
        pf for pf in filtered_files if pf["category"] == selected_category
    ]
if selected_subcategory != "全部":
    filtered_files = [
        pf for pf in filtered_files if pf["subcategory"] == selected_subcategory
    ]

# 创建标签页
tab1, tab2, tab3 = st.tabs(["📋 Prompt 列表", "🔍 详细查看", "📊 使用统计"])

with tab1:
    st.subheader(f"📋 Prompt 文件列表 ({len(filtered_files)} 个)")

    if filtered_files:
        # 创建表格数据
        table_data = []
        for pf in filtered_files:
            table_data.append(
                {
                    "文件名": pf["filename"],
                    "类别": pf["category"],
                    "子类别": pf["subcategory"] or "-",
                    "版本": pf["version"],
                    "描述": (
                        pf["description"][:50] + "..."
                        if len(pf["description"]) > 50
                        else pf["description"]
                    ),
                }
            )

        # 显示表格
        st.dataframe(table_data, use_container_width=True, hide_index=True)

        # 选择要查看的文件
        st.markdown("---")
        selected_filename = st.selectbox(
            "选择要详细查看的 prompt 文件:",
            options=[pf["filename"] for pf in filtered_files],
            format_func=lambda x: f"{x} - {next(pf['description'] for pf in filtered_files if pf['filename'] == x)[:30]}...",
        )

        if selected_filename:
            selected_prompt = next(
                pf for pf in filtered_files if pf["filename"] == selected_filename
            )

            st.markdown(f"### 📄 {selected_filename}")
            display_prompt_info(selected_prompt)
    else:
        st.info("没有符合筛选条件的 prompt 文件")

with tab2:
    st.subheader("🔍 Prompt 详细查看")

    if filtered_files:
        # 使用选择框选择文件
        prompt_options = {
            f"{pf['filename']} ({pf['category']})": pf for pf in filtered_files
        }

        selected_option = st.selectbox(
            "选择 Prompt 文件:", options=list(prompt_options.keys())
        )

        if selected_option:
            selected_prompt = prompt_options[selected_option]
            display_prompt_info(selected_prompt)
    else:
        st.info("请先在侧边栏选择筛选条件")

with tab3:
    st.subheader("📊 使用统计")

    if prompt_files:
        # 类别分布图表
        categories_count = {}
        for pf in prompt_files:
            cat = pf["category"]
            if cat not in categories_count:
                categories_count[cat] = 0
            categories_count[cat] += 1

        # 显示图表
        st.markdown("**按类别分布:**")
        for cat, count in categories_count.items():
            st.progress(count / len(prompt_files), text=f"{cat}: {count} 个")

        # 版本分布
        versions = {}
        for pf in prompt_files:
            ver = pf["version"]
            if ver not in versions:
                versions[ver] = 0
            versions[ver] += 1

        st.markdown("**版本分布:**")
        col1, col2 = st.columns(2)
        for i, (ver, count) in enumerate(versions.items()):
            if i % 2 == 0:
                col1.metric(f"版本 {ver}", count)
            else:
                col2.metric(f"版本 {ver}", count)

        # 系统信息
        with st.expander("📈 系统信息"):
            st.markdown("**Prompt 文件映射:**")

            # 问题生成映射
            st.markdown("*问题生成 Prompts:*")
            question_files = prompt_manager.get_question_prompt_files()
            for category, filename in question_files.items():
                st.write(f"- {category}: `{filename}`")

            # 分析映射
            st.markdown("*分析 Prompts:*")
            analysis_files = prompt_manager.get_analysis_prompt_files()
            for category, filename in analysis_files.items():
                st.write(f"- {category}: `{filename}`")

            # 详细统计
            st.json(
                {
                    "总文件数": len(prompt_files),
                    "类别统计": categories_count,
                    "版本统计": versions,
                    "平均描述长度": (
                        sum(len(pf["description"]) for pf in prompt_files)
                        / len(prompt_files)
                        if prompt_files
                        else 0
                    ),
                    "Prompts 路径": prompt_manager.prompts_path,
                }
            )
    else:
        st.info("暂无统计数据")

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        基于 <a href='https://python.langchain.com/docs/modules/model_io/prompts/prompt_templates/prompt_serialization' target='_blank'>LangChain Prompt Serialization</a> 
        的模块化 YAML Prompt 管理系统
    </div>
    """,
    unsafe_allow_html=True,
)
