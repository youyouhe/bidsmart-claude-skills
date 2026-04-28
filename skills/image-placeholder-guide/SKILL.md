---
name: image-placeholder-guide
description: >
  Educate AI about using static.photos placeholder image service in web projects.
  This guide is injected into web-builder-initial and web-builder-update prompts
  to enable AI to generate proper placeholder image URLs with categories, dimensions,
  and seeds for consistent, themed placeholder images.

  Usage: Not directly user-invoked; included as context in web-builder prompts
---

# Image Placeholder Guide - static.photos Service Documentation

## Overview

The `image-placeholder-guide` skill provides **complete documentation** for the http://static.photos placeholder image service. This guide is **injected into web-builder-initial and web-builder-update prompts** so the AI knows how to generate proper placeholder image URLs.

## Why Placeholder Images?

During web prototyping and POC development:
- **No real images available yet**: Project is in concept stage
- **Need visual balance**: Empty `<img>` tags break layout
- **Want themed content**: Images should match the project theme (not random cats)
- **Require consistency**: Same seed → same image across page loads

## static.photos Service

### URL Format

```
http://static.photos/[category]/[dimensions]/[seed]
```

**All parameters are optional**:
- Omit category → random category
- Omit dimensions → default size (640x360)
- Omit seed → random image each time

### Dimensions

**Supported sizes** (MUST use one of these):

| Dimension | Ratio | Use Case |
|-----------|-------|----------|
| `200x200` | 1:1 | Avatar, icon, small square |
| `320x240` | 4:3 | Thumbnail, card image |
| `640x360` | 16:9 | Blog post header, video thumbnail |
| `1024x576` | 16:9 | Hero section, featured image |
| `1200x630` | ~2:1 | Open Graph, social media preview |

**⚠️ Invalid dimensions will fail** - only use the 5 sizes above.

### Seed Numbers

**Purpose**: Get consistent images across page loads

- **Seed range**: Any positive integer (1-999+)
- **Same seed = same image**: `http://static.photos/nature/640x360/42` always returns the same nature image
- **Different seed = different image**: `http://static.photos/nature/640x360/43` returns a different nature image
- **Omit seed = random**: `http://static.photos/nature/640x360` returns random nature image each time

**Best practice**: Use sequential seeds for multiple images on same page (42, 43, 44...).

### Categories

**60+ categories available**:

#### Nature & Outdoor
- `nature` - Natural landscapes, forests, mountains
- `aerial` - Aerial/drone views
- `outdoor` - Outdoor scenes
- `season` - Seasonal imagery (spring, fall, etc.)
- `travel` - Travel destinations

#### Professional & Work
- `office` - Office spaces, workstations
- `workspace` - Workspace setups
- `people` - People in various settings
- `technology` - Tech gadgets, devices
- `industry` - Industrial scenes

#### Style & Aesthetic
- `minimal` - Minimalist compositions
- `abstract` - Abstract patterns
- `blurred` - Blurred/out-of-focus
- `bokeh` - Bokeh effects
- `gradient` - Gradient backgrounds
- `monochrome` - Black and white
- `vintage` - Vintage/retro style

#### Color-Based
- `white` - White/light backgrounds
- `black` - Black/dark backgrounds
- `blue` - Blue tones
- `red` - Red tones
- `green` - Green tones
- `yellow` - Yellow tones

#### Urban & Architecture
- `cityscape` - City skylines, urban scenes
- `indoor` - Indoor spaces
- `studio` - Studio photography

#### Food & Dining
- `food` - Food photography
- `restaurant` - Restaurant scenes

#### Industry-Specific
- `finance` - Financial/business imagery
- `medical` - Medical/healthcare
- `legal` - Legal/professional
- `estate` - Real estate, property
- `retail` - Retail, shopping
- `wellness` - Wellness, spa, relaxation
- `agriculture` - Farming, agriculture
- `construction` - Construction, building
- `craft` - Handicrafts, artisanal
- `cosmetic` - Beauty, cosmetics
- `automotive` - Cars, vehicles
- `gaming` - Gaming, esports
- `education` - Education, learning

#### Events & Lifestyle
- `holiday` - Holidays, celebrations
- `event` - Events, gatherings
- `sport` - Sports, athletics

#### Other
- `textures` - Textural backgrounds
- `science` - Scientific imagery

## Usage Examples

### Example 1: Simple Image (No Parameters)

```html
<img src="http://static.photos" alt="Random placeholder">
```

**Result**: Random category, default size (640x360), random image

### Example 2: Specific Category

```html
<img src="http://static.photos/nature" alt="Nature placeholder">
```

