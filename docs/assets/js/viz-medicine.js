/* ==========================================================================
   Geometric Medicine — Interactive Visualizations
   1. Clinical A*: Pathfinding through clinical states with boundary penalties
   2. Moral Injury Accumulator: Timeline of boundary crossings
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initClinicalAStar();
  initMoralInjuryAccumulator();
});

/* ==========================================================================
   1. CLINICAL A* — A* search through clinical decision space
   Grid with clinical states. Boundary penalties for do-no-harm, consent, futility.
   ========================================================================== */
function initClinicalAStar() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const toc = section.querySelector('.toc-grid');
  if (!toc) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.innerHTML =
    '<h3 class="demo-title">Clinical A* Pathfinding</h3>' +
    '<p class="demo-subtitle">A* finds the clinical geodesic. Boundary strata add penalties: do-no-harm (red), consent required (gold), futility (gray).</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="clinical-canvas" width="520" height="340"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">' +
        '<button class="btn btn-secondary" id="clinical-run">Find Clinical Geodesic</button>' +
        '<button class="btn btn-secondary" id="clinical-reset">Reset</button>' +
      '</div>' +
      '<div style="display:flex;gap:16px;justify-content:center;margin-top:8px;font-size:11px;color:var(--text-secondary);flex-wrap:wrap">' +
        '<span><span style="color:#d95f02">\u25A0</span> Do-no-harm boundary</span>' +
        '<span><span style="color:#e6ab02">\u25A0</span> Consent required</span>' +
        '<span><span style="color:#666">\u25A0</span> Futility zone</span>' +
        '<span><span style="color:#1b9e77">\u25A0</span> Optimal path</span>' +
      '</div>' +
      '<div style="display:flex;gap:24px;justify-content:center;margin-top:8px;font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--text-secondary)">' +
        '<span>g(n) = <span id="clin-g" style="color:#1b9e77">0</span></span>' +
        '<span>h(n) = <span id="clin-h" style="color:#d95f02">0</span></span>' +
        '<span>Boundaries crossed: <span id="clin-bounds" style="color:#7570b3">0</span></span>' +
      '</div>' +
    '</div>';

  toc.parentNode.insertBefore(demo, toc.nextSibling);

  const canvas = document.getElementById('clinical-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const cols = 26, rows = 17;
  const cellW = canvas.width / cols;
  const cellH = canvas.height / rows;
  let grid = [];
  const startPos = { x: 1, y: 8 };
  const goalPos = { x: 24, y: 8 };
  let running = false;

  // Boundary types: 'harm' = do-no-harm, 'consent' = consent required, 'futility' = futility zone
  function initGrid() {
    grid = [];
    for (let y = 0; y < rows; y++) {
      grid[y] = [];
      for (let x = 0; x < cols; x++) {
        let cost = 1;
        let boundary = null;

        // Do-no-harm boundaries (high cost, red)
        if (x >= 6 && x <= 7 && y >= 2 && y <= 14 && y !== 5 && y !== 11) {
          cost = 15; boundary = 'harm';
        }
        // Consent required zones (moderate cost, gold)
        if (x >= 12 && x <= 13 && y >= 3 && y <= 13 && y !== 8) {
          cost = 8; boundary = 'consent';
        }
        // Futility zone (very high cost, gray)
        if (x >= 18 && x <= 19 && y >= 1 && y <= 15 && y !== 4 && y !== 12) {
          cost = 25; boundary = 'futility';
        }

        // Rough clinical terrain
        if (x >= 9 && x <= 10 && y >= 1 && y <= 4) cost = Math.max(cost, 3);
        if (x >= 15 && x <= 16 && y >= 11 && y <= 15) cost = Math.max(cost, 3);

        grid[y][x] = { cost, boundary, visited: false, path: false, exploring: false };
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
        else if (cell.exploring) color = 'rgba(117,112,179,0.6)';
        else if (cell.visited) color = 'rgba(141,160,203,0.15)';
        else if (cell.boundary === 'harm') color = 'rgba(217,95,2,0.3)';
        else if (cell.boundary === 'consent') color = 'rgba(230,171,2,0.25)';
        else if (cell.boundary === 'futility') color = 'rgba(102,102,102,0.3)';
        else if (cell.cost > 1) color = 'rgba(140,110,90,0.15)';
        else color = 'rgba(20,37,54,0.5)';
        ctx.fillStyle = color;
        ctx.fillRect(x * cellW + 1, y * cellH + 1, cellW - 2, cellH - 2);
      }
    }
    // Start label
    ctx.fillStyle = '#1b9e77';
    ctx.beginPath();
    ctx.arc(startPos.x * cellW + cellW / 2, startPos.y * cellH + cellH / 2, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = '8px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Dx', startPos.x * cellW + cellW / 2, startPos.y * cellH + cellH / 2 + 3);

    // Goal label
    ctx.fillStyle = '#d95f02';
    ctx.beginPath();
    ctx.arc(goalPos.x * cellW + cellW / 2, goalPos.y * cellH + cellH / 2, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.fillText('Rx', goalPos.x * cellW + cellW / 2, goalPos.y * cellH + cellH / 2 + 3);

    // Boundary labels
    ctx.font = '9px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#d95f02';
    ctx.fillText('Harm', 6.5 * cellW, 1.2 * cellH);
    ctx.fillStyle = '#e6ab02';
    ctx.fillText('Consent', 12.5 * cellW, 2.2 * cellH);
    ctx.fillStyle = '#666';
    ctx.fillText('Futility', 18.5 * cellW, 0.5 * cellH);
  }

  function heuristic(a, b) {
    return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
  }

  async function runClinicalAStar() {
    if (running) return;
    running = true;
    initGrid();
    const open = [{ ...startPos, g: 0, h: heuristic(startPos, goalPos) }];
    open[0].f = open[0].g + open[0].h;
    const closed = new Set();
    const parents = {};
    let boundsCrossed = 0;

    while (open.length > 0) {
      open.sort((a, b) => a.f - b.f);
      const current = open.shift();
      const key = `${current.x},${current.y}`;
      if (closed.has(key)) continue;
      closed.add(key);

      grid[current.y][current.x].visited = true;
      grid[current.y][current.x].exploring = true;

      const gEl = document.getElementById('clin-g');
      const hEl = document.getElementById('clin-h');
      if (gEl) gEl.textContent = current.g.toFixed(1);
      if (hEl) hEl.textContent = current.h.toFixed(1);

      drawGrid();

      if (current.x === goalPos.x && current.y === goalPos.y) {
        let node = key;
        while (node) {
          const [px, py] = node.split(',').map(Number);
          grid[py][px].path = true;
          grid[py][px].exploring = false;
          if (grid[py][px].boundary) boundsCrossed++;
          node = parents[node];
        }
        drawGrid();
        document.getElementById('clin-bounds').textContent = boundsCrossed;
        running = false;
        return;
      }

      await new Promise(r => setTimeout(r, 18));
      grid[current.y][current.x].exploring = false;

      const dirs = [[0,1],[0,-1],[1,0],[-1,0]];
      for (const [dx, dy] of dirs) {
        const nx = current.x + dx, ny = current.y + dy;
        if (nx < 0 || nx >= cols || ny < 0 || ny >= rows) continue;
        const nKey = `${nx},${ny}`;
        if (closed.has(nKey)) continue;
        const g = current.g + grid[ny][nx].cost;
        const h = heuristic({ x: nx, y: ny }, goalPos);
        parents[nKey] = key;
        open.push({ x: nx, y: ny, g, h, f: g + h });
      }
    }
    running = false;
  }

  initGrid();
  drawGrid();

  document.getElementById('clinical-run').addEventListener('click', () => {
    if (!running) runClinicalAStar();
  });
  document.getElementById('clinical-reset').addEventListener('click', () => {
    running = false;
    initGrid();
    drawGrid();
    ['clin-g', 'clin-h', 'clin-bounds'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '0';
    });
  });
}

