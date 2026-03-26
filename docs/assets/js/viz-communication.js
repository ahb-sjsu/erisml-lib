/* ==========================================================================
   Geometric Communication — Interactive Visualizations
   1. Rosetta Trajectory: Animated signal path through communication stations
   2. Poincare Disk: Interactive hyperbolic geometry visualization
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initRosettaTrajectory();
  initPoincareDisc();
});

/* ==========================================================================
   1. ROSETTA TRAJECTORY — Signal travels from whale clicks to moral language
   Each station lights up as the signal traverses the geometric pipeline.
   ========================================================================== */
function initRosettaTrajectory() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const toc = section.querySelector('.toc-grid');
  if (!toc) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.innerHTML =
    '<h3 class="demo-title">The Rosetta Trajectory</h3>' +
    '<p class="demo-subtitle">Watch the geometric signal travel from whale clicks through birdsong, cuneiform, and into moral language.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="rosetta-canvas" width="520" height="300"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">' +
        '<button class="btn btn-secondary" id="rosetta-play">Play Trajectory</button>' +
        '<button class="btn btn-secondary" id="rosetta-reset">Reset</button>' +
      '</div>' +
      '<div style="text-align:center;margin-top:8px;font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--text-secondary)">' +
        'Stage: <span id="rosetta-stage" style="color:#1b9e77">Ready</span>' +
      '</div>' +
    '</div>';

  toc.parentNode.insertBefore(demo, toc.nextSibling);

  const canvas = document.getElementById('rosetta-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const stations = [
    { x: 60,  y: 150, name: 'Whale Clicks', icon: '\u{1F433}', color: '#1b9e77', desc: 'Codas & hierarchical structure' },
    { x: 180, y: 90,  name: 'Birdsong',     icon: '\u{1F426}', color: '#d95f02', desc: 'Recursive syntax in song' },
    { x: 300, y: 150, name: 'Cuneiform',    icon: '\u{1F4DC}', color: '#7570b3', desc: 'First written symbols' },
    { x: 420, y: 90,  name: 'Human Lang.',   icon: '\u{1F4AC}', color: '#e6ab02', desc: 'Natural language' },
    { x: 460, y: 210, name: 'Moral Lang.',   icon: '\u{2696}',  color: '#e7298a', desc: 'Deontic structure preserved' },
  ];

  let activeStation = -1;
  let signalPos = { x: stations[0].x, y: stations[0].y };
  let animating = false;
  let trailPoints = [];

  function draw() {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Draw connecting path
    ctx.strokeStyle = 'rgba(102,194,165,0.2)';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(stations[0].x, stations[0].y);
    for (let i = 1; i < stations.length; i++) {
      const prev = stations[i - 1];
      const curr = stations[i];
      const cpx = (prev.x + curr.x) / 2;
      const cpy = Math.min(prev.y, curr.y) - 30;
      ctx.quadraticCurveTo(cpx, cpy, curr.x, curr.y);
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw trail
    if (trailPoints.length > 1) {
      ctx.strokeStyle = 'rgba(27,158,119,0.4)';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(trailPoints[0].x, trailPoints[0].y);
      for (let i = 1; i < trailPoints.length; i++) {
        ctx.lineTo(trailPoints[i].x, trailPoints[i].y);
      }
      ctx.stroke();
    }

    // Draw stations
    for (let i = 0; i < stations.length; i++) {
      const s = stations[i];
      const isActive = i <= activeStation;
      const isCurrent = i === activeStation;

      // Station circle
      ctx.beginPath();
      ctx.arc(s.x, s.y, isCurrent ? 28 : 22, 0, Math.PI * 2);
      ctx.fillStyle = isActive ? s.color + '30' : 'rgba(20,37,54,0.6)';
      ctx.fill();
      ctx.strokeStyle = isActive ? s.color : 'rgba(102,194,165,0.2)';
      ctx.lineWidth = isCurrent ? 3 : 1.5;
      ctx.stroke();

      // Icon
      ctx.font = isCurrent ? '22px serif' : '18px serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(s.icon, s.x, s.y);

      // Name
      ctx.fillStyle = isActive ? s.color : '#5c7a94';
      ctx.font = (isCurrent ? '600 ' : '') + '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(s.name, s.x, s.y + 38);

      // Description (only for active)
      if (isCurrent) {
        ctx.fillStyle = '#8fa4b8';
        ctx.font = '10px Inter, sans-serif';
        ctx.fillText(s.desc, s.x, s.y + 52);
      }
    }

    // Signal dot
    if (animating) {
      ctx.beginPath();
      ctx.arc(signalPos.x, signalPos.y, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#1b9e77';
      ctx.fill();
      ctx.beginPath();
      ctx.arc(signalPos.x, signalPos.y, 12, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(27,158,119,0.3)';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Invariant label
    ctx.fillStyle = '#5c7a94';
    ctx.font = '11px "Crimson Pro", serif';
    ctx.textAlign = 'center';
    ctx.fillText('Geometric structure is preserved across all communication systems', w / 2, h - 15);
  }

  function animateTrajectory() {
    if (animating) return;
    animating = true;
    activeStation = -1;
    trailPoints = [];
    let currentSegment = 0;
    let segProgress = 0;

    function step() {
      if (currentSegment >= stations.length - 1) {
        activeStation = stations.length - 1;
        animating = false;
        draw();
        document.getElementById('rosetta-stage').textContent = 'Complete: Structure preserved!';
        document.getElementById('rosetta-stage').style.color = '#e7298a';
        return;
      }

      segProgress += 0.02;
      if (segProgress >= 1) {
        segProgress = 0;
        currentSegment++;
        activeStation = currentSegment;
        const s = stations[activeStation];
        document.getElementById('rosetta-stage').textContent = s.name;
        document.getElementById('rosetta-stage').style.color = s.color;
      }

      if (currentSegment < stations.length - 1) {
        activeStation = currentSegment;
        const from = stations[currentSegment];
        const to = stations[currentSegment + 1];
        const t = segProgress;
        // Quadratic bezier interpolation
        const cpx = (from.x + to.x) / 2;
        const cpy = Math.min(from.y, to.y) - 30;
        signalPos.x = (1 - t) * (1 - t) * from.x + 2 * (1 - t) * t * cpx + t * t * to.x;
        signalPos.y = (1 - t) * (1 - t) * from.y + 2 * (1 - t) * t * cpy + t * t * to.y;
        trailPoints.push({ x: signalPos.x, y: signalPos.y });
      }

      draw();
      requestAnimationFrame(step);
    }

    activeStation = 0;
    document.getElementById('rosetta-stage').textContent = stations[0].name;
    document.getElementById('rosetta-stage').style.color = stations[0].color;
    requestAnimationFrame(step);
  }

  draw();

  document.getElementById('rosetta-play').addEventListener('click', () => {
    activeStation = -1;
    trailPoints = [];
    animateTrajectory();
  });

  document.getElementById('rosetta-reset').addEventListener('click', () => {
    animating = false;
    activeStation = -1;
    trailPoints = [];
    signalPos = { x: stations[0].x, y: stations[0].y };
    document.getElementById('rosetta-stage').textContent = 'Ready';
    document.getElementById('rosetta-stage').style.color = '#1b9e77';
    draw();
  });
}

/* ==========================================================================
   2. POINCARE DISK — Interactive hyperbolic geometry
   Drag points to see hyperbolic distance vs Euclidean distance.
   ========================================================================== */
function initPoincareDisc() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const prev = section.querySelectorAll('.scalar-tensor-demo');
  const anchor = prev[prev.length - 1];
  if (!anchor) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.style.marginTop = '32px';
  demo.innerHTML =
    '<h3 class="demo-title">The Poincar\u00E9 Disk Model</h3>' +
    '<p class="demo-subtitle">Drag the orange point. Near the boundary, small Euclidean moves become huge hyperbolic distances. Hierarchy embeds naturally.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="poincare-canvas" width="420" height="420"></canvas>' +
    '</div>' +
    '<div style="text-align:center;font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--text-secondary);margin-top:8px">' +
      'Euclidean dist: <span id="poinc-euclid" style="color:#1b9e77">0.00</span> &mdash; ' +
      'Hyperbolic dist: <span id="poinc-hyper" style="color:#d95f02">0.00</span> &mdash; ' +
      'Ratio: <span id="poinc-ratio" style="color:#7570b3">1.0x</span>' +
    '</div>';

  anchor.parentNode.insertBefore(demo, anchor.nextSibling);

  const canvas = document.getElementById('poincare-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const cx = 210, cy = 210, diskR = 180;
  let pointA = { x: 0, y: 0 };     // Center (fixed)
  let pointB = { x: 0.3, y: 0.2 }; // Draggable (in disk coordinates -1..1)
  let dragging = false;

  // Hierarchy nodes for tree visualization
  const treeNodes = [
    { x: 0, y: 0, label: 'Root', depth: 0 },
    { x: -0.3, y: 0.35, label: '', depth: 1 },
    { x: 0.3, y: 0.35, label: '', depth: 1 },
    { x: -0.5, y: 0.6, label: '', depth: 2 },
    { x: -0.15, y: 0.6, label: '', depth: 2 },
    { x: 0.15, y: 0.6, label: '', depth: 2 },
    { x: 0.5, y: 0.6, label: '', depth: 2 },
    { x: -0.6, y: 0.78, label: '', depth: 3 },
    { x: -0.4, y: 0.78, label: '', depth: 3 },
    { x: 0.4, y: 0.78, label: '', depth: 3 },
    { x: 0.6, y: 0.78, label: '', depth: 3 },
  ];
  const treeEdges = [[0,1],[0,2],[1,3],[1,4],[2,5],[2,6],[3,7],[3,8],[6,9],[6,10]];

  function diskToCanvas(px, py) {
    return { x: cx + px * diskR, y: cy + py * diskR };
  }

  function canvasToDisk(mx, my) {
    return { x: (mx - cx) / diskR, y: (my - cy) / diskR };
  }

  function hyperbolicDist(ax, ay, bx, by) {
    const dx = bx - ax, dy = by - ay;
    const eucSq = dx * dx + dy * dy;
    const denom = (1 - ax * ax - ay * ay) * (1 - bx * bx - by * by);
    if (denom <= 0) return Infinity;
    const arg = 1 + 2 * eucSq / denom;
    return Math.acosh(Math.max(1, arg));
  }

  function draw() {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Disk boundary
    ctx.beginPath();
    ctx.arc(cx, cy, diskR, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(20,37,54,0.6)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(102,194,165,0.4)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Concentric hyperbolic circles (equal hyperbolic spacing)
    for (let r = 0.2; r < 1; r += 0.2) {
      ctx.beginPath();
      ctx.arc(cx, cy, r * diskR, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(102,194,165,0.08)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Draw tree edges
    ctx.strokeStyle = 'rgba(117,112,179,0.3)';
    ctx.lineWidth = 1.5;
    for (const [i, j] of treeEdges) {
      const a = diskToCanvas(treeNodes[i].x, treeNodes[i].y);
      const b = diskToCanvas(treeNodes[j].x, treeNodes[j].y);
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }

    // Draw tree nodes
    for (const node of treeNodes) {
      const p = diskToCanvas(node.x, node.y);
      const size = Math.max(2, 6 - node.depth * 1.2);
      ctx.beginPath();
      ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
      ctx.fillStyle = node.depth === 0 ? '#7570b3' : 'rgba(117,112,179,0.5)';
      ctx.fill();
      if (node.label) {
        ctx.fillStyle = '#8fa4b8';
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(node.label, p.x, p.y - 10);
      }
    }

    // Line between points
    const pA = diskToCanvas(pointA.x, pointA.y);
    const pB = diskToCanvas(pointB.x, pointB.y);
    ctx.strokeStyle = 'rgba(217,95,2,0.4)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 3]);
    ctx.beginPath();
    ctx.moveTo(pA.x, pA.y);
    ctx.lineTo(pB.x, pB.y);
    ctx.stroke();
    ctx.setLineDash([]);

    // Point A (fixed, center)
    ctx.beginPath();
    ctx.arc(pA.x, pA.y, 7, 0, Math.PI * 2);
    ctx.fillStyle = '#1b9e77';
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = '9px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('A', pA.x, pA.y + 3);

    // Point B (draggable)
    ctx.beginPath();
    ctx.arc(pB.x, pB.y, 8, 0, Math.PI * 2);
    ctx.fillStyle = '#d95f02';
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.fillText('B', pB.x, pB.y + 3);

    // Update distance display
    const eDist = Math.sqrt((pointB.x - pointA.x) ** 2 + (pointB.y - pointA.y) ** 2);
    const hDist = hyperbolicDist(pointA.x, pointA.y, pointB.x, pointB.y);
    const ratio = eDist > 0.001 ? hDist / eDist : 1;

    const eEl = document.getElementById('poinc-euclid');
    const hEl = document.getElementById('poinc-hyper');
    const rEl = document.getElementById('poinc-ratio');
    if (eEl) eEl.textContent = eDist.toFixed(2);
    if (hEl) hEl.textContent = isFinite(hDist) ? hDist.toFixed(2) : '\u221E';
    if (rEl) rEl.textContent = isFinite(ratio) ? ratio.toFixed(1) + 'x' : '\u221E';

    // Labels
    ctx.fillStyle = '#5c7a94';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Boundary = \u221E distance', cx, cy + diskR + 18);
    ctx.fillText('Hierarchy embeds with equal spacing', cx, cy + diskR + 32);
  }

  draw();

  canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) * (canvas.width / rect.width);
    const my = (e.clientY - rect.top) * (canvas.height / rect.height);
    const dp = diskToCanvas(pointB.x, pointB.y);
    if (Math.hypot(mx - dp.x, my - dp.y) < 20) dragging = true;
  });

  canvas.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) * (canvas.width / rect.width);
    const my = (e.clientY - rect.top) * (canvas.height / rect.height);
    const dp = canvasToDisk(mx, my);
    const r = Math.sqrt(dp.x * dp.x + dp.y * dp.y);
    if (r < 0.95) {
      pointB.x = dp.x;
      pointB.y = dp.y;
    } else {
      // Clamp to disk boundary
      pointB.x = dp.x / r * 0.95;
      pointB.y = dp.y / r * 0.95;
    }
    draw();
  });

  canvas.addEventListener('mouseup', () => { dragging = false; });
  canvas.addEventListener('mouseleave', () => { dragging = false; });

  // Touch support
  canvas.addEventListener('touchstart', (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const touch = e.touches[0];
    const mx = (touch.clientX - rect.left) * (canvas.width / rect.width);
    const my = (touch.clientY - rect.top) * (canvas.height / rect.height);
    const dp = diskToCanvas(pointB.x, pointB.y);
    if (Math.hypot(mx - dp.x, my - dp.y) < 30) dragging = true;
  }, { passive: false });

  canvas.addEventListener('touchmove', (e) => {
    if (!dragging) return;
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const touch = e.touches[0];
    const mx = (touch.clientX - rect.left) * (canvas.width / rect.width);
    const my = (touch.clientY - rect.top) * (canvas.height / rect.height);
    const dp = canvasToDisk(mx, my);
    const r = Math.sqrt(dp.x * dp.x + dp.y * dp.y);
    if (r < 0.95) { pointB.x = dp.x; pointB.y = dp.y; }
    else { pointB.x = dp.x / r * 0.95; pointB.y = dp.y / r * 0.95; }
    draw();
  }, { passive: false });

  canvas.addEventListener('touchend', () => { dragging = false; });
}
