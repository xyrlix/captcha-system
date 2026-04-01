"""
验证码引擎 - 实现业界主流的所有验证码类型
"""
import random
import string
import math
import time
import base64
import hashlib
import io
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from captcha.image import ImageCaptcha
from captcha.audio import AudioCaptcha


# ────────────────────────────────────────────────────────────
# 1. 数字验证码（最简单）
# ────────────────────────────────────────────────────────────
def gen_numeric(length=4):
    """纯数字验证码"""
    code = ''.join(random.choices(string.digits, k=length))
    img = _render_text_captcha(code, noise_level=1)
    return {"code": code, "image": _to_base64(img), "type": "numeric"}


# ────────────────────────────────────────────────────────────
# 2. 字母数字混合验证码
# ────────────────────────────────────────────────────────────
def gen_alphanumeric(length=5):
    """字母+数字混合"""
    chars = string.ascii_uppercase + string.digits
    # 去掉容易混淆的字符
    chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    code = ''.join(random.choices(chars, k=length))
    img = _render_text_captcha(code, noise_level=2)
    return {"code": code, "image": _to_base64(img), "type": "alphanumeric"}


# ────────────────────────────────────────────────────────────
# 3. 扭曲变形图片验证码（传统CAPTCHA）
# ────────────────────────────────────────────────────────────
def gen_distorted(length=5):
    """PIL渲染的扭曲变形验证码"""
    chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
    code = ''.join(random.choices(chars, k=length))
    
    width, height = 200, 70
    img = Image.new('RGB', (width, height), color=_random_light_color())
    draw = ImageDraw.Draw(img)
    
    # 背景干扰线
    for _ in range(8):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=_random_color(), width=1)
    
    # 背景噪点
    for _ in range(100):
        x, y = random.randint(0, width-1), random.randint(0, height-1)
        draw.point((x, y), fill=_random_color())
    
    # 绘制文字（每个字符单独旋转）
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    x_pos = 10
    for char in code:
        # 创建单字符图像并旋转
        char_img = Image.new('RGBA', (40, 50), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((5, 5), char, font=font, fill=_random_dark_color())
        angle = random.randint(-25, 25)
        char_img = char_img.rotate(angle, expand=True)
        img.paste(char_img, (x_pos, random.randint(5, 20)), char_img)
        x_pos += 35
    
    # 轻微模糊
    img = img.filter(ImageFilter.SMOOTH)
    return {"code": code, "image": _to_base64(img), "type": "distorted"}


# ────────────────────────────────────────────────────────────
# 4. 算术验证码
# ────────────────────────────────────────────────────────────
def gen_arithmetic():
    """数学运算验证码"""
    ops = ['+', '-', '×']
    op = random.choice(ops)
    if op == '+':
        a, b = random.randint(1, 20), random.randint(1, 20)
        answer = str(a + b)
    elif op == '-':
        a, b = random.randint(5, 20), random.randint(1, 5)
        answer = str(a - b)
    else:
        a, b = random.randint(2, 9), random.randint(2, 9)
        answer = str(a * b)
    
    question = f"{a} {op} {b} = ?"
    img = _render_text_captcha(question, noise_level=1, width=220, height=60, font_size=28)
    return {"code": answer, "image": _to_base64(img), "question": question, "type": "arithmetic"}


# ────────────────────────────────────────────────────────────
# 5. 中文验证码
# ────────────────────────────────────────────────────────────
def gen_chinese(length=4):
    """中文汉字验证码"""
    # 常用中文字符集（简单汉字）
    chinese_chars = (
        "安百保报北本比边表别部不才产长城出处传大当到地点电都动段对多发法方分风府高各给工公关广规国过还好和河话"
        "化回会几家见建交教界金经就具开来乐力里联留龙路率每门名明年农朋其期起前强全人任日如入三山上设社生时识"
        "事市是手首书数水所他太特天通同头万为文问无系现向小新信性学业一以义已因应用有又于原越在这正知只中重主"
    )
    chars = random.choices(chinese_chars, k=length)
    code = ''.join(chars)
    img = _render_chinese_captcha(code)
    return {"code": code, "image": _to_base64(img), "type": "chinese"}


# ────────────────────────────────────────────────────────────
# 6. 滑块验证码
# ────────────────────────────────────────────────────────────
def gen_slider():
    """滑块拼图验证码 - 生成带缺口的背景图和滑块图"""
    width, height = 320, 160
    
    # 生成背景图（随机色块填充，模拟图片）
    bg = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(bg)
    
    # 绘制随机背景
    for i in range(0, width, 20):
        for j in range(0, height, 20):
            color = (
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(50, 200)
            )
            draw.rectangle([i, j, i+20, j+20], fill=color)
    
    # 添加一些图案使背景更真实
    for _ in range(5):
        x, y = random.randint(0, width-50), random.randint(0, height-50)
        r = random.randint(10, 30)
        draw.ellipse([x, y, x+r*2, y+r*2], fill=_random_color())
    
    # 缺口位置（x位置是答案）
    gap_x = random.randint(60, width - 80)
    gap_y = random.randint(20, height - 60)
    gap_size = 40
    
    # 裁剪滑块内容
    slider_img = bg.crop((gap_x, gap_y, gap_x + gap_size, gap_y + gap_size))
    
    # 在背景上画缺口（半透明灰色）
    bg_with_gap = bg.copy()
    gap_draw = ImageDraw.Draw(bg_with_gap)
    gap_draw.rectangle(
        [gap_x, gap_y, gap_x + gap_size, gap_y + gap_size],
        fill=(200, 200, 200, 128)
    )
    # 缺口边框
    gap_draw.rectangle(
        [gap_x, gap_y, gap_x + gap_size, gap_y + gap_size],
        outline=(100, 100, 100), width=2
    )
    
    # 滑块加边框
    slider_draw = ImageDraw.Draw(slider_img)
    slider_draw.rectangle([0, 0, gap_size-1, gap_size-1], outline=(255, 255, 255), width=2)
    
    return {
        "type": "slider",
        "background": _to_base64(bg_with_gap),
        "slider": _to_base64(slider_img),
        "answer": gap_x,  # 正确的x位置
        "gap_y": gap_y,
        "tolerance": 15,  # 允许15px误差
    }


# ────────────────────────────────────────────────────────────
# 7. 点选验证码（点击图中指定文字）
# ────────────────────────────────────────────────────────────
def gen_click_text():
    """点选验证码 - 图中显示多个文字，按顺序点击指定的"""
    width, height = 300, 200
    
    # 候选字符
    chars = list("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
    random.shuffle(chars)
    selected_chars = chars[:6]  # 展示6个
    
    # 生成图片
    img = Image.new('RGB', (width, height), color=_random_light_color())
    draw = ImageDraw.Draw(img)
    
    # 背景干扰
    for _ in range(50):
        x, y = random.randint(0, width), random.randint(0, height)
        draw.point((x, y), fill=_random_color())
    for _ in range(5):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=_random_color(), width=1)
    
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    # 随机放置字符
    positions = []
    placed = []
    for char in selected_chars:
        for _ in range(50):  # 最多尝试50次
            x = random.randint(20, width - 40)
            y = random.randint(20, height - 40)
            # 检查不重叠
            overlap = False
            for px, py in placed:
                if abs(x - px) < 40 and abs(y - py) < 40:
                    overlap = True
                    break
            if not overlap:
                placed.append((x, y))
                positions.append({"char": char, "x": x, "y": y})
                draw.text((x, y), char, font=font, fill=_random_dark_color())
                break
    
    # 要求点击的顺序（随机选3个）
    target = random.sample(positions, min(3, len(positions)))
    target_chars = [t["char"] for t in target]
    answer = [{"x": t["x"] + 15, "y": t["y"] + 15} for t in target]  # 字符中心
    
    return {
        "type": "click_text",
        "image": _to_base64(img),
        "question": f"请依次点击：{'、'.join(target_chars)}",
        "answer": answer,
        "tolerance": 20,
    }


# ────────────────────────────────────────────────────────────
# 8. 旋转验证码
# ────────────────────────────────────────────────────────────
def gen_rotate():
    """旋转验证码 - 将图片旋转一定角度，用户拖动还原"""
    size = 150
    
    # 生成带内容的图片
    img = Image.new('RGB', (size, size), color=(240, 248, 255))
    draw = ImageDraw.Draw(img)
    
    # 画一个明显的图案（使旋转可感知）
    # 箭头形状
    center = size // 2
    draw.ellipse([20, 20, size-20, size-20], outline=(70, 130, 180), width=4)
    draw.line([(center, 20), (center, size-20)], fill=(70, 130, 180), width=3)
    draw.line([(20, center), (size-20, center)], fill=(70, 130, 180), width=3)
    # 画一个指针
    draw.polygon([(center, 25), (center-8, 45), (center+8, 45)], fill=(220, 50, 50))
    draw.text((center-10, center+5), "TOP", fill=(50, 50, 150))
    
    # random rotation angle (smaller range for easier adjustment)
    angle = random.randint(30, 270)
    rotated = img.rotate(-angle, resample=Image.BICUBIC)

    return {
        "type": "rotate",
        "image": _to_base64(rotated),
        "answer": angle,
        "tolerance": 30,  # allow 30 degree error
    }


# ────────────────────────────────────────────────────────────
# 9. 图片选择验证码（选出所有含某类物体的图片）
# ────────────────────────────────────────────────────────────
def gen_image_select():
    """图片选择验证码 - 选出正确类别（模拟版，用几何图形代替真实图片）"""
    categories = {
        "圆形": _make_shape_img("circle"),
        "方形": _make_shape_img("square"),
        "三角形": _make_shape_img("triangle"),
        "星形": _make_shape_img("star"),
    }
    
    # 随机选择目标类别
    target_category = random.choice(list(categories.keys()))
    
    # 生成9张图片（3~5张是目标，其余是干扰）
    images = []
    correct_indices = []
    
    # 目标数量
    target_count = random.randint(3, 5)
    decoy_categories = [c for c in categories.keys() if c != target_category]
    
    for i in range(9):
        if i < target_count:
            img = categories[target_category]()
            correct_indices.append(i)
        else:
            decoy = random.choice(decoy_categories)
            img = categories[decoy]()
        images.append(_to_base64(img))
    
    # 打乱顺序
    combined = list(zip(images, [i in correct_indices for i in range(9)]))
    random.shuffle(combined)
    images_shuffled, answers = zip(*combined)
    correct_set = [i for i, a in enumerate(answers) if a]
    
    return {
        "type": "image_select",
        "question": f"请选出所有包含「{target_category}」的图片",
        "images": list(images_shuffled),
        "answer": correct_set,
    }


# ────────────────────────────────────────────────────────────
# 10. 语义问答验证码
# ────────────────────────────────────────────────────────────
def gen_semantic():
    """语义问答验证码 - 生活常识题"""
    questions = [
        {"q": "一年有几个月？", "a": "12", "hint": "数字"},
        {"q": "天空是什么颜色？", "a": "蓝", "hint": "一个字"},
        {"q": "一周有几天？", "a": "7", "hint": "数字"},
        {"q": "太阳从哪边升起？", "a": "东", "hint": "一个字"},
        {"q": "水的化学符号是？", "a": "H2O", "hint": "化学式"},
        {"q": "中国的首都是？", "a": "北京", "hint": "城市名"},
        {"q": "地球上最大的海洋是？", "a": "太平洋", "hint": "海洋名"},
        {"q": "三角形有几条边？", "a": "3", "hint": "数字"},
        {"q": "1+1等于几？", "a": "2", "hint": "数字"},
        {"q": "一天有多少小时？", "a": "24", "hint": "数字"},
        {"q": "彩虹有几种颜色？", "a": "7", "hint": "数字"},
        {"q": "人类有几根手指？", "a": "10", "hint": "数字"},
    ]
    item = random.choice(questions)
    return {
        "type": "semantic",
        "question": item["q"],
        "hint": f"提示：{item['hint']}",
        "answer": item["a"],
    }


# ────────────────────────────────────────────────────────────
# 11. 行为验证码（蜜罐/不可见）
# ────────────────────────────────────────────────────────────
def gen_invisible():
    """不可见验证码（蜜罐模式）- 用于机器人检测"""
    # 生成一个挑战令牌，前端通过鼠标移动轨迹、时间差等验证
    token = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
    return {
        "type": "invisible",
        "token": token,
        "min_time": 3000,  # 最少需要3秒（毫秒）
        "description": "这是一个不可见验证码，通过行为分析判断是否为机器人",
    }


# ────────────────────────────────────────────────────────────
# 12. 拼图验证码（九宫格拼图）
# ────────────────────────────────────────────────────────────
def gen_puzzle():
    """九宫格拼图验证码 - 打乱后让用户拖拽还原"""
    size = 180
    piece_size = size // 3  # 每块60x60
    
    # 生成原始图片
    original = Image.new('RGB', (size, size))
    draw = ImageDraw.Draw(original)
    
    # 渐变背景 + 图案
    for y in range(size):
        for x in range(size):
            r = int(100 + 155 * x / size)
            g = int(50 + 150 * y / size)
            b = int(200 - 100 * x / size)
            original.putpixel((x, y), (r, g, b))
    
    # 绘制数字 1-9
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    for i in range(9):
        row, col = i // 3, i % 3
        cx = col * piece_size + piece_size // 2 - 10
        cy = row * piece_size + piece_size // 2 - 15
        draw.text((cx, cy), str(i + 1), font=font, fill=(255, 255, 255))
        draw.rectangle(
            [col * piece_size, row * piece_size,
             (col + 1) * piece_size - 1, (row + 1) * piece_size - 1],
            outline=(255, 255, 255), width=2
        )
    
    # 切割成9块
    pieces = []
    for i in range(9):
        row, col = i // 3, i % 3
        piece = original.crop([
            col * piece_size, row * piece_size,
            (col + 1) * piece_size, (row + 1) * piece_size
        ])
        pieces.append(_to_base64(piece))
    
    # 打乱顺序（保留一个错位保证有解）
    order = list(range(9))
    while True:
        random.shuffle(order)
        if order != list(range(9)):
            break
    
    return {
        "type": "puzzle",
        "pieces": [pieces[i] for i in order],
        "shuffled_order": order,
        "answer": list(range(9)),  # 正确顺序
        "piece_size": piece_size,
    }


# ────────────────────────────────────────────────────────────
# 内部辅助函数
# ────────────────────────────────────────────────────────────

def _render_text_captcha(text, noise_level=2, width=180, height=60, font_size=32):
    img = Image.new('RGB', (width, height), color=_random_light_color())
    draw = ImageDraw.Draw(img)
    
    if noise_level >= 1:
        for _ in range(5 * noise_level):
            x1, y1 = random.randint(0, width), random.randint(0, height)
            x2, y2 = random.randint(0, width), random.randint(0, height)
            draw.line([(x1, y1), (x2, y2)], fill=_random_color(), width=1)
    
    if noise_level >= 2:
        for _ in range(80):
            x, y = random.randint(0, width-1), random.randint(0, height-1)
            draw.point((x, y), fill=_random_color())
    
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # 居中文字
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except:
        text_w, text_h = len(text) * font_size * 0.6, font_size
    
    x = (width - text_w) // 2
    y = (height - text_h) // 2
    draw.text((x, y), text, font=font, fill=_random_dark_color())
    
    return img


def _render_chinese_captcha(text, width=200, height=65):
    img = Image.new('RGB', (width, height), color=_random_light_color())
    draw = ImageDraw.Draw(img)
    
    # 干扰线
    for _ in range(5):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=_random_color(), width=1)
    
    # 尝试多种中文字体
    font = None
    chinese_fonts = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simkai.ttf",
    ]
    for f in chinese_fonts:
        try:
            font = ImageFont.truetype(f, 36)
            break
        except:
            continue
    
    if font is None:
        font = ImageFont.load_default()
    
    x_pos = 10
    for char in text:
        draw.text((x_pos, 10 + random.randint(-5, 5)), char, font=font, fill=_random_dark_color())
        x_pos += 46
    
    return img


