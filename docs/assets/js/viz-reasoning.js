/* ==========================================================================
   Geometric Reasoning — Interactive Visualizations
   1. Geodesic Pathfinder on a 2D manifold with obstacles
   2. Heuristic Corruption slider demo
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initReasoningGeodesicPathfinder();
  initHeuristicCorruption();
});

/* ==========================================================================
   1. GEODESIC PATHFINDER — A* search on a 2D manifold with obstacles
   User clicks to set start/end, watches optimal path animate.
   ========================================================================== */
function initReasoningGeodesicPathfinder() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const toc = section.querySelector('.toc-grid');
  if (!toc) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.innerHTML =
    '<h3 class="demo-title">Geodesic Pathfinder on a Reasoning Manifold</h3>' +
    '<p class="demo-subtitle">Click to place Start (green) then Goal (orange). Watch A* find the optimal path through obstacles.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="reason-geodesic-canvas" width="520" height="320"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">' +
        '<button class="btn btn-secondary" id="reason-run-btn">Run A* Search</button>' +
        '<button class="btn btn-secondary" id="reason-reset-btn">Reset</button>' +
      '</div>' +
      '<div style="display:flex;gap:24px;justify-content:center;margin-top:12px;font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--text-secondary)">' +
        '<span>g(n) = <span id="rg-g" style="color:#1b9e77">0</span></span>' +
        '<span>h(n) = <span id="rg-h" style="color:#d95f02">0</span></span>' +
        '<span>f(n) = <span id="rg-f" style="color:#7570b3">0</span></span>' +
        '<span>Nodes: <span id="rg-nodes" style="color:#8fa4b8">0</span></span>' +
      '</div>' +
    '</div>';

  toc.parentNode.insertBefore(demo, toc.nextSibling);

  const canvas = document.getElementById('reason-geodesic-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const cols = 26, rows = 16;
  const cellW = canvas.width / cols;
  const cellH = canvas.height / rows;
  let grid = [];
  let start = { x: 2, y: 8 };
  let goal = { x: 23, y: 8 };
  let clickState = 0; // 0 = place start, 1 = place goal, 2 = ready
  let running = false;

  function initGrid() {
    grid = [];
    for (let y = 0; y < rows; y++) {
      grid[y] = [];
      for (let x = 0; x < cols; x++) {
        let cost = 1;
        // Obstacles: walls with gaps
        if (x === 7 && y >= 1 && y <= 13 && y !== 4 && y !== 10) cost = 50;
        if (x === 13 && y >= 2 && y <= 14 && y !== 7 && y !== 12) cost = 50;
        if (x === 19 && y >= 0 && y <= 12 && y !== 3 && y !== 9) cost = 50;
        // Rough terrain patches
        if (x >= 9 && x <= 11 && y >= 1 && y <= 5) cost = Math.max(cost, 3);
        if (x >= 15 && x <= 17 && y >= 9 && y <= 13) cost = Math.max(cost, 4);
        grid[y][x] = { cost, visited: false, path: false, exploring: false };
      }
    }
  }

  function drawGrid() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const cell = grid[y][x];
        let color;
        if (cell.path) color = 'rgba(27,158,119,0.65)';
        else if (cell.exploring) color = 'rgba(117,112,179,0.7)';
        else if (cell.visited) color = 'rgba(141,160,203,0.2)';
        else if (cell.cost >= 50) color = 'rgba(100,80,60,0.5)';
        else if (cell.cost > 1) color = 'rgba(140,110,90,0.2)';
        else color = 'rgba(20,37,54,0.5)';
        ctx.fillStyle = color;
        ctx.fillRect(x * cellW + 1, y * cellH + 1, cellW - 2, cellH - 2);
      }
    }
    // Start
    ctx.fillStyle = '#1b9e77';
    ctx.beginPath();
    ctx.arc(start.x * cellW + cellW / 2, start.y * cellH + cellH / 2, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = '9px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('S', start.x * cellW + cellW / 2, start.y * cellH + cellH / 2 + 3);
    // Goal
    ctx.fillStyle = '#d95f02';
    ctx.beginPath();
    ctx.arc(goal.x * cellW + cellW / 2, goal.y * cellH + cellH / 2, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.fillText('G', goal.x * cellW + cellW / 2, goal.y * cellH + cellH / 2 + 3);
  }

  canvas.addEventListener('click', (e) => {
    if (running) return;
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) * (canvas.width / rect.width);
    const my = (e.clientY - rect.top) * (canvas.height / rect.height);
    const gx = Math.floor(mx / cellW);
    const gy = Math.floor(my / cellH);
    if (gx < 0 || gx >= cols || gy < 0 || gy >= rows) return;
    if (clickState === 0) { start = { x: gx, y: gy }; clickState = 1; }
    else if (clickState === 1) { goal = { x: gx, y: gy }; clickState = 2; }
    else { start = { x: gx, y: gy }; clickState = 1; }
    initGrid();
    drawGrid();
  });

  function heuristic(a, b) {
    return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
  }

  async function runAStar() {
    if (running) return;
    running = true;
    initGrid();
    const open = [{ ...start, g: 0, h: heuristic(start, goal), parent: null }];
    open[0].f = open[0].g + open[0].h;
    const closed = new Set();
    const parents = {};
    let nodesExplored = 0;

    while (open.length > 0) {
      open.sort((a, b) => a.f - b.f);
      const current = open.shift();
      const key = `${current.x},${current.y}`;
      if (closed.has(key)) continue;
      closed.add(key);
      nodesExplored++;

      grid[current.y][current.x].visited = true;
      grid[current.y][current.x].exploring = true;
      const gEl = document.getElementById('rg-g');
      const hEl = document.getElementById('rg-h');
      const fEl = document.getElementById('rg-f');
      const nEl = document.getElementById('rg-nodes');
      if (gEl) gEl.textContent = current.g.toFixed(1);
      if (hEl) hEl.textContent = current.h.toFixed(1);
      if (fEl) fEl.textContent = current.f.toFixed(1);
      if (nEl) nEl.textContent = nodesExplored;
      drawGrid();

      if (current.x === goal.x && current.y === goal.y) {
        let node = key;
        while (node) {
          const [px, py] = node.split(',').map(Number);
          grid[py][px].path = true;
          grid[py][px].exploring = false;
          node = parents[node];
        }
        drawGrid();
        running = false;
        return;
      }
      await new Promise(r => setTimeout(r, 20));
      grid[current.y][current.x].exploring = false;

      const dirs = [[0,1],[0,-1],[1,0],[-1,0]];
      for (const [dx, dy] of dirs) {
        const nx = current.x + dx, ny = current.y + dy;
        if (nx < 0 || nx >= cols || ny < 0 || ny >= rows) continue;
        const nKey = `${nx},${ny}`;
        if (closed.has(nKey)) continue;
        const g = current.g + grid[ny][nx].cost;
        const h = heuristic({ x: nx, y: ny }, goal);
        parents[nKey] = key;
        open.push({ x: nx, y: ny, g, h, f: g + h });
      }
    }
    running = false;
  }

  initGrid();
  drawGrid();

  document.getElementById('reason-run-btn').addEventListener('click', () => { if (!running) runAStar(); });
  document.getElementById('reason-reset-btn').addEventListener('click', () => {
    running = false;
    clickState = 0;
    start = { x: 2, y: 8 };
    goal = { x: 23, y: 8 };
    initGrid();
    drawGrid();
    ['rg-g','rg-h','rg-f','rg-nodes'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '0';
    });
  });
}

