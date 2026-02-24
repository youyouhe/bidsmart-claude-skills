#!/usr/bin/env python3
"""
Word文档图片水印工具

为Word文档(.docx)中的所有图片添加水印。
"""

import os
import logging
from pathlib import Path
from io import BytesIO
from docx import Document
from docx.shared import Inches
from PIL import Image

from watermark import add_watermark, get_project_name_from_analysis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def add_watermark_to_docx(
    docx_path: str | Path,
    output_path: str | Path | None = None,
    watermark_text: str = "",
    position: str = "bottom_right",
    opacity: int = 128,
    font_size: int = 20,
    color: tuple = (128, 128, 128),
    margin: int = 15,
    rotation: int = 0,
    tile: bool = False,
) -> str:
    """为Word文档中的所有图片添加水印

    Args:
        docx_path: 输入Word文档路径
        output_path: 输出Word文档路径（如果为None，则覆盖原文件）
        watermark_text: 水印文字
        position: 水印位置
        opacity: 透明度 (0-255)
        font_size: 字体大小
        color: 水印颜色 (R, G, B)
        rotation: 旋转角度（-45=斜向）
        tile: 是否平铺贯穿整个图片
        margin: 水印边距

    Returns:
        输出文档路径
    """
    if not watermark_text:
        logger.warning("Watermark text is empty, skipping watermark")
        return str(docx_path)

    docx_path = Path(docx_path)
    if not docx_path.exists():
        raise FileNotFoundError(f"Word document not found: {docx_path}")

    if output_path is None:
        output_path = docx_path
    else:
        output_path = Path(output_path)

    logger.info(f"Processing Word document: {docx_path}")

    # 打开Word文档
    doc = Document(docx_path)

    processed_count = 0
    skipped_count = 0

    # 处理所有InlineShape（嵌入式图片）
    for rel_id, rel in doc.part.rels.items():
        if "image" in rel.target_ref:
            try:
                # 获取图片数据
                image_part = rel.target_part
                image_bytes = image_part.blob

                # 将图片数据转换为PIL Image
                image = Image.open(BytesIO(image_bytes))

                # 只处理PNG/JPG格式
                if image.format not in ['PNG', 'JPEG']:
                    logger.debug(f"Skipping non-PNG/JPG image: {image.format}")
                    skipped_count += 1
                    continue

                logger.debug(f"Processing image: {rel.target_ref}, format: {image.format}, size: {image.size}")

                # 保存原始图片到临时文件
                temp_image = BytesIO()
                if image.format == 'JPEG':
                    image.save(temp_image, format='JPEG', quality=95)
                else:
                    image.save(temp_image, format='PNG')
                temp_image.seek(0)

                # 写入临时文件用于水印处理
                temp_path = Path(f"/tmp/temp_image_{rel_id}.png")
                with open(temp_path, 'wb') as f:
                    f.write(temp_image.getvalue())

                # 添加水印
                add_watermark(
                    image_path=temp_path,
                    output_path=temp_path,
                    watermark_text=watermark_text,
                    position=position,
                    opacity=opacity,
                    font_size=font_size,
                    color=color,
                    margin=margin,
                    rotation=rotation,
                    tile=tile,
                )

                # 读取处理后的图片
                with open(temp_path, 'rb') as f:
                    watermarked_bytes = f.read()

                # 替换Word文档中的图片数据
                image_part._blob = watermarked_bytes

                # 清理临时文件
                temp_path.unlink()

                processed_count += 1
                logger.debug(f"Added watermark to image: {rel.target_ref}")

            except Exception as e:
                logger.error(f"Failed to process image {rel.target_ref}: {e}")
                skipped_count += 1

    # 保存处理后的文档
    doc.save(output_path)

    logger.info(f"Processed {processed_count} images, skipped {skipped_count} images")
    logger.info(f"Saved watermarked document to: {output_path}")

    return str(output_path)


def batch_add_watermark_to_docx(
    input_dir: str | Path,
    output_dir: str | Path | None = None,
    watermark_text: str = "",
    **kwargs
) -> list[str]:
    """批量为目录下的Word文档添加水印

    Args:
        input_dir: 输入目录
        output_dir: 输出目录（如果为None，则覆盖原文件）
        watermark_text: 水印文字
        **kwargs: 传递给 add_watermark_to_docx 的其他参数

    Returns:
        处理成功的文档路径列表
    """
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    processed = []

    for docx_path in input_dir.glob("*.docx"):
        # 跳过临时文件
        if docx_path.name.startswith("~$"):
            continue

        try:
            if output_dir:
                output_path = output_dir / docx_path.name
            else:
                output_path = None

            result_path = add_watermark_to_docx(
                docx_path,
                output_path,
                watermark_text,
                **kwargs
            )
            processed.append(result_path)

        except Exception as e:
            logger.error(f"Failed to process {docx_path}: {e}")

    logger.info(f"Batch processed {len(processed)} documents")
    return processed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add watermark to images in Word documents")
    parser.add_argument("input", help="Input Word document or directory")
    parser.add_argument("-o", "--output", help="Output document or directory")
    parser.add_argument("-t", "--text", help="Watermark text")
    parser.add_argument("-p", "--position", default="center",
                        choices=["bottom_right", "bottom_center", "bottom_left",
                                "top_right", "top_center", "top_left", "center"],
                        help="Watermark position")
    parser.add_argument("--opacity", type=int, default=128,
                        help="Watermark opacity (0-255)")
    parser.add_argument("--font-size", type=int, default=20,
                        help="Font size")
    parser.add_argument("--color", default="128,128,128",
                        help="Watermark color (R,G,B)")
    parser.add_argument("--margin", type=int, default=15,
                        help="Margin from edge")
    parser.add_argument("--rotation", type=int, default=-45,
                        help="Rotation angle in degrees (e.g., -45 for diagonal)")
    parser.add_argument("--tile", action="store_true",
                        help="Tile watermark across entire image")
    parser.add_argument("--auto-project-name", action="store_true",
                        help="Auto-detect project name from 分析报告.md")
    parser.add_argument("--batch", action="store_true",
                        help="Process all Word documents in directory")

    args = parser.parse_args()

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

    # 处理文档
    input_path = Path(args.input)

    if args.batch or input_path.is_dir():
        # 批量处理
        processed = batch_add_watermark_to_docx(
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
        print(f"Processed {len(processed)} Word documents")
    else:
        # 单个文档
        result = add_watermark_to_docx(
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
        print(f"Watermarked document saved to: {result}")
