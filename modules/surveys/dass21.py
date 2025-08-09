"""
DASS-21 抑郁·焦虑·压力量表模块
"""

import streamlit as st
from typing import Dict, Tuple


# DASS-21 问卷数据
DASS21_QUESTIONS = {
    1: "我发现自己很难放松",
    2: "我感到口干",
    3: "我似乎无法体验任何积极的感受",
    4: "我出现呼吸困难（例如呼吸过快，未运动时也感到气喘）",
    5: "我发觉事情提不起劲去做",
    6: "我往往对情况反应过度",
    7: "我出现颤抖（例如手发抖）",
    8: "我感觉自己消耗了很多神经能量",
    9: "我担心自己在可能惊慌而出丑的场合",
    10: "我觉得没有什么值得期待",
    11: "我发现自己变得容易激动",
    12: "我发现自己难以放松",
    13: "我感到情绪低落、忧郁",
    14: "任何妨碍我做事的事情都会让我无法容忍",
    15: "我觉得自己接近惊恐",
    16: "我对任何事情都无法产生热情",
    17: "我觉得自己作为一个人没有什么价值",
    18: "我觉得自己有些敏感易怒",
    19: "在未进行体力活动时，我能感受到自己的心跳（例如心率加快或漏跳）",
    20: "我毫无理由地感到害怕",
    21: "我感到人生毫无意义",
}

DASS21_DIMENSIONS = {
    "depression": [3, 5, 10, 13, 16, 17, 21],
    "anxiety": [2, 4, 7, 9, 15, 19, 20],
    "stress": [1, 6, 8, 11, 12, 14, 18],
}

DASS21_SEVERITY_TABLE = {
    "depression": [
        (0, 9, "正常"),
        (10, 13, "轻度"),
        (14, 20, "中度"),
        (21, 27, "重度"),
        (28, 999, "极重度"),
    ],
    "anxiety": [
        (0, 7, "正常"),
        (8, 9, "轻度"),
        (10, 14, "中度"),
        (15, 19, "重度"),
        (20, 999, "极重度"),
    ],
    "stress": [
        (0, 14, "正常"),
        (15, 18, "轻度"),
        (19, 25, "中度"),
        (26, 33, "重度"),
        (34, 999, "极重度"),
    ],
}


def calculate_dass21_scores(
    responses: Dict[int, int],
) -> Tuple[Dict[str, int], Dict[str, str]]:
    """
    计算 DASS-21 得分和等级

    Args:
        responses: {question_num: score} 用户回答

    Returns:
        Tuple[Dict[str, int], Dict[str, str]]: (scores, levels)
    """
    scores = {}
    levels = {}

    for dimension, items in DASS21_DIMENSIONS.items():
        raw_score = sum(responses.get(i, 0) for i in items)
        # DASS-21 需将得分乘以 2 才能与完整版 DASS-42 对齐
        final_score = raw_score * 2
        scores[dimension] = final_score

        # 确定等级
        for lower, upper, label in DASS21_SEVERITY_TABLE[dimension]:
            if lower <= final_score <= upper:
                levels[dimension] = label
                break
        else:
            levels[dimension] = "未知"

    return scores, levels


def format_dass21_results(scores: Dict[str, int], levels: Dict[str, str]) -> str:
    """
    格式化 DASS-21 结果为文本

    Args:
        scores: 得分字典
        levels: 等级字典

    Returns:
        str: 格式化的结果文本
    """
    dimension_names = {"depression": "抑郁", "anxiety": "焦虑", "stress": "压力"}

    result_text = "DASS-21 心理状态评估结果：\n\n"
    for dim_key, dim_name in dimension_names.items():
        score = scores.get(dim_key, 0)
        level = levels.get(dim_key, "未知")
        result_text += f"• {dim_name}水平：{score}分 ({level})\n"

    return result_text


def render_dass21_form() -> Dict[int, int]:
    """
    渲染 DASS-21 问卷表单

    Returns:
        Dict[int, int]: 用户的回答 {question_num: score}
    """
    st.markdown(
        """
        **说明**  
        - 本量表共有 21 个条目，请根据过去一周（含今天）的实际感受作答。  
        - 每个条目请选择 0～3 之间的一个分值：  
            * 0 = 完全不符合  
            * 1 = 有时符合  
            * 2 = 大部分时间符合  
            * 3 = 几乎一直如此  
        - 本问卷仅用于自我检测，结果不能替代专业心理咨询或临床诊断。  
        """
    )

    # 初始化 responses
    if "dass21_temp_responses" not in st.session_state:
        st.session_state.dass21_temp_responses = {}

    responses = {}

    # 问卷表单
    with st.form("dass21_form"):
        st.markdown("### 📋 问卷题目")

        for num, text in DASS21_QUESTIONS.items():
            responses[num] = st.radio(
                label=f"{num}. {text}",
                options=[0, 1, 2, 3],
                horizontal=True,
                key=f"dass21_q{num}",
                index=st.session_state.dass21_temp_responses.get(num, 0),
            )

        # 提交按钮
        submitted = st.form_submit_button("📊 提交并计算得分", use_container_width=True)

        if submitted:
            # 检查是否所有问题都已回答
            if len(responses) == 21:
                st.session_state.dass21_temp_responses = responses
                return responses
            else:
                st.error("请回答所有21个问题")
                return {}

    return {}


def render_dass21_results(scores: Dict[str, int], levels: Dict[str, str]):
    """
    渲染 DASS-21 结果显示

    Args:
        scores: 得分字典
        levels: 等级字典
    """
    st.success("✅ DASS-21 量表评估已完成！")

    # 显示结果
    st.markdown("### 📊 评估结果")
    col1, col2, col3 = st.columns(3)

    with col1:
        depression_score = scores.get("depression", 0)
        depression_level = levels.get("depression", "未知")
        st.metric("抑郁 (Depression)", depression_score, depression_level)

    with col2:
        anxiety_score = scores.get("anxiety", 0)
        anxiety_level = levels.get("anxiety", "未知")
        st.metric("焦虑 (Anxiety)", anxiety_score, anxiety_level)

    with col3:
        stress_score = scores.get("stress", 0)
        stress_level = levels.get("stress", "未知")
        st.metric("压力 (Stress)", stress_score, stress_level)

    # 提醒信息
    has_moderate_or_above = any(
        level in ["中度", "重度", "极重度"]
        for level in [depression_level, anxiety_level, stress_level]
    )

    if has_moderate_or_above:
        st.warning("⚠️ 检测到中度及以上水平，建议寻求专业心理健康支持。")
    else:
        st.info("💚 您的心理状态评估结果显示在正常范围内。")


class DASS21Survey:
    """DASS-21 问卷类"""

    def __init__(self):
        self.questions = DASS21_QUESTIONS
        self.dimensions = DASS21_DIMENSIONS
        self.severity_table = DASS21_SEVERITY_TABLE

    def calculate_scores(
        self, responses: Dict[int, int]
    ) -> Tuple[Dict[str, int], Dict[str, str]]:
        """计算得分和等级"""
        return calculate_dass21_scores(responses)

    def format_results(self, scores: Dict[str, int], levels: Dict[str, str]) -> str:
        """格式化结果"""
        return format_dass21_results(scores, levels)

    def render_form(self) -> Dict[int, int]:
        """渲染表单"""
        return render_dass21_form()

    def render_results(self, scores: Dict[str, int], levels: Dict[str, str]):
        """渲染结果"""
        render_dass21_results(scores, levels)
