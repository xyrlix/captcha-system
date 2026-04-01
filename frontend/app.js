/**
 * 验证码系统 - 前端脚本
 * 处理所有验证码的交互和验证逻辑
 */

const API_BASE = 'http://localhost:8000/api/captcha';

// Session ID 存储
const sessions = {};

// 特殊验证码的状态
const captchaState = {
    slider: { isDragging: false, startX: 0, currentX: 0 },
    clickText: { clicks: [] },
    rotate: { angle: 0 },
    imageSelect: { selected: [] },
    invisible: { startTime: null, mouseMoved: false },
    puzzle: { order: [] },
    // 新增验证码状态
    pinyin: { answer: '' },
    patternLock: { path: [], drawing: false },
    iconSelect: { selected: [] },
    spatialReasoning: { answer: null },
    oddOneOut: { clickX: -1 },       // 文字找不同：点击的x坐标（图片坐标系）
    patternRule: { answer: null },    // 图形找规律：选择的选项索引
    audio: { answer: '' },
    tileRotate: { userRots: [0, 0, 0, 0] },  // 用户对每块累计顺时针旋转角度
    colorMix: { answer: null },
    clock: { hour: 12, minute: 0 }
};

// ────────────────────────────────────────────────────────────
// 通用函数
// ────────────────────────────────────────────────────────────

function getSession(type) {
    return sessions[type];
}

function setSession(type, sid) {
    sessions[type] = sid;
}

function showResult(type, success, message) {
    const resultEl = document.getElementById(`${type}-result`);
    console.log(`showResult called: type=${type}, element=`, resultEl);
    if (resultEl) {
        resultEl.className = `result ${success ? 'success' : 'error'}`;
        resultEl.textContent = message;
        resultEl.style.display = 'block';  // 强制显示
        console.log(`[${type}] ${success ? '✓' : '✗'} ${message}`);
        console.log(`Result element className:`, resultEl.className);
        console.log(`Result element display:`, resultEl.style.display);
    } else {
        console.error(`Result element not found: ${type}-result`);
    }
}

// ────────────────────────────────────────────────────────────
// 刷新验证码
// ────────────────────────────────────────────────────────────

