import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="길건너 친구들",
    page_icon="🐤",
    layout="centered",
)

st.markdown(
    """
    <style>
        .block-container {padding-top: 2rem; padding-bottom: 1rem; max-width: 480px;}
        header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🐤 길건너 친구들")
st.caption("도로와 강을 건너 최대한 멀리 가보세요! 방향키 / WASD / 아래 버튼으로 조작합니다.")

# ---------------------------------------------------------------------------
# 이미지 에셋 로드 (assets/ 폴더의 이미지를 base64 데이터 URI로 변환)
# 나중에 자신만의 이미지로 바꾸고 싶다면 assets/ 폴더의 같은 파일명을
# 자신의 이미지(svg, png, jpg 등)로 덮어쓰고 아래 EXT/MIME만 맞춰주면 됩니다.
# ---------------------------------------------------------------------------
ASSETS_DIR = Path(__file__).parent / "assets"

MIME_TYPES = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def load_data_uri(filename: str) -> str:
    """assets 폴더에서 이미지를 읽어 base64 데이터 URI로 변환합니다."""
    path = ASSETS_DIR / filename
    ext = path.suffix.lower()
    mime = MIME_TYPES.get(ext, "image/svg+xml")
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


PLAYER_IMG = load_data_uri("player.svg")
CAR_RED_IMG = load_data_uri("car_red.svg")
CAR_BLUE_IMG = load_data_uri("car_blue.svg")
LOG_IMG = load_data_uri("log_tile.svg")

GAME_JS = r"""
(function () {
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');

  const TILE = 40;
  const COLS = 9;
  const VIEW_ROWS = 15;
  const W = TILE * COLS;
  const H = TILE * VIEW_ROWS;
  canvas.width = W;
  canvas.height = H;

  const COLORS = {
    grass: ['#8bc34a', '#7cb342'],
    road: '#4a4a4a',
    water: '#4fc3f7',
  };

  // ---- 이미지 로드 ----
  const ASSET_SRC = window.ASSET_SRC || {};
  const images = {};
  function loadImage(key, src) {
    const img = new Image();
    img.src = src;
    images[key] = img;
  }
  loadImage('player', ASSET_SRC.player);
  loadImage('car1', ASSET_SRC.car1);
  loadImage('car2', ASSET_SRC.car2);
  loadImage('log', ASSET_SRC.log);

  function imgReady(key) {
    const img = images[key];
    return !!img && img.complete && img.naturalWidth > 0;
  }

  let lanes = {};
  let player, cameraRow, score, best, running;

  function loadBest() {
    try {
      return parseInt(localStorage.getItem('crossy_best') || '0', 10);
    } catch (e) {
      return 0;
    }
  }
  function saveBest(v) {
    try { localStorage.setItem('crossy_best', String(v)); } catch (e) {}
  }

  function makeLane(row) {
    if (row <= 0) {
      lanes[row] = { type: 'grass', obstacles: [], speed: 0 };
      return;
    }
    let type;
    const r = Math.random();
    if (row % 5 === 0) {
      type = 'grass';
    } else if (r < 0.45) {
      type = 'road';
    } else if (r < 0.75) {
      type = 'water';
    } else {
      type = 'grass';
    }

    const lane = { type, obstacles: [], speed: 0 };
    if (type === 'road') {
      const dir = Math.random() < 0.5 ? 1 : -1;
      const speed = (0.6 + Math.random() * 1.0) * dir;
      lane.speed = speed;
      const gap = 3 + Math.floor(Math.random() * 2);
      const carLen = 1;
      const carType = Math.random() < 0.5 ? 'car1' : 'car2';
      let x = Math.random() * COLS;
      for (let i = 0; i < COLS; i += gap) {
        lanesPushObstacle(lane, (x + i) % COLS, carLen, carType);
      }
    } else if (type === 'water') {
      const dir = Math.random() < 0.5 ? 1 : -1;
      const speed = (0.5 + Math.random() * 0.8) * dir;
      lane.speed = speed;
      const gap = 3 + Math.floor(Math.random() * 2);
      const logLen = 2 + Math.floor(Math.random() * 2);
      let x = Math.random() * COLS;
      for (let i = 0; i < COLS; i += gap) {
        lanesPushObstacle(lane, (x + i) % COLS, logLen, 'log');
      }
    }
    lanes[row] = lane;
  }

  function lanesPushObstacle(lane, x, len, kind) {
    lane.obstacles.push({ x: x, len: len, kind: kind });
  }

  function ensureLanes(upTo) {
    for (let r = 0; r <= upTo; r++) {
      if (!lanes[r]) makeLane(r);
    }
  }

  // ---- 부드러운 연속 이동 ----
  // 키를 누를 때마다 한 칸씩 순간이동하지 않고, 누르고 있는 동안 자연스럽게 이동합니다.
  const MOVE_SPEED = 5.2;
  const keys = { up: false, down: false, left: false, right: false };

  function resetGame() {
    lanes = {};
    player = { row: 0, x: Math.floor(COLS / 2), offsetX: 0 };
    cameraRow = 0;
    score = 0;
    best = loadBest();
    running = true;
    keys.up = keys.down = keys.left = keys.right = false;
    ensureLanes(20);
  }

  function keyToDir(key) {
    switch (key) {
      case 'ArrowUp': case 'w': case 'W': return 'up';
      case 'ArrowDown': case 's': case 'S': return 'down';
      case 'ArrowLeft': case 'a': case 'A': return 'left';
      case 'ArrowRight': case 'd': case 'D': return 'right';
      default: return null;
    }
  }

  function setKey(dir, pressed) {
    if (dir) keys[dir] = pressed;
  }

  // ---- 가상 조이스틱 ----
  const joystick = {
    active: false,
    pointerId: null,
    cx: 0,
    cy: 0,
    x: 0,
    y: 0,
    maxRadius: 42
  };

  function setJoystickVisual(x, y) {
    const knob = document.getElementById('joystick-knob');
    if (knob) knob.style.transform = `translate(${x}px, ${y}px)`;
  }

  function updateJoystick(clientX, clientY) {
    let dx = clientX - joystick.cx;
    let dy = clientY - joystick.cy;
    const dist = Math.hypot(dx, dy);

    if (dist > joystick.maxRadius) {
      dx = dx / dist * joystick.maxRadius;
      dy = dy / dist * joystick.maxRadius;
    }

    joystick.x = dx / joystick.maxRadius;
    joystick.y = dy / joystick.maxRadius;
    setJoystickVisual(dx, dy);
  }

  function startJoystick(e) {
    if (!running) {
      resetGame();
      return;
    }
    e.preventDefault();

    joystick.active = true;
    joystick.pointerId = e.pointerId;

    const rect = e.currentTarget.getBoundingClientRect();
    joystick.cx = rect.left + rect.width / 2;
    joystick.cy = rect.top + rect.height / 2;

    updateJoystick(e.clientX, e.clientY);
    e.currentTarget.setPointerCapture(e.pointerId);
  }

  function moveJoystick(e) {
    if (!joystick.active || e.pointerId !== joystick.pointerId) return;
    e.preventDefault();
    updateJoystick(e.clientX, e.clientY);
  }

  function endJoystick(e) {
    if (e.pointerId !== joystick.pointerId) return;

    joystick.active = false;
    joystick.pointerId = null;
    joystick.x = 0;
    joystick.y = 0;
    setJoystickVisual(0, 0);
  }

  function setupJoystick() {
    const base = document.getElementById('joystick-base');
    if (!base) return;

    base.addEventListener('pointerdown', startJoystick);
    base.addEventListener('pointermove', moveJoystick);
    base.addEventListener('pointerup', endJoystick);
    base.addEventListener('pointercancel', endJoystick);
  }

  const MOVE_SPEED = 4.8;

  window.crossyRestart = function () { resetGame(); };


  let lastTime = null;
  function update(dt) {
    if (!running) return;

    // 방향키 입력에 따라 실수 좌표로 직접 이동해 부드럽게 움직입니다.
    let dx = 0;
    let dy = 0;
    if (keys.left) dx -= 1;
    if (keys.right) dx += 1;
    if (keys.up) dy += 1;
    if (keys.down) dy -= 1;

    // 대각선 이동이 더 빨라지지 않도록 보정합니다.
    if (dx !== 0 && dy !== 0) {
      const inv = 1 / Math.sqrt(2);
      dx *= inv;
      dy *= inv;
    }

    player.x += dx * MOVE_SPEED * dt;
    player.row += dy * MOVE_SPEED * dt;

    player.x = Math.max(0, Math.min(COLS - 1, player.x));
    player.row = Math.max(0, player.row);

    ensureLanes(Math.ceil(player.row) + VIEW_ROWS + 2);
    // 조이스틱을 기울인 방향으로 캐릭터가 부드럽게 연속 이동
    if (joystick.active) {
      const magnitude = Math.hypot(joystick.x, joystick.y);

      if (magnitude > 0.12) {
        player.x += joystick.x * MOVE_SPEED * dt;
        player.row += (-joystick.y) * MOVE_SPEED * dt;

        player.x = Math.max(0, Math.min(COLS - 1, player.x));
        player.row = Math.max(0, player.row);

        const scoreRow = Math.floor(player.row);
        ensureLanes(scoreRow + 15);
        if (scoreRow > score) score = scoreRow;
      }
    }


    const currentScore = Math.floor(player.row);
    if (currentScore > score) score = currentScore;

    const targetCamera = Math.max(player.row - 4, 0);
    cameraRow += (targetCamera - cameraRow) * Math.min(1, dt * 6);

    for (const key in lanes) {
      const lane = lanes[key];
      if (lane.speed === 0) continue;
      for (const ob of lane.obstacles) {
        ob.x += lane.speed * dt;
        if (ob.x > COLS + 2) ob.x -= (COLS + 4);
        if (ob.x < -4) ob.x += (COLS + 4);
      }
    }

    const lane = lanes[Math.floor(player.row)];
    if (lane && lane.type === 'water') {
      player.offsetX += lane.speed * dt;
      const effectiveX = player.x + player.offsetX;
      if (effectiveX < -0.3 || effectiveX > COLS - 0.7) {
        die();
        return;
      }
      let onLog = false;
      for (const ob of lane.obstacles) {
        if (effectiveX + 0.5 > ob.x && effectiveX + 0.5 < ob.x + ob.len) {
          onLog = true;
          break;
        }
      }
      if (!onLog) { die(); return; }
    }

    if (lane && lane.type === 'road') {
      const px = player.x + player.offsetX;
      for (const ob of lane.obstacles) {
        if (px + 0.5 > ob.x && px + 0.5 < ob.x + ob.len) {
          die();
          return;
        }
      }
    }
  }

  function die() {
    running = false;
    if (score > best) { best = score; saveBest(best); }
  }

  function drawCar(ob, y, faceRight) {
    const w = ob.len * TILE;
    const h = TILE - 8;
    const x = ob.x * TILE;
    const oy = y + 4;
    if (imgReady(ob.kind)) {
      const img = images[ob.kind];
      ctx.save();
      if (!faceRight) {
        ctx.translate(x + w, oy);
        ctx.scale(-1, 1);
        ctx.drawImage(img, 0, 0, w, h);
      } else {
        ctx.drawImage(img, x, oy, w, h);
      }
      ctx.restore();
    } else {
      ctx.fillStyle = '#e53935';
      ctx.fillRect(x + 2, oy, w - 4, h);
    }
  }

  function drawLog(ob, y) {
    const w = ob.len * TILE;
    const h = TILE - 14;
    const x = ob.x * TILE;
    const oy = y + 7;
    if (imgReady('log')) {
      ctx.drawImage(images.log, x, oy, w, h);
    } else {
      ctx.fillStyle = '#8d6e63';
      ctx.fillRect(x + 1, oy, w - 2, h);
    }
  }

  function drawPlayerSprite(px, py) {
    const size = TILE * 0.95;
    if (imgReady('player')) {
      ctx.drawImage(images.player, px - size / 2, py - size / 2, size, size);
    } else {
      ctx.font = `${TILE * 0.8}px serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('🐤', px, py + 2);
    }
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    const camInt = cameraRow;
    for (let sr = 0; sr < VIEW_ROWS; sr++) {
      const row = Math.floor(camInt) + (VIEW_ROWS - 1 - sr);
      const frac = camInt - Math.floor(camInt);
      drawLaneAt(row, sr + frac);
    }

    const playerScreenRow = (VIEW_ROWS - 1) - (player.row - camInt);
    const px = (player.x + player.offsetX) * TILE + TILE / 2;
    const py = playerScreenRow * TILE + TILE / 2;
    drawPlayerSprite(px, py);

    ctx.textAlign = 'left';
    ctx.font = 'bold 18px sans-serif';
    ctx.fillStyle = '#222';
    ctx.fillText(`점수: ${score}`, 10, 24);
    ctx.fillText(`최고: ${best}`, 10, 46);

    if (!running) {
      ctx.fillStyle = 'rgba(0,0,0,0.55)';
      ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#fff';
      ctx.textAlign = 'center';
      ctx.font = 'bold 26px sans-serif';
      ctx.fillText('게임 오버', W / 2, H / 2 - 20);
      ctx.font = '16px sans-serif';
      ctx.fillText(`점수 ${score} / 최고 ${best}`, W / 2, H / 2 + 10);
      ctx.fillText('스페이스바 또는 재시작 버튼', W / 2, H / 2 + 36);
    }
  }

  function drawLaneAt(row, screenRowFloat) {
    const lane = lanes[row];
    const y = screenRowFloat * TILE;
    if (!lane) return;
    if (lane.type === 'grass' || !lane.type) {
      ctx.fillStyle = row % 2 === 0 ? COLORS.grass[0] : COLORS.grass[1];
      ctx.fillRect(0, y, W, TILE + 1);
      return;
    }
    if (lane.type === 'road') {
      ctx.fillStyle = COLORS.road;
      ctx.fillRect(0, y, W, TILE + 1);
      const faceRight = lane.speed > 0;
      for (const ob of lane.obstacles) {
        drawCar(ob, y, faceRight);
      }
    } else if (lane.type === 'water') {
      ctx.fillStyle = COLORS.water;
      ctx.fillRect(0, y, W, TILE + 1);
      for (const ob of lane.obstacles) {
        drawLog(ob, y);
      }
    }
  }

  function loop(t) {
    if (lastTime === null) lastTime = t;
    const dt = Math.min((t - lastTime) / 1000, 0.05);
    lastTime = t;
    update(dt);
    draw();
    requestAnimationFrame(loop);
  }

  resetGame();
  requestAnimationFrame(loop);
})();
"""

GAME_HTML = f"""
<div style="display:flex; flex-direction:column; align-items:center; font-family: sans-serif;">
  <canvas id="game" style="border-radius:12px; box-shadow:0 4px 14px rgba(0,0,0,0.25); touch-action:none;"></canvas>

  <div id="joystick-base" style="
      width:112px;
      height:112px;
      margin-top:14px;
      border-radius:50%;
      background:#37474f;
      box-shadow:inset 0 0 0 5px rgba(255,255,255,0.12), 0 4px 10px rgba(0,0,0,0.2);
      position:relative;
      touch-action:none;
      user-select:none;">
    <div id="joystick-knob" style="
        width:54px;
        height:54px;
        border-radius:50%;
        background:#78909c;
        box-shadow:0 3px 8px rgba(0,0,0,0.35);
        position:absolute;
        left:29px;
        top:29px;
        transition:transform 0.04s linear;
        pointer-events:none;"></div>
  </div>

  <button onclick="crossyRestart()" style="margin-top:14px; padding:8px 20px; border-radius:8px; border:none; background:#ff7043; color:white; font-weight:bold; font-size:14px; cursor:pointer;">
    🔄 다시 시작
  </button>
</div>

<style>
  .ctrl-btn {{
    font-size: 20px;
    border-radius: 10px;
    border: none;
    background: #37474f;
    color: white;
    cursor: pointer;
  }}
  .ctrl-btn:active {{
    background: #263238;
  }}
</style>

<script>
  window.ASSET_SRC = {{
    player: "{PLAYER_IMG}",
    car1: "{CAR_RED_IMG}",
    car2: "{CAR_BLUE_IMG}",
    log: "{LOG_IMG}"
  }};
</script>
<script>
{GAME_JS}
</script>
"""

components.html(GAME_HTML, height=780, scrolling=False)

st.markdown(
    """
    ---
    **조작 방법**
    - 조이스틱: 원하는 방향으로 기울여 부드럽게 이동
    - 모바일/PC 모두 터치 또는 마우스로 조작
    - 도로(회색)에서는 자동차를 피하고, 강(파란색)에서는 통나무를 밟고 이동하세요.
    - 최고 점수는 브라우저에 자동 저장됩니다.

    **이미지 교체하기**: `assets/` 폴더의 `player.svg`, `car_red.svg`, `car_blue.svg`, `log_tile.svg` 파일을
    원하는 이미지(같은 파일명, 또는 png/jpg 등)로 바꾸면 캐릭터·자동차·통나무 그림이 바로 바뀝니다.
    """
)