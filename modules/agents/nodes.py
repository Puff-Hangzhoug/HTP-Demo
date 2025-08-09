"""
LangGraph 节点模块
"""

import streamlit as st
import base64
import time
import difflib
import re
from typing import Any, Dict, List
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage

from modules.utils.state import HTPState, add_chat_message, add_conversation_entry
from modules.prompts.manager import get_prompt_manager
from modules.surveys.dass21 import calculate_dass21_scores, format_dass21_results


def _get_qa_config(state) -> Dict[str, Any]:
    """安全读取 QA 配置，带默认回退。"""
    default = {
        "max_questions_per_category": 2,
        "max_total_questions": 8,
        "enable_smart_coverage": True,
        "coverage_threshold": 0.7,
        "dedupe_similarity_threshold": 0.88,
    }
    cfg = state.get("qa_config") or {}
    return {**default, **cfg}


CATEGORY_TOPICS: Dict[str, List[Dict[str, Any]]] = {
    "person": [
        {"name": "身份/人物是谁", "keywords": ["是谁", "你吗", "别人", "他", "她"]},
        {"name": "行为/正在做什么", "keywords": ["做什么", "在做", "正在", "动作"]},
        {
            "name": "情绪/感觉",
            "keywords": ["开心", "害怕", "紧张", "情绪", "感觉", "感受"],
        },
        {"name": "陪伴/社交", "keywords": ["有人", "陪", "朋友", "孤独", "陪伴"]},
        {"name": "穿着/个性", "keywords": ["衣服", "穿", "个性", "风格"]},
        {"name": "内心独白", "keywords": ["说什么", "会说", "一句话"]},
    ],
    "house": [
        {"name": "位置/环境", "keywords": ["城里", "郊外", "位置", "环境"]},
        {"name": "归属/所有权", "keywords": ["属于", "你的", "谁的", "认识的人的"]},
        {"name": "内部是否有人/希望", "keywords": ["里面", "有人", "谁住", "希望谁"]},
        {"name": "门开合/接纳", "keywords": ["门", "开", "关", "走进来"]},
        {"name": "大小/适配", "keywords": ["大", "小", "刚刚好", "太大", "太小"]},
        {"name": "功能/保护与展示", "keywords": ["保护", "展示"]},
        {"name": "拟人表达", "keywords": ["说话", "会说什么"]},
    ],
    "tree": [
        {"name": "来源/记忆", "keywords": ["见过", "来自哪里", "哪里", "从哪"]},
        {"name": "健康/经历", "keywords": ["健康", "经历", "经历过", "成长"]},
        {"name": "特征/叶果", "keywords": ["叶子", "果实", "特别", "枝"]},
        {"name": "根/稳定", "keywords": ["根", "扎", "稳", "稳定"]},
        {"name": "象征/自我投射", "keywords": ["象征", "哪部分", "你的一部分"]},
        {"name": "孤独/同伴", "keywords": ["孤独", "朋友", "别的树"]},
    ],
    "overall": [
        {"name": "创作时想法", "keywords": ["想什么", "在想", "创作"]},
        {"name": "代表近期状态", "keywords": ["代表", "最近", "状态"]},
        {"name": "氛围/情绪", "keywords": ["氛围", "平静", "自由", "紧张", "感觉"]},
        {"name": "空白/意义", "keywords": ["空白", "意义", "特别"]},
        {"name": "色彩/情绪", "keywords": ["色彩", "颜色", "情绪"]},
        {"name": "重点部位/原因", "keywords": ["特别想", "部分", "为什么"]},
    ],
}


