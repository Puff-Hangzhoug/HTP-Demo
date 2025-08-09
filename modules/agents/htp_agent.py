"""
HTP 分析代理主模块

这里包含了实际的 LangGraph 工作流定义
但在当前实现中，我们简化为直接调用节点函数
"""

from typing import Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from modules.utils.state import HTPState
from modules.agents.nodes import (
    analyze_image_node,
    generate_question_node,
    decide_next_category_node,
    process_user_response_node,
    category_analysis_node,
    comprehensive_analysis_node,
    process_dass21_node,
    final_report_node,
)


class HTPAgent:
    """HTP 分析代理类"""

    def __init__(self, llm: Any):
        """
        初始化 HTP 代理

        Args:
            llm: LLM 模型实例
        """
        self.llm = llm
        self.workflow = None
        self._create_workflow()

    def _create_workflow(self):
        """创建 LangGraph 工作流（当前版本中暂未使用）"""
        # 这里定义了 LangGraph 工作流，但实际使用中我们直接调用节点函数
        # 这样做的原因是 Streamlit 的状态管理与 LangGraph 的状态管理有一些冲突

        def analyze_image(state: HTPState) -> HTPState:
            return analyze_image_node(state, self.llm)

        def generate_question(state: HTPState) -> HTPState:
            return generate_question_node(state, self.llm)

        def category_analysis(state: HTPState) -> HTPState:
            return category_analysis_node(state, self.llm)

        def comprehensive_analysis(state: HTPState) -> HTPState:
            return comprehensive_analysis_node(state, self.llm)

        def final_report(state: HTPState) -> HTPState:
            return final_report_node(state, self.llm)

        # 创建状态图
        workflow = StateGraph(HTPState)

        # 添加节点
        workflow.add_node("analyze_image", analyze_image)
        workflow.add_node("generate_question", generate_question)
        workflow.add_node("category_analysis", category_analysis)
        workflow.add_node("comprehensive_analysis", comprehensive_analysis)
        workflow.add_node("final_report", final_report)

        # 定义边
        workflow.set_entry_point("analyze_image")
        workflow.add_edge("analyze_image", "generate_question")
        workflow.add_edge("category_analysis", "comprehensive_analysis")
        workflow.add_edge("comprehensive_analysis", "final_report")
        workflow.add_edge("final_report", END)

        # 编译图
        memory = MemorySaver()
        self.workflow = workflow.compile(checkpointer=memory)

    def analyze_image(self, state: HTPState) -> HTPState:
        """分析图像"""
        return analyze_image_node(state, self.llm)

    def generate_question(self, state: HTPState) -> HTPState:
        """生成问题"""
        return generate_question_node(state, self.llm)

    def decide_next_category(self, state: HTPState) -> str:
        """决定下一个类别"""
        return decide_next_category_node(state)

    def process_user_response(self, state: HTPState, user_response: str) -> HTPState:
        """处理用户回答"""
        return process_user_response_node(state, user_response)

    def analyze_categories(self, state: HTPState) -> HTPState:
        """进行类别分析"""
        return category_analysis_node(state, self.llm)

    def comprehensive_analysis(self, state: HTPState) -> HTPState:
        """进行综合分析"""
        return comprehensive_analysis_node(state, self.llm)

    def process_dass21(self, state: HTPState, responses: dict) -> HTPState:
        """处理 DASS-21 问卷"""
        return process_dass21_node(state, responses)

    def generate_final_report(self, state: HTPState) -> HTPState:
        """生成最终报告"""
        return final_report_node(state, self.llm)


def create_htp_agent(llm: Any) -> HTPAgent:
    """
    创建 HTP 分析代理实例

    Args:
        llm: LLM 模型实例

    Returns:
        HTPAgent: HTP 代理实例
    """
    return HTPAgent(llm)