async function refreshCaptcha(type) {
    try {
        const response = await fetch(`${API_BASE}/${type}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();

        setSession(type, data.session_id);

        // 根据类型处理不同的展示方式
        switch (type) {
            case 'numeric':
            case 'alphanumeric':
            case 'distorted':
            case 'chinese': {
                const imgEl = document.getElementById(`${type}-img`);
                if (imgEl && data.image) {
                    imgEl.src = data.image;
                    document.getElementById(`${type}-input`).value = '';
                    console.log(`Loaded ${type} captcha`);
                } else {
                    console.error(`Failed to load ${type}:`, data);
                }
                break;
            }

            case 'arithmetic':
                document.getElementById(`arithmetic-img`).src = data.image;
                document.getElementById(`arithmetic-input`).value = '';
                break;

            case 'slider':
                document.getElementById('slider-bg-img').src = data.background;
                document.getElementById('slider-thumb-img').src = data.slider;
                captchaState.slider.currentX = 0;
                document.getElementById('slider-thumb').style.left = '0%';
                break;

            case 'click_text':
                document.getElementById('click-img').src = data.image;
                document.getElementById('click-question').textContent = data.question;
                // 清除之前的点击标记
                document.querySelectorAll('.click-mark').forEach(el => el.remove());
                captchaState.clickText.clicks = [];
                break;

            case 'rotate':
                document.getElementById('rotate-img').src = data.image;
                document.getElementById('rotate-range').value = 0;
                document.getElementById('rotate-value').textContent = '0';
                captchaState.rotate.angle = 0;
                break;

            case 'image_select': {
                document.getElementById('image-select-question').textContent = data.question;
                const grid = document.getElementById('image-select-grid');
                grid.innerHTML = '';
                data.images.forEach((imgSrc, idx) => {
                    const div = document.createElement('div');
                    div.className = 'image-select-item';
                    div.dataset.index = idx;
                    div.innerHTML = `<img src="${imgSrc}" alt="图片${idx}">`;
                    div.onclick = () => toggleImageSelect(idx);
                    grid.appendChild(div);
                });
                captchaState.imageSelect.selected = [];
                break;
            }

            case 'semantic':
                document.getElementById('semantic-question').textContent = data.question;
                document.getElementById('semantic-hint').textContent = data.hint;
                document.getElementById('semantic-input').value = '';
                break;

            case 'invisible':
                document.getElementById('invisible-time').textContent = data.min_time;
                document.getElementById('invisible-elapsed').textContent = '0';
                document.getElementById('invisible-status').textContent = '请将鼠标移入此区域';
                document.getElementById('invisible-hint').textContent = '计时将从鼠标进入开始';
                document.getElementById('invisible-indicator').style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                document.getElementById('invisible-verify-btn').disabled = false;
                // reset state - timer will start on mouseenter
                captchaState.invisible.startTime = null;
                captchaState.invisible.mouseMoved = false;
                captchaState.invisible.token = data.token;
                captchaState.invisible.minTime = data.min_time;
                stopInvisibleTimer();
                console.log('[invisible] token saved: ' + data.token);
                break;

            case 'puzzle': {
                const container = document.getElementById('puzzle-container');
                container.innerHTML = '';
                data.pieces.forEach((pieceSrc, idx) => {
                    const div = document.createElement('div');
                    div.className = 'puzzle-piece';
                    div.dataset.originalIdx = data.shuffled_order[idx];
                    div.draggable = true;
                    div.innerHTML = '<img src="' + pieceSrc + '" alt="拼图块' + idx + '">';
                    container.appendChild(div);
                });
                initPuzzleDrag();
                captchaState.puzzle.order = data.shuffled_order;
                break;
            }

            // ────────────────────────────────────────────────────────────
            // 新增验证码初始化 (13-20)
            // ────────────────────────────────────────────────────────────

            case 'pinyin':
                document.getElementById('pinyin-img').src = data.image;
                document.getElementById('pinyin-hint').textContent = data.hint;
                document.getElementById('pinyin-input').value = '';
                captchaState.pinyin.answer = '';
                break;

            case 'pattern_lock':
                captchaState.patternLock.path = [];
                captchaState.patternLock.drawing = false;
                document.getElementById('pattern-hint-img').src = data.hint_image;
                document.getElementById('pattern-count').textContent = '0';
                initPatternCanvas();
                break;

            case 'odd_one_out':
                document.getElementById('odd-img').src = data.image;
                document.getElementById('odd-question').textContent = data.question;
                captchaState.oddOneOut.clickX = -1;
                document.getElementById('odd-clicked').textContent = '-';
                // 清除旧标记
                document.querySelectorAll('#odd-canvas .click-mark').forEach(el => el.remove());
                break;

            case 'pattern_rule':
                document.getElementById('pattern-rule-img').src = data.image;
                document.getElementById('pattern-rule-question').textContent = data.question;
                captchaState.patternRule.answer = null;
                initPatternRuleOptions(data.options);
                break;

            case 'audio':
                // 图片（主要）
                if (data.image) {
                    document.getElementById('audio-captcha-img').src = data.image;
                }
                // 音频（辅助）
                if (data.audio) {
                    const fmt = data.audio_format || 'wav';
                    const mimeMap = { wav: 'audio/wav', mp3: 'audio/mpeg' };
                    const mime = mimeMap[fmt] || 'audio/wav';
                    document.getElementById('audio-player').src = `data:${mime};base64,${data.audio}`;
                } else {
                    document.getElementById('audio-player').src = '';
                }
                document.getElementById('audio-answer').value = '';
                captchaState.audio.answer = '';
                break;

            case 'tile_rotate':
                captchaState.tileRotate.userRots = [0, 0, 0, 0];
                initTileRotate(data.tiles);
                break;

            case 'color_mix':
                document.getElementById('color-img').src = data.image;
                document.getElementById('color-question').textContent = data.question;
                captchaState.colorMix.answer = null;
                initColorOptions(data.options);
                break;

            case 'clock':
                document.getElementById('clock-question').textContent = data.question;
                document.getElementById('clock-img').src = data.image;
                // 重置输入
                document.getElementById('clock-hour').value = 12;
                document.getElementById('clock-minute').value = 0;
                captchaState.clock.targetHour = data.hour;
                captchaState.clock.targetMinute = data.minute;
                break;
        }

        // 清除结果提示
        const resultEl = document.getElementById(`${type}-result`);
        if (resultEl) {
            resultEl.style.display = 'none';
        }

    } catch (error) {
        console.error('刷新验证码失败:', error);
        showResult(type, false, `刷新失败: ${error.message}`);
    }
}

// ────────────────────────────────────────────────────────────
// 验证验证码
// ────────────────────────────────────────────────────────────

async function verifyCaptcha(type) {
    let answer;
    const sid = getSession(type);

    console.log(`[verifyCaptcha] type=${type}, sid=${sid}`);

    if (!sid) {
        showResult(type, false, '验证码已过期，请刷新');
        return;
    }

    switch (type) {
        case 'numeric':
        case 'alphanumeric':
        case 'distorted':
        case 'chinese':
        case 'arithmetic':
        case 'semantic': {
            const inputEl = document.getElementById(`${type}-input`);
            answer = inputEl ? inputEl.value : '';
            console.log(`[${type}] input value: "${answer}"`);
            break;
        }

        case 'slider': {
            // 计算滑块对应的x坐标
            const sliderTrack = document.querySelector('.slider-track');
            const sliderWidth = sliderTrack ? sliderTrack.offsetWidth : 280;
            const bgWidth = 320;
            const sliderAnswer = Math.round((captchaState.slider.currentX / sliderWidth) * bgWidth);
            console.log(`[slider] currentX=${captchaState.slider.currentX}, sliderWidth=${sliderWidth}, answer=${sliderAnswer}`);
            answer = sliderAnswer;
            break;
        }

        case 'click_text':
            answer = captchaState.clickText.clicks;
            break;

        case 'rotate':
            console.log(`[rotate] angle=${captchaState.rotate.angle}`);
            answer = captchaState.rotate.angle;
            break;

        case 'image_select':
            answer = captchaState.imageSelect.selected;
            break;

        case 'invisible': {
            const elapsed = Date.now() - captchaState.invisible.startTime;
            answer = {
                elapsed_ms: elapsed,
                mouse_moved: captchaState.invisible.mouseMoved,
                token: captchaState.invisible.token || ''
            };
            // stop timer during verification
            if (invisibleTimer) clearInterval(invisibleTimer);
            break;
        }

        case 'puzzle': {
            const pieces = document.querySelectorAll('.puzzle-piece');
            answer = Array.from(pieces).map(p => parseInt(p.dataset.originalIdx));
            break;
        }

        // ────────────────────────────────────────────────────────────
        // 新增验证码答案收集 (13-20)
        // ────────────────────────────────────────────────────────────

        case 'pinyin':
            answer = document.getElementById('pinyin-input').value.trim();
            break;

        case 'pattern_lock':
            answer = captchaState.patternLock.path;
            break;

        case 'odd_one_out':
            answer = { x: captchaState.oddOneOut.clickX };
            break;

        case 'pattern_rule':
            answer = captchaState.patternRule.answer;
            break;

        case 'audio':
            answer = document.getElementById('audio-answer').value;
            break;

        case 'tile_rotate':
            answer = captchaState.tileRotate.userRots;
            break;

        case 'color_mix':
            answer = captchaState.colorMix.answer;
            break;

        case 'clock':
            answer = {
                hour: parseInt(document.getElementById('clock-hour').value),
                minute: parseInt(document.getElementById('clock-minute').value)
            };
            break;
    }

    try {
        const response = await fetch(`${API_BASE}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sid,
                answer: answer
            })
        });

        const result = await response.json();
        console.log(`[${type}] verify response:`, result);
        showResult(type, result.success, result.message);

        if (result.success) {
            // 验证成功后3秒自动刷新
            setTimeout(() => refreshCaptcha(type), 3000);
        }

    } catch (error) {
        console.error('验证失败:', error);
        showResult(type, false, '验证请求失败，请刷新验证码');
    }
}