**Result**: Nature image, default size (640x360), random each time

### Example 3: Category + Dimensions

```html
<img src="http://static.photos/office/320x240" alt="Office thumbnail">
```

**Result**: Office image, 320×240px, random each time

### Example 4: Full URL with Seed

```html
<img src="http://static.photos/technology/1200x630/42" alt="Tech hero">
```

**Result**: Technology image, 1200×630px, **always the same image** (seed 42)

### Example 5: Multiple Consistent Images

```html
<!-- Hero section -->
<img src="http://static.photos/nature/1024x576/100" alt="Hero">

<!-- Feature cards (same theme, different images) -->
<img src="http://static.photos/nature/320x240/101" alt="Feature 1">
<img src="http://static.photos/nature/320x240/102" alt="Feature 2">
<img src="http://static.photos/nature/320x240/103" alt="Feature 3">
```

**Result**: 4 different nature images, all consistent across page loads

## Category Selection Guide

### For Portfolio Websites
```html
<!-- Hero -->
<img src="http://static.photos/minimal/1024x576/1" alt="Portfolio hero">

<!-- Project thumbnails -->
<img src="http://static.photos/abstract/320x240/10" alt="Project 1">
<img src="http://static.photos/workspace/320x240/11" alt="Project 2">
<img src="http://static.photos/technology/320x240/12" alt="Project 3">
```

### For E-commerce Sites
```html
<!-- Product images -->
<img src="http://static.photos/white/640x360/20" alt="Product 1">
<img src="http://static.photos/white/640x360/21" alt="Product 2">
<img src="http://static.photos/minimal/640x360/22" alt="Product 3">

<!-- Category banners -->
<img src="http://static.photos/retail/1200x630/30" alt="Electronics">
<img src="http://static.photos/cosmetic/1200x630/31" alt="Beauty">
```

### For Restaurant Websites
```html
<!-- Hero -->
<img src="http://static.photos/food/1200x630/50" alt="Restaurant hero">

<!-- Menu items -->
<img src="http://static.photos/food/320x240/51" alt="Appetizer">
<img src="http://static.photos/food/320x240/52" alt="Main course">
<img src="http://static.photos/food/320x240/53" alt="Dessert">

<!-- Ambiance -->
<img src="http://static.photos/restaurant/640x360/60" alt="Interior">
```

### For SaaS Landing Pages
```html
<!-- Hero -->
<img src="http://static.photos/technology/1024x576/70" alt="Platform screenshot">

<!-- Features -->
<img src="http://static.photos/office/320x240/71" alt="Feature 1">
<img src="http://static.photos/workspace/320x240/72" alt="Feature 2">
<img src="http://static.photos/people/320x240/73" alt="Team collaboration">
```

### For Blog/Content Sites
```html
<!-- Featured post -->
<img src="http://static.photos/nature/1200x630/80" alt="Featured article">

<!-- Recent posts -->
<img src="http://static.photos/travel/640x360/81" alt="Post 1">
<img src="http://static.photos/cityscape/640x360/82" alt="Post 2">
<img src="http://static.photos/food/640x360/83" alt="Post 3">
```

### For Real Estate Sites
```html
<!-- Property listings -->
<img src="http://static.photos/estate/640x360/90" alt="Property 1">
<img src="http://static.photos/estate/640x360/91" alt="Property 2">
<img src="http://static.photos/indoor/640x360/92" alt="Interior">
<img src="http://static.photos/outdoor/640x360/93" alt="Exterior">
```

### For Health/Fitness Sites
```html
<!-- Hero -->
<img src="http://static.photos/wellness/1024x576/100" alt="Fitness hero">

<!-- Services -->
<img src="http://static.photos/sport/320x240/101" alt="Training">
<img src="http://static.photos/wellness/320x240/102" alt="Yoga">
<img src="http://static.photos/people/320x240/103" alt="Personal training">
```

## Best Practices

### 1. Consistent Theme

Use the **same category** for related images to maintain visual coherence:

**✅ Good**:
```html
<img src="http://static.photos/nature/1024x576/1" alt="Hero">
<img src="http://static.photos/nature/320x240/2" alt="Card 1">
<img src="http://static.photos/nature/320x240/3" alt="Card 2">
```

**❌ Bad** (mixed themes):
```html
<img src="http://static.photos/nature/1024x576/1" alt="Hero">
<img src="http://static.photos/technology/320x240/2" alt="Card 1">  <!-- Inconsistent -->
<img src="http://static.photos/food/320x240/3" alt="Card 2">  <!-- Inconsistent -->
```

### 2. Use Seeds for Consistency

Always use **seed numbers** for production-like POCs:

