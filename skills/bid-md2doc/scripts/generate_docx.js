#!/usr/bin/env node
/**
 * Markdown 转 Word 文档生成器
 * 将响应文件目录下的所有.md文件合并为一个格式化的Word文档
 */

const fs = require('fs');
const path = require('path');
const {
  Document,
  Paragraph,
  TextRun,
  HeadingLevel,
  Table,
  TableCell,
  TableRow,
  WidthType,
  AlignmentType,
  BorderStyle,
  ImageRun,
  PageBreak,
  Header,
  Footer,
  PageNumber,
  NumberFormat,
} = require('docx');
const { Packer } = require('docx');

// === CONFIG START ===
const CONFIG = {
  inputDir: 'C:\\Users\\Administrator\\Documents\\bid\\TC261901F1\\响应文件',
  outputFile: '响应文件-琪信通达-清华房屋土地数智化平台.docx',
  headerText: '清华大学房屋土地数智化管理平台采购项目 响应文件',
  footerCompany: '琪信通达（北京）科技有限公司',
  excludeFiles: ['核对报告.md', '装订指南.md', '扫描件资料清单.md', '扫描件替换完成报告.md', '扫描件替换报告.md', '资料检索替换完成报告.md', '信息填写进度报告.md', 'Word文档待完善清单.md'],
};
// === CONFIG END ===

// 读取所有.md文件
function getMdFiles(dir) {
  const files = fs.readdirSync(dir)
    .filter(f => f.endsWith('.md'))
    .filter(f => !CONFIG.excludeFiles.includes(f))
    .sort((a, b) => {
      // 按文件名排序（数字优先）
      const numA = parseInt(a.match(/^\d+/)?.[0] || '999');
      const numB = parseInt(b.match(/^\d+/)?.[0] || '999');
      return numA - numB;
    });

  return files.map(f => path.join(dir, f));
}

// 解析Markdown标题层级
function getHeadingLevel(line) {
  const match = line.match(/^(#{1,6})\s+(.+)$/);
  if (!match) return null;

  const level = match[1].length;
  const text = match[2].trim();

  const levelMap = {
    1: HeadingLevel.HEADING_1,
    2: HeadingLevel.HEADING_2,
    3: HeadingLevel.HEADING_3,
    4: HeadingLevel.HEADING_4,
    5: HeadingLevel.HEADING_5,
    6: HeadingLevel.HEADING_6,
  };

  return { level: levelMap[level], text };
}

// 解析Markdown表格
function parseTable(lines, startIdx) {
  const tableLines = [];
  let idx = startIdx;

  // 跳过空行
  while (idx < lines.length && lines[idx].trim() === '') idx++;

  // 读取表格行
  while (idx < lines.length && lines[idx].includes('|')) {
    const line = lines[idx].trim();
    if (line.startsWith('|') && line.endsWith('|')) {
      tableLines.push(line);
    }
    idx++;
  }

  if (tableLines.length < 2) return { table: null, nextIdx: startIdx + 1 };

  // 解析表头
  const headers = tableLines[0]
    .split('|')
    .filter(cell => cell.trim())
    .map(cell => cell.trim());

  // 跳过分隔行
  const rows = tableLines.slice(2).map(line =>
    line.split('|')
      .filter(cell => cell.trim())
      .map(cell => cell.trim())
  );

  // 创建Word表格
  const tableRows = [
    // 表头
    new TableRow({
      children: headers.map(header =>
        new TableCell({
          children: [new Paragraph({ text: header, bold: true })],
          shading: { fill: 'E0E0E0' },
        })
      ),
    }),
    // 数据行
    ...rows.map(row =>
      new TableRow({
        children: row.map(cell =>
          new TableCell({
            children: [new Paragraph({ text: cell })],
          })
        ),
      })
    ),
  ];

  const table = new Table({
    rows: tableRows,
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 1 },
      bottom: { style: BorderStyle.SINGLE, size: 1 },
      left: { style: BorderStyle.SINGLE, size: 1 },
      right: { style: BorderStyle.SINGLE, size: 1 },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1 },
      insideVertical: { style: BorderStyle.SINGLE, size: 1 },
    },
  });

  return { table, nextIdx: idx };
}

// 解析图片
function parseImage(line, baseDir) {
  const match = line.match(/!\[(.*?)\]\((.*?)\)/);
  if (!match) return null;

  const alt = match[1];
  const imgPath = match[2];
  const fullPath = path.isAbsolute(imgPath) ? imgPath : path.join(baseDir, imgPath);

  try {
    if (!fs.existsSync(fullPath)) {
      console.warn(`图片不存在: ${fullPath}`);
      return new Paragraph({
        children: [new TextRun({ text: `[图片缺失: ${imgPath}]`, color: 'FF0000' })],
      });
    }

    const imageData = fs.readFileSync(fullPath);
    const ext = path.extname(fullPath).toLowerCase();

    // 获取图片尺寸（简单处理，固定宽度）
    const maxWidth = 550; // 约15cm

    return new Paragraph({
      children: [
        new ImageRun({
          data: imageData,
          transformation: {
            width: maxWidth,
            height: Math.floor(maxWidth * 0.75), // 假设4:3比例
          },
        }),
      ],
      alignment: AlignmentType.CENTER,
    });
  } catch (error) {
    console.error(`图片加载失败: ${fullPath}`, error.message);
    return new Paragraph({
      children: [new TextRun({ text: `[图片加载失败: ${imgPath}]`, color: 'FF0000' })],
    });
  }
}

// 解析Markdown内容
function parseMdContent(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  // 处理CRLF和LF混合的换行符，并去除每行末尾的\r
  const lines = content.split(/\r?\n/);
  const elements = [];
  const baseDir = path.dirname(filePath);

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    // 空行
    if (line.trim() === '') {
      i++;
      continue;
    }

    // HTML注释（辅助信息）
    if (line.trim().match(/^<!--.*-->$/)) {
      i++;
      continue;
    }

    // 分隔线
    if (line.trim().match(/^[-*_]{3,}$/)) {
      i++;
      continue;
    }

    // 标题
    const heading = getHeadingLevel(line);
    if (heading) {
      // 获取标题级别对应的字号
      const fontSize = {
        [HeadingLevel.HEADING_1]: 32,
        [HeadingLevel.HEADING_2]: 28,
        [HeadingLevel.HEADING_3]: 24,
        [HeadingLevel.HEADING_4]: 22,
        [HeadingLevel.HEADING_5]: 20,
        [HeadingLevel.HEADING_6]: 20,
      }[heading.level] || 24;

      elements.push(
        new Paragraph({
          children: [
            new TextRun({
              text: heading.text,
              bold: true,
              size: fontSize,
            })
          ],
          heading: heading.level,
          spacing: { before: 240, after: 120 },
        })
      );
      i++;
      continue;
    }

    // 表格
    if (line.includes('|')) {
      const { table, nextIdx } = parseTable(lines, i);
      if (table) {
        elements.push(table);
        elements.push(new Paragraph({ text: '' })); // 表格后空行
        i = nextIdx;
        continue;
      }
    }

    // 图片（支持被**包裹的图片）
    if (line.trim().includes('![')) {
      const img = parseImage(line, baseDir);
      if (img) elements.push(img);
      i++;
      continue;
    }

    // 代码块
    if (line.trim().startsWith('```')) {
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // 跳过结束的```

      elements.push(
        new Paragraph({
          children: [new TextRun({ text: codeLines.join('\n'), font: 'Consolas' })],
          shading: { fill: 'F5F5F5' },
        })
      );
      continue;
    }

    // 列表项（包括后续缩进内容）
    if (line.trim().match(/^[-*+]\s+/) || line.trim().match(/^\d+\.\s+/)) {
      // 移除列表前缀
      let text = line.trim();
      if (text.match(/^[-*+]\s+/)) {
        text = text.replace(/^[-*+]\s+/, '');
      } else if (text.match(/^\d+\.\s+/)) {
        text = text.replace(/^\d+\.\s+/, '');
      }

      // 收集后续的缩进内容（3空格或更多）
      let j = i + 1;
      const continuations = [];
      while (j < lines.length) {
        const nextLine = lines[j];
        // 空行结束当前列表项
        if (nextLine.trim() === '') {
          j++;
          break;
        }
        // 缩进内容（3+空格开头，且不是新列表项）
        if (nextLine.match(/^\s{3,}/) && !nextLine.trim().match(/^[-*+\d]+[\.)]\s+/)) {
          continuations.push(nextLine.trim());
          j++;
        } else {
          break;
        }
      }

      // 合并文本：标题 + 空格 + 内容
      const fullText = continuations.length > 0
        ? text + ' ' + continuations.join(' ')
        : text;

      // 处理粗体
      const parts = fullText.split(/(\*\*.*?\*\*)/);
      const children = parts
        .filter(part => part.length > 0) // 先过滤空字符串
        .map(part => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return new TextRun({ text: part.slice(2, -2), bold: true });
          }
          return new TextRun({ text: part });
        });

      // 只有当children不为空时才添加段落
      if (children.length > 0) {
        elements.push(
          new Paragraph({
            children: children,
            bullet: { level: 0 },
          })
        );
      }

      i = j; // 跳过已处理的行
      continue;
    }

    // 普通段落
    const text = line.trim();
    if (text) {
      // 处理粗体 **text**
      const parts = text.split(/(\*\*.*?\*\*)/);
      const children = parts
        .filter(part => part.length > 0) // 过滤空字符串
        .map(part => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return new TextRun({ text: part.slice(2, -2), bold: true });
          }
          return new TextRun({ text: part });
        });

      if (children.length > 0) {
        elements.push(new Paragraph({ children }));
      }
    }

    i++;
  }

  return elements;
}

