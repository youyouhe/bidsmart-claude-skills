#!/usr/bin/env python3
"""
图片水印工具

为投标材料图片添加项目名称水印，防止材料被滥用。
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)


def add_watermark(
    image_path: str | Path,
    output_path: str | Path | None = None,
    watermark_text: str = "",
    position: str = "bottom_right",
    opacity: int = 128,
    font_size: int = 24,
    color: tuple = (128, 128, 128),
    margin: int = 20,
) -> str:
    """为图片添加水印

    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径（如果为 None，则覆盖原图）
        watermark_text: 水印文字
        position: 水印位置 (bottom_right, bottom_center, bottom_left, top_right, top_center, top_left)
        opacity: 透明度 (0-255，0为完全透明，255为完全不透明)
        font_size: 字体大小
        color: 水印颜色 (R, G, B)
        margin: 水印边距（像素）

    Returns:
        输出图片路径
    """
    if not watermark_text:
        logger.warning("Watermark text is empty, skipping watermark")
        return str(image_path)

    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # 如果没有指定输出路径，覆盖原图
    if output_path is None:
        output_path = image_path
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # 打开图片
    img = Image.open(image_path)

    # 转换为 RGBA 模式（支持透明度）
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # 创建一个透明层用于绘制水印
    watermark_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(watermark_layer)

    # 尝试加载中文字体
    # 格式：(字体路径, 字体索引)
    # TTC文件包含多个字体，需要指定索引
    # index=3 通常是简体中文 (SC)
    font = None
    font_configs = [
        # Linux 常见中文字体路径
        ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0),
        ("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", 0),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 3),  # index=3 是简体中文
        # macOS 中文字体
        ("/System/Library/Fonts/PingFang.ttc", 0),
        ("/Library/Fonts/Arial Unicode.ttf", 0),
        # Windows 中文字体
        ("C:\\Windows\\Fonts\\msyh.ttc", 0),  # 微软雅黑
        ("C:\\Windows\\Fonts\\simhei.ttf", 0),  # 黑体
    ]

    for font_path, font_index in font_configs:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size, index=font_index)
                logger.debug(f"Loaded font: {font_path} (index={font_index})")
                break
            except Exception as e:
                logger.debug(f"Failed to load font {font_path} (index={font_index}): {e}")
                continue

    if font is None:
        # 使用默认字体
        font = ImageFont.load_default()
        logger.warning("Using default font (may not support Chinese and numbers)")

    # 获取文字尺寸
    try:
        # PIL 10.0.0+ 使用 textbbox
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        # 旧版本 PIL 使用 textsize
        text_width, text_height = draw.textsize(watermark_text, font=font)

    # 计算水印位置
    img_width, img_height = img.size

    if position == "bottom_right":
        x = img_width - text_width - margin
        y = img_height - text_height - margin
    elif position == "bottom_center":
        x = (img_width - text_width) // 2
        y = img_height - text_height - margin
    elif position == "bottom_left":
        x = margin
        y = img_height - text_height - margin
    elif position == "top_right":
        x = img_width - text_width - margin
        y = margin
    elif position == "top_center":
        x = (img_width - text_width) // 2
        y = margin
    elif position == "top_left":
        x = margin
        y = margin
    else:
        # 默认右下角
        x = img_width - text_width - margin
        y = img_height - text_height - margin

    # 绘制水印（带透明度）
    text_color = (*color, opacity)
    draw.text((x, y), watermark_text, font=font, fill=text_color)

    # 合并图层
    watermarked = Image.alpha_composite(img, watermark_layer)

    # 如果原图不是 PNG，转回原格式
    if image_path.suffix.lower() in ['.jpg', '.jpeg']:
        watermarked = watermarked.convert('RGB')
        watermarked.save(output_path, 'JPEG', quality=95)
    else:
        watermarked.save(output_path, 'PNG')

    logger.info(f"Added watermark to {image_path} -> {output_path}")
    return str(output_path)


def get_project_name_from_analysis(analysis_path: str | Path = "分析报告.md") -> str:
    """从分析报告中获取项目名称

    Args:
        analysis_path: 分析报告路径

    Returns:
        项目名称，如果未找到则返回空字符串
    """
    analysis_path = Path(analysis_path)

    if not analysis_path.exists():
        logger.warning(f"Analysis file not found: {analysis_path}")
        return ""

    try:
        with open(analysis_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 尝试从多个位置提取项目名称
        patterns = [
            "项目名称：",
            "项目名称:",
            "**项目名称**：",
            "**项目名称**:",
            "项目：",
            "项目:",
        ]

        for pattern in patterns:
            if pattern in content:
                # 找到模式后的内容
                start = content.find(pattern) + len(pattern)
                # 提取到换行符为止
                end = content.find('\n', start)
                if end == -1:
                    end = len(content)

                project_name = content[start:end].strip()
                # 去除可能的 markdown 格式
                project_name = project_name.replace('**', '').replace('*', '').strip()

                if project_name:
                    logger.info(f"Found project name: {project_name}")
                    return project_name

        logger.warning("Project name not found in analysis file")
        return ""

    except Exception as e:
        logger.error(f"Failed to read analysis file: {e}")
        return ""


def add_watermark_batch(
    image_dir: str | Path,
    output_dir: str | Path | None = None,
    watermark_text: str = "",
    **kwargs
) -> list[str]:
    """批量为目录下的图片添加水印

    Args:
        image_dir: 输入图片目录
        output_dir: 输出目录（如果为 None，则覆盖原图）
        watermark_text: 水印文字
        **kwargs: 传递给 add_watermark 的其他参数

    Returns:
        处理成功的图片路径列表
    """
    image_dir = Path(image_dir)
    if not image_dir.exists():
        raise FileNotFoundError(f"Directory not found: {image_dir}")

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    processed = []
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}

    for image_path in image_dir.iterdir():
        if image_path.suffix.lower() in image_extensions:
            try:
                if output_dir:
                    output_path = output_dir / image_path.name
                else:
                    output_path = None

                result_path = add_watermark(
                    image_path,
                    output_path,
                    watermark_text,
                    **kwargs
                )
                processed.append(result_path)

            except Exception as e:
                logger.error(f"Failed to add watermark to {image_path}: {e}")

    logger.info(f"Processed {len(processed)} images")
    return processed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add watermark to images")
    parser.add_argument("input", help="Input image or directory")
    parser.add_argument("-o", "--output", help="Output image or directory")
    parser.add_argument("-t", "--text", help="Watermark text")
    parser.add_argument("-p", "--position", default="bottom_right",
                        choices=["bottom_right", "bottom_center", "bottom_left",
                                "top_right", "top_center", "top_left"],
                        help="Watermark position")
    parser.add_argument("--opacity", type=int, default=128,
                        help="Watermark opacity (0-255)")
    parser.add_argument("--font-size", type=int, default=24,
                        help="Font size")
    parser.add_argument("--color", default="128,128,128",
                        help="Watermark color (R,G,B)")
    parser.add_argument("--margin", type=int, default=20,
                        help="Margin from edge")
    parser.add_argument("--auto-project-name", action="store_true",
                        help="Auto-detect project name from 分析报告.md")
    parser.add_argument("--batch", action="store_true",
                        help="Process all images in directory")

    args = parser.parse_args()

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 获取水印文字
    watermark_text = args.text
    if args.auto_project_name and not watermark_text:
        watermark_text = get_project_name_from_analysis()
        if not watermark_text:
            print("Error: Could not find project name in 分析报告.md")
            exit(1)

    if not watermark_text:
        print("Error: Watermark text is required")
        exit(1)

    # 解析颜色
    try:
        color = tuple(map(int, args.color.split(',')))
        if len(color) != 3:
            raise ValueError
    except ValueError:
        print("Error: Invalid color format. Use R,G,B (e.g., 128,128,128)")
        exit(1)

    # 处理图片
    input_path = Path(args.input)

    if args.batch or input_path.is_dir():
        # 批量处理
        processed = add_watermark_batch(
            input_path,
            args.output,
            watermark_text,
            position=args.position,
            opacity=args.opacity,
            font_size=args.font_size,
            color=color,
            margin=args.margin,
        )
        print(f"Processed {len(processed)} images")
    else:
        # 单个图片
        result = add_watermark(
            input_path,
            args.output,
            watermark_text,
            position=args.position,
            opacity=args.opacity,
            font_size=args.font_size,
            color=color,
            margin=args.margin,
        )
        print(f"Watermarked image saved to: {result}")
