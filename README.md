# 🔐 验证码系统 - 全行业解决方案

完整的验证码系统，实现业界主流的 **20 种验证码类型**，从简单到复杂，满足各种安全需求。

---

## 📋 功能特性

### 📝 基础文字验证码

| 类型      | API 端点         | 难度  |
| ------- | -------------- | --- |
| 数字验证码   | `numeric`      | 简单  |
| 字母数字混合  | `alphanumeric` | 简单  |
| 扭曲变形验证码 | `distorted`    | 中等  |
| 中文验证码   | `chinese`      | 中等  |
| 拼音输入    | `pinyin`       | 简单  |

### 🎯 交互操作验证码

| 类型      | API 端点         | 难度  |
| ------- | -------------- | --- |
| 滑块拼图验证码 | `slider`       | 困难  |
| 点选验证码   | `click_text`   | 困难  |
| 旋转验证码   | `rotate`       | 困难  |
| 图案锁     | `pattern_lock` | 困难  |
| 拼图旋转    | `tile_rotate`  | 困难  |

### 🧠 认知推理验证码

| 类型      | API 端点         | 难度  |
| ------- | -------------- | --- |
| 算术验证码   | `arithmetic`   | 简单  |
| 语义问答验证码 | `semantic`     | 简单  |
| 形近字找不同  | `odd_one_out`  | 困难  |
| 图形找规律   | `pattern_rule` | 专家  |
| 颜色混合    | `color_mix`    | 中等  |
| 时钟验证码   | `clock`        | 中等  |

### 🎨 多媒体识别验证码

| 类型       | API 端点         | 难度  |
| -------- | -------------- | --- |
| 图片选择验证码  | `image_select` | 专家  |
| 图片+音频双模式 | `audio`        | 中等  |

### 🔮 行为与特殊验证码

| 类型     | API 端点      | 难度  |
| ------ | ----------- | --- |
| 不可见验证码 | `invisible` | 专家  |
| 九宫格拼图  | `puzzle`    | 专家  |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd captcha-system/backend
pip install -r requirements.txt
```

### 2. 启动服务

**Windows：**

```bat
start.bat
```

**Linux / macOS：**

```bash
chmod +x start.sh
./start.sh
```

**手动启动：**

```bash
cd captcha-system/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. 访问系统

打开浏览器访问：http://localhost:8000

---

## 📁 项目结构

```
captcha-system/
├── backend/
│   ├── main.py              # FastAPI 主程序（20种验证码接口）
│   ├── captcha_engine.py    # 验证码引擎（所有类型的生成逻辑）
│   └── requirements.txt     # 依赖列表
├── frontend/
│   ├── index.html           # 主页面（5分类展示所有验证码）
│   └── app.js               # 前端交互脚本
├── start.bat                # Windows 启动脚本
├── start.sh                 # Linux / macOS 启动脚本
└── README.md                # 本文档
```

---

## 📁界面展示

![FireShot Capture 006 - 验证码系统 - 全行业解决方案 - [localhost]](D:\Chrome下载\FireShot\FireShot%20Capture%20006%20-%20验证码系统%20-%20全行业解决方案%20-%20[localhost].png)

---

## 🔧 API 接口

### 生成验证码

```http
GET /api/captcha/{type}
```

**响应示例（文字类）：**

```json
{
  "session_id": "abc123",
  "image": "data:image/png;base64,...",
  "type": "numeric"
}
```

### 验证验证码

```http
POST /api/captcha/verify
Content-Type: application/json

{
  "session_id": "abc123",
  "answer": "用户输入的答案"
}
```

**响应示例：**

```json
{
  "success": true,
  "message": "验证成功 ✓"
}
```

**不同类型的 answer 格式：**

| 类型                                                 | answer 格式                                                   |
| -------------------------------------------------- | ----------------------------------------------------------- |
| 文字类（numeric/alphanumeric/distorted/chinese/pinyin） | `"字符串"`                                                     |
| 算术/语义问答                                            | `"字符串"`                                                     |
| 滑块（slider）                                         | `整数（像素偏移量）`                                                 |
| 点选（click_text）                                     | `[{"x": 100, "y": 50}, ...]`                                |
| 旋转（rotate）                                         | `整数（角度，顺时针）`                                                |
| 图案锁（pattern_lock）                                  | `[0, 4, 8, ...]（格子索引序列）`                                    |
| 图片选择（image_select）                                 | `[0, 2, 3]（选中的图片索引）`                                        |
| 不可见（invisible）                                     | `{"elapsed_ms": 1500, "token": "...", "mouse_moved": true}` |
| 九宫格拼图（puzzle）                                      | `[0, 1, 2, ...]（正确顺序）`                                      |
| 拼图旋转（tile_rotate）                                  | `[0, 90, 180, 270]（每块旋转角度）`                                 |
| 颜色混合（color_mix）                                    | `[R, G, B]`                                                 |
| 时钟（clock）                                          | `{"hour": 3, "minute": 30}`                                 |

---

## 🛠️ 技术栈

### 后端

- **FastAPI** - 高性能 Web 框架
- **Pillow** - 图像处理
- **captcha** - 验证码生成
- **Python 3.8+**

### 前端

- **原生 HTML/CSS/JavaScript** - 无外部依赖
- **Drag & Drop API** - 拖拽交互
- **Canvas API** - 图案锁绘制
- **Web Audio API** - 音频播放

---

## 📝 扩展开发

### 添加新的验证码类型

1. 在 `backend/captcha_engine.py` 中添加生成函数
2. 在 `backend/main.py` 中添加对应的 GET 接口和验证逻辑
3. 在 `frontend/index.html` 中添加前端卡片
4. 在 `frontend/app.js` 中添加交互逻辑

```python
# captcha_engine.py
def gen_custom():
    code = "自定义验证码"
    img = Image.new('RGB', (200, 60))
    # ... 绘制逻辑
    return {"code": code, "image": _to_base64(img), "type": "custom"}

# main.py
@app.get("/api/captcha/custom")
def get_custom():
    data = engine.gen_custom()
    sid = _save_session({"type": "custom", "answer": data["code"]})
    return {"session_id": sid, "image": data["image"], "type": "custom"}
```

---

## ⚠️ 注意事项

1. **Session 存储**：当前使用内存存储，重启后 session 丢失；生产环境建议使用 Redis
2. **超时时间**：验证码默认 5 分钟过期
3. **字体依赖**：中文/拼音验证码依赖系统字体（Linux 需安装中文字体，如 `fonts-wqy-zenhei`）
4. **跨域配置**：已配置 CORS 允许所有来源，生产环境建议限制

### Linux 中文字体安装

```bash
# Debian/Ubuntu
sudo apt-get install fonts-wqy-zenhei fonts-wqy-microhei

# CentOS/RHEL
sudo yum install wqy-zenhei-fonts wqy-microhei-fonts

# Arch Linux
sudo pacman -S wqy-zenhei wqy-microhei
```

---

## 📄 License

MIT License