// 生成Word文档
async function generateDocx() {
  console.log('='.repeat(60));
  console.log('Markdown 转 Word 文档生成器');
  console.log('='.repeat(60));
  console.log(`输入目录: ${CONFIG.inputDir}`);
  console.log(`输出文件: ${CONFIG.outputFile}`);
  console.log();

  const mdFiles = getMdFiles(CONFIG.inputDir);
  console.log(`找到 ${mdFiles.length} 个 Markdown 文件\n`);

  if (mdFiles.length === 0) {
    console.error('错误：未找到任何 .md 文件');
    process.exit(1);
  }

  const sections = [];
  let imageCount = 0;

  // 处理每个Markdown文件
  for (const filePath of mdFiles) {
    const fileName = path.basename(filePath);
    console.log(`处理: ${fileName}`);

    try {
      const elements = parseMdContent(filePath);

      // 统计图片数量
      imageCount += elements.filter(el =>
        el.root && el.root.some(child => child.constructor.name === 'ImageRun')
      ).length;

      // 添加文件分隔（除了第一个文件）
      if (sections.length > 0) {
        elements.unshift(
          new Paragraph({
            children: [new PageBreak()],
          })
        );
      }

      sections.push(...elements);
    } catch (error) {
      console.error(`  错误: ${error.message}`);
    }
  }

  console.log();
  console.log(`共处理 ${mdFiles.length} 个文件`);
  console.log(`嵌入 ${imageCount} 张图片`);
  console.log();

  // 创建文档
  const doc = new Document({
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: 1440,    // 1英寸 = 1440 twips
              right: 1440,
              bottom: 1440,
              left: 1440,
            },
          },
        },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                children: [new TextRun({ text: CONFIG.headerText, size: 20 })],
                alignment: AlignmentType.CENTER,
                border: {
                  bottom: {
                    style: BorderStyle.SINGLE,
                    size: 6,
                  },
                },
              }),
            ],
          }),
        },
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                children: [
                  new TextRun({ text: CONFIG.footerCompany, size: 18 }),
                  new TextRun({ text: '                                              第 ', size: 18 }),
                  new TextRun({
                    children: [PageNumber.CURRENT],
                  }),
                  new TextRun({ text: ' 页', size: 18 }),
                ],
                alignment: AlignmentType.CENTER,
                border: {
                  top: {
                    style: BorderStyle.SINGLE,
                    size: 6,
                  },
                },
              }),
            ],
          }),
        },
        children: sections,
      },
    ],
  });

  // 保存文档
  const outputPath = path.join(CONFIG.inputDir, CONFIG.outputFile);
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);

  const stats = fs.statSync(outputPath);
  const sizeKB = (stats.size / 1024).toFixed(2);

  console.log('='.repeat(60));
  console.log('生成完成！');
  console.log('='.repeat(60));
  console.log(`输出文件: ${outputPath}`);
  console.log(`文件大小: ${sizeKB} KB`);
  console.log(`MD文件数: ${mdFiles.length}`);
  console.log(`图片数: ${imageCount}`);
  console.log(`排除文件: ${CONFIG.excludeFiles.join(', ')}`);
  console.log('状态: SUCCESS');
  console.log('='.repeat(60));

  console.log('\n--- BID-MD2DOC COMPLETE ---');
  console.log(`输出文件: ${outputPath}`);
  console.log(`文件大小: ${sizeKB} KB`);
  console.log(`MD文件数: ${mdFiles.length}`);
  console.log(`图片数: ${imageCount}`);
  console.log(`排除文件: ${CONFIG.excludeFiles.join(', ')}`);
  console.log('状态: SUCCESS');
  console.log('--- END ---');
}

// 运行
generateDocx().catch(error => {
  console.error('生成失败:', error);
  process.exit(1);
});