/* ==========================================================================
   2. MORAL INJURY ACCUMULATOR — Timeline with boundary crossings
   Events add to MI score. Separate bars for burnout vs moral injury.
   ========================================================================== */
function initMoralInjuryAccumulator() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const prev = section.querySelectorAll('.scalar-tensor-demo');
  const anchor = prev[prev.length - 1];
  if (!anchor) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.style.marginTop = '32px';
  demo.innerHTML =
    '<h3 class="demo-title">Moral Injury Accumulator</h3>' +
    '<p class="demo-subtitle">Clinical events cross moral boundaries. Watch burnout (resource depletion) and moral injury (boundary violations) accumulate independently.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="mi-canvas" width="520" height="320"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">' +
        '<button class="btn btn-secondary mi-event-btn" data-event="triage">Triage Decision</button>' +
        '<button class="btn btn-secondary mi-event-btn" data-event="futile">Futile Care Order</button>' +
        '<button class="btn btn-secondary mi-event-btn" data-event="resource">Resource Denial</button>' +
        '<button class="btn btn-secondary mi-event-btn" data-event="death">Patient Death</button>' +
        '<button class="btn btn-secondary" id="mi-reset">Reset</button>' +
      '</div>' +
      '<div style="display:flex;gap:20px;justify-content:center;margin-top:8px;font-size:11px;color:var(--text-secondary)">' +
        '<span><span style="color:#d95f02">\u25A0</span> Burnout g(n): resource depletion</span>' +
        '<span><span style="color:#7570b3">\u25A0</span> Moral Injury h(n): boundary damage</span>' +
      '</div>' +
    '</div>';

  anchor.parentNode.insertBefore(demo, anchor.nextSibling);

  const canvas = document.getElementById('mi-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const eventTypes = {
    triage:   { burnout: 8,  injury: 15, label: 'Triage', color: '#e6ab02' },
    futile:   { burnout: 5,  injury: 20, label: 'Futile Care', color: '#7570b3' },
    resource: { burnout: 15, injury: 10, label: 'Resource Denied', color: '#d95f02' },
    death:    { burnout: 12, injury: 25, label: 'Patient Death', color: '#e7298a' },
  };

  let events = [];
  let burnout = 0;
  let injury = 0;
  const maxVal = 100;
  let animBurnout = 0;
  let animInjury = 0;

  function draw() {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Timeline area
    const tlY = 40;
    const tlH = 100;
    const tlLeft = 60;
    const tlRight = w - 30;
    const tlWidth = tlRight - tlLeft;

    // Timeline line
    ctx.strokeStyle = 'rgba(102,194,165,0.2)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(tlLeft, tlY + tlH / 2);
    ctx.lineTo(tlRight, tlY + tlH / 2);
    ctx.stroke();

    // Timeline events
    const maxEvents = 12;
    events.forEach((ev, i) => {
      const x = tlLeft + (i + 0.5) * (tlWidth / Math.max(maxEvents, events.length));
      const et = eventTypes[ev];

      // Event dot
      ctx.beginPath();
      ctx.arc(x, tlY + tlH / 2, 8, 0, Math.PI * 2);
      ctx.fillStyle = et.color + '40';
      ctx.fill();
      ctx.strokeStyle = et.color;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Event label
      ctx.fillStyle = et.color;
      ctx.font = '9px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(et.label, x, tlY + tlH / 2 - 16);

      // Boundary crossing indicator
      ctx.fillStyle = '#5c7a94';
      ctx.font = '8px "JetBrains Mono", monospace';
      ctx.fillText('+' + et.injury, x, tlY + tlH / 2 + 20);
    });

    // Timeline label
    ctx.fillStyle = '#8fa4b8';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Timeline', tlLeft, tlY - 5);
    ctx.fillStyle = '#5c7a94';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(events.length + ' events', tlRight, tlY - 5);

    // Bars area
    const barTop = tlY + tlH + 40;
    const barH = 35;
    const barLeft = 160;
    const barWidth = w - barLeft - 40;

    // Burnout bar (g(n) depletion)
    const burnoutFrac = Math.min(1, animBurnout / maxVal);
    ctx.fillStyle = 'rgba(217,95,2,0.15)';
    ctx.fillRect(barLeft, barTop, barWidth, barH);
    ctx.fillStyle = burnoutFrac > 0.8 ? '#d95f02' : 'rgba(217,95,2,0.6)';
    ctx.fillRect(barLeft, barTop, barWidth * burnoutFrac, barH);
    ctx.strokeStyle = 'rgba(217,95,2,0.3)';
    ctx.strokeRect(barLeft, barTop, barWidth, barH);

    ctx.fillStyle = '#d95f02';
    ctx.font = '600 12px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText('Burnout g(n)', barLeft - 10, barTop + barH / 2 + 4);
    ctx.fillStyle = '#e8ecf0';
    ctx.font = '600 13px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(Math.round(animBurnout) + '%', barLeft + barWidth / 2, barTop + barH / 2 + 5);

    // Moral injury bar (h(n) damage)
    const injuryTop = barTop + barH + 20;
    const injuryFrac = Math.min(1, animInjury / maxVal);
    ctx.fillStyle = 'rgba(117,112,179,0.15)';
    ctx.fillRect(barLeft, injuryTop, barWidth, barH);
    ctx.fillStyle = injuryFrac > 0.8 ? '#7570b3' : 'rgba(117,112,179,0.6)';
    ctx.fillRect(barLeft, injuryTop, barWidth * injuryFrac, barH);
    ctx.strokeStyle = 'rgba(117,112,179,0.3)';
    ctx.strokeRect(barLeft, injuryTop, barWidth, barH);

    ctx.fillStyle = '#7570b3';
    ctx.font = '600 12px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText('Moral Injury h(n)', barLeft - 10, injuryTop + barH / 2 + 4);
    ctx.fillStyle = '#e8ecf0';
    ctx.font = '600 13px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(Math.round(animInjury) + '%', barLeft + barWidth / 2, injuryTop + barH / 2 + 5);

    // Status indicator
    const totalStress = (burnoutFrac + injuryFrac) / 2;
    let statusText, statusColor;
    if (totalStress < 0.3) { statusText = 'Sustainable'; statusColor = '#1b9e77'; }
    else if (totalStress < 0.6) { statusText = 'Accumulating strain'; statusColor = '#e6ab02'; }
    else if (totalStress < 0.85) { statusText = 'Critical threshold approaching'; statusColor = '#d95f02'; }
    else { statusText = 'Crisis: moral injury + burnout compounding'; statusColor = '#e7298a'; }

    ctx.fillStyle = statusColor;
    ctx.font = '600 13px "Crimson Pro", serif';
    ctx.textAlign = 'center';
    ctx.fillText(statusText, w / 2, h - 15);

    // Key insight
    ctx.fillStyle = '#5c7a94';
    ctx.font = '10px Inter, sans-serif';
    ctx.fillText('Burnout (energy depletion) and moral injury (value violation) are geometrically independent', w / 2, h - 35);
  }

  function animateTo(targetBurnout, targetInjury) {
    function step() {
      let moved = false;
      if (Math.abs(animBurnout - targetBurnout) > 0.5) {
        animBurnout += (targetBurnout - animBurnout) * 0.1;
        moved = true;
      } else {
        animBurnout = targetBurnout;
      }
      if (Math.abs(animInjury - targetInjury) > 0.5) {
        animInjury += (targetInjury - animInjury) * 0.1;
        moved = true;
      } else {
        animInjury = targetInjury;
      }
      draw();
      if (moved) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  draw();

  document.querySelectorAll('.mi-event-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const evType = btn.dataset.event;
      if (!eventTypes[evType]) return;
      events.push(evType);
      burnout = Math.min(maxVal, burnout + eventTypes[evType].burnout);
      injury = Math.min(maxVal, injury + eventTypes[evType].injury);
      animateTo(burnout, injury);
    });
  });

  document.getElementById('mi-reset').addEventListener('click', () => {
    events = [];
    burnout = 0;
    injury = 0;
    animateTo(0, 0);
  });
}