/* ==========================================================================
   2. HEURISTIC CORRUPTION — Slider degrades heuristic quality
   Shows how corrupted heuristics cause search path to degrade.
   ========================================================================== */
function initHeuristicCorruption() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const prev = document.querySelector('.scalar-tensor-demo');
  if (!prev) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.style.marginTop = '32px';
  demo.innerHTML =
    '<h3 class="demo-title">Heuristic Corruption</h3>' +
    '<p class="demo-subtitle">Slide to corrupt the heuristic. Watch the search path degrade from geodesic to wandering.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="corrupt-canvas" width="520" height="280"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<label class="demo-slider-label">' +
        '<span>Corruption</span>' +
        '<input type="range" min="0" max="100" value="0" class="demo-slider" id="corrupt-slider">' +
        '<span class="demo-val" id="corrupt-val">0%</span>' +
      '</label>' +
      '<div style="display:flex;gap:24px;justify-content:center;margin-top:8px;font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--text-secondary)">' +
        '<span>Nodes explored: <span id="corrupt-nodes" style="color:#d95f02">0</span></span>' +
        '<span>Path cost: <span id="corrupt-cost" style="color:#1b9e77">0</span></span>' +
        '<span>Quality: <span id="corrupt-quality" style="color:#7570b3">Optimal</span></span>' +
      '</div>' +
    '</div>';

  prev.parentNode.insertBefore(demo, prev.nextSibling);

  const canvas = document.getElementById('corrupt-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const cols = 26, rows = 14;
  const cellW = canvas.width / cols;
  const cellH = canvas.height / rows;
  const startPos = { x: 1, y: 7 };
  const goalPos = { x: 24, y: 7 };

  function makeGrid() {
    const g = [];
    for (let y = 0; y < rows; y++) {
      g[y] = [];
      for (let x = 0; x < cols; x++) {
        let cost = 1;
        if (x === 8 && y >= 1 && y <= 11 && y !== 4 && y !== 9) cost = 50;
        if (x === 17 && y >= 2 && y <= 12 && y !== 6 && y !== 11) cost = 50;
        g[y][x] = { cost, visited: false, path: false };
      }
    }
    return g;
  }

  function drawCorruptGrid(grid) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const cell = grid[y][x];
        let color;
        if (cell.path) color = 'rgba(27,158,119,0.6)';
        else if (cell.visited) color = 'rgba(217,95,2,0.15)';
        else if (cell.cost >= 50) color = 'rgba(100,80,60,0.45)';
        else color = 'rgba(20,37,54,0.5)';
        ctx.fillStyle = color;
        ctx.fillRect(x * cellW + 1, y * cellH + 1, cellW - 2, cellH - 2);
      }
    }
    ctx.fillStyle = '#1b9e77';
    ctx.beginPath();
    ctx.arc(startPos.x * cellW + cellW / 2, startPos.y * cellH + cellH / 2, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#d95f02';
    ctx.beginPath();
    ctx.arc(goalPos.x * cellW + cellW / 2, goalPos.y * cellH + cellH / 2, 6, 0, Math.PI * 2);
    ctx.fill();
  }

  function runCorruptSearch(corruption) {
    const grid = makeGrid();
    const noise = corruption / 100;
    const open = [{ x: startPos.x, y: startPos.y, g: 0, h: 0, f: 0 }];
    open[0].h = Math.abs(startPos.x - goalPos.x) + Math.abs(startPos.y - goalPos.y);
    open[0].f = open[0].h;
    const closed = new Set();
    const parents = {};
    let nodesExplored = 0;

    while (open.length > 0) {
      open.sort((a, b) => a.f - b.f);
      const current = open.shift();
      const key = `${current.x},${current.y}`;
      if (closed.has(key)) continue;
      closed.add(key);
      nodesExplored++;
      grid[current.y][current.x].visited = true;

      if (current.x === goalPos.x && current.y === goalPos.y) {
        let node = key;
        let pathCost = 0;
        while (node) {
          const [px, py] = node.split(',').map(Number);
          grid[py][px].path = true;
          pathCost += grid[py][px].cost;
          node = parents[node];
        }
        drawCorruptGrid(grid);
        return { nodes: nodesExplored, cost: pathCost };
      }

      const dirs = [[0,1],[0,-1],[1,0],[-1,0]];
      for (const [dx, dy] of dirs) {
        const nx = current.x + dx, ny = current.y + dy;
        if (nx < 0 || nx >= cols || ny < 0 || ny >= rows) continue;
        const nKey = `${nx},${ny}`;
        if (closed.has(nKey)) continue;
        const g = current.g + grid[ny][nx].cost;
        let h = Math.abs(nx - goalPos.x) + Math.abs(ny - goalPos.y);
        // Corrupt the heuristic with noise
        h = h * (1 + noise * (Math.random() * 2 - 1) * 5);
        h = Math.max(0, h);
        parents[nKey] = key;
        open.push({ x: nx, y: ny, g, h, f: g + h });
      }
    }
    drawCorruptGrid(grid);
    return { nodes: nodesExplored, cost: 0 };
  }

  // Initial run
  let result = runCorruptSearch(0);
  const baseNodes = result.nodes;
  const baseCost = result.cost;
  document.getElementById('corrupt-nodes').textContent = result.nodes;
  document.getElementById('corrupt-cost').textContent = result.cost;

  document.getElementById('corrupt-slider').addEventListener('input', function() {
    const val = parseInt(this.value);
    document.getElementById('corrupt-val').textContent = val + '%';
    const r = runCorruptSearch(val);
    document.getElementById('corrupt-nodes').textContent = r.nodes;
    document.getElementById('corrupt-cost').textContent = r.cost;
    const q = r.nodes <= baseNodes * 1.2 ? 'Optimal' :
              r.nodes <= baseNodes * 2 ? 'Degraded' :
              r.nodes <= baseNodes * 3 ? 'Poor' : 'Wandering';
    const qEl = document.getElementById('corrupt-quality');
    qEl.textContent = q;
    qEl.style.color = q === 'Optimal' ? '#1b9e77' : q === 'Degraded' ? '#e6ab02' : '#d95f02';
  });
}
