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
    rotation: int = 0,
    tile: bool = False,
) -> str:
    """为图片添加水印

    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径（如果为 None，则覆盖原图）
        watermark_text: 水印文字
        position: 水印位置 (bottom_right, bottom_center, bottom_left, top_right, top_center, top_left, center)
        opacity: 透明度 (0-255，0为完全透明，255为完全不透明)
        font_size: 字体大小
        color: 水印颜色 (R, G, B)
        margin: 水印边距（像素）
        rotation: 旋转角度（逆时针，0=水平，-45=右下到左上斜向）
        tile: 是否平铺多个水印贯穿整个图片

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

    # 使用混合字体方案：中文用CJK字体，数字/ASCII用西文字体
    # 这样可以避免CJK字体对ASCII字符支持不完整的问题

    # 加载中文字体
    cn_font = None
    cn_font_paths = [
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "C:\\Windows\\Fonts\\simhei.ttf",
    ]

    for font_path in cn_font_paths:
        if os.path.exists(font_path):
            try:
                if font_path.endswith('.ttc'):
                    cn_font = ImageFont.truetype(font_path, font_size, index=2)
                else:
                    cn_font = ImageFont.truetype(font_path, font_size)
                logger.debug(f"Loaded Chinese font: {font_path}")
                break
            except Exception as e:
                logger.debug(f"Failed to load Chinese font {font_path}: {e}")
                continue

    # 加载西文/数字字体
    en_font = None
    en_font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]

    for font_path in en_font_paths:
        if os.path.exists(font_path):
            try:
                en_font = ImageFont.truetype(font_path, font_size)
                logger.debug(f"Loaded English font: {font_path}")
                break
            except Exception as e:
                logger.debug(f"Failed to load English font {font_path}: {e}")
                continue

    # 如果无法加载字体，使用默认字体
    if cn_font is None:
        cn_font = ImageFont.load_default()
        logger.warning("Using default font for Chinese")
    if en_font is None:
        en_font = ImageFont.load_default()
        logger.warning("Using default font for English")

    # 将文本分段：中文字符用cn_font，ASCII字符用en_font
    import re
    segments = []
    current_segment = ""
    current_type = None

    for char in watermark_text:
        # 判断字符类型：ASCII (包括数字) 或 非ASCII (中文等)
        is_ascii = ord(char) < 128

        if current_type is None:
            current_type = 'ascii' if is_ascii else 'chinese'
            current_segment = char
        elif (is_ascii and current_type == 'ascii') or (not is_ascii and current_type == 'chinese'):
            current_segment += char
        else:
            segments.append((current_type, current_segment))
            current_type = 'ascii' if is_ascii else 'chinese'
            current_segment = char

    if current_segment:
        segments.append((current_type, current_segment))

    # 计算总宽度
    total_width = 0
    max_height = 0
    for seg_type, seg_text in segments:
        font = en_font if seg_type == 'ascii' else cn_font
        try:
            bbox = draw.textbbox((0, 0), seg_text, font=font)
            seg_width = bbox[2] - bbox[0]
            seg_height = bbox[3] - bbox[1]
        except AttributeError:
            seg_width, seg_height = draw.textsize(seg_text, font=font)
        total_width += seg_width
        max_height = max(max_height, seg_height)

    # 计算起始位置
    img_width, img_height = img.size
    text_color = (*color, opacity)

    # 如果需要旋转或平铺，使用特殊绘制逻辑
    if rotation != 0 or tile:
        # 创建文本图层（刚好容纳文本，留一些padding）
        padding = 50
        text_layer_w = int(total_width + padding * 2)
        text_layer_h = int(max_height + padding * 2)
        text_layer = Image.new('RGBA', (text_layer_w, text_layer_h), (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_layer)

        # 在文本图层中心绘制水印
        text_x = padding
        text_y = padding
        current_x = text_x

        for seg_type, seg_text in segments:
            font = en_font if seg_type == 'ascii' else cn_font
            text_draw.text((current_x, text_y), seg_text, font=font, fill=text_color)
            try:
                bbox = text_draw.textbbox((current_x, text_y), seg_text, font=font)
                current_x = bbox[2]
            except AttributeError:
                seg_width, _ = text_draw.textsize(seg_text, font=font)
                current_x += seg_width

        # 旋转文本图层
        if rotation != 0:
            text_layer = text_layer.rotate(rotation, expand=True, resample=Image.BICUBIC)

        # 平铺或单个水印
        if tile:
            # 计算需要平铺的行数和列数
            text_w, text_h = text_layer.size
            # 使用原始文本大小作为间距基准
            spacing_x = int(total_width * 1.5)
            spacing_y = int(max_height * 2)

            for y_offset in range(-text_h, img_height + text_h, spacing_y):
                for x_offset in range(-text_w, img_width + text_w, spacing_x):
                    watermark_layer.paste(text_layer, (x_offset, y_offset), text_layer)
        else:
            # 单个水印，根据position定位
            text_w, text_h = text_layer.size
            if position == "center":
                paste_x = (img_width - text_w) // 2
                paste_y = (img_height - text_h) // 2
            elif position == "bottom_right":
                paste_x = img_width - text_w - margin
                paste_y = img_height - text_h - margin
            elif position == "bottom_center":
                paste_x = (img_width - text_w) // 2
                paste_y = img_height - text_h - margin
            elif position == "bottom_left":
                paste_x = margin
                paste_y = img_height - text_h - margin
            elif position == "top_right":
                paste_x = img_width - text_w - margin
                paste_y = margin
            elif position == "top_center":
                paste_x = (img_width - text_w) // 2
                paste_y = margin
            elif position == "top_left":
                paste_x = margin
                paste_y = margin
            else:
                paste_x = (img_width - text_w) // 2
                paste_y = (img_height - text_h) // 2

            watermark_layer.paste(text_layer, (paste_x, paste_y), text_layer)
    else:
        # 原有的非旋转逻辑
        if position == "bottom_right":
            x = img_width - total_width - margin
            y = img_height - max_height - margin
        elif position == "bottom_center":
            x = (img_width - total_width) // 2
            y = img_height - max_height - margin
        elif position == "bottom_left":
            x = margin
            y = img_height - max_height - margin
        elif position == "top_right":
            x = img_width - total_width - margin
            y = margin
        elif position == "top_center":
            x = (img_width - total_width) // 2
            y = margin
        elif position == "top_left":
            x = margin
            y = margin
        elif position == "center":
            x = (img_width - total_width) // 2
            y = (img_height - max_height) // 2
        else:
            x = img_width - total_width - margin
            y = img_height - max_height - margin

        # 分段绘制水印
        current_x = x
        for seg_type, seg_text in segments:
            font = en_font if seg_type == 'ascii' else cn_font
            draw.text((current_x, y), seg_text, font=font, fill=text_color)
            try:
                bbox = draw.textbbox((current_x, y), seg_text, font=font)
                current_x = bbox[2]
            except AttributeError:
                seg_width, _ = draw.textsize(seg_text, font=font)
                current_x += seg_width

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
    parser.add_argument("-p", "--position", default="center",
                        choices=["bottom_right", "bottom_center", "bottom_left",
                                "top_right", "top_center", "top_left", "center"],
                        help="Watermark position")
    parser.add_argument("--opacity", type=int, default=128,
                        help="Watermark opacity (0-255)")
    parser.add_argument("--font-size", type=int, default=24,
                        help="Font size")
    parser.add_argument("--color", default="128,128,128",
                        help="Watermark color (R,G,B)")
    parser.add_argument("--margin", type=int, default=20,
                        help="Margin from edge")
    parser.add_argument("--rotation", type=int, default=0,
                        help="Rotation angle in degrees (e.g., -45 for diagonal)")
    parser.add_argument("--tile", action="store_true",
                        help="Tile watermark across entire image")
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
            rotation=args.rotation,
            tile=args.tile,
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
            rotation=args.rotation,
            tile=args.tile,
        )
        print(f"Watermarked image saved to: {result}")
