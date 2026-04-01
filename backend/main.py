"""
验证码系统 - FastAPI 后端
提供20种验证码的生成与验证接口
"""
import time
import hashlib
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import captcha_engine as engine

app = FastAPI(title="验证码系统", version="1.0.0")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存 Session 存储（生产环境用 Redis）
_sessions: Dict[str, Dict] = {}
_SESSION_TTL = 300  # 5分钟过期


# ────────────────────────────────────────────────────────────
# 工具函数
# ────────────────────────────────────────────────────────────

def _make_session_id(data: dict) -> str:
    raw = str(time.time()) + str(data)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _save_session(data: dict) -> str:
    sid = _make_session_id(data)
    _sessions[sid] = {**data, "_created": time.time()}
    # 清理过期 session
    expired = [k for k, v in _sessions.items() if time.time() - v["_created"] > _SESSION_TTL]
    for k in expired:
        del _sessions[k]
    return sid


def _get_session(sid: str) -> dict | None:
    s = _sessions.get(sid)
    if not s:
        return None
    if time.time() - s["_created"] > _SESSION_TTL:
        del _sessions[sid]
        return None
    return s


# ────────────────────────────────────────────────────────────
# 请求/响应模型
# ────────────────────────────────────────────────────────────

class VerifyRequest(BaseModel):
    session_id: str
    answer: Any


class VerifyResponse(BaseModel):
    success: bool
    message: str


# ────────────────────────────────────────────────────────────
# 生成接口（GET /api/captcha/{type}）
# ────────────────────────────────────────────────────────────

@app.get("/api/captcha/numeric")
def get_numeric():
    data = engine.gen_numeric()
    sid = _save_session({"type": "numeric", "answer": data["code"].lower()})
    return {"session_id": sid, "image": data["image"], "type": data["type"]}


@app.get("/api/captcha/alphanumeric")
def get_alphanumeric():
    data = engine.gen_alphanumeric()
    sid = _save_session({"type": "alphanumeric", "answer": data["code"].lower()})
    return {"session_id": sid, "image": data["image"], "type": data["type"]}


@app.get("/api/captcha/distorted")
def get_distorted():
    data = engine.gen_distorted()
    sid = _save_session({"type": "distorted", "answer": data["code"].lower()})
    return {"session_id": sid, "image": data["image"], "type": data["type"]}


@app.get("/api/captcha/arithmetic")
def get_arithmetic():
    data = engine.gen_arithmetic()
    sid = _save_session({"type": "arithmetic", "answer": data["code"]})
    return {"session_id": sid, "image": data["image"], "question": data["question"], "type": data["type"]}


@app.get("/api/captcha/chinese")
def get_chinese():
    data = engine.gen_chinese()
    sid = _save_session({"type": "chinese", "answer": data["code"]})
    return {"session_id": sid, "image": data["image"], "type": data["type"]}


@app.get("/api/captcha/slider")
def get_slider():
    data = engine.gen_slider()
    sid = _save_session({
        "type": "slider",
        "answer": data["answer"],
        "tolerance": data["tolerance"],
    })
    return {
        "session_id": sid,
        "background": data["background"],
        "slider": data["slider"],
        "gap_y": data["gap_y"],
        "type": data["type"],
    }


@app.get("/api/captcha/click_text")
def get_click_text():
    data = engine.gen_click_text()
    sid = _save_session({
        "type": "click_text",
        "answer": data["answer"],
        "tolerance": data["tolerance"],
    })
    return {
        "session_id": sid,
        "image": data["image"],
        "question": data["question"],
        "type": data["type"],
    }


@app.get("/api/captcha/rotate")
def get_rotate():
    data = engine.gen_rotate()
    sid = _save_session({
        "type": "rotate",
        "answer": data["answer"],
        "tolerance": data["tolerance"],
    })
    return {
        "session_id": sid,
        "image": data["image"],
        "type": data["type"],
    }


@app.get("/api/captcha/image_select")
def get_image_select():
    data = engine.gen_image_select()
    sid = _save_session({"type": "image_select", "answer": sorted(data["answer"])})
    return {
        "session_id": sid,
        "images": data["images"],
        "question": data["question"],
        "type": data["type"],
    }


@app.get("/api/captcha/semantic")
def get_semantic():
    data = engine.gen_semantic()
    sid = _save_session({"type": "semantic", "answer": data["answer"]})
    return {
        "session_id": sid,
        "question": data["question"],
        "hint": data["hint"],
        "type": data["type"],
    }


@app.get("/api/captcha/invisible")
def get_invisible():
    data = engine.gen_invisible()
    sid = _save_session({
        "type": "invisible",
        "token": data["token"],
        "min_time": data["min_time"],
        "_start_time": time.time() * 1000,
    })
    return {
        "session_id": sid,
        "token": data["token"],
        "min_time": data["min_time"],
        "type": data["type"],
        "description": data["description"],
    }