// ────────────────────────────────────────────────────────────
// 滑块验证码逻辑
// ────────────────────────────────────────────────────────────

function initSlider() {
    const thumb = document.getElementById('slider-thumb');
    const track = document.querySelector('.slider-track');

    thumb.addEventListener('mousedown', (e) => {
        captchaState.slider.isDragging = true;
        const trackRect = track.getBoundingClientRect();
        captchaState.slider.startX = e.clientX - trackRect.left - thumb.offsetLeft;
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (!captchaState.slider.isDragging) return;

        const trackRect = track.getBoundingClientRect();
        let newX = e.clientX - trackRect.left - captchaState.slider.startX;
        newX = Math.max(0, Math.min(newX, trackRect.width - thumb.offsetWidth));

        captchaState.slider.currentX = newX;
        thumb.style.left = newX + 'px';
    });

    document.addEventListener('mouseup', () => {
        captchaState.slider.isDragging = false;
    });
}

// ────────────────────────────────────────────────────────────
// 点选验证码逻辑
// ────────────────────────────────────────────────────────────

function handleClickText(e) {
    console.log('[click_text] === CLICK EVENT FIRED ===');
    const canvas = document.getElementById('click-canvas');
    const img = document.getElementById('click-img');

    const canvasRect = canvas.getBoundingClientRect();
    const displayX = e.clientX - canvasRect.left;
    const displayY = e.clientY - canvasRect.top;

    const imgW = img.offsetWidth || canvasRect.width;
    const imgH = img.offsetHeight || canvasRect.height;
    const sx = 300 / imgW;
    const sy = 200 / imgH;

    const imgX = Math.round(displayX * sx);
    const imgY = Math.round(displayY * sy);

    console.log('[click_text] canvas(' + canvasRect.width.toFixed(0) + 'x' + canvasRect.height.toFixed(0) + ') img(' + imgW + 'x' + imgH + ')');
    console.log('[click_text] click(' + displayX.toFixed(0) + ',' + displayY.toFixed(0) + ') -> original(' + imgX + ',' + imgY + ') scale(' + sx.toFixed(2) + ',' + sy.toFixed(2) + ')');

    const mark = document.createElement('div');
    mark.className = 'click-mark';
    mark.style.left = displayX + 'px';
    mark.style.top = displayY + 'px';
    canvas.appendChild(mark);

    captchaState.clickText.clicks.push({ x: imgX, y: imgY });

    if (captchaState.clickText.clicks.length > 3) {
        captchaState.clickText.clicks.shift();
        const marks = canvas.querySelectorAll('.click-mark');
        if (marks.length > 0) marks[0].remove();
    }
}

