#!/usr/bin/env node

/**
 * generate_pptx.js — 将 HTML 幻灯片转换为 PPTX 文件
 *
 * 用法: node generate_pptx.js
 *
 * 依赖: npm install pptxgenjs cheerio
 *   - pptxgenjs: PPTX 生成库
 *   - cheerio: HTML 解析
 *
 * 工作原理:
 *   1. 读取 slides.html，解析每张 .slide 的内容
 *   2. 提取文字、布局、配色信息
 *   3. 用 pptxgenjs 生成对应的 PPTX 幻灯片
 */

// === CONFIG START ===
const CONFIG = {
  inputFile: './slides.html',          // HTML 幻灯片路径
  outputFile: './演示文稿.pptx',       // 输出 PPTX 路径
  slideWidth: 13.33,                   // 16:9 宽度（英寸）
  slideHeight: 7.5,                    // 16:9 高度（英寸）
  defaultFontFace: 'Microsoft YaHei',  // 默认中文字体
  titleFontSize: 36,                   // 标题字号（pt）
  bodyFontSize: 16,                    // 正文字号（pt）
  subtitleFontSize: 20,                // 副标题字号（pt）
};
// === CONFIG END ===

const fs = require('fs');
const path = require('path');

// 检查依赖
let pptxgen, cheerio;
try {
  pptxgen = require('pptxgenjs');
  cheerio = require('cheerio');
} catch (e) {
  console.error('缺少依赖，请先安装：');
  console.error('  npm install pptxgenjs cheerio');
  process.exit(1);
}

// 解析 CSS 变量中的颜色
function extractCSSColors(html) {
  const colors = {
    primary: '1a1a2e',
    secondary: '16213e',
    accent: '0f3460',
    text: 'ffffff',
    textSecondary: 'cccccc',
  };

  const varPatterns = [
    [/--color-primary:\s*([^;]+)/i, 'primary'],
    [/--color-secondary:\s*([^;]+)/i, 'secondary'],
    [/--color-accent:\s*([^;]+)/i, 'accent'],
    [/--color-text:\s*([^;]+)/i, 'text'],
    [/--color-text-secondary:\s*([^;]+)/i, 'textSecondary'],
  ];

  for (const [pattern, key] of varPatterns) {
    const match = html.match(pattern);
    if (match) {
      let color = match[1].trim();
      // 去掉 # 号，pptxgenjs 需要纯 hex
      color = color.replace(/^#/, '');
      if (/^[0-9a-fA-F]{3,8}$/.test(color)) {
        // 3位转6位
        if (color.length === 3) {
          color = color[0] + color[0] + color[1] + color[1] + color[2] + color[2];
        }
        colors[key] = color.substring(0, 6);
      }
    }
  }

  return colors;
}

// 清理 HTML 文本
function cleanText(text) {
  if (!text) return '';
  return text
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

// 解析单张幻灯片
function parseSlide($, slideEl) {
  const slide = {
    texts: [],
    hasChart: false,
    bgColor: null,
  };

  // 提取背景色
  const style = $(slideEl).attr('style') || '';
  const bgMatch = style.match(/background(?:-color)?:\s*([^;]+)/i);
  if (bgMatch) {
    const bg = bgMatch[1].trim().replace(/^#/, '');
    if (/^[0-9a-fA-F]{6}$/.test(bg)) {
      slide.bgColor = bg;
    }
  }

  // 提取所有文本元素
  $(slideEl).find('h1, h2, h3, h4, h5, h6, p, li, span.big-number, .stat-number').each(function () {
    const el = $(this);
    const tag = this.tagName.toLowerCase();
    const text = cleanText(el.text());

    if (!text) return;

    let role = 'body';
    let fontSize = CONFIG.bodyFontSize;
    let bold = false;

    if (tag === 'h1') {
      role = 'title';
      fontSize = CONFIG.titleFontSize;
      bold = true;
    } else if (tag === 'h2') {
      role = 'title';
      fontSize = CONFIG.titleFontSize - 4;
      bold = true;
    } else if (tag === 'h3') {
      role = 'subtitle';
      fontSize = CONFIG.subtitleFontSize;
      bold = true;
    } else if (tag === 'h4' || tag === 'h5' || tag === 'h6') {
      role = 'subtitle';
      fontSize = CONFIG.subtitleFontSize - 2;
      bold = true;
    } else if (el.hasClass('big-number') || el.hasClass('stat-number')) {
      role = 'highlight';
      fontSize = 48;
      bold = true;
    }

    slide.texts.push({ text, role, fontSize, bold, tag });
  });

  // 检测是否有图表
  if ($(slideEl).find('canvas, .chart-container, .chart').length > 0) {
    slide.hasChart = true;
  }

  return slide;
}

async function main() {
  // 读取 HTML
  if (!fs.existsSync(CONFIG.inputFile)) {
    console.error(`文件不存在: ${CONFIG.inputFile}`);
    console.error('请先生成 slides.html');
    process.exit(1);
  }

  const html = fs.readFileSync(CONFIG.inputFile, 'utf-8');
  const $ = cheerio.load(html);
  const colors = extractCSSColors(html);

  // 查找所有幻灯片
  const slideEls = $('.slide').toArray();
  if (slideEls.length === 0) {
    console.error('未找到 .slide 元素，请确认 HTML 结构');
    process.exit(1);
  }

  console.log(`找到 ${slideEls.length} 张幻灯片`);
  console.log(`配色: primary=#${colors.primary}, accent=#${colors.accent}`);

  // 创建 PPTX
  const pres = new pptxgen();
  pres.defineLayout({
    name: 'CUSTOM_16x9',
    width: CONFIG.slideWidth,
    height: CONFIG.slideHeight,
  });
  pres.layout = 'CUSTOM_16x9';

  // 逐页生成
  for (let i = 0; i < slideEls.length; i++) {
    const parsed = parseSlide($, slideEls[i]);
    const pptSlide = pres.addSlide();

    // 设置背景
    const bgColor = parsed.bgColor || colors.primary;
    pptSlide.background = { color: bgColor };

    // 判断是浅色还是深色背景
    const bgBrightness = parseInt(bgColor.substring(0, 2), 16) * 0.299
      + parseInt(bgColor.substring(2, 4), 16) * 0.587
      + parseInt(bgColor.substring(4, 6), 16) * 0.114;
    const isLightBg = bgBrightness > 150;
    const textColor = isLightBg ? colors.text : colors.text;

    // 布局文本
    let yPos = 0.5; // 起始 Y 位置（英寸）

    for (const item of parsed.texts) {
      const opts = {
        x: 0.8,
        y: yPos,
        w: CONFIG.slideWidth - 1.6,
        fontSize: item.fontSize,
        fontFace: CONFIG.defaultFontFace,
        color: item.role === 'highlight' ? colors.accent : textColor,
        bold: item.bold,
        breakType: 'none',
        wrap: true,
      };

      if (item.role === 'title') {
        opts.y = yPos;
        opts.h = 1.0;
        pptSlide.addText(item.text, opts);
        yPos += 1.2;
      } else if (item.role === 'highlight') {
        opts.fontSize = 48;
        opts.h = 1.0;
        opts.align = 'center';
        pptSlide.addText(item.text, opts);
        yPos += 1.2;
      } else if (item.role === 'subtitle') {
        opts.h = 0.6;
        opts.color = colors.textSecondary;
        pptSlide.addText(item.text, opts);
        yPos += 0.8;
      } else {
        opts.h = 0.5;
        pptSlide.addText(item.text, opts);
        yPos += 0.6;
      }

      // 防止超出幻灯片
      if (yPos > CONFIG.slideHeight - 0.5) break;
    }

    // 如果有图表，添加占位提示
    if (parsed.hasChart && yPos < CONFIG.slideHeight - 1.5) {
      pptSlide.addText('[ 图表 — 请在 PowerPoint 中替换为实际图表 ]', {
        x: 0.8,
        y: yPos + 0.3,
        w: CONFIG.slideWidth - 1.6,
        h: 2.5,
        fontSize: 14,
        fontFace: CONFIG.defaultFontFace,
        color: colors.textSecondary,
        align: 'center',
        valign: 'middle',
        border: { type: 'dash', color: colors.accent, pt: 1 },
      });
    }

    console.log(`  幻灯片 ${i + 1}: ${parsed.texts.length} 个文本元素${parsed.hasChart ? ' + 图表' : ''}`);
  }

  // 保存
  const outputPath = path.resolve(CONFIG.outputFile);
  await pres.writeFile({ fileName: outputPath });
  console.log(`\n✅ PPTX 已生成: ${outputPath}`);
  console.log(`   文件大小: ${(fs.statSync(outputPath).size / 1024).toFixed(1)} KB`);
}

main().catch((err) => {
  console.error('❌ 生成失败:', err.message);
  process.exit(1);
});