def _to_base64(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def _random_light_color():
    return (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))


def _random_dark_color():
    return (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))


def _make_shape_img(shape_type):
    """工厂函数，返回绘制指定形状的函数"""
    def draw_func():
        size = 80
        img = Image.new('RGB', (size, size), color=_random_light_color())
        draw = ImageDraw.Draw(img)
        color = _random_dark_color()
        margin = 15
        
        if shape_type == "circle":
            draw.ellipse([margin, margin, size-margin, size-margin], fill=color)
        elif shape_type == "square":
            draw.rectangle([margin, margin, size-margin, size-margin], fill=color)
        elif shape_type == "triangle":
            draw.polygon([
                (size//2, margin),
                (margin, size-margin),
                (size-margin, size-margin)
            ], fill=color)
        elif shape_type == "star":
            # 五角星
            cx, cy = size//2, size//2
            r_outer = size//2 - margin//2
            r_inner = r_outer // 2
            points = []
            for i in range(10):
                angle = math.pi * i / 5 - math.pi / 2
                r = r_outer if i % 2 == 0 else r_inner
                points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            draw.polygon(points, fill=color)
        
        return img
    return draw_func


# ────────────────────────────────────────────────────────────
# 13. 拼音输入验证码
# ────────────────────────────────────────────────────────────
def gen_pinyin_captcha():
    """显示汉字，用户输入对应拼音（首字母缩写）"""
    # 常见汉字及其拼音首字母
    word_bank = [
        ("苹果", "pg"), ("香蕉", "xj"), ("西瓜", "xg"), ("草莓", "cm"),
        ("橙子", "cz"), ("葡萄", "pt"), ("菠萝", "bl"), ("芒果", "mg"),
        ("猫咪", "mm"), ("小狗", "xg"), ("老虎", "lh"), ("大象", "dx"),
        ("飞机", "fj"), ("汽车", "qc"), ("火车", "hc"), ("轮船", "lc"),
        ("太阳", "ty"), ("月亮", "yl"), ("星星", "xx"), ("彩虹", "ch"),
        ("苹果", "pg"), ("电话", "dh"), ("电脑", "dn"), ("手机", "sj"),
        ("学校", "xx"), ("医院", "yy"), ("银行", "yh"), ("图书馆", "tsg"),
        ("篮球", "lq"), ("足球", "zq"), ("排球", "pq"), ("乒乓球", "ppq"),
        ("唱歌", "cg"), ("跳舞", "tw"), ("游泳", "yy"), ("跑步", "pb"),
    ]
    word, pinyin = random.choice(word_bank)
    
    width, height = 280, 120
    img = Image.new('RGB', (width, height), color=(245, 245, 255))
    draw = ImageDraw.Draw(img)
    
    # 干扰背景
    for _ in range(5):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(*_random_color(), 80), width=1)
    
    # 绘制汉字（放大）
    try:
        font_big = ImageFont.truetype("msyh.ttc", 52)
        font_hint = ImageFont.truetype("msyh.ttc", 16)
    except:
        try:
            font_big = ImageFont.truetype("simhei.ttf", 52)
            font_hint = ImageFont.truetype("simhei.ttf", 16)
        except:
            font_big = ImageFont.load_default()
            font_hint = font_big
    
    # 计算文字居中位置
    try:
        bbox = draw.textbbox((0, 0), word, font=font_big)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except:
        tw, th = len(word) * 40, 50
    
    x = (width - tw) // 2
    y = (height - th) // 2 - 5
    
    # 随机颜色+轻微位移绘制文字（增加识别难度）
    draw.text((x + random.randint(-2, 2), y + random.randint(-2, 2)), word,
              font=font_big, fill=_random_dark_color())
    
    # 底部提示
    hint = f"请输入「{word}」的拼音首字母"
    draw.text((10, height - 25), hint, font=font_hint, fill=(100, 100, 100))
    
    # 添加噪点
    for _ in range(200):
        px, py = random.randint(0, width - 1), random.randint(0, height - 1)
        draw.point((px, py), fill=_random_color())
    
    return {
        "type": "pinyin",
        "image": _to_base64(img),
        "word": word,
        "answer": pinyin,
        "hint": f"请输入「{word}」的拼音首字母（小写字母）",
    }