function initClickText() {
}

// ────────────────────────────────────────────────────────────
// 旋转验证码逻辑
// ────────────────────────────────────────────────────────────

function initRotate() {
    const range = document.getElementById('rotate-range');
    const img = document.getElementById('rotate-img');
    const value = document.getElementById('rotate-value');

    range.addEventListener('input', (e) => {
        const angle = parseInt(e.target.value);
        img.style.transform = `rotate(${angle}deg)`;
        value.textContent = angle;
        captchaState.rotate.angle = angle;
    });
}

// ────────────────────────────────────────────────────────────
// 图片选择验证码逻辑
// ────────────────────────────────────────────────────────────

function toggleImageSelect(idx) {
    const idxStr = String(idx);
    const idxNum = idx;
    const selectedSet = new Set(captchaState.imageSelect.selected);

    if (selectedSet.has(idxNum)) {
        selectedSet.delete(idxNum);
    } else {
        selectedSet.add(idxNum);
    }

    captchaState.imageSelect.selected = Array.from(selectedSet);

    // 更新UI
    document.querySelectorAll('.image-select-item').forEach(item => {
        if (item.dataset.index === idxStr) {
            item.classList.toggle('selected');
        }
    });
}

// ────────────────────────────────────────────────────────────
// 不可见验证码逻辑
// ────────────────────────────────────────────────────────────

var invisibleTimer = null;

function startInvisibleTimer() {
    if (invisibleTimer) clearInterval(invisibleTimer);
    invisibleTimer = setInterval(updateInvisibleStatus, 100);
}

function stopInvisibleTimer() {
    if (invisibleTimer) {
        clearInterval(invisibleTimer);
        invisibleTimer = null;
    }
}

