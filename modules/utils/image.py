"""
图像处理工具模块
"""

import base64
from io import BytesIO
from PIL import Image
from typing import Tuple


def encode_image(image_file: BytesIO) -> Tuple[str, str]:
    """
    将上传的图像文件转换为 base64 字符串

    Args:
        image_file: 图像文件的 BytesIO 对象

    Returns:
        Tuple[str, str]: (base64_string, media_type)
    """
    image = Image.open(image_file)

    # 处理透明度
    if image.mode in ("RGBA", "LA"):
        pass
    else:
        image = image.convert("RGB")

    # 转换为 PNG 格式的 bytes
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    # 编码为 base64
    base64_string = base64.b64encode(image_bytes).decode()

    return base64_string, "image/png"


def decode_base64_image(base64_string: str) -> Image.Image:
    """
    将 base64 字符串解码为 PIL 图像

    Args:
        base64_string: base64 编码的图像字符串（可能包含 data:image 前缀）

    Returns:
        PIL.Image.Image: 解码后的图像对象
    """
    # 移除可能的 data:image 前缀
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]

    # 解码 base64
    image_bytes = base64.b64decode(base64_string)

    # 创建 PIL 图像
    image = Image.open(BytesIO(image_bytes))

    return image


def resize_image(
    image: Image.Image, max_size: Tuple[int, int] = (800, 600)
) -> Image.Image:
    """
    调整图像大小，保持纵横比

    Args:
        image: PIL 图像对象
        max_size: 最大尺寸 (width, height)

    Returns:
        PIL.Image.Image: 调整后的图像
    """
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    return image


def get_image_info(image: Image.Image) -> dict:
    """
    获取图像的基本信息

    Args:
        image: PIL 图像对象

    Returns:
        dict: 包含图像信息的字典
    """
    return {
        "size": image.size,
        "mode": image.mode,
        "format": image.format,
        "width": image.width,
        "height": image.height,
    }