@app.get("/api/captcha/puzzle")
def get_puzzle():
    data = engine.gen_puzzle()
    sid = _save_session({
        "type": "puzzle",
        "answer": data["answer"],
        "shuffled_order": data["shuffled_order"],
    })
    return {
        "session_id": sid,
        "pieces": data["pieces"],
        "shuffled_order": data["shuffled_order"],
        "piece_size": data["piece_size"],
        "type": data["type"],
    }


# ────────────────────────────────────────────────────────────
# 验证接口（POST /api/captcha/verify）
# ────────────────────────────────────────────────────────────

@app.post("/api/captcha/verify")
def verify_captcha(req: VerifyRequest):
    session = _get_session(req.session_id)
    if not session:
        return VerifyResponse(success=False, message="验证码已过期，请刷新")

    ctype = session.get("type")
    answer = session.get("answer")
    user_answer = req.answer

    success = False

    try:
        if ctype in ("numeric", "alphanumeric", "distorted", "chinese"):
            success = str(user_answer).strip().lower() == str(answer).lower()

        elif ctype == "arithmetic":
            success = str(user_answer).strip() == str(answer).strip()

        elif ctype == "slider":
            user_x = int(user_answer)
            tolerance = session.get("tolerance", 15)
            success = abs(user_x - answer) <= tolerance

        elif ctype == "click_text":
            tolerance = session.get("tolerance", 20)
            correct = answer or []
            user_clicks = user_answer if isinstance(user_answer, list) else []
            if len(user_clicks) != len(correct):
                success = False
            else:
                all_match = all(
                    abs(u["x"] - c["x"]) <= tolerance and abs(u["y"] - c["y"]) <= tolerance
                    for u, c in zip(user_clicks, correct)
                )
                success = all_match

        elif ctype == "rotate":
            user_angle = int(user_answer)
            # answer is the angle the image was rotated counter-clockwise
            # user needs to rotate clockwise to restore, so the correct answer is (360 - answer) % 360
            correct_angle = (360 - answer) % 360
            diff = abs(user_angle - correct_angle) % 360
            diff = min(diff, 360 - diff)
            tolerance = session.get("tolerance", 30)
            success = diff <= tolerance

        elif ctype == "image_select":
            user_set = sorted([int(i) for i in (user_answer or [])])
            success = user_set == sorted(answer or [])

        elif ctype == "semantic":
            success = str(user_answer).strip().lower() == str(answer).strip().lower()

        elif ctype == "invisible":
            elapsed = user_answer.get("elapsed_ms", 0) if isinstance(user_answer, dict) else 0
            token = user_answer.get("token", "") if isinstance(user_answer, dict) else ""
            moved = user_answer.get("mouse_moved", False) if isinstance(user_answer, dict) else False
            success = (
                elapsed >= session.get("min_time", 1000)
                and token == session.get("token", "")
                and moved
            )

        elif ctype == "puzzle":
            user_order = [int(i) for i in (user_answer or [])]
            success = user_order == (answer or [])

        # ────────────────────────────────────────────────────────────
        # 新增验证码验证逻辑 (13-20)
        # ────────────────────────────────────────────────────────────

        elif ctype == "pinyin":
            # 拼音首字母验证：大小写不敏感
            success = str(user_answer).strip().lower() == str(answer).strip().lower()

        elif ctype == "pattern_lock":
            # 图案锁验证：用户绘制的路径与正确路径相同
            user_path = [int(i) for i in (user_answer or [])]
            success = user_path == (answer or [])

        elif ctype == "odd_one_out":
            # 用户点击的是第几个字（0-based），通过点击x坐标换算
            try:
                if isinstance(user_answer, dict):
                    click_x = float(user_answer.get("x", -1))
                    img_w = 360.0
                    count = session.get("count", 6)
                    cell_w = session.get("cell_w", 60)
                    # 将点击x映射到格子索引
                    clicked_idx = int(click_x * count / img_w)
                    clicked_idx = max(0, min(count - 1, clicked_idx))
                else:
                    clicked_idx = int(user_answer)
                success = clicked_idx == answer
            except:
                success = False

        elif ctype == "pattern_rule":
            try:
                success = int(user_answer) == int(answer)
            except:
                success = False

        elif ctype == "audio":
            user_code = str(user_answer).upper() if user_answer else ""
            success = user_code == str(answer).upper()

        elif ctype == "tile_rotate":
            # user_answer: [rot0, rot1, rot2, rot3] 用户对每块累计点击旋转的总角度
            # answer: 后端记录的初始旋转角度，用户需要把每块转回0
            initial_rots = answer  # list of 4 angles [90,180,270,...]
            user_rots = [int(r) % 360 for r in (user_answer or [0, 0, 0, 0])]
            # 用户转回正确：初始角 + 用户点击累计角 ≡ 0 (mod 360)
            success = all(
                (initial_rots[i] + user_rots[i]) % 360 == 0
                for i in range(4)
            )

        elif ctype == "color_mix":
            user_color = user_answer if isinstance(user_answer, list) else [0, 0, 0]
            diff = sum(abs(u - a) for u, a in zip(user_color, answer))
            success = diff < 50  # 允许一定的颜色误差

        elif ctype == "clock":
            user_time = user_answer if isinstance(user_answer, dict) else {}
            user_hour = int(user_time.get("hour", 0))
            user_minute = int(user_time.get("minute", 0))
            target_hour = session.get("hour", 12)
            target_minute = session.get("minute", 0)
            # 精确匹配（时钟只有整刻钟，分钟只有0/15/30/45）
            success = (user_hour == target_hour and user_minute == target_minute)

    except Exception:
        success = False

    # 验证成功后删除 session（防止重放）
    if success and req.session_id in _sessions:
        del _sessions[req.session_id]

    return VerifyResponse(
        success=success,
        message="验证成功 ✓" if success else "验证失败，请重试"
    )