function updateInvisibleStatus() {
    if (!captchaState.invisible.startTime) return;

    var elapsed = Date.now() - captchaState.invisible.startTime;
    var minTime = captchaState.invisible.minTime || 3000;
    var moved = captchaState.invisible.mouseMoved;

    document.getElementById('invisible-elapsed').textContent = elapsed;

    var statusEl = document.getElementById('invisible-status');
    var hintEl = document.getElementById('invisible-hint');
    var indicatorEl = document.getElementById('invisible-indicator');

    if (elapsed >= minTime && moved) {
        statusEl.textContent = '检测完成';
        hintEl.textContent = '可以点击验证了';
        indicatorEl.style.background = 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)';
    } else if (elapsed >= minTime && !moved) {
        statusEl.textContent = '等待交互...';
        hintEl.textContent = '请移动鼠标或点击页面';
        indicatorEl.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
    } else {
        statusEl.textContent = '正在检测行为...';
        hintEl.textContent = '停留时间不足，请等待';
        indicatorEl.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    }
}

function initInvisible() {
    var indicator = document.getElementById('invisible-indicator');

    // only start timer when mouse enters the area
    indicator.addEventListener('mouseenter', function() {
        if (!captchaState.invisible.startTime) {
            captchaState.invisible.startTime = Date.now();
            captchaState.invisible.mouseMoved = false;
            startInvisibleTimer();
        }
    });

    // track mouse movement inside the area
    indicator.addEventListener('mousemove', function() {
        if (!captchaState.invisible.mouseMoved) {
            captchaState.invisible.mouseMoved = true;
        }
    });

    // reset when mouse leaves (only if not yet completed)
    indicator.addEventListener('mouseleave', function() {
        var minTime = captchaState.invisible.minTime || 3000;
        var elapsed = captchaState.invisible.startTime ? (Date.now() - captchaState.invisible.startTime) : 0;
        var moved = captchaState.invisible.mouseMoved;

        // only reset if conditions not met yet
        if (elapsed < minTime || !moved) {
            stopInvisibleTimer();
            captchaState.invisible.startTime = null;
            captchaState.invisible.mouseMoved = false;
            document.getElementById('invisible-elapsed').textContent = '0';
            document.getElementById('invisible-status').textContent = '请将鼠标移入此区域';
            document.getElementById('invisible-hint').textContent = '计时将从鼠标进入开始';
            indicator.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        }
    });
}

// ────────────────────────────────────────────────────────────
// 九宫格拼图逻辑
// ────────────────────────────────────────────────────────────

function initPuzzleDrag() {
    const pieces = document.querySelectorAll('.puzzle-piece');
    let draggedItem = null;

    pieces.forEach(piece => {
        piece.addEventListener('dragstart', (e) => {
            draggedItem = piece;
            piece.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        });

        piece.addEventListener('dragend', () => {
            piece.classList.remove('dragging');
            draggedItem = null;
        });

        piece.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });

        piece.addEventListener('drop', (e) => {
            e.preventDefault();
            if (draggedItem && draggedItem !== piece) {
                // 交换两个拼图块的内容
                const tempHTML = draggedItem.innerHTML;
                const tempIdx = draggedItem.dataset.originalIdx;

                draggedItem.innerHTML = piece.innerHTML;
                draggedItem.dataset.originalIdx = piece.dataset.originalIdx;

                piece.innerHTML = tempHTML;
                piece.dataset.originalIdx = tempIdx;
            }
        });
    });
}

// ────────────────────────────────────────────────────────────
// 新增验证码交互函数 (13-20)
// ────────────────────────────────────────────────────────────

// 13. 拼音输入验证码
document.addEventListener('DOMContentLoaded', function() {
    var pinyinInput = document.getElementById('pinyin-input');
    if (pinyinInput) {
        pinyinInput.addEventListener('input', function() {
            captchaState.pinyin.answer = this.value.trim();
        });
    }
});

