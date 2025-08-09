"""
LLM 模型管理模块
"""

import streamlit as st
import os
from langchain_aws import ChatBedrockConverse
from typing import Optional, List
import boto3

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())


@st.cache_data(show_spinner=False)
def list_bedrock_foundation_models(
    aws_region: str,
    aws_access_key: Optional[str] = None,
    aws_secret_key: Optional[str] = None,
    multimodal_only: bool = True,
) -> List[str]:
    """从 AWS Bedrock 动态获取可用的基础模型

    Args:
        aws_region: 区域，例如 "us-east-1"
        aws_access_key: 可选，访问密钥
        aws_secret_key: 可选，私密密钥
        multimodal_only: 是否仅返回支持 文本+图像 -> 文本 的多模态模型

    Returns:
        模型 ID 列表（按字母排序）。失败时返回安全的回退列表。
    """
    # 安全回退列表（Amazon Nova 系列，支持 text+image->text）
    fallback_models = [
        "amazon.nova-pro-v1:0",
        "amazon.nova-lite-v1:0",
        "amazon.nova-micro-v1:0",
    ]

    try:
        # 优先使用显式凭据，否则走默认凭据链（环境变量/本地配置）
        if aws_access_key and aws_secret_key:
            session = boto3.Session(
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region,
            )
        else:
            session = boto3.Session(region_name=aws_region)

        client = session.client("bedrock", region_name=aws_region)

        # 处理分页
        summaries = []
        next_token = None
        while True:
            if next_token:
                resp = client.list_foundation_models(nextToken=next_token)
            else:
                resp = client.list_foundation_models()
            summaries.extend(resp.get("modelSummaries", []))
            next_token = resp.get("nextToken")
            if not next_token:
                break

        if not summaries:
            return fallback_models

        def supports_text_image_to_text(summary: dict) -> bool:
            inputs = set(summary.get("inputModalities", []) or [])
            outputs = set(summary.get("outputModalities", []) or [])
            return {"TEXT", "IMAGE"}.issubset(inputs) and "TEXT" in outputs

        filtered = []
        for s in summaries:
            # 仅选择支持按需推理的模型，尽量提升可用性
            inference_types = set(s.get("inferenceTypesSupported", []) or [])
            if "ON_DEMAND" not in inference_types:
                continue
            if multimodal_only and not supports_text_image_to_text(s):
                continue
            model_id = s.get("modelId")
            if model_id:
                filtered.append(model_id)

        # 去重并排序
        unique_sorted = sorted(list(dict.fromkeys(filtered)))

        # 如果包含 nova-pro，则提升为默认（放到列表首位）
        preferred_model = "amazon.nova-pro-v1:0"
        if preferred_model in unique_sorted:
            unique_sorted = [preferred_model] + [
                m for m in unique_sorted if m != preferred_model
            ]

        return unique_sorted or fallback_models
    except Exception as e:
        # 出错时回退并提示
        st.warning(f"未能动态获取 Bedrock 模型列表，使用默认列表。原因: {str(e)}")
        return fallback_models


def get_foundation_models() -> list[str]:
    """兼容旧接口：从环境变量读取区域与凭据，动态返回模型列表。"""
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    access = os.getenv("AWS_ACCESS_KEY_ID")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    return list_bedrock_foundation_models(
        aws_region=region,
        aws_access_key=access,
        aws_secret_key=secret,
        multimodal_only=True,
    )


@st.cache_resource
def create_chat_model(
    _aws_access_key: str,
    _aws_secret_key: str,
    _aws_region: str,
    _model_id: str,
    _temperature: float,
    _max_tokens: int,
) -> Optional[ChatBedrockConverse]:
    """创建并缓存 ChatBedrockConverse 模型"""
    try:
        # 设置环境变量
        os.environ["AWS_ACCESS_KEY_ID"] = _aws_access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = _aws_secret_key
        os.environ["AWS_DEFAULT_REGION"] = _aws_region

        llm = ChatBedrockConverse(
            model=_model_id,
            temperature=_temperature,
            max_tokens=_max_tokens,
            region_name=_aws_region,
        )
        return llm
    except Exception as e:
        st.error(f"模型创建失败: {str(e)}")
        return None


def get_model_config_ui():
    """获取模型配置的 UI 组件"""
    st.subheader("🤖 模型配置")

    aws_access_key = st.text_input(
        "AWS Access Key",
        type="password",
        value=os.getenv("AWS_ACCESS_KEY_ID", ""),
        help="输入您的 AWS Access Key ID",
    )

    aws_secret_key = st.text_input(
        "AWS Secret Key",
        type="password",
        value=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        help="输入您的 AWS Secret Access Key",
    )

    aws_region = st.selectbox(
        "AWS Region", ["us-east-1", "us-west-2"], index=0, help="选择 AWS 区域"
    )

    multimodal_only = st.checkbox(
        "仅显示多模态模型（文本+图像 → 文本）", value=True, help="用于图像总结与对话"
    )

    # 动态列出可用模型
    model_options = list_bedrock_foundation_models(
        aws_region=aws_region,
        aws_access_key=aws_access_key or None,
        aws_secret_key=aws_secret_key or None,
        multimodal_only=multimodal_only,
    )
    model_id = st.selectbox("Foundation Model", model_options, help="选择基础模型")

    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider(
            "Temperature", 0.0, 1.0, 0.7, 0.1, help="控制输出的创造性，值越高越有创意"
        )
    with col2:
        max_tokens = st.slider(
            "Max Tokens", 500, 5000, 3000, 100, help="限制输出的最大长度"
        )

    return {
        "aws_access_key": aws_access_key,
        "aws_secret_key": aws_secret_key,
        "aws_region": aws_region,
        "model_id": model_id,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def create_llm_from_config(config: dict) -> Optional[ChatBedrockConverse]:
    """根据配置创建 LLM 模型"""
    if not config["aws_access_key"] or not config["aws_secret_key"]:
        return None

    return create_chat_model(
        config["aws_access_key"],
        config["aws_secret_key"],
        config["aws_region"],
        config["model_id"],
        config["temperature"],
        config["max_tokens"],
    )