def _normalize(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _collect_category_qa(state, category: str) -> List[Dict[str, str]]:
    return [
        e
        for e in state.get("conversation_history", [])
        if e.get("category") == category
    ]


def _build_context_for_prompt(state, category: str) -> Dict[str, str]:
    qa_entries = _collect_category_qa(state, category)
    asked_questions = [e["question"] for e in qa_entries if e.get("question")]
    qa_pairs_lines = []
    for e in qa_entries:
        q = e.get("question", "").strip()
        r = e.get("response", "").strip()
        if q or r:
            qa_pairs_lines.append(f"Q: {q}\nA: {r}")

    asked_questions_str = "\n".join(asked_questions[-6:])  # 仅保留近6条
    qa_pairs_str = "\n\n".join(qa_pairs_lines[-6:])

    # 计算未覆盖的主题（基于启发式关键词）
    combined_text = (
        "\n".join(asked_questions)
        + "\n"
        + "\n".join([e.get("response", "") for e in qa_entries])
    ).strip()
    topics = CATEGORY_TOPICS.get(category, [])
    covered = set()
    for t in topics:
        if any(k.lower() in combined_text.lower() for k in t["keywords"]):
            covered.add(t["name"])
    missing = [t["name"] for t in topics if t["name"] not in covered]
    missing_aspects_str = (
        "、".join(missing) if missing else "（已覆盖主要方向，可收束）"
    )

    return {
        "asked_questions": asked_questions_str,
        "qa_pairs": qa_pairs_str,
        "missing_aspects": missing_aspects_str,
    }


def _should_mark_category_complete(state, category: str) -> bool:
    cfg = _get_qa_config(state)
    max_per_cat = int(cfg.get("max_questions_per_category", 2))
    entries = _collect_category_qa(state, category)
    if len(entries) >= max_per_cat:
        return True

    if not cfg.get("enable_smart_coverage", True):
        return False

    # 简单启发式：如果最近一次回答与历史回答相似度很高，或信息增量很低，则认为已基本覆盖
    responses = [e.get("response", "") for e in entries]
    if len(responses) < 1:
        return False
    combined_prev = "\n".join(responses[:-1]) if len(responses) > 1 else ""
    last = responses[-1]
    if not combined_prev:
        return False
    sim = _similar(last, combined_prev)
    # 相似度高视为收敛
    if sim >= max(0.6, cfg.get("coverage_threshold", 0.7) - 0.1):
        return True
    return False


def analyze_image_node(state: HTPState, llm: Any) -> HTPState:
    """
    图像分析节点

    Args:
        state: HTP 状态
        llm: LLM 模型

    Returns:
        HTPState: 更新后的状态
    """
    if state["image_analysis"]:
        return state

    prompt_manager = get_prompt_manager()
    image_prompt = prompt_manager.load_prompt_from_yaml("01_image_analysis.yaml")

    if not image_prompt:
        st.error("无法加载图像分析 prompt")
        return state

    if not state["uploaded_image"]:
        st.error("未找到上传的图像")
        return state

    try:
        with st.spinner("🔍 正在分析图像内容..."):
            messages = [
                SystemMessage(content=image_prompt.format()),
                HumanMessage(
                    content=[
                        {"type": "text", "text": "请分析这张HTP绘画图像："},
                        {
                            "type": "image",
                            "image": {
                                "format": "png",
                                "source": {
                                    "bytes": base64.b64decode(state["uploaded_image"])
                                },
                            },
                        },
                    ]
                ),
            ]

            response = llm.invoke(messages)
            analysis = response.content

            state["image_analysis"] = analysis
            state["current_stage"] = "qa_loop"
            state["stage_progress"]["image_analysis"] = True

            # 添加到聊天记录
            state = add_chat_message(
                state, "assistant", f"✅ 图像分析完成！\n\n**分析结果：**\n{analysis}"
            )

            st.success("✅ 图像分析完成")

    except Exception as e:
        st.error(f"图像分析失败: {str(e)}")

    return state


def generate_question_node(state: HTPState, llm: Any) -> HTPState:
    """
    生成问题节点

    Args:
        state: HTP 状态
        llm: LLM 模型

    Returns:
        HTPState: 更新后的状态
    """
    category = state["current_category"]
    if not category:
        return state

    # 检查是否达到该类别或全局的最大问题数
    cfg = _get_qa_config(state)
    max_questions = int(cfg.get("max_questions_per_category", 2))
    max_total = int(cfg.get("max_total_questions", 8))
    current_responses = len(state["collected_info"].get(category, []))

    # 全局上限保护
    if state.get("total_questions_asked", 0) >= max_total:
        state["categories_covered"].append(category)
        state["current_category"] = None
        return state

    if current_responses >= max_questions:
        state["categories_covered"].append(category)
        state["current_category"] = None
        return state

    # 生成问题
    try:
        prompt_manager = get_prompt_manager()
        prompt_files = prompt_manager.get_question_prompt_files()

        question_prompt = prompt_manager.load_prompt_from_yaml(prompt_files[category])
        if not question_prompt:
            st.error(f"无法加载 {category} 问题 prompt")
            return state

        # 构建上下文（包含历史问答、已问问题、缺失方面）
        rich_ctx = _build_context_for_prompt(state, category)
        context_parts = []
        if rich_ctx.get("qa_pairs"):
            context_parts.append("之前的问答：\n" + rich_ctx["qa_pairs"])
        if rich_ctx.get("asked_questions"):
            context_parts.append(
                "之前问过的问题（避免重复）：\n" + rich_ctx["asked_questions"]
            )
        if rich_ctx.get("missing_aspects"):
            context_parts.append(
                "尚未充分探索的方向（可优先考虑）：\n" + rich_ctx["missing_aspects"]
            )
        context = "\n\n".join(context_parts).strip()

        with st.spinner(f"🤔 正在生成{category}相关问题..."):
            formatted_prompt = question_prompt.format(
                image_analysis=state["image_analysis"], context=context
            )

            def generate_once(extra_instruction: str = "") -> str:
                messages = [
                    SystemMessage(content=formatted_prompt),
                    HumanMessage(
                        content=(
                            "请生成一个合适的问题，聚焦未覆盖的方向，"
                            "并且避免与先前问答重复或类似的问题。"
                            + (f" {extra_instruction}" if extra_instruction else "")
                        )
                    ),
                ]
                resp = llm.invoke(messages)
                return (resp.content or "").strip()

            # 首次生成
            new_question = generate_once()

            # 去重：与历史已问问题比较相似度
            qa_entries = _collect_category_qa(state, category)
            asked_questions = [
                e.get("question", "") for e in qa_entries if e.get("question")
            ]
            threshold = float(cfg.get("dedupe_similarity_threshold", 0.88))
            retry = 0
            max_retries = 2
            while retry < max_retries and any(
                _similar(new_question, q) >= threshold for q in asked_questions
            ):
                retry += 1
                new_question = generate_once(
                    "上个提案与既有问题过于相似，请换一个角度或主题。避免与任何历史问题重复。"
                )

            # 仍然过于相似，则基于缺失主题直接构建一个 fallback 问句
            if any(_similar(new_question, q) >= threshold for q in asked_questions):
                missing = (
                    rich_ctx.get("missing_aspects", "")
                    .replace("（已覆盖主要方向，可收束）", "")
                    .strip()
                )
                if missing:
                    new_question = f"关于你画作中尚未充分谈到的‘{missing.split('、')[0]}’这一面，你愿意多分享一点吗？"

            state["current_question"] = new_question
            state["total_questions_asked"] += 1
            state["waiting_for_user_input"] = True

            # 添加到聊天记录
            category_names = {
                "person": "👤 人物",
                "house": "🏠 房子",
                "tree": "🌳 树木",
                "overall": "🎨 整体感受",
            }

            state = add_chat_message(
                state,
                "assistant",
                f"**{category_names[category]} 相关问题：**\n\n{new_question}",
            )

    except Exception as e:
        st.error(f"问题生成失败: {str(e)}")

    return state


def decide_next_category_node(state: HTPState) -> str:
    """
    决定下一个问答类别

    Args:
        state: HTP 状态

    Returns:
        str: 下一步行动
    """
    cfg = _get_qa_config(state)
    categories = ["person", "house", "tree", "overall"]

    # 如果全局问题数已达上限，则直接进入分析阶段
    if state.get("total_questions_asked", 0) >= int(cfg.get("max_total_questions", 8)):
        state["is_qa_complete"] = True
        state["current_stage"] = "category_analysis"
        return "category_analysis"

    for category in categories:
        if category in state["categories_covered"]:
            continue
        # 若已有对话且覆盖度达到阈值，则标记完成并跳过
        if _should_mark_category_complete(state, category):
            if category not in state["categories_covered"]:
                state["categories_covered"].append(category)
            continue
        state["current_category"] = category
        return "generate_question"

    # 所有类别都完成了
    state["is_qa_complete"] = True
    state["current_stage"] = "category_analysis"
    return "category_analysis"


def process_user_response_node(state: HTPState, user_response: str) -> HTPState:
    """
    处理用户回答节点

    Args:
        state: HTP 状态
        user_response: 用户回答

    Returns:
        HTPState: 更新后的状态
    """
    if not state["current_category"] or not user_response.strip():
        return state

    category = state["current_category"]

    # 初始化类别信息收集
    if category not in state["collected_info"]:
        state["collected_info"][category] = []

    # 添加到对话记录和收集信息
    state = add_conversation_entry(
        state, category, state["current_question"], user_response
    )

    # 添加到聊天记录
    state = add_chat_message(state, "user", user_response)

    # 清除当前问题
    state["current_question"] = None
    state["waiting_for_user_input"] = False

    return state


def category_analysis_node(state: HTPState, llm: Any) -> HTPState:
    """
    各类别分析节点

    Args:
        state: HTP 状态
        llm: LLM 模型

    Returns:
        HTPState: 更新后的状态
    """
    if not state["stage_progress"].get("category_analysis", False):

        with st.spinner("📝 正在进行各类别详细分析..."):

            prompt_manager = get_prompt_manager()
            prompt_files = prompt_manager.get_analysis_prompt_files()

            for category in ["person", "house", "tree", "overall"]:
                if (
                    category in state["collected_info"]
                    and state["collected_info"][category]
                ):
                    try:
                        # 获取该类别的分析prompt
                        analysis_prompt = prompt_manager.load_prompt_from_yaml(
                            prompt_files[category]
                        )
                        if not analysis_prompt:
                            continue

                        # 准备数据
                        responses = "\n".join(state["collected_info"][category])

                        formatted_prompt = analysis_prompt.format(
                            image_analysis=state["image_analysis"],
                            **{f"{category}_responses": responses},
                        )

                        messages = [
                            SystemMessage(content=formatted_prompt),
                            HumanMessage(content="请根据以上信息进行分析。"),
                        ]

                        response = llm.invoke(messages)
                        state["category_analyses"][category] = response.content

                        time.sleep(0.5)  # 避免过快调用API

                    except Exception as e:
                        st.error(f"{category}类别分析失败: {str(e)}")
                        state["category_analyses"][category] = f"分析失败: {str(e)}"

        state["stage_progress"]["category_analysis"] = True
        state["current_stage"] = "comprehensive"

        # 添加到聊天记录
        state = add_chat_message(
            state, "assistant", "✅ 各类别分析完成，正在进行综合分析..."
        )

        st.success("✅ 各类别分析完成")

    return state


def comprehensive_analysis_node(state: HTPState, llm: Any) -> HTPState:
    """
    综合分析节点

    Args:
        state: HTP 状态
        llm: LLM 模型

    Returns:
        HTPState: 更新后的状态
    """
    if not state["stage_progress"].get("comprehensive", False):

        try:
            with st.spinner("🧠 正在进行综合整合分析..."):
                # 加载综合分析prompt
                prompt_manager = get_prompt_manager()
                comprehensive_prompt = prompt_manager.load_prompt_from_yaml(
                    "10_comprehensive_analysis.yaml"
                )
                if not comprehensive_prompt:
                    st.error("无法加载综合分析 prompt")
                    return state

                # 准备所有数据
                prompt_data = {
                    "image_analysis": state["image_analysis"],
                    "person_responses": "\n".join(
                        state["collected_info"].get("person", [])
                    ),
                    "house_responses": "\n".join(
                        state["collected_info"].get("house", [])
                    ),
                    "tree_responses": "\n".join(
                        state["collected_info"].get("tree", [])
                    ),
                    "overall_responses": "\n".join(
                        state["collected_info"].get("overall", [])
                    ),
                    "person_analysis": state["category_analyses"].get("person", ""),
                    "house_analysis": state["category_analyses"].get("house", ""),
                    "tree_analysis": state["category_analyses"].get("tree", ""),
                    "overall_analysis": state["category_analyses"].get("overall", ""),
                }

                formatted_prompt = comprehensive_prompt.format(**prompt_data)

                messages = [
                    SystemMessage(content=formatted_prompt),
                    HumanMessage(content="请进行综合整合分析。"),
                ]

                response = llm.invoke(messages)
                state["comprehensive_analysis"] = response.content

                state["stage_progress"]["comprehensive"] = True
                state["current_stage"] = "dass21"

                # 添加到聊天记录
                state = add_chat_message(
                    state, "assistant", "✅ 综合分析完成！请继续完成 DASS-21 量表评估。"
                )

                st.success("✅ 综合分析完成，准备进入量表评估")

        except Exception as e:
            st.error(f"综合分析失败: {str(e)}")

    return state


def process_dass21_node(state: HTPState, responses: dict) -> HTPState:
    """
    处理DASS-21问卷结果节点

    Args:
        state: HTP 状态
        responses: DASS-21 回答

    Returns:
        HTPState: 更新后的状态
    """
    if responses and len(responses) == 21:
        try:
            # 计算得分和等级
            scores, levels = calculate_dass21_scores(responses)

            # 更新状态
            state["dass21_responses"] = responses
            state["dass21_scores"] = scores
            state["dass21_levels"] = levels
            state["is_dass21_complete"] = True
            state["stage_progress"]["dass21"] = True
            state["current_stage"] = "final_report"

            # 添加到聊天记录
            state = add_chat_message(
                state,
                "assistant",
                f"✅ DASS-21 量表评估完成！\n\n{format_dass21_results(scores, levels)}",
            )

            st.success("✅ DASS-21 量表评估完成")

        except Exception as e:
            st.error(f"DASS-21 评估处理失败: {str(e)}")

    return state


def final_report_node(state: HTPState, llm: Any) -> HTPState:
    """
    最终报告生成节点

    Args:
        state: HTP 状态
        llm: LLM 模型

    Returns:
        HTPState: 更新后的状态
    """
    if not state["stage_progress"].get("final_report", False):

        try:
            with st.spinner("📊 正在生成最终心理评估报告..."):
                # 加载最终评估prompt
                prompt_manager = get_prompt_manager()
                final_prompt = prompt_manager.load_prompt_from_yaml(
                    "11_final_evaluation.yaml"
                )
                if not final_prompt:
                    st.error("无法加载最终评估 prompt")
                    return state

                # 准备完整数据
                conversation_summary = ""
                for entry in state["conversation_history"]:
                    conversation_summary += f"[{entry['category']}] Q: {entry['question']}\nA: {entry['response']}\n\n"

                # 格式化DASS-21结果
                dass21_summary = ""
                if state.get("dass21_scores") and state.get("dass21_levels"):
                    dass21_summary = format_dass21_results(
                        state["dass21_scores"], state["dass21_levels"]
                    )

                prompt_data = {
                    "image_analysis": state["image_analysis"],
                    "comprehensive_analysis": state["comprehensive_analysis"],
                    "person_analysis": state["category_analyses"].get("person", ""),
                    "house_analysis": state["category_analyses"].get("house", ""),
                    "tree_analysis": state["category_analyses"].get("tree", ""),
                    "overall_analysis": state["category_analyses"].get("overall", ""),
                    "conversation_history": conversation_summary,
                    "dass21_results": dass21_summary,
                }

                formatted_prompt = final_prompt.format(**prompt_data)

                messages = [
                    SystemMessage(content=formatted_prompt),
                    HumanMessage(content="请生成完整的心理状态多维度评估报告。"),
                ]

                response = llm.invoke(messages)
                state["final_report"] = response.content

                state["stage_progress"]["final_report"] = True
                state["analysis_timestamp"] = datetime.now().isoformat()

                # 添加到聊天记录
                state = add_chat_message(
                    state,
                    "assistant",
                    "🎉 完整的心理评估报告已生成！请查看报告标签页。",
                )

                st.success("✅ 完整报告生成完成")

        except Exception as e:
            st.error(f"最终报告生成失败: {str(e)}")

    return state