// 14. 图案锁验证码
function initPatternCanvas() {
    var canvas = document.getElementById('pattern-canvas');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');

    // 重置路径
    captchaState.patternLock.path = [];
    captchaState.patternLock.lastNode = null;
    document.getElementById('pattern-count').textContent = '0';

    // 3×3 点阵位置（与后端一致）
    var margin = 40;
    var spacing = 80;
    var points = [];
    for (var r = 0; r < 3; r++) {
        for (var c = 0; c < 3; c++) {
            points.push({ x: margin + c * spacing, y: margin + r * spacing, idx: r * 3 + c });
        }
    }

    // 绘制初始点阵
    function drawBase() {
        ctx.clearRect(0, 0, 240, 240);
        ctx.fillStyle = '#1e1e32';
        ctx.fillRect(0, 0, 240, 240);
        for (var i = 0; i < points.length; i++) {
            var p = points[i];
            ctx.beginPath();
            ctx.arc(p.x, p.y, 12, 0, Math.PI * 2);
            ctx.fillStyle = '#505078';
            ctx.fill();
            ctx.strokeStyle = '#9696c8';
            ctx.lineWidth = 2;
            ctx.stroke();
            // 编号
            ctx.fillStyle = '#ccc';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(String(i + 1), p.x, p.y);
        }
    }

    drawBase();

    var path = [];
    var lastNode = null;
    var drawing = false;

    function getNodeAt(x, y) {
        for (var i = 0; i < points.length; i++) {
            var p = points[i];
            if (Math.sqrt((x - p.x) ** 2 + (y - p.y) ** 2) < 18) return p;
        }
        return null;
    }

    canvas.onmousedown = function(e) {
        drawing = true;
        var rect = canvas.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;
        var node = getNodeAt(x, y);
        if (node && !path.includes(node.idx)) {
            path = [node.idx];
            lastNode = node;
            captchaState.patternLock.path = path;
            document.getElementById('pattern-count').textContent = path.length;
            drawBase();
            ctx.beginPath();
            ctx.arc(node.x, node.y, 14, 0, Math.PI * 2);
            ctx.fillStyle = '#3296ff';
            ctx.fill();
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 13px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('1', node.x, node.y);
        }
    };

    canvas.onmousemove = function(e) {
        if (!drawing || !lastNode) return;
        var rect = canvas.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;
        var node = getNodeAt(x, y);
        if (node && !path.includes(node.idx)) {
            path.push(node.idx);
            captchaState.patternLock.path = path;
            document.getElementById('pattern-count').textContent = path.length;

            // 重绘（连线 + 已激活节点）
            drawBase();
            // 画连线
            ctx.strokeStyle = '#64c8ff';
            ctx.lineWidth = 4;
            for (var i = 0; i < path.length - 1; i++) {
                var a = points[path[i]], b = points[path[i+1]];
                ctx.beginPath();
                ctx.moveTo(a.x, a.y);
                ctx.lineTo(b.x, b.y);
                ctx.stroke();
            }
            // 高亮已选节点
            for (var j = 0; j < path.length; j++) {
                var pt = points[path[j]];
                ctx.beginPath();
                ctx.arc(pt.x, pt.y, 14, 0, Math.PI * 2);
                ctx.fillStyle = '#3296ff';
                ctx.fill();
                ctx.fillStyle = '#fff';
                ctx.font = 'bold 13px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(String(j + 1), pt.x, pt.y);
            }
            lastNode = node;
        }
    };

    canvas.onmouseup = function() { drawing = false; };
    canvas.onmouseleave = function() { drawing = false; };
}



// 15. 文字找不同
function handleOddClick(e) {
    var canvas = document.getElementById('odd-canvas');
    var img = document.getElementById('odd-img');
    var canvasRect = canvas.getBoundingClientRect();
    var displayX = e.clientX - canvasRect.left;
    var imgDisplayW = img.offsetWidth || canvasRect.width;
    // 映射到图片坐标系（图片宽度360px）
    var imgX = Math.round(displayX * 360 / imgDisplayW);
    captchaState.oddOneOut.clickX = imgX;
    document.getElementById('odd-clicked').textContent = '第 ' + (Math.floor(imgX * 6 / 360) + 1) + ' 个';

    // 清除旧标记，画新标记
    document.querySelectorAll('#odd-canvas .click-mark').forEach(function(el) { el.remove(); });
    var mark = document.createElement('div');
    mark.className = 'click-mark';
    mark.style.left = displayX + 'px';
    mark.style.top = (e.clientY - canvasRect.top) + 'px';
    canvas.appendChild(mark);
}