**✅ Good** (with seeds):
```html
<img src="http://static.photos/office/640x360/42" alt="Office">
<!-- Always shows the same office image -->
```

**❌ Bad** (no seed):
```html
<img src="http://static.photos/office/640x360" alt="Office">
<!-- Shows different office image on each page load -->
```

### 3. Match Dimensions to Use Case

Choose appropriate sizes for each element:

| Element | Recommended Size | Example |
|---------|------------------|---------|
| Avatar | `200x200` | Profile pictures |
| Card image | `320x240` | Product cards, blog thumbnails |
| Blog post header | `640x360` | Article headers |
| Hero section | `1024x576` | Landing page hero |
| Open Graph | `1200x630` | Social media previews |

### 4. Sequential Seeds for Sets

Use **consecutive seeds** for image sets:

```html
<!-- Team section: seeds 20-23 -->
<img src="http://static.photos/people/200x200/20" alt="Team member 1">
<img src="http://static.photos/people/200x200/21" alt="Team member 2">
<img src="http://static.photos/people/200x200/22" alt="Team member 3">
<img src="http://static.photos/people/200x200/23" alt="Team member 4">

<!-- Feature section: seeds 30-32 -->
<img src="http://static.photos/technology/320x240/30" alt="Feature 1">
<img src="http://static.photos/technology/320x240/31" alt="Feature 2">
<img src="http://static.photos/technology/320x240/32" alt="Feature 3">
```

### 5. Category Fallbacks

If unsure about category, use safe defaults:

- **General purpose**: `minimal`, `abstract`, `white`
- **Professional**: `office`, `workspace`, `technology`
- **Creative**: `nature`, `gradient`, `bokeh`
- **Commercial**: `retail`, `white`, `studio`

## Common Mistakes

### Mistake 1: Invalid Dimensions

**❌ Wrong**:
```html
<img src="http://static.photos/nature/800x600/1" alt="Wrong">
<!-- 800x600 is NOT supported -->
```

**✅ Correct**:
```html
<img src="http://static.photos/nature/1024x576/1" alt="Correct">
<!-- Use closest supported size -->
```

### Mistake 2: Typo in Category

**❌ Wrong**:
```html
<img src="http://static.photos/natur/640x360/1" alt="Typo">
<!-- "natur" should be "nature" -->
```

**✅ Correct**:
```html
<img src="http://static.photos/nature/640x360/1" alt="Correct">
```

### Mistake 3: Missing Alt Text

**❌ Wrong**:
```html
<img src="http://static.photos/nature/640x360/1">
<!-- No alt text (accessibility issue) -->
```

**✅ Correct**:
```html
<img src="http://static.photos/nature/640x360/1" alt="Mountain landscape">
<!-- Descriptive alt text -->
```

### Mistake 4: No Seed for Important Images

**❌ Wrong**:
```html
<!-- Logo/brand image without seed -->
<img src="http://static.photos/minimal/200x200" alt="Logo">
<!-- Will change on each page load -->
```

**✅ Correct**:
```html
<img src="http://static.photos/minimal/200x200/1" alt="Logo">
<!-- Consistent across loads -->
```

## Prompt Injection Template

This section shows how to inject the image placeholder guide into web-builder prompts.

### For web-builder-initial

Add this to the system prompt:

```
If you want to use image placeholder, http://static.photos Usage:

Format: http://static.photos/[category]/[dimensions]/[seed]

where:
- dimensions must be one of: 200x200, 320x240, 640x360, 1024x576, or 1200x630
- seed can be any number (1-999+) for consistent images or omit for random
- categories include: nature, office, people, technology, minimal, abstract, aerial,
  blurred, bokeh, gradient, monochrome, vintage, white, black, blue, red, green,
  yellow, cityscape, workspace, food, travel, textures, industry, indoor, outdoor,
  studio, finance, medical, season, holiday, event, sport, science, legal, estate,
  restaurant, retail, wellness, agriculture, construction, craft, cosmetic,
  automotive, gaming, education

Examples:
- http://static.photos/red/320x240/133 (red-themed with seed 133)
- http://static.photos/640x360 (random category and image)
- http://static.photos/nature/1200x630/42 (nature-themed with seed 42)

IMPORTANT: Always use seeds for consistent placeholder images. Choose categories that
match your project theme (e.g., 'food' for restaurant sites, 'office' for SaaS).
```

### For web-builder-update

Same injection, but add a note about consistency:

```
[Same content as above]

IMPORTANT: When adding new images to existing project, maintain consistency:
- Use the same category as existing images
- Use sequential seed numbers (if existing images use seeds 1-5, use 6-10 for new images)
- Match dimensions to similar elements
```

