"""
Prompt 管理器模块
"""

import os
import yaml
import glob
import streamlit as st
from typing import Dict, Any, List, Optional
from langchain_core.prompts import load_prompt


class PromptManager:
    """Prompt 管理器类"""

    def __init__(self, prompts_path: str):
        """
        初始化 Prompt 管理器

        Args:
            prompts_path: prompts 文件夹路径
        """
        self.prompts_path = prompts_path
        self._prompt_cache = {}

    @st.cache_data(ttl=300)
    def load_yaml_metadata(_self, file_path: str) -> Dict[str, Any]:
        """加载 YAML 文件的 metadata"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data.get("metadata", {})
        except Exception as e:
            return {"error": str(e)}

    @st.cache_data(ttl=300)
    def get_all_prompt_files(_self) -> List[Dict[str, Any]]:
        """获取所有 prompt 文件信息"""
        prompt_files = []

        if not os.path.exists(_self.prompts_path):
            return prompt_files

        yaml_files = glob.glob(os.path.join(_self.prompts_path, "*.yaml"))

        for file_path in sorted(yaml_files):
            filename = os.path.basename(file_path)
            metadata = _self.load_yaml_metadata(file_path)

            prompt_files.append(
                {
                    "filename": filename,
                    "filepath": file_path,
                    "metadata": metadata,
                    "category": metadata.get("category", "unknown"),
                    "subcategory": metadata.get("subcategory", ""),
                    "version": metadata.get("version", "1.0"),
                    "description": metadata.get("description", ""),
                }
            )

        return prompt_files

    @st.cache_data(ttl=300)
    def load_prompt_with_langchain(_self, file_path: str) -> Dict[str, Any]:
        """使用 LangChain load_prompt 加载 prompt"""
        try:
            prompt = load_prompt(file_path)
            return {
                "success": True,
                "prompt": prompt,
                "input_variables": getattr(prompt, "input_variables", []),
                "template": getattr(prompt, "template", ""),
                "prompt_type": type(prompt).__name__,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def load_prompt_from_yaml(self, filename: str):
        """从 YAML 文件加载 LangChain prompt"""
        try:
            file_path = os.path.join(self.prompts_path, filename)

            # 使用缓存
            if filename in self._prompt_cache:
                return self._prompt_cache[filename]

            prompt = load_prompt(file_path)
            self._prompt_cache[filename] = prompt
            return prompt
        except Exception as e:
            st.error(f"加载 prompt 失败 ({filename}): {str(e)}")
            return None

    def get_prompt_by_category(
        self, category: str, subcategory: str = None
    ) -> Optional[str]:
        """根据类别获取 prompt 文件名"""
        prompt_files = self.get_all_prompt_files()

        for pf in prompt_files:
            if pf["category"] == category:
                if subcategory is None or pf["subcategory"] == subcategory:
                    return pf["filename"]

        return None

    def get_question_prompt_files(self) -> Dict[str, str]:
        """获取问题生成的 prompt 文件映射"""
        return {
            "person": "02_person_question.yaml",
            "house": "03_house_question.yaml",
            "tree": "04_tree_question.yaml",
            "overall": "05_overall_question.yaml",
        }

    def get_analysis_prompt_files(self) -> Dict[str, str]:
        """获取分析的 prompt 文件映射"""
        return {
            "person": "06_person_analysis.yaml",
            "house": "07_house_analysis.yaml",
            "tree": "08_tree_analysis.yaml",
            "overall": "09_overall_analysis.yaml",
        }

    def clear_cache(self):
        """清除缓存"""
        self._prompt_cache.clear()
        # 清除 Streamlit 缓存
        self.load_yaml_metadata.clear()
        self.get_all_prompt_files.clear()
        self.load_prompt_with_langchain.clear()


# 全局 Prompt 管理器实例
def get_prompt_manager(prompts_path: str = None) -> PromptManager:
    """获取 Prompt 管理器实例"""
    if prompts_path is None:
        # 默认路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, "..", "..")
        prompts_path = os.path.join(project_root, "prompts")

    if "prompt_manager" not in st.session_state:
        st.session_state.prompt_manager = PromptManager(prompts_path)

    return st.session_state.prompt_manager