// 16. 图形找规律
function initPatternRuleOptions(optionImgs) {
    var container = document.getElementById('pattern-rule-options');
    container.innerHTML = '';
    captchaState.patternRule.answer = null;

    optionImgs.forEach(function(imgSrc, idx) {
        var wrapper = document.createElement('div');
        wrapper.style.cssText = 'border:3px solid #ddd;border-radius:6px;cursor:pointer;overflow:hidden;padding:2px;background:#fff;';
        var img = document.createElement('img');
        img.src = imgSrc;
        img.style.cssText = 'width:100%;display:block;';
        wrapper.appendChild(img);
        wrapper.onclick = function() {
            container.querySelectorAll('div').forEach(function(b) {
                b.style.border = '3px solid #ddd';
                b.style.background = '#fff';
            });
            this.style.border = '3px solid #667eea';
            this.style.background = '#f0f2ff';
            captchaState.patternRule.answer = idx;
        };
        container.appendChild(wrapper);
    });
}

// 17. 音频验证码
function playAudio() {
    var player = document.getElementById('audio-player');
    if (player.src) {
        player.play();
    } else {
        alert('音频加载失败，请刷新重试');
    }
}

// 18. 拼图旋转
function initTileRotate(tiles) {
    var grid = document.getElementById('tile-rotate-grid');
    if (!grid) return;
    grid.innerHTML = '';
    captchaState.tileRotate.userRots = [0, 0, 0, 0];

    tiles.forEach(function(tileSrc, idx) {
        var wrapper = document.createElement('div');
        wrapper.style.cssText = 'position:relative;width:100px;height:100px;cursor:pointer;border:2px solid #ddd;border-radius:4px;overflow:hidden;';

        var img = document.createElement('img');
        img.src = tileSrc;
        img.style.cssText = 'width:100%;height:100%;display:block;transform:rotate(0deg);transition:transform 0.25s;';
        img.dataset.idx = idx;
        img.dataset.rot = '0';

        wrapper.appendChild(img);

        // 点击顺时针旋转90度
        wrapper.onclick = function() {
            var currentRot = parseInt(img.dataset.rot) || 0;
            var newRot = (currentRot + 90) % 360;
            img.dataset.rot = String(newRot);
            img.style.transform = 'rotate(' + newRot + 'deg)';
            captchaState.tileRotate.userRots[idx] = newRot;

            // 更新已修正计数（用户转到0度视为"修正"）
            var correct = captchaState.tileRotate.userRots.filter(function(r) { return r === 0; }).length;
            document.getElementById('tile-correct-count').textContent = correct;
        };

        grid.appendChild(wrapper);
    });

    document.getElementById('tile-correct-count').textContent = '0';
}

// 19. 颜色混合
function initColorOptions(options) {
    var container = document.getElementById('color-options');
    container.innerHTML = '';
    captchaState.colorMix.answer = null;

    options.forEach(function(color) {
        var btn = document.createElement('div');
        btn.style.width = '100%';
        btn.style.height = '40px';
        btn.style.borderRadius = '4px';
        btn.style.border = '2px solid #ddd';
        btn.style.cursor = 'pointer';
        btn.style.backgroundColor = 'rgb(' + color[0] + ',' + color[1] + ',' + color[2] + ')';
        btn.onclick = function() {
            container.querySelectorAll('div').forEach(function(b) {
                b.style.border = '2px solid #ddd';
            });
            this.style.border = '3px solid #e74c3c';
            captchaState.colorMix.answer = color;
        };
        container.appendChild(btn);
    });
}

// 20. 时钟验证码 - 读图输入，不需要额外JS绘制

// ────────────────────────────────────────────────────────────
// 初始化所有验证码
// ────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    // 初始化各种验证码的事件监听
    initSlider();
    initClickText();
    initRotate();
    initInvisible();

    // 延迟加载验证码，等待API就绪
    setTimeout(async () => {
        const captchaTypes = [
            'numeric', 'alphanumeric', 'distorted', 'chinese',
            'arithmetic', 'slider', 'click_text', 'rotate',
            'image_select', 'semantic', 'invisible', 'puzzle',
            // 新增验证码
            'pinyin', 'pattern_lock', 'odd_one_out', 'pattern_rule',
            'audio', 'tile_rotate', 'color_mix', 'clock'
        ];

        for (const type of captchaTypes) {
            await refreshCaptcha(type);
            // 每个间隔100ms，避免请求过快
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }, 1000); // 延迟1秒开始加载
});