## Integration with web-builder Skills

### In web-builder-initial SKILL.md

Add to System Prompt section:

```markdown
## System Prompt (with Image Placeholder Guide)

When calling the LLM, inject the image placeholder guide into the prompt:

```python
INITIAL_PROMPT = f"""
{INITIAL_SYSTEM_PROMPT}

{IMAGE_PLACEHOLDER_GUIDE}

User Request: {user_request}
"""
```

Where `IMAGE_PLACEHOLDER_GUIDE` is the content from this skill.
```

### In web-builder-update SKILL.md

Similar injection pattern:

```markdown
## System Prompt (with Image Placeholder Guide)

```python
UPDATE_PROMPT = f"""
{FOLLOW_UP_SYSTEM_PROMPT}

{IMAGE_PLACEHOLDER_GUIDE}

Current Files:
{current_files}

User Request: {user_request}
"""
```
```

## Testing

### Test Case 1: Verify URL Format

```python
def test_placeholder_url():
    url = "http://static.photos/nature/640x360/42"

    # Test URL is accessible
    import requests
    response = requests.get(url)

    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('image/')
    print("✅ URL format valid")
```

### Test Case 2: Verify Consistency

```python
def test_seed_consistency():
    import requests
    import hashlib

    url = "http://static.photos/nature/640x360/42"

    # Fetch same URL twice
    response1 = requests.get(url)
    response2 = requests.get(url)

    # Compare content hashes
    hash1 = hashlib.md5(response1.content).hexdigest()
    hash2 = hashlib.md5(response2.content).hexdigest()

    assert hash1 == hash2, "Same seed should return same image"
    print("✅ Seed consistency verified")
```

### Test Case 3: Verify Dimensions

```python
def test_dimensions():
    from PIL import Image
    from io import BytesIO
    import requests

    url = "http://static.photos/nature/640x360/42"
    response = requests.get(url)

    img = Image.open(BytesIO(response.content))
    assert img.size == (640, 360), f"Expected 640x360, got {img.size}"
    print("✅ Dimensions correct")
```

## Bilingual Version (Chinese)

### 中文版本

```
如果你想使用图片占位符,可以使用 http://static.photos 服务:

格式: http://static.photos/[分类]/[尺寸]/[种子]

其中:
- 尺寸必须是以下之一: 200x200, 320x240, 640x360, 1024x576, 或 1200x630
- 种子可以是任意数字 (1-999+) 用于获取一致的图片,或省略以获取随机图片
- 分类包括: nature(自然), office(办公), people(人物), technology(科技), minimal(极简),
  abstract(抽象), aerial(航拍), blurred(模糊), bokeh(景深), gradient(渐变),
  monochrome(单色), vintage(复古), white(白色), black(黑色), blue(蓝色), red(红色),
  green(绿色), yellow(黄色), cityscape(城市), workspace(工作空间), food(美食),
  travel(旅行), textures(纹理), industry(工业), indoor(室内), outdoor(户外),
  studio(工作室), finance(金融), medical(医疗), season(季节), holiday(节日),
  event(活动), sport(体育), science(科学), legal(法律), estate(房地产),
  restaurant(餐厅), retail(零售), wellness(健康), agriculture(农业),
  construction(建筑), craft(手工艺), cosmetic(美容), automotive(汽车),
  gaming(游戏), education(教育)

示例:
- http://static.photos/red/320x240/133 (红色主题,种子133)
- http://static.photos/640x360 (随机分类和图片)
- http://static.photos/nature/1200x630/42 (自然主题,种子42)

重要: 始终使用种子以获得一致的占位图片。选择与项目主题匹配的分类
(例如,餐厅网站使用 'food',SaaS 使用 'office')。
```

## Summary

This guide ensures that:
1. ✅ AI knows how to use static.photos correctly
2. ✅ Generated code uses valid dimensions (5 supported sizes only)
3. ✅ Images have consistent seeds for production-like POCs
4. ✅ Categories match project themes
5. ✅ Alt text is always included for accessibility
6. ✅ Image URLs follow best practices

When injected into web-builder prompts, this guide eliminates common placeholder image errors and produces professional-looking POC websites with themed, consistent placeholder images.

---

**Implementation Status**: ✅ Complete - Ready for injection
**BuildFlow Source**: `/mnt/oldroot/home/bird/buildflow/lib/prompts.ts` line 13, 403-405
**Dependencies**: None (documentation only)
**Used By**: `web-builder-initial`, `web-builder-update` (as prompt context)
**Last Updated**: 2026-03-30
