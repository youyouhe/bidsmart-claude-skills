#!/usr/bin/env node

/**
 * merge.js — 合并所有单页 HTML 为一个完整的 slides.html
 *
 * 用法: node merge.js
 *
 * 工作原理:
 *   1. 查找当前目录所有 slide-*.html 文件
 *   2. 按文件名排序（slide-01, slide-02, ...）
 *   3. 提取每个文件的 <div class="slide"> 内容
 *   4. 从第一个文件提取完整 <head> 和 CSS
 *   5. 合并为一个 slides.html，包含导航 JS
 */

const fs = require('fs');
const path = require('path');

// 查找所有 slide-*.html 文件
const files = fs.readdirSync('.')
  .filter(f => /^slide-\d+-.+\.html$/.test(f))
  .sort((a, b) => {
    const numA = parseInt(a.match(/slide-(\d+)/)[1]);
    const numB = parseInt(b.match(/slide-(\d+)/)[1]);
    return numA - numB;
  });

if (files.length === 0) {
  console.error('未找到 slide-*.html 文件');
  process.exit(1);
}

console.log(`找到 ${files.length} 个幻灯片文件：`);
files.forEach((f, i) => console.log(`  ${i + 1}. ${f}`));

// 读取第一个文件，提取 <head>
const firstFile = fs.readFileSync(files[0], 'utf-8');
const headMatch = firstFile.match(/<head>([\s\S]*?)<\/head>/);
if (!headMatch) {
  console.error('无法从第一个文件提取 <head>');
  process.exit(1);
}
const headContent = headMatch[1];

// 提取所有 slide 内容
const slides = [];
for (const file of files) {
  const content = fs.readFileSync(file, 'utf-8');
  const slideMatch = content.match(/<div class="slide"[^>]*>([\s\S]*?)<\/div>\s*<script/);
  if (slideMatch) {
    slides.push(slideMatch[1].trim());
  } else {
    console.warn(`警告: ${file} 中未找到 <div class="slide">`);
  }
}

// 生成合并后的 HTML
const mergedHTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
${headContent}
</head>
<body>
${slides.map((slideContent, i) => `  <div class="slide" id="slide-${i + 1}">
${slideContent}
  </div>`).join('\n\n')}

  <script>
    let currentSlide = 0;
    const slides = document.querySelectorAll('.slide');
    const totalSlides = slides.length;

    function showSlide(n) {
      slides[currentSlide].style.display = 'none';
      currentSlide = (n + totalSlides) % totalSlides;
      slides[currentSlide].style.display = 'flex';
    }

    // 初始化：只显示第一页
    slides.forEach((slide, i) => {
      slide.style.display = i === 0 ? 'flex' : 'none';
    });

    // 键盘导航
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') showSlide(currentSlide - 1);
      if (e.key === 'ArrowRight') showSlide(currentSlide + 1);
    });
  </script>
</body>
</html>
`;

// 写入 slides.html
fs.writeFileSync('slides.html', mergedHTML, 'utf-8');
console.log(`\n✅ 已生成 slides.html (${slides.length} 页)`);
console.log(`   文件大小: ${(fs.statSync('slides.html').size / 1024).toFixed(1)} KB`);
console.log(`\n🌐 用浏览器打开 slides.html 预览，使用左右箭头键翻页`);
