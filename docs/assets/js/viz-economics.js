/* ==========================================================================
   Geometric Economics — Interactive Visualizations
   1. GDP Collapse: 9 economic dimensions collapsed to scalar
   2. Bond Geodesic Equilibrium: Two agents, Nash vs BGE paths
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initGDPCollapse();
  initBondGeodesicEquilibrium();
});

/* ==========================================================================
   1. GDP COLLAPSE — 9 economic dimensions collapsed to a scalar
   Two economies with same GDP but different dimensional profiles.
   ========================================================================== */
function initGDPCollapse() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const toc = section.querySelector('.toc-grid');
  if (!toc) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.innerHTML =
    '<h3 class="demo-title">GDP Scalar Collapse</h3>' +
    '<p class="demo-subtitle">Two economies with the same GDP. Drag the slider to collapse 9 dimensions into one number.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="econ-tensor-canvas" width="520" height="300"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<label class="demo-slider-label">' +
        '<span>Collapse</span>' +
        '<input type="range" min="0" max="100" value="0" class="demo-slider" id="gdp-collapse-slider">' +
        '<span class="demo-val" id="gdp-collapse-val">Tensor</span>' +
      '</label>' +
    '</div>';

  toc.parentNode.insertBefore(demo, toc.nextSibling);

  const canvas = document.getElementById('econ-tensor-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const dimNames = ['Output', 'Employ', 'Equity', 'Health', 'Educ', 'Environ', 'Innov', 'Infra', 'Govern'];
  const dimColors = ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#8da0cb', '#66c2a5'];

  // Two economies with same average but different profiles
  const econA = [0.90, 0.40, 0.30, 0.85, 0.70, 0.25, 0.80, 0.55, 0.65]; // avg ~0.60
  const econB = [0.55, 0.65, 0.70, 0.50, 0.60, 0.75, 0.45, 0.70, 0.50]; // avg ~0.60

  function draw(collapse) {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const t = collapse / 100;
    const barW = 20;
    const gap = 6;
    const maxH = 200;
    const baseY = h - 50;
    const groupW = dimNames.length * (barW + gap);
    const offsetA = (w / 2 - groupW) / 2;
    const offsetB = w / 2 + (w / 2 - groupW) / 2;

    const avgA = econA.reduce((a, b) => a + b, 0) / econA.length;
    const avgB = econB.reduce((a, b) => a + b, 0) / econB.length;

    // Labels
    ctx.fillStyle = '#e8ecf0';
    ctx.font = '600 14px "Crimson Pro", serif';
    ctx.textAlign = 'center';
    ctx.fillText('Economy A', w / 4, 22);
    ctx.fillText('Economy B', 3 * w / 4, 22);

    for (let i = 0; i < dimNames.length; i++) {
      // Economy A
      const vA = econA[i] * (1 - t) + avgA * t;
      const bHA = vA * maxH;
      const xA = offsetA + i * (barW + gap);
      ctx.fillStyle = (t < 1) ? dimColors[i] + '33' : 'transparent';
      ctx.fillRect(xA, baseY - maxH, barW, maxH);
      ctx.fillStyle = (t < 0.95) ? dimColors[i] : '#8899aa';
      ctx.fillRect(xA, baseY - bHA, barW, bHA);

      // Economy B
      const vB = econB[i] * (1 - t) + avgB * t;
      const bHB = vB * maxH;
      const xB = offsetB + i * (barW + gap);
      ctx.fillStyle = (t < 1) ? dimColors[i] + '33' : 'transparent';
      ctx.fillRect(xB, baseY - maxH, barW, maxH);
      ctx.fillStyle = (t < 0.95) ? dimColors[i] : '#8899aa';
      ctx.fillRect(xB, baseY - bHB, barW, bHB);

      // Dim labels (fade out as collapse increases)
      if (t < 0.8) {
        ctx.fillStyle = `rgba(143,164,184,${1 - t})`;
        ctx.font = '9px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(dimNames[i], xA + barW / 2, baseY + 14);
        ctx.fillText(dimNames[i], xB + barW / 2, baseY + 14);
      }
    }

    // GDP scalar values
    ctx.fillStyle = t > 0.5 ? '#e8ecf0' : '#5c7a94';
    ctx.font = '600 16px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('GDP: ' + avgA.toFixed(2), w / 4, baseY + 34);
    ctx.fillText('GDP: ' + avgB.toFixed(2), 3 * w / 4, baseY + 34);

    if (t > 0.8) {
      ctx.fillStyle = '#d95f02';
      ctx.font = '12px Inter, sans-serif';
      ctx.fillText('Same GDP. Different economies.', w / 2, baseY + 54);
      ctx.fillText('Which dimensions? Unknown.', w / 2, baseY + 70);
    }

    // Divider
    ctx.strokeStyle = 'rgba(102,194,165,0.2)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(w / 2, 10);
    ctx.lineTo(w / 2, h - 10);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  draw(0);

  document.getElementById('gdp-collapse-slider').addEventListener('input', function() {
    const v = parseInt(this.value);
    document.getElementById('gdp-collapse-val').textContent = v < 30 ? 'Tensor' : v < 70 ? 'Collapsing...' : 'Scalar';
    draw(v);
  });
}

/* ==========================================================================
   2. BOND GEODESIC EQUILIBRIUM — Two agents find paths on a grid
   Nash equilibrium (selfish) vs BGE (tensor-aware, boundary-respecting).
   ========================================================================== */
function initBondGeodesicEquilibrium() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const prev = section.querySelectorAll('.scalar-tensor-demo');
  const anchor = prev[prev.length - 1];
  if (!anchor) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.style.marginTop = '32px';
  demo.innerHTML =
    '<h3 class="demo-title">Nash Equilibrium vs Bond Geodesic Equilibrium</h3>' +
    '<p class="demo-subtitle">Two agents navigate a shared space. Nash: each optimizes selfishly. BGE: paths respect boundaries and other agents.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="bge-canvas" width="520" height="320"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">' +
        '<button class="btn btn-secondary" id="bge-nash-btn">Show Nash Paths</button>' +
        '<button class="btn btn-secondary" id="bge-bge-btn">Show BGE Paths</button>' +
        '<button class="btn btn-secondary" id="bge-reset-btn">Reset</button>' +
      '</div>' +
      '<div style="display:flex;gap:24px;justify-content:center;margin-top:8px;font-size:12px;color:var(--text-secondary)">' +
        '<span style="color:#1b9e77">Agent A (teal)</span>' +
        '<span style="color:#d95f02">Agent B (orange)</span>' +
        '<span style="color:#7570b3">Boundary zone (purple)</span>' +
      '</div>' +
    '</div>';

  anchor.parentNode.insertBefore(demo, anchor.nextSibling);

  const canvas = document.getElementById('bge-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const cols = 20, rows = 16;
  const cellW = canvas.width / cols;
  const cellH = canvas.height / rows;

  const agentA = { sx: 1, sy: 1, gx: 18, gy: 14, color: '#1b9e77' };
  const agentB = { sx: 18, sy: 1, gx: 1, gy: 14, color: '#d95f02' };

  // Boundary zone in the middle
  const boundaries = [];
  for (let y = 4; y <= 11; y++) {
    for (let x = 8; x <= 11; x++) {
      boundaries.push({ x, y });
    }
  }
  const bSet = new Set(boundaries.map(b => `${b.x},${b.y}`));

  let pathA = [];
  let pathB = [];
  let mode = 'none';

  function drawBGEGrid() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        ctx.fillStyle = bSet.has(`${x},${y}`) ? 'rgba(117,112,179,0.15)' : 'rgba(20,37,54,0.4)';
        ctx.fillRect(x * cellW + 1, y * cellH + 1, cellW - 2, cellH - 2);
      }
    }

    // Draw boundary label
    if (bSet.size > 0) {
      ctx.fillStyle = 'rgba(117,112,179,0.5)';
      ctx.font = '11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Moral Boundary', 9.5 * cellW, 3.3 * cellH);
    }

    // Draw paths
    function drawPath(path, color, offset) {
      if (path.length < 2) return;
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.lineJoin = 'round';
      ctx.beginPath();
      ctx.moveTo(path[0].x * cellW + cellW / 2 + offset, path[0].y * cellH + cellH / 2);
      for (let i = 1; i < path.length; i++) {
        ctx.lineTo(path[i].x * cellW + cellW / 2 + offset, path[i].y * cellH + cellH / 2);
      }
      ctx.stroke();
    }

    drawPath(pathA, 'rgba(27,158,119,0.8)', -2);
    drawPath(pathB, 'rgba(217,95,2,0.8)', 2);

    // Agent markers
    [agentA, agentB].forEach(agent => {
      // Start
      ctx.fillStyle = agent.color;
      ctx.beginPath();
      ctx.arc(agent.sx * cellW + cellW / 2, agent.sy * cellH + cellH / 2, 6, 0, Math.PI * 2);
      ctx.fill();
      // Goal
      ctx.strokeStyle = agent.color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(agent.gx * cellW + cellW / 2, agent.gy * cellH + cellH / 2, 6, 0, Math.PI * 2);
      ctx.stroke();
    });
  }

  function findPath(sx, sy, gx, gy, avoidBoundary) {
    const path = [];
    let x = sx, y = sy;
    path.push({ x, y });
    const maxSteps = 200;
    let steps = 0;
    while ((x !== gx || y !== gy) && steps < maxSteps) {
      steps++;
      const candidates = [];
      const dirs = [[0,1],[0,-1],[1,0],[-1,0]];
      for (const [dx, dy] of dirs) {
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || nx >= cols || ny < 0 || ny >= rows) continue;
        const dist = Math.abs(nx - gx) + Math.abs(ny - gy);
        let penalty = 0;
        if (avoidBoundary && bSet.has(`${nx},${ny}`)) penalty = 20;
        candidates.push({ x: nx, y: ny, score: dist + penalty });
      }
      candidates.sort((a, b) => a.score - b.score);
      if (candidates.length === 0) break;
      x = candidates[0].x;
      y = candidates[0].y;
      path.push({ x, y });
    }
    return path;
  }

  drawBGEGrid();

  document.getElementById('bge-nash-btn').addEventListener('click', () => {
    mode = 'nash';
    // Nash: agents cut through boundary (selfish, scalar-optimizing)
    pathA = findPath(agentA.sx, agentA.sy, agentA.gx, agentA.gy, false);
    pathB = findPath(agentB.sx, agentB.sy, agentB.gx, agentB.gy, false);
    drawBGEGrid();
    // Draw conflict indicator
    ctx.fillStyle = '#d95f02';
    ctx.font = '12px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Nash: Paths cross boundary. Conflicts at intersection.', canvas.width / 2, canvas.height - 8);
  });

  document.getElementById('bge-bge-btn').addEventListener('click', () => {
    mode = 'bge';
    // BGE: agents respect boundary strata
    pathA = findPath(agentA.sx, agentA.sy, agentA.gx, agentA.gy, true);
    pathB = findPath(agentB.sx, agentB.sy, agentB.gx, agentB.gy, true);
    drawBGEGrid();
    ctx.fillStyle = '#1b9e77';
    ctx.font = '12px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('BGE: Paths respect boundary. No moral violations.', canvas.width / 2, canvas.height - 8);
  });

  document.getElementById('bge-reset-btn').addEventListener('click', () => {
    pathA = [];
    pathB = [];
    mode = 'none';
    drawBGEGrid();
  });
}