# ────────────────────────────────────────────────────────────
# 14. 图形密码验证码（Android图案锁风格）
# ────────────────────────────────────────────────────────────
def gen_pattern_lock():
    """3×3 图案锁验证码 - 按提示的顺序连接圆点"""
    # 随机生成一个3-5步的图案路径（使用 0-8 索引）
    # 约束：相邻节点不能跨越未经过的节点（简化版：只要不重复即可）
    all_nodes = list(range(9))
    path_len = random.randint(4, 6)
    path = random.sample(all_nodes, path_len)
    
    # 绘制"正确图案"预览图（用于提示）
    size = 240
    margin = 40
    spacing = (size - 2 * margin) // 2  # = 80
    
    def node_pos(idx):
        r, c = divmod(idx, 3)
        return (margin + c * spacing, margin + r * spacing)
    
    # 绘制提示图（展示正确路径）
    hint_img = Image.new('RGB', (size, size), color=(30, 30, 50))
    hint_draw = ImageDraw.Draw(hint_img)
    
    # 绘制所有节点
    for i in range(9):
        px, py = node_pos(i)
        hint_draw.ellipse([px - 12, py - 12, px + 12, py + 12],
                          fill=(80, 80, 120), outline=(150, 150, 200), width=2)
        # 节点编号
        try:
            nfont = ImageFont.truetype("arial.ttf", 12)
        except:
            nfont = ImageFont.load_default()
        hint_draw.text((px - 4, py - 7), str(i + 1), font=nfont, fill=(200, 200, 200))
    
    # 绘制路径连线
    for j in range(len(path) - 1):
        p1 = node_pos(path[j])
        p2 = node_pos(path[j + 1])
        hint_draw.line([p1, p2], fill=(100, 200, 255), width=4)
    
    # 在路径上标注顺序数字
    for idx, node in enumerate(path):
        px, py = node_pos(node)
        hint_draw.ellipse([px - 14, py - 14, px + 14, py + 14],
                          fill=(50, 150, 255), outline=(200, 230, 255), width=2)
        try:
            nfont2 = ImageFont.truetype("arial.ttf", 14)
        except:
            nfont2 = ImageFont.load_default()
        hint_draw.text((px - 5, py - 8), str(idx + 1), font=nfont2, fill=(255, 255, 255))
    
    return {
        "type": "pattern_lock",
        "hint_image": _to_base64(hint_img),
        "path": path,          # 正确路径（节点索引列表）
        "path_len": path_len,
    }


# ────────────────────────────────────────────────────────────
# 15. 形近字找不同验证码
# ────────────────────────────────────────────────────────────
def gen_odd_one_out():
    """一行6个汉字，5个相同，1个是形近字（字形相似但不同），点击找出那个形近字"""
    # 形近字组（主字 → 形近字列表）
    similar_groups = [
        ("己", ["已", "巳"]),
        ("土", ["士", "工"]),
        ("日", ["目", "曰"]),
        ("人", ["入", "八"]),
        ("大", ["太", "犬"]),
        ("未", ["末", "木"]),
        ("申", ["甲", "由"]),
        ("力", ["刀", "勺"]),
        ("千", ["干", "于"]),
        ("戊", ["戌", "戍"]),
        ("天", ["夭", "无"]),
        ("刺", ["剌", "束"]),
        ("拔", ["拨", "拔"]),
        ("度", ["渡", "席"]),
        ("侯", ["候", "猴"]),
        ("武", ["式", "试"]),
        ("戒", ["械", "诫"]),
        ("徒", ["途", "涂"]),
    ]
    # 随机选一组
    group = random.choice(similar_groups)
    main_char = group[0]
    similar_chars = group[1]
    odd_char = random.choice(similar_chars)

    count = 6  # 总共6格，5格主字，1格形近字
    odd_idx = random.randint(0, count - 1)

    width, height = 420, 90
    img = Image.new('RGB', (width, height), color=(252, 252, 248))
    draw = ImageDraw.Draw(img)

    # 字体尝试（中文字体）
    font = None
    for font_path in [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simkai.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_path, 38)
            break
        except:
            continue
    if font is None:
        font = ImageFont.load_default()

    # 统一颜色：深墨色，让视觉无差异，只能靠认字
    normal_color = (20, 20, 40)
    odd_color = (20, 20, 40)  # 故意相同——只能靠认字来区分

    cell_w = width // count

    # 轻微干扰线（背景）
    for _ in range(4):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(200, 200, 210), width=1)

    for i in range(count):
        cx = i * cell_w + cell_w // 2
        cy = height // 2
        char = odd_char if i == odd_idx else main_char
        color = odd_color if i == odd_idx else normal_color

        try:
            bbox = draw.textbbox((0, 0), char, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except:
            tw, th = 36, 36

        # 轻微随机偏移（增加难度，防止机器精准定位）
        ox = random.randint(-3, 3)
        oy = random.randint(-3, 3)
        draw.text((cx - tw // 2 + ox, cy - th // 2 + oy), char, font=font, fill=color)

        # 每格分隔线
        if i > 0:
            draw.line([(i * cell_w, 10), (i * cell_w, height - 10)], fill=(210, 210, 220), width=1)

    # 噪点
    for _ in range(80):
        px = random.randint(0, width - 1)
        py = random.randint(0, height - 1)
        draw.point((px, py), fill=(random.randint(160, 230),) * 3)

    return {
        "type": "odd_one_out",
        "image": _to_base64(img),
        "question": f"点击找出与其他不同的那个字（形近字）",
        "main_char": main_char,
        "odd_char": odd_char,
        "answer": odd_idx,          # 0-5 的索引
        "count": count,
        "cell_w": cell_w,
        "height": height,
    }


# ────────────────────────────────────────────────────────────
# 16. 图形找规律验证码
# ────────────────────────────────────────────────────────────
def gen_pattern_rule():
    """3×3矩阵，最后一格空缺，从4个选项中选出符合规律的图形"""
    # 规律类型：形状/颜色/大小 在行或列上递增/交替
    rule_types = ["shape_row", "color_row", "size_row"]
    rule = random.choice(rule_types)

    shapes = ["circle", "square", "triangle"]
    colors_rgb = [(220, 60, 60), (60, 140, 220), (50, 180, 80)]
    sizes = [15, 22, 30]

    cell = 70  # 每格大小
    grid_w = cell * 3
    grid_h = cell * 3

    def draw_shape(draw, cx, cy, shape, color, size):
        if shape == "circle":
            draw.ellipse([cx-size, cy-size, cx+size, cy+size], fill=color)
        elif shape == "square":
            draw.rectangle([cx-size, cy-size, cx+size, cy+size], fill=color)
        elif shape == "triangle":
            draw.polygon([(cx, cy-size), (cx-size, cy+size), (cx+size, cy+size)], fill=color)

    def make_grid_img(matrix, missing=True):
        """matrix: list of 9 (shape, color_idx, size_idx), missing=True时第9格空缺"""
        img = Image.new('RGB', (grid_w, grid_h), color=(248, 248, 255))
        draw = ImageDraw.Draw(img)
        # 网格线
        for i in range(4):
            draw.line([(i*cell, 0), (i*cell, grid_h)], fill=(200, 200, 220), width=1)
            draw.line([(0, i*cell), (grid_w, i*cell)], fill=(200, 200, 220), width=1)
        for idx, (shape, ci, si) in enumerate(matrix):
            if missing and idx == 8:
                # 空缺格子打问号
                cx = (idx % 3) * cell + cell // 2
                cy = (idx // 3) * cell + cell // 2
                draw.rectangle([cx-25, cy-25, cx+25, cy+25], fill=(240, 240, 240))
                try:
                    fnt = ImageFont.truetype("arial.ttf", 28)
                except:
                    fnt = ImageFont.load_default()
                draw.text((cx-8, cy-14), "?", font=fnt, fill=(150, 150, 150))
                continue
            cx = (idx % 3) * cell + cell // 2
            cy = (idx // 3) * cell + cell // 2
            draw_shape(draw, cx, cy, shape, colors_rgb[ci], sizes[si])
        return img

    def make_option_img(shape, ci, si):
        img = Image.new('RGB', (60, 60), color=(248, 248, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 59, 59], outline=(200, 200, 220), width=1)
        draw_shape(draw, 30, 30, shape, colors_rgb[ci], sizes[si])
        return img

    # 生成3×3规律矩阵
    if rule == "shape_row":
        # 每行shape相同，每列循环shape
        matrix = []
        for r in range(3):
            s = r  # 行固定shape index
            for c in range(3):
                ci = c  # 列固定颜色
                si = 1  # 大小固定
                matrix.append((shapes[s], ci, si))
        correct = matrix[8]

    elif rule == "color_row":
        # 每行颜色相同，列循环形状
        matrix = []
        for r in range(3):
            ci = r  # 行固定颜色
            for c in range(3):
                s = c  # 列固定shape
                si = 1
                matrix.append((shapes[s], ci, si))
        correct = matrix[8]

    else:  # size_row
        # 每格大小从左到右递增，形状按行循环
        matrix = []
        for r in range(3):
            for c in range(3):
                s = r
                ci = 0
                si = c
                matrix.append((shapes[s], ci, si))
        correct = matrix[8]

    # 生成主图（最后格空缺）
    main_img = make_grid_img(matrix, missing=True)

    # 生成4个选项（1个正确 + 3个干扰）
    correct_shape, correct_ci, correct_si = correct
    options = [correct]
    used = {correct}
    while len(options) < 4:
        fake_shape = random.choice(shapes)
        fake_ci = random.randint(0, 2)
        fake_si = random.randint(0, 2)
        fake = (fake_shape, fake_ci, fake_si)
        if fake not in used:
            options.append(fake)
            used.add(fake)
    random.shuffle(options)
    correct_opt_idx = options.index(correct)

    option_imgs = [_to_base64(make_option_img(*opt)) for opt in options]

    return {
        "type": "pattern_rule",
        "image": _to_base64(main_img),
        "question": "找规律：选出 ? 处应填入的图形",
        "options": option_imgs,
        "answer": correct_opt_idx,
    }


# ────────────────────────────────────────────────────────────
# 17. 双模式验证码（图片 + 音频辅助）
# ────────────────────────────────────────────────────────────
def gen_audio_captcha():
    """双模式验证码：显示模糊噪声图片（主要）+ 可选播放音频（辅助），输入4位数字"""
    digits = [random.randint(0, 9) for _ in range(4)]
    code = ''.join(str(d) for d in digits)
    cn_digits = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九']
    cn_text = ''.join(cn_digits[d] for d in digits)

    # ── 生成带噪声的图片（数字清晰可辨，有干扰线和噪点）──
    width, height = 220, 80
    bg_color = (random.randint(230, 250), random.randint(230, 250), random.randint(230, 250))
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 干扰线（5条随机颜色）
    for _ in range(6):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=_random_color(), width=2)

    # 噪点
    for _ in range(150):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        draw.point((x, y), fill=_random_color())

    # 数字文字（逐字绘制，带随机旋转和颜色变化）
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    x_pos = 12
    for ch in code:
        char_img = Image.new('RGBA', (52, 60), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((6, 4), ch, font=font, fill=(*_random_dark_color(), 255))
        angle = random.randint(-18, 18)
        char_img = char_img.rotate(angle, expand=True)
        img.paste(char_img, (x_pos, random.randint(6, 16)), char_img)
        x_pos += 50

    # 前景干扰线（压在文字上方）
    for _ in range(2):
        x1 = random.randint(0, width // 2)
        x2 = random.randint(width // 2, width)
        y1 = random.randint(20, height - 20)
        y2 = random.randint(20, height - 20)
        draw.line([(x1, y1), (x2, y2)], fill=_random_dark_color(), width=2)

    img = img.filter(ImageFilter.SMOOTH)

    # ── 生成音频（辅助，可选）──
    audio_base64 = ""
    audio_format = ""

    # 优先用 pyttsx3
    try:
        import pyttsx3, tempfile, os as _os
        engine_tts = pyttsx3.init()
        engine_tts.setProperty('rate', 130)
        voices = engine_tts.getProperty('voices')
        for v in voices:
            if 'zh' in v.id.lower() or 'chinese' in v.name.lower() or 'huihui' in v.name.lower():
                engine_tts.setProperty('voice', v.id)
                break
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name
        engine_tts.save_to_file(cn_text, tmp_path)
        engine_tts.runAndWait()
        with open(tmp_path, 'rb') as f:
            audio_base64 = base64.b64encode(f.read()).decode('utf-8')
        _os.unlink(tmp_path)
        audio_format = "wav"
    except Exception:
        # 回退 gTTS
        try:
            from gtts import gTTS
            tts = gTTS(text=cn_text, lang='zh-cn', slow=True)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            audio_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            audio_format = "mp3"
        except Exception:
            # 最终回退：captcha库英文音频
            try:
                audio_obj = AudioCaptcha()
                audio_data = audio_obj.generate(code)
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                audio_format = "wav"
            except Exception:
                audio_base64 = ""
                audio_format = ""

    return {
        "type": "audio",
        "image": _to_base64(img),
        "audio": audio_base64,
        "audio_format": audio_format,
        "code": code,
        "cn_text": cn_text,
        "hint": "图片中有4位数字，可点击播放音频辅助确认",
    }


# ────────────────────────────────────────────────────────────
# 18. 拼图旋转验证码
# ────────────────────────────────────────────────────────────
def gen_tile_rotate():
    """将一张图片切成2×2四块，每块随机旋转90/180/270度，用户点击旋转回正确方向"""
    size = 200  # 整图尺寸
    tile = size // 2  # 每块 100×100

    # 生成每一块独立的图片（每块上有清晰的大箭头，正确时箭头朝上）
    block_colors = [
        (220, 100, 80),   # 红
        (80, 140, 220),   # 蓝
        (80, 190, 100),   # 绿
        (200, 160, 40),   # 黄
    ]

    def make_block(color):
        """生成一块带大箭头的图片，箭头朝上为正确方向"""
        img = Image.new('RGB', (tile, tile), color=(240, 245, 255))
        draw = ImageDraw.Draw(img)

        # 背景底色
        r, g, b = color
        draw.rectangle([4, 4, tile-4, tile-4],
                       fill=(min(r+60, 255), min(g+60, 255), min(b+60, 255)),
                       outline=color, width=3)

        # 画一个清晰的箭头（朝上）
        cx, cy = tile // 2, tile // 2
        # 箭头头部（三角形）
        draw.polygon([
            (cx, 12),           # 顶点
            (cx - 22, 48),      # 左下
            (cx + 22, 48),      # 右下
        ], fill=color)
        # 箭头杆
        draw.rectangle([cx - 10, 45, cx + 10, tile - 12], fill=color)

        return img

    # 切块 + 随机旋转
    tiles_data = []
    rotations = []
    for i in range(4):
        piece = make_block(block_colors[i])
        rot = random.choice([90, 180, 270])  # 保证每块都旋转了
        rotations.append(rot)
        rotated = piece.rotate(-rot, expand=False)  # PIL rotate逆时针，用负数表示顺时针旋转
        tiles_data.append(_to_base64(rotated))

    return {
        "type": "tile_rotate",
        "tiles": tiles_data,          # 4张 base64 图片（旋转后的）
        "rotations": rotations,       # 每块当前偏转角度（后端记录，用于验证）
        "tile_size": tile,
    }


# ────────────────────────────────────────────────────────────
# 19. 颜色混合验证码
# ────────────────────────────────────────────────────────────
def gen_color_mix():
    """选择两种颜色混合后的结果"""
    color_pairs = [
        ((255, 0, 0), (0, 0, 255), (128, 0, 128), "红+蓝=紫"),
        ((255, 0, 0), (255, 255, 0), (255, 128, 0), "红+黄=橙"),
        ((0, 255, 0), (0, 0, 255), (0, 128, 128), "绿+蓝=青"),
        ((255, 255, 255), (0, 0, 0), (128, 128, 128), "白+黑=灰"),
        ((255, 0, 0), (255, 255, 255), (255, 128, 128), "红+白=粉"),
    ]
    
    selected = random.choice(color_pairs)
    color1, color2, result, desc = selected
    
    size = 80
    img = Image.new('RGB', (size * 3 + 40, size), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 绘制两个原始色块
    draw.rectangle([0, 0, size, size], fill=color1)
    draw.rectangle([size + 20, 0, size * 2 + 20, size], fill=color2)
    
    # 生成选项（包含正确答案）
    options = [result]
    while len(options) < 4:
        fake = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        if fake not in options and fake != result:
            options.append(fake)
    random.shuffle(options)
    
    return {
        "type": "color_mix",
        "image": _to_base64(img),
        "question": f"{desc}，选择混合后的颜色",
        "answer": result,
        "options": options,
    }


# ────────────────────────────────────────────────────────────
# 20. 时钟验证码（读图输入）
# ────────────────────────────────────────────────────────────
def gen_clock_captcha():
    """展示一个带指针的时钟图片，用户直接输入读出的时间"""
    size = 200
    cx, cy = size // 2, size // 2
    radius = 85

    hour = random.randint(1, 12)
    minute = random.choice([0, 15, 30, 45])

    img = Image.new('RGB', (size, size), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 外圈
    draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius],
                 fill=(245, 248, 255), outline=(50, 50, 80), width=3)

    # 刻度 + 数字
    try:
        num_font = ImageFont.truetype("arial.ttf", 13)
    except:
        num_font = ImageFont.load_default()

    for i in range(1, 13):
        angle = math.pi * i / 6 - math.pi / 2
        # 大刻度线
        x1 = cx + (radius - 12) * math.cos(angle)
        y1 = cy + (radius - 12) * math.sin(angle)
        x2 = cx + (radius - 4) * math.cos(angle)
        y2 = cy + (radius - 4) * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=(60, 60, 80), width=2)
        # 数字
        nx = cx + (radius - 22) * math.cos(angle) - 5
        ny = cy + (radius - 22) * math.sin(angle) - 7
        draw.text((nx, ny), str(i), font=num_font, fill=(60, 60, 80))

    # 分针（长）
    min_angle = math.pi * minute / 30 - math.pi / 2
    draw.line([(cx, cy),
               (cx + (radius - 20) * math.cos(min_angle),
                cy + (radius - 20) * math.sin(min_angle))],
              fill=(30, 80, 200), width=3)

    # 时针（短）
    hour_angle = math.pi * (hour + minute / 60) / 6 - math.pi / 2
    draw.line([(cx, cy),
               (cx + (radius - 40) * math.cos(hour_angle),
                cy + (radius - 40) * math.sin(hour_angle))],
              fill=(20, 20, 20), width=5)

    # 中心点
    draw.ellipse([cx-5, cy-5, cx+5, cy+5], fill=(80, 80, 80))

    return {
        "type": "clock",
        "image": _to_base64(img),
        "question": f"图中时钟显示的是几点几分？",
        "hour": hour,
        "minute": minute,
        "tolerance": 0,  # 精确匹配（选项只有整刻钟，不需要容差）
    }
