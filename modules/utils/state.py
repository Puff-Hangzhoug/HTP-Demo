"""
HTP 状态管理模块
"""

from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime


class HTPState(TypedDict):
    """HTP 分析系统的完整状态定义"""

    # 原始数据
    image_analysis: Optional[str]
    uploaded_image: Optional[str]  # base64 image

    # 问答阶段数据
    current_category: Optional[str]  # "person", "house", "tree", "overall"
    conversation_history: List[Dict[str, str]]
    collected_info: Dict[str, List[str]]  # {category: [responses]}
    categories_covered: List[str]
    is_qa_complete: bool
    current_question: Optional[str]
    total_questions_asked: int

    # 问答配置
    qa_config: Dict[str, Any]
    # 每个类别的覆盖评估结果
    category_coverage: Dict[str, Dict[str, Any]]

    # DASS-21 问卷数据
    dass21_responses: Dict[int, int]  # {question_num: score}
    dass21_scores: Dict[
        str, int
    ]  # {"depression": score, "anxiety": score, "stress": score}
    dass21_levels: Dict[
        str, str
    ]  # {"depression": "轻度", "anxiety": "正常", "stress": "中度"}
    is_dass21_complete: bool

    # 分析阶段数据
    category_analyses: Dict[str, str]  # {category: analysis_result}
    comprehensive_analysis: Optional[str]  # 综合分析结果
    final_report: Optional[str]  # 最终完整报告

    # 流程控制
    current_stage: str  # "image_analysis", "qa_loop", "category_analysis", "comprehensive", "dass21", "final_report"
    stage_progress: Dict[str, bool]
    analysis_timestamp: Optional[str]

    # 聊天界面相关
    chat_messages: List[Dict[str, str]]  # 聊天记录
    waiting_for_user_input: bool


def create_initial_state() -> HTPState:
    """创建初始的 HTP 状态"""
    return HTPState(
        image_analysis=None,
        uploaded_image=None,
        current_category=None,
        conversation_history=[],
        collected_info={},
        categories_covered=[],
        is_qa_complete=False,
        current_question=None,
        total_questions_asked=0,
        qa_config={
            # 每个类别的最多提问数（上限，用于防止无限循环）
            "max_questions_per_category": 2,
            # 全局最多提问总数（所有类别累计）
            "max_total_questions": 8,
            # 是否启用智能覆盖度评估
            "enable_smart_coverage": False,
            # 达到该覆盖度阈值（0-1）即可视为该类别“已覆盖充分”
            "coverage_threshold": 0.7,
            # 生成的新问题与历史问题的相似度阈值（0-1），超过则视为重复并重试
            "dedupe_similarity_threshold": 0.88,
        },
        category_coverage={},
        dass21_responses={},
        dass21_scores={},
        dass21_levels={},
        is_dass21_complete=False,
        category_analyses={},
        comprehensive_analysis=None,
        final_report=None,
        current_stage="image_analysis",
        stage_progress={
            "image_analysis": False,
            "qa_loop": False,
            "category_analysis": False,
            "comprehensive": False,
            "dass21": False,
            "final_report": False,
        },
        analysis_timestamp=None,
        chat_messages=[],
        waiting_for_user_input=False,
    )


def reset_state(state: HTPState) -> HTPState:
    """重置状态到初始状态"""
    return create_initial_state()


def get_stage_display_name(stage: str) -> str:
    """获取阶段的显示名称"""
    stage_names = {
        "image_analysis": "🔍 图像分析",
        "qa_loop": "💬 问答阶段",
        "category_analysis": "📝 类别分析",
        "comprehensive": "🧠 综合分析",
        "dass21": "📝 DASS-21 量表",
        "final_report": "📊 完整报告",
    }
    return stage_names.get(stage, stage)


def get_category_display_name(category: str) -> str:
    """获取类别的显示名称"""
    category_names = {
        "person": "👤 人物",
        "house": "🏠 房子",
        "tree": "🌳 树木",
        "overall": "🎨 整体感受",
    }
    return category_names.get(category, category)


def update_stage_progress(
    state: HTPState, stage: str, completed: bool = True
) -> HTPState:
    """更新阶段进度"""
    state["stage_progress"][stage] = completed
    if completed:
        state["analysis_timestamp"] = datetime.now().isoformat()
    return state


def add_chat_message(state: HTPState, role: str, content: str) -> HTPState:
    """添加聊天消息"""
    state["chat_messages"].append({"role": role, "content": content})
    return state


def add_conversation_entry(
    state: HTPState, category: str, question: str, response: str
) -> HTPState:
    """添加对话记录"""
    state["conversation_history"].append(
        {
            "category": category,
            "question": question,
            "response": response,
            "timestamp": datetime.now().isoformat(),
        }
    )

    # 同时添加到收集的信息中
    if category not in state["collected_info"]:
        state["collected_info"][category] = []
    state["collected_info"][category].append(response)

    return state