# ────────────────────────────────────────────────────────────
# 静态文件服务（前端）
# ────────────────────────────────────────────────────────────

import os
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))


    # ────────────────────────────────────────────────────────────
    # 新增验证码 API (13-20)
    # ────────────────────────────────────────────────────────────

    @app.get("/api/captcha/pinyin")
    def get_pinyin_captcha():
        data = engine.gen_pinyin_captcha()
        sid = _save_session({
            "type": "pinyin",
            "answer": data["answer"],
        })
        return {
            "session_id": sid,
            "image": data["image"],
            "hint": data["hint"],
            "type": data["type"],
        }

    @app.get("/api/captcha/pattern_lock")
    def get_pattern_lock():
        data = engine.gen_pattern_lock()
        sid = _save_session({
            "type": "pattern_lock",
            "answer": data["path"],
        })
        return {
            "session_id": sid,
            "hint_image": data["hint_image"],
            "path_len": data["path_len"],
            "type": data["type"],
        }

    @app.get("/api/captcha/odd_one_out")
    def get_odd_one_out():
        data = engine.gen_odd_one_out()
        sid = _save_session({
            "type": "odd_one_out",
            "answer": data["answer"],
            "count": data["count"],
            "cell_w": data["cell_w"],
            "height": data["height"],
        })
        return {
            "session_id": sid,
            "image": data["image"],
            "question": data["question"],
            "count": data["count"],
            "cell_w": data["cell_w"],
            "height": data["height"],
            "type": data["type"],
        }

    @app.get("/api/captcha/pattern_rule")
    def get_pattern_rule():
        data = engine.gen_pattern_rule()
        sid = _save_session({
            "type": "pattern_rule",
            "answer": data["answer"],
        })
        return {
            "session_id": sid,
            "image": data["image"],
            "question": data["question"],
            "options": data["options"],
            "type": data["type"],
        }

    @app.get("/api/captcha/audio")
    def get_audio_captcha():
        data = engine.gen_audio_captcha()
        sid = _save_session({
            "type": "audio",
            "answer": data["code"],
        })
        return {
            "session_id": sid,
            "image": data["image"],
            "audio": data["audio"],
            "audio_format": data.get("audio_format", ""),
            "hint": data["hint"],
            "type": data["type"],
        }

    @app.get("/api/captcha/tile_rotate")
    def get_tile_rotate():
        data = engine.gen_tile_rotate()
        sid = _save_session({
            "type": "tile_rotate",
            "answer": data["rotations"],   # 初始各块旋转角度，用于验证
        })
        return {
            "session_id": sid,
            "tiles": data["tiles"],        # 4块 base64 图片
            "tile_size": data["tile_size"],
            "type": data["type"],
        }

    @app.get("/api/captcha/color_mix")
    def get_color_mix():
        data = engine.gen_color_mix()
        sid = _save_session({
            "type": "color_mix",
            "answer": data["answer"],
        })
        return {
            "session_id": sid,
            "image": data["image"],
            "question": data["question"],
            "options": data["options"],
            "type": data["type"],
        }

    @app.get("/api/captcha/clock")
    def get_clock_captcha():
        data = engine.gen_clock_captcha()
        sid = _save_session({
            "type": "clock",
            "hour": data["hour"],
            "minute": data["minute"],
            "tolerance": data["tolerance"],
        })
        return {
            "session_id": sid,
            "image": data["image"],
            "question": data["question"],
            "hour": data["hour"],
            "minute": data["minute"],
            "type": data["type"],
        }

    @app.get("/app.js")
    def serve_app_js():
        from fastapi.responses import Response
        with open(os.path.join(frontend_dir, "app.js"), "r", encoding="utf-8") as f:
            content = f.read()
        return Response(
            content=content,
            media_type="application/javascript; charset=utf-8",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
