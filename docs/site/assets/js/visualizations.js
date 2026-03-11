/* ==========================================================================
   Geometric Ethics — Rich Visual Interactions
   Canvas/SVG animations for exploring mathematical concepts
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initScalarVsTensorDemo();
  initInteractiveDimensionDrag();
  initTensorContractionAnim();
  initGeodesicPathfinder();
  initConservationFlowAnim();
  initStratificationCrossing();
  initConceptExploration();
});

/* ==========================================================================
   1. SCALAR vs TENSOR — Animated side-by-side comparison
   Shows what scalar collapse loses. Inserted into Core Argument section.
   ========================================================================== */
function initScalarVsTensorDemo() {
  const section = document.getElementById('core-argument');
  if (!section) return;
  const grid = section.querySelector('.argument-grid');
  if (!grid) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.innerHTML =
    '<h3 class="demo-title">Scalar Collapse: What Gets Lost</h3>' +
    '<p class="demo-subtitle">Drag the slider to see how collapsing a 3D evaluation to a single number destroys structure</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="tensor-canvas" width="360" height="280"></canvas>' +
      '<div class="demo-arrow-col">' +
        '<svg viewBox="0 0 60 40" width="60" height="40"><path d="M5 20 L45 20 M35 10 L45 20 L35 30" fill="none" stroke="var(--accent-light)" stroke-width="2" opacity="0.5"/></svg>' +
        '<span class="demo-arrow-label">contract</span>' +
      '</div>' +
      '<canvas id="scalar-canvas" width="160" height="280"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<label class="demo-slider-label">' +
        '<span>Welfare (D<sub>1</sub>)</span>' +
        '<input type="range" min="0" max="100" value="80" class="demo-slider" data-dim="0">' +
        '<span class="demo-val">0.80</span>' +
      '</label>' +
      '<label class="demo-slider-label">' +
        '<span>Rights (D<sub>2</sub>)</span>' +
        '<input type="range" min="0" max="100" value="30" class="demo-slider" data-dim="1">' +
        '<span class="demo-val">0.30</span>' +
      '</label>' +
      '<label class="demo-slider-label">' +
        '<span>Justice (D<sub>3</sub>)</span>' +
        '<input type="range" min="0" max="100" value="60" class="demo-slider" data-dim="2">' +
        '<span class="demo-val">0.60</span>' +
      '</label>' +
    '</div>';

  grid.parentNode.insertBefore(demo, grid.nextSibling);

  const tensorCanvas = document.getElementById('tensor-canvas');
  const scalarCanvas = document.getElementById('scalar-canvas');
  if (!tensorCanvas || !scalarCanvas) return;

  const tCtx = tensorCanvas.getContext('2d');
  const sCtx = scalarCanvas.getContext('2d');
  const dims = [0.8, 0.3, 0.6];
  const dimNames = ['D1 Welfare', 'D2 Rights', 'D3 Justice'];
  const dimColors = ['#1b9e77', '#d95f02', '#7570b3'];

  function drawTensor() {
    const w = tensorCanvas.width, h = tensorCanvas.height;
    tCtx.clearRect(0, 0, w, h);

    const cx = w / 2, cy = h / 2 + 10;
    const barW = 40, gap = 30;
    const maxH = 180;

    // Draw 3 bars (vector components)
    dims.forEach((v, i) => {
      const x = cx + (i - 1) * (barW + gap) - barW / 2;
      const barH = v * maxH;
      const y = cy - barH;

      // Bar
      tCtx.fillStyle = dimColors[i] + '33';
      tCtx.fillRect(x, cy - maxH, barW, maxH);
      tCtx.fillStyle = dimColors[i];
      tCtx.fillRect(x, y, barW, barH);

      // Value label
      tCtx.fillStyle = dimColors[i];
      tCtx.font = '600 13px Inter, sans-serif';
      tCtx.textAlign = 'center';
      tCtx.fillText(v.toFixed(2), x + barW / 2, y - 8);

      // Dim label
      tCtx.fillStyle = '#8fa4b8';
      tCtx.font = '11px Inter, sans-serif';
      tCtx.fillText(dimNames[i], x + barW / 2, cy + 20);
    });

    // Title
    tCtx.fillStyle = '#e8ecf0';
    tCtx.font = '600 14px "Crimson Pro", serif';
    tCtx.textAlign = 'center';
    tCtx.fillText('Tensor: 3 components', w / 2, 20);
    tCtx.fillStyle = '#5c7a94';
    tCtx.font = '11px Inter, sans-serif';
    tCtx.fillText('Direction + magnitude preserved', w / 2, 38);
  }

  function drawScalar() {
    const w = scalarCanvas.width, h = scalarCanvas.height;
    sCtx.clearRect(0, 0, w, h);

    const scalar = (dims[0] + dims[1] + dims[2]) / 3;
    const cx = w / 2, cy = h / 2 + 10;
    const maxH = 180;
    const barW = 50;
    const barH = scalar * maxH;

    // Background
    sCtx.fillStyle = '#8899aa22';
    sCtx.fillRect(cx - barW / 2, cy - maxH, barW, maxH);

    // Blended color
    sCtx.fillStyle = '#8899aa';
    sCtx.fillRect(cx - barW / 2, cy - barH, barW, barH);

    // Value
    sCtx.fillStyle = '#8899aa';
    sCtx.font = '600 16px Inter, sans-serif';
    sCtx.textAlign = 'center';
    sCtx.fillText(scalar.toFixed(2), cx, cy - barH - 10);

    // Label
    sCtx.fillStyle = '#e8ecf0';
    sCtx.font = '600 14px "Crimson Pro", serif';
    sCtx.fillText('Scalar', cx, 20);
    sCtx.fillStyle = '#5c7a94';
    sCtx.font = '11px Inter, sans-serif';
    sCtx.fillText('All structure lost', cx, 38);

    // Show what's lost
    sCtx.fillStyle = '#5c7a94';
    sCtx.font = '11px Inter, sans-serif';
    sCtx.fillText('Which dims?', cx, cy + 20);
    sCtx.fillText('Unknown.', cx, cy + 36);
  }

  function update() {
    drawTensor();
    drawScalar();
  }

  demo.querySelectorAll('.demo-slider').forEach(slider => {
    slider.addEventListener('input', () => {
      const i = parseInt(slider.dataset.dim);
      dims[i] = parseInt(slider.value) / 100;
      slider.nextElementSibling.textContent = dims[i].toFixed(2);
      update();
    });
  });

  update();
}

/* ==========================================================================
   2. INTERACTIVE DIMENSION WHEEL — Drag dots to reshape the polygon
   Enhances the existing dimension wheel with draggable values.
   ========================================================================== */
function initInteractiveDimensionDrag() {
  const svg = document.getElementById('dimension-wheel');
  if (!svg) return;

  const dims = [0.85, 0.75, 0.80, 0.70, 0.60, 0.65, 0.72, 0.68, 0.55];
  const cx = 250, cy = 250, maxR = 180;
  const n = dims.length;
  const angleStep = (2 * Math.PI) / n;

  // Add instruction
  const vizContainer = svg.closest('.dimension-viz');
  if (vizContainer) {
    const hint = document.createElement('p');
    hint.style.cssText = 'text-align:center;font-size:12px;color:var(--text-muted);margin-top:8px';
    hint.textContent = 'Drag the dots to reshape the moral profile';
    vizContainer.appendChild(hint);
  }

  let dragging = null;
  const dots = svg.querySelectorAll('#dim-lines circle');
  const polygon = document.getElementById('dim-polygon');

  function updatePolygon() {
    const points = dims.map((v, i) => {
      const angle = -Math.PI / 2 + i * angleStep;
      const px = cx + maxR * v * Math.cos(angle);
      const py = cy + maxR * v * Math.sin(angle);
      return `${px},${py}`;
    });
    if (polygon) polygon.setAttribute('points', points.join(' '));
  }

  function getSVGPoint(e) {
    const pt = svg.createSVGPoint();
    const touch = e.touches ? e.touches[0] : e;
    pt.x = touch.clientX;
    pt.y = touch.clientY;
    return pt.matrixTransform(svg.getScreenCTM().inverse());
  }

  dots.forEach((dot, i) => {
    dot.style.cursor = 'grab';

    const startDrag = (e) => {
      e.preventDefault();
      dragging = i;
      dot.style.cursor = 'grabbing';
      dot.setAttribute('r', '8');
    };

    dot.addEventListener('mousedown', startDrag);
    dot.addEventListener('touchstart', startDrag, { passive: false });
  });

  const moveDrag = (e) => {
    if (dragging === null) return;
    e.preventDefault();
    const pt = getSVGPoint(e);
    const dx = pt.x - cx;
    const dy = pt.y - cy;
    const dist = Math.sqrt(dx * dx + dy * dy);
    dims[dragging] = Math.max(0.05, Math.min(1, dist / maxR));

    const angle = -Math.PI / 2 + dragging * angleStep;
    const px = cx + maxR * dims[dragging] * Math.cos(angle);
    const py = cy + maxR * dims[dragging] * Math.sin(angle);
    dots[dragging].setAttribute('cx', px);
    dots[dragging].setAttribute('cy', py);

    updatePolygon();

    // Update dim card display
    const dimCards = document.querySelectorAll('.dim-card');
    if (dimCards[dragging]) {
      dimCards[dragging].classList.add('active');
    }
  };

  const endDrag = () => {
    if (dragging !== null && dots[dragging]) {
      dots[dragging].style.cursor = 'grab';
      dots[dragging].setAttribute('r', '5');
    }
    dragging = null;
  };

  svg.addEventListener('mousemove', moveDrag);
  svg.addEventListener('touchmove', moveDrag, { passive: false });
  document.addEventListener('mouseup', endDrag);
  document.addEventListener('touchend', endDrag);
}

/* ==========================================================================
   3. TENSOR CONTRACTION ANIMATION — Animate the collapse from tensor to scalar
   Shows the rank reduction step by step with residue.
   ========================================================================== */
function initTensorContractionAnim() {
  const section = document.getElementById('tensor-hierarchy');
  if (!section) return;
  const controls = section.querySelector('.hierarchy-controls');
  if (!controls) return;

  // Add "Animate Contraction" button
  const animBtn = document.createElement('button');
  animBtn.className = 'level-btn contraction-btn';
  animBtn.innerHTML = 'Animate<br><small>Contraction</small>';
  controls.appendChild(animBtn);

  const svg = document.getElementById('hierarchy-svg');
  if (!svg) return;

  let animating = false;

  animBtn.addEventListener('click', () => {
    if (animating) return;
    animating = true;
    animBtn.classList.add('active');

    // Show all levels in sequence
    const levels = svg.querySelectorAll('.h-level');
    const btns = section.querySelectorAll('.level-btn:not(.contraction-btn)');
    let step = 0;

    function showStep() {
      if (step >= levels.length) {
        animating = false;
        animBtn.classList.remove('active');
        return;
      }

      btns.forEach(b => b.classList.remove('active'));
      if (btns[step]) btns[step].classList.add('active');

      levels.forEach(l => {
        l.style.display = 'none';
        l.classList.remove('active');
      });

      levels[step].style.display = '';
      levels[step].classList.add('active');
      levels[step].style.opacity = '0';
      requestAnimationFrame(() => {
        levels[step].style.transition = 'opacity 0.6s ease';
        levels[step].style.opacity = '1';
      });

      step++;
      setTimeout(showStep, 2000);
    }

    showStep();
  });
}

/* ==========================================================================
   4. GEODESIC PATHFINDER — Animated A* search on a moral landscape
   Visual demo of f(n) = g(n) + h(n) for the equation section.
   ========================================================================== */
function initGeodesicPathfinder() {
  const section = document.getElementById('equation');
  if (!section) return;
  const container = section.querySelector('.container');
  if (!container) return;

  const demo = document.createElement('div');
  demo.className = 'geodesic-demo';
  demo.innerHTML =
    '<div class="geodesic-header">' +
      '<h4>A* Pathfinding on the Moral Manifold</h4>' +
      '<p>Watch the algorithm find the optimal path. Blue = explored. Green = path found.</p>' +
    '</div>' +
    '<div class="geodesic-canvas-wrap">' +
      '<canvas id="geodesic-canvas" width="500" height="300"></canvas>' +
    '</div>' +
    '<div class="geodesic-controls">' +
      '<button class="btn btn-secondary geodesic-run">Run A* Search</button>' +
      '<button class="btn btn-secondary geodesic-reset">Reset</button>' +
      '<div class="geodesic-stats">' +
        '<span class="gs-item">g(n) = <span id="gs-g">0</span></span>' +
        '<span class="gs-item">h(n) = <span id="gs-h">0</span></span>' +
        '<span class="gs-item">f(n) = <span id="gs-f">0</span></span>' +
      '</div>' +
    '</div>';
  container.appendChild(demo);

  const canvas = document.getElementById('geodesic-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const cols = 25, rows = 15;
  const cellW = canvas.width / cols;
  const cellH = canvas.height / rows;

  // Create landscape with "moral terrain"
  let grid = [];
  let start = { x: 1, y: 7 };
  let goal = { x: 23, y: 7 };

  function initGrid() {
    grid = [];
    for (let y = 0; y < rows; y++) {
      grid[y] = [];
      for (let x = 0; x < cols; x++) {
        // Create varied terrain costs (moral complexity)
        let cost = 1;
        // Add "boundaries" (high-cost regions)
        if ((x === 8 && y >= 2 && y <= 12) || (x === 16 && y >= 3 && y <= 11)) cost = 8;
        if (x === 8 && (y === 5 || y === 9)) cost = 2; // gaps in boundaries
        if (x === 16 && (y === 6 || y === 10)) cost = 2;
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
        if (cell.path) color = 'rgba(27,158,119,0.6)';
        else if (cell.exploring) color = 'rgba(141,160,203,0.7)';
        else if (cell.visited) color = 'rgba(141,160,203,0.2)';
        else if (cell.cost > 5) color = 'rgba(140,110,90,0.3)';
        else if (cell.cost > 1) color = 'rgba(140,110,90,0.15)';
        else color = 'rgba(20,37,54,0.5)';

        ctx.fillStyle = color;
        ctx.fillRect(x * cellW + 1, y * cellH + 1, cellW - 2, cellH - 2);
      }
    }

    // Start & goal
    ctx.fillStyle = '#1b9e77';
    ctx.beginPath();
    ctx.arc(start.x * cellW + cellW / 2, start.y * cellH + cellH / 2, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = '9px Inter';
    ctx.textAlign = 'center';
    ctx.fillText('S', start.x * cellW + cellW / 2, start.y * cellH + cellH / 2 + 3);

    ctx.fillStyle = '#d95f02';
    ctx.beginPath();
    ctx.arc(goal.x * cellW + cellW / 2, goal.y * cellH + cellH / 2, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.fillText('G', goal.x * cellW + cellW / 2, goal.y * cellH + cellH / 2 + 3);
  }

  function heuristic(a, b) {
    return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
  }

  async function runAStar() {
    const open = [{ ...start, g: 0, h: heuristic(start, goal), parent: null }];
    open[0].f = open[0].g + open[0].h;
    const closed = new Set();
    const parents = {};

    const gEl = document.getElementById('gs-g');
    const hEl = document.getElementById('gs-h');
    const fEl = document.getElementById('gs-f');

    while (open.length > 0) {
      open.sort((a, b) => a.f - b.f);
      const current = open.shift();
      const key = `${current.x},${current.y}`;

      if (closed.has(key)) continue;
      closed.add(key);

      grid[current.y][current.x].visited = true;
      grid[current.y][current.x].exploring = true;

      if (gEl) gEl.textContent = current.g.toFixed(1);
      if (hEl) hEl.textContent = current.h.toFixed(1);
      if (fEl) fEl.textContent = current.f.toFixed(1);

      drawGrid();

      if (current.x === goal.x && current.y === goal.y) {
        // Trace path
        let node = key;
        while (node) {
          const [px, py] = node.split(',').map(Number);
          grid[py][px].path = true;
          grid[py][px].exploring = false;
          node = parents[node];
        }
        drawGrid();
        return;
      }

      await new Promise(r => setTimeout(r, 30));
      grid[current.y][current.x].exploring = false;

      // Neighbors
      const dirs = [[0, 1], [0, -1], [1, 0], [-1, 0]];
      for (const [dx, dy] of dirs) {
        const nx = current.x + dx;
        const ny = current.y + dy;
        if (nx < 0 || nx >= cols || ny < 0 || ny >= rows) continue;
        const nKey = `${nx},${ny}`;
        if (closed.has(nKey)) continue;

        const g = current.g + grid[ny][nx].cost;
        const h = heuristic({ x: nx, y: ny }, goal);
        parents[nKey] = key;
        open.push({ x: nx, y: ny, g, h, f: g + h });
      }
    }
  }

  initGrid();
  drawGrid();

  const runBtn = demo.querySelector('.geodesic-run');
  const resetBtn = demo.querySelector('.geodesic-reset');

  runBtn.addEventListener('click', () => {
    initGrid();
    drawGrid();
    runAStar();
  });

  resetBtn.addEventListener('click', () => {
    initGrid();
    drawGrid();
    const gEl = document.getElementById('gs-g');
    const hEl = document.getElementById('gs-h');
    const fEl = document.getElementById('gs-f');
    if (gEl) gEl.textContent = '0';
    if (hEl) hEl.textContent = '0';
    if (fEl) fEl.textContent = '0';
  });
}

/* ==========================================================================
   5. CONSERVATION FLOW — Animated harm flow showing conservation
   Particles flow around the Noether diagram, total is conserved.
   ========================================================================== */
function initConservationFlowAnim() {
  const vizContainer = document.querySelector('.conservation-viz');
  if (!vizContainer) return;

  const canvas = document.createElement('canvas');
  canvas.width = 400;
  canvas.height = 400;
  canvas.style.cssText = 'position:absolute;inset:0;pointer-events:none;';
  vizContainer.style.position = 'relative';
  vizContainer.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  const particles = [];
  const cx = 200, cy = 200, radius = 150;

  // Create orbiting harm particles
  for (let i = 0; i < 12; i++) {
    const angle = (i / 12) * Math.PI * 2;
    particles.push({
      angle,
      r: radius - 10 + Math.random() * 20,
      speed: 0.003 + Math.random() * 0.002,
      size: 2 + Math.random() * 2,
      alpha: 0.3 + Math.random() * 0.4
    });
  }

  function animate() {
    ctx.clearRect(0, 0, 400, 400);

    particles.forEach(p => {
      p.angle += p.speed;
      const x = cx + p.r * Math.cos(p.angle);
      const y = cy + p.r * Math.sin(p.angle);

      ctx.beginPath();
      ctx.arc(x, y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(27,158,119,${p.alpha})`;
      ctx.fill();

      // Trail
      const tx = cx + p.r * Math.cos(p.angle - 0.3);
      const ty = cy + p.r * Math.sin(p.angle - 0.3);
      ctx.beginPath();
      ctx.moveTo(tx, ty);
      ctx.lineTo(x, y);
      ctx.strokeStyle = `rgba(27,158,119,${p.alpha * 0.3})`;
      ctx.lineWidth = 1;
      ctx.stroke();
    });

    // Total harm counter
    ctx.fillStyle = 'rgba(27,158,119,0.8)';
    ctx.font = '600 11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Total H = const', cx, cy + 60);

    requestAnimationFrame(animate);
  }

  // Only animate when visible
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) animate();
  }, { threshold: 0.3 });
  observer.observe(vizContainer);
}

/* ==========================================================================
   6. STRATIFICATION CROSSING — Animated boundary transitions
   Visual demo in the tensor hierarchy stratified level.
   ========================================================================== */
function initStratificationCrossing() {
  const section = document.getElementById('tensor-hierarchy');
  if (!section) return;

  // Add animation to the stratified level when it's shown
  const stratLevel = document.getElementById('h-level-5');
  if (!stratLevel) return;

  // Create an animated dot that crosses boundaries
  const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  dot.setAttribute('r', '6');
  dot.setAttribute('fill', '#4dd9c0');
  dot.setAttribute('opacity', '0.8');
  dot.style.transition = 'all 0.8s ease';
  stratLevel.appendChild(dot);

  const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  label.setAttribute('font-size', '10');
  label.setAttribute('fill', '#e8ecf0');
  label.setAttribute('text-anchor', 'middle');
  label.style.transition = 'all 0.8s ease';
  stratLevel.appendChild(label);

  const positions = [
    { x: 300, y: 85, text: 'Normal ops', regime: 'normal' },
    { x: 300, y: 128, text: 'Approaching boundary...', regime: 'boundary' },
    { x: 300, y: 170, text: 'Emergency regime!', regime: 'emergency' },
    { x: 300, y: 213, text: 'Crossing nullifier...', regime: 'boundary2' },
    { x: 300, y: 255, text: 'Absorbing state', regime: 'absorbing' },
  ];

  let step = 0;
  let intervalId;

  function animateStep() {
    const pos = positions[step];
    dot.setAttribute('cx', pos.x);
    dot.setAttribute('cy', pos.y);
    label.setAttribute('x', pos.x);
    label.setAttribute('y', pos.y - 14);
    label.textContent = pos.text;

    if (pos.regime === 'boundary' || pos.regime === 'boundary2') {
      dot.setAttribute('fill', '#e6ab02');
      dot.setAttribute('r', '8');
    } else if (pos.regime === 'emergency') {
      dot.setAttribute('fill', '#8899aa');
      dot.setAttribute('r', '6');
    } else if (pos.regime === 'absorbing') {
      dot.setAttribute('fill', '#8da0cb');
      dot.setAttribute('r', '5');
    } else {
      dot.setAttribute('fill', '#4dd9c0');
      dot.setAttribute('r', '6');
    }

    step = (step + 1) % positions.length;
  }

  // Start animation when the stratified level becomes visible
  const observer = new MutationObserver(() => {
    if (stratLevel.style.display !== 'none' && stratLevel.classList.contains('active')) {
      if (!intervalId) {
        step = 0;
        animateStep();
        intervalId = setInterval(animateStep, 2000);
      }
    } else {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    }
  });
  observer.observe(stratLevel, { attributes: true, attributeFilter: ['class', 'style'] });
}

/* ==========================================================================
   7. CONCEPT EXPLORATION — Deep content for every chapter
   Adds clickable concept tags + modal with formal definitions.
   ========================================================================== */
function initConceptExploration() {
  /* ---- Concept data: every chapter, 3-5 key concepts each ---- */
  const concepts = {
    1: [
      { name: 'Flatland Problem',
        formal: 'Scalar ethical evaluation projects a multi-dimensional moral situation onto a single real number, losing all directional information.',
        desc: 'Just as a 2D being in Flatland cannot perceive a sphere passing through its plane, scalar ethics cannot perceive the full structure of moral situations. The book identifies three specific failures: AI alignment collapses multi-stakeholder values to a single reward signal, policy analysis reduces complex tradeoffs to cost-benefit ratios, and moral philosophy itself often reduces rich evaluative structure to "good" vs "bad."',
        related: ['Scalar Collapse', 'Moral Manifold'] },
      { name: 'Parable of the Horse',
        formal: 'A narrative demonstrating that moral evaluation requires suspension of judgment across time — the label "good" or "bad" is a premature contraction.',
        desc: 'An old man\'s horse runs away. "Bad luck," say the neighbors. The horse returns with wild horses. "Good luck!" His son breaks his leg riding them. "Bad luck!" The army comes recruiting and passes over the injured son. "Good luck!" Each event\'s moral valence depends on what follows — illustrating why scalar snap-judgments fail.',
        related: ['Tensor Contraction', 'Moral Uncertainty'] },
      { name: 'Geometry as Language',
        formal: 'Moral reasoning has inherent geometric structure: direction (what dimensions matter), magnitude (how much), curvature (context-dependence), and topology (boundaries that cannot be crossed).',
        desc: 'The central claim is not that ethics should be geometrized, but that it already is geometric — we just lack the formal language. When we say a decision "weighs" multiple considerations, "balances" competing interests, or "crosses a line," we are using geometric metaphors for geometric structure.',
        related: ['Moral Manifold', 'Moral Metric'] },
    ],
    2: [
      { name: 'Scalar Collapse',
        formal: 'The projection S = g(O, I) from a rank-(1,1) tensor to a rank-0 scalar, losing directional information. Irreversible: cannot reconstruct O and I from S alone.',
        desc: 'When a utilitarian assigns "utility = 7.3" to a situation, they have contracted a rich tensor structure — which dimensions are satisfied, which are violated, and how they trade off — into a single number. This is exactly analogous to computing a dot product: the result is a scalar that tells you the magnitude of alignment but not which components contributed.',
        related: ['Tensor Hierarchy', 'Moral Residue'] },
      { name: 'Directional Information',
        formal: 'In a 9-dimensional moral space M, a vector O has 9 independent components. Collapsing to a scalar loses 8 degrees of freedom.',
        desc: 'A policy that scores 0.7 overall might achieve this through (High welfare, Low rights, Medium justice) or (Low welfare, High rights, Medium justice). The scalar 0.7 is identical in both cases, but the moral situations are completely different. Directional information is what distinguishes these — and scalar ethics discards it.',
        related: ['Nine Dimensions', 'Obligation Vector'] },
      { name: 'Uncertainty Has Shape',
        formal: 'Moral uncertainty is not a single error bar but an ellipsoid in 9-dimensional space, with different widths along different dimensions.',
        desc: 'When we are uncertain about a moral situation, we are not equally uncertain about everything. We might be very confident about the welfare implications but deeply uncertain about the justice implications. This asymmetric uncertainty is captured by an ellipsoid, not a number — another structure that scalar ethics cannot represent.',
        related: ['Moral Uncertainty', 'Moral Metric'] },
    ],
    3: [
      { name: 'Aristotle as Calibration',
        formal: 'The Aristotelian mean is reinterpreted as selecting a point on a manifold that is neither too close to one boundary nor another — a calibration problem, not a simple average.',
        desc: 'Aristotle\'s doctrine of the mean says courage lies between cowardice and recklessness. In geometric ethics, this is finding the geodesic midpoint between two boundary strata on the moral manifold — a genuinely geometric operation that depends on the local metric.',
        related: ['Moral Metric', 'Whitney Stratification'] },
      { name: 'Kant as Invariance',
        formal: 'The categorical imperative "act only according to that maxim you could will as universal law" is a gauge invariance condition: moral evaluation must be invariant under permutation of agent labels.',
        desc: 'Kant\'s universalizability requirement says the moral status of an action cannot depend on who performs it. In geometric language, this is exactly a symmetry requirement: the moral metric must be invariant under the gauge transformation that relabels agents. This connects to the Bond Invariance Principle (BIP).',
        related: ['BIP Gauge Symmetry', 'Moral Metric'] },
      { name: 'Ross as Vectors',
        formal: 'W.D. Ross\'s prima facie duties (fidelity, reparation, gratitude, justice, beneficence, self-improvement, non-maleficence) are recast as basis vectors in obligation space.',
        desc: 'Ross argued that we have multiple independent duties that can conflict. Geometric ethics formalizes this: each duty is a vector component, and when duties conflict, we need a metric to determine which resultant vector to follow. This is exactly the tensor framework.',
        related: ['Obligation Vector', 'Tensor Hierarchy'] },
      { name: 'Hohfeld as Gauge',
        formal: 'Hohfeld\'s 8 jural positions (right/duty, privilege/no-right, power/liability, immunity/disability) form the octad — pairs linked by correlative and opposite relations forming a D4 dihedral symmetry group.',
        desc: 'Wesley Hohfeld\'s 1917 analysis of legal relations identified 8 fundamental normative positions connected by logical relations. Geometric ethics shows these relations have the symmetry structure of the dihedral group D4, making them amenable to gauge-theoretic treatment.',
        related: ['D4 Symmetry', 'Dear Ethicist Game'] },
    ],
    4: [
      { name: 'Smooth Manifold',
        formal: 'A topological space M that is locally homeomorphic to R^n, equipped with a smooth atlas of coordinate charts. The moral manifold M is 9-dimensional.',
        desc: 'A manifold is a space that looks like flat Euclidean space in any small neighborhood but may have global curvature and topology. The moral manifold is the space of all possible moral situations — each point represents a complete specification of the morally relevant features of a situation.',
        related: ['Moral Manifold', 'Nine Dimensions'] },
      { name: 'Tangent Bundle',
        formal: 'TM = {(p, v) : p in M, v in T_pM}. The union of all tangent spaces. Obligation vectors live in the tangent bundle.',
        desc: 'At each point of the moral manifold, there is a tangent space — the space of all possible "directions" one could move. Obligations are vectors in this tangent space: they have both direction (which moral dimensions are implicated) and magnitude (how strong the obligation is). The tangent bundle collects all these tangent spaces together.',
        related: ['Obligation Vector', 'Parallel Transport'] },
      { name: 'Covector / 1-Form',
        formal: 'An element of the cotangent space T*_pM. A linear functional that maps vectors to scalars: I: T_pM -> R. Interests are covectors.',
        desc: 'While obligations push in a direction (vectors), interests measure the value of moving in a direction (covectors). The interest covector I takes an obligation vector O and returns a scalar S = I(O) — the satisfaction. This vector-covector duality is fundamental to the tensor framework.',
        related: ['Interest Covector', 'Satisfaction Scalar'] },
      { name: 'Fiber Bundle',
        formal: 'A structure (E, B, pi, F) where E is the total space, B is the base space, pi: E -> B is the projection, and F is the fiber. The moral fiber bundle has base M and fiber containing normative positions.',
        desc: 'Each point on the moral manifold has attached to it a "fiber" — additional structure representing the normative positions available at that situation. The BIP gauge symmetry acts on the fiber, and the connection on the fiber bundle determines how normative positions change as we move through moral space.',
        related: ['BIP Gauge Symmetry', 'Moral Connection'] },
    ],
    5: [
      { name: 'Moral Manifold M',
        formal: 'A 9-dimensional smooth manifold whose points represent complete moral situations. Locally modeled on R^9 with the 3x3 derivation: 3 ethical domains (welfare, rights, justice) x 3 relational scales (individual, institutional, societal).',
        desc: 'The moral manifold is the central object of the framework. Each point is a complete moral situation, and nearby points represent situations that differ only slightly. The 9 dimensions come from a systematic derivation: 3 fundamental ethical domains crossed with 3 scales of moral relationship, giving 9 independent coordinates.',
        related: ['Nine Dimensions', 'Three Domains'] },
      { name: 'Nine Dimensions',
        formal: 'Derived from 3x3 scope/mode grid. Scope: individual, relational, institutional. Mode: deontic, evaluative, epistemic. D1: consequences/outcomes, D2: rights/obligations, D3: fairness/justice, D4: autonomy, D5: trust, D6: social/relational impact, D7: identity/dignity/virtue, D8: institutional legitimacy, D9: epistemic status.',
        desc: 'The 9 dimensions arise from crossing three scopes (individual, relational, institutional) with three modes (deontic, evaluative, epistemic). Each dimension captures an independent aspect of moral evaluation. Every moral state is encoded as an attribute vector a(v) in R^9, scoring all nine dimensions simultaneously.',
        related: ['Moral Manifold', 'Dimension Wheel'] },
      { name: 'Admissible Transformations',
        formal: 'Coordinate changes phi: U -> R^9 that preserve the smooth structure and moral content. Not all reparametrizations are admissible — only those preserving dimensional independence.',
        desc: 'You can relabel the coordinates of the moral manifold (e.g., reorder the dimensions), but not all relabelings are meaningful. Admissible transformations are those that preserve the moral structure — they are the diffeomorphisms that respect the separation of domains and scales.',
        related: ['Moral Manifold', 'BIP Gauge Symmetry'] },
      { name: 'Moral Singularities',
        formal: 'Points where the moral metric degenerates (det(g) = 0) or the manifold structure breaks down. Correspond to situations where moral reasoning itself fails.',
        desc: 'Some moral situations are genuinely singular — the framework does not pretend to resolve them. These include true moral dilemmas (where the metric becomes degenerate), situations of radical incommensurability, and boundary cases where the manifold structure breaks down. Recognizing singularities is a feature, not a bug.',
        related: ['Moral Metric', 'Whitney Stratification'] },
    ],
    6: [
      { name: 'Tensor Hierarchy',
        formal: 'Level 0: Scalar S in R. Level 1: Covector I in T*M. Level 2: Vector O in TM. Level 3: Metric g in T*M tensor T*M. Level 4: Full moral tensor T in TM tensor T*M. Level 5: Stratified tensor on Whitney-stratified M.',
        desc: 'The tensor hierarchy is the central organizational structure. At each level, more information is preserved. A scalar gives only magnitude. A covector gives magnitude and sensitivity to direction. A vector gives direction and magnitude. The metric gives distances and angles. The full tensor gives the complete moral structure.',
        related: ['Scalar Collapse', 'Moral Metric'] },
      { name: 'Obligation Vector O',
        formal: 'O in T_pM. A tangent vector at point p in the moral manifold. Components O^i represent the strength and direction of obligation along each of the 9 moral dimensions.',
        desc: 'An obligation is not a single number but a vector — it has components in each of the 9 dimensions. "You should help this person" might decompose into strong individual welfare (O^1 = 0.9), moderate rights respect (O^2 = 0.5), and varying institutional components. The full vector captures what a scalar "obligation score" cannot.',
        related: ['Tangent Bundle', 'Satisfaction Scalar'] },
      { name: 'Interest Covector I',
        formal: 'I in T*_pM. A cotangent vector (1-form) at point p. Components I_j represent how much a stakeholder\'s interests are affected along each moral dimension.',
        desc: 'Interests are dual to obligations — they are the "measuring instruments" that evaluate how well obligations are fulfilled. An interest covector assigns a weight to each dimension: how much does this stakeholder care about welfare vs. rights vs. justice? The pairing I(O) = I_j O^j gives the satisfaction scalar.',
        related: ['Obligation Vector', 'Satisfaction Scalar'] },
      { name: 'Satisfaction Scalar',
        formal: 'S = g(O, I) = g_ij O^i I^j. The contraction of obligation vector with interest covector using the moral metric. The unique rank-0 invariant of the framework.',
        desc: 'When you contract the obligation vector with the interest covector using the moral metric, you get a single number: the satisfaction. This is the moment of decision — but unlike starting with a scalar, you arrive at the scalar with full knowledge of what was lost in the contraction. The scalar is the last step, not the first.',
        related: ['Tensor Hierarchy', 'Moral Residue'] },
      { name: 'Moral Metric g',
        formal: 'g: TM x TM -> R. A symmetric, positive-definite (0,2)-tensor field on M that defines distances, angles, and the inner product between moral vectors.',
        desc: 'The moral metric determines how to measure "distances" in moral space — how different two moral situations are, how much effort it takes to move from one to another. Different ethical traditions correspond to different metrics: a utilitarian metric weights welfare dimensions heavily; a deontological metric weights rights dimensions.',
        related: ['Geodesic', 'Moral Connection'] },
    ],
    7: [
      { name: 'One Case Five Levels',
        formal: 'A single medical allocation case (distributing a scarce treatment among patients) is analyzed at each of the 6 tensor levels, demonstrating what each level reveals that lower levels cannot.',
        desc: 'The same case is analyzed as: (0) a simple good/bad judgment, (1) a weighted evaluation showing which interests are at stake, (2) a directed obligation showing what must be done, (3) a metric-aware analysis showing how dimensions trade off, (4) a full tensor revealing the complete moral structure, (5) a stratified analysis showing boundary effects.',
        related: ['Tensor Hierarchy', 'Scalar Collapse'] },
      { name: 'Six Claims',
        formal: 'Six specific claims that require tensor structure to express: (1) direction matters, (2) obligations and interests are distinct, (3) tradeoffs are metric-dependent, (4) context changes the calculation, (5) boundaries exist, (6) path matters.',
        desc: 'The chapter presents six concrete claims about the medical allocation case that cannot be expressed in scalar ethics. Each claim requires at minimum a specific tensor level, providing a constructive argument for why the full hierarchy is needed.',
        related: ['Tensor Hierarchy', 'Moral Residue'] },
    ],
    8: [
      { name: 'Whitney Stratification',
        formal: 'A decomposition of M into smooth strata S_alpha satisfying Whitney\'s conditions A and B, ensuring well-behaved boundary geometry. M = union S_alpha with dim(S_alpha) varying.',
        desc: 'Not all of moral space is smooth — there are boundaries between moral regimes (e.g., the line between "acceptable risk" and "negligence"). Whitney stratification provides the mathematical framework for these boundaries, ensuring they are well-behaved: you can approach them smoothly, and the geometry near them is controlled.',
        related: ['Moral Boundaries', 'Phase Transitions'] },
      { name: 'Moral Boundaries',
        formal: 'Codimension-1 strata in M where the moral regime changes. Include: thresholds (gradual), phase transitions (abrupt), absorbing strata (irreversible), forbidden regions (inaccessible).',
        desc: 'Moral space has genuine boundaries — lines that, once crossed, change the moral regime. Some are gradual (increasing risk becomes negligence), some are abrupt (phase transitions like the moment consent is violated), and some are irreversible (absorbing strata like taking a life — you cannot "uncross" that boundary).',
        related: ['Whitney Stratification', 'Absorbing Strata'] },
      { name: 'Absorbing Strata',
        formal: 'A stratum S_abs such that once a trajectory enters S_abs, it cannot exit: for any geodesic gamma with gamma(t_0) in S_abs, gamma(t) in S_abs for all t > t_0.',
        desc: 'Some moral boundaries are one-way: once you cross them, you cannot return. Taking a human life, breaking a sacred trust, or causing irreversible environmental damage — these are absorbing strata. The framework formally captures the intuition that some moral actions are irreversible, regardless of later compensation.',
        related: ['Moral Boundaries', 'Stratification Crossing'] },
      { name: 'Semantic Gates',
        formal: 'Points on a boundary stratum where the vocabulary changes — the semantic frame shifts as one crosses from one moral regime to another.',
        desc: 'When you cross from "business competition" to "exploitation," the very words used to describe the situation change. Semantic gates formalize this: they are points where the descriptive vocabulary undergoes a discontinuous shift, reflecting a genuine change in moral regime.',
        related: ['Phase Transitions', 'Moral Boundaries'] },
    ],
    9: [
      { name: 'Origin of the Metric',
        formal: 'Four accounts of where the moral metric comes from: (1) Realist — discovered in moral reality, (2) Constructivist — built through rational agreement, (3) Expressivist — reflects attitudes, (4) Governance — a policy tool.',
        desc: 'The framework is meta-ethical pluralist about the origin of the metric. It works regardless of whether you think the metric is discovered (moral realism), constructed (Rawlsian contractualism), expressed (Blackburn), or governed (pragmatism). This is a deliberate design choice: the geometric structure is compatible with multiple meta-ethical positions.',
        related: ['Moral Metric', 'Meta-Metric'] },
      { name: 'Admissible Metrics',
        formal: 'Constraints: (1) symmetry g(u,v) = g(v,u), (2) positive-definiteness g(v,v) > 0 for v != 0, (3) smoothness, (4) BIP invariance, (5) dimensional independence. Not all metrics are morally meaningful.',
        desc: 'Not any metric will do. The framework places constraints on what counts as an admissible moral metric: it must be symmetric (the distance from A to B equals B to A), positive-definite (all directions have positive "cost"), smooth (small changes in situation produce small changes in evaluation), and BIP-invariant.',
        related: ['Moral Metric', 'BIP Gauge Symmetry'] },
      { name: 'Meta-Metric',
        formal: 'A higher-order metric on the space of admissible metrics. Measures the "distance" between ethical frameworks. Enables pluralism without relativism.',
        desc: 'Different ethical traditions correspond to different metrics. The meta-metric measures how far apart two ethical frameworks are — not in terms of conclusions, but in terms of the structure they impose on moral space. Two frameworks that agree on most cases but disagree on edge cases are "close" in meta-metric terms.',
        related: ['Origin of the Metric', 'Moral Pluralism'] },
    ],
    10: [
      { name: 'Moral Connection',
        formal: 'A connection nabla on TM compatible with the moral metric: nabla_X g = 0. Determines how to parallel-transport obligation vectors along paths in M.',
        desc: 'A connection tells you how to compare vectors at different points. In moral terms: if you have an obligation "here" and move to a different moral situation "there," how does the obligation change? The moral connection formalizes the intuition that context changes the calculation — the same duty looks different in different circumstances.',
        related: ['Parallel Transport', 'Holonomy'] },
      { name: 'Parallel Transport',
        formal: 'Given a curve gamma in M and a vector O at gamma(0), parallel transport produces O(t) at gamma(t) satisfying nabla_{gamma\'} O = 0. The obligation is "held constant" along the path.',
        desc: 'Parallel transport carries an obligation vector along a path while "keeping it as constant as possible." On a curved manifold, the result depends on the path — transporting an obligation through different moral contexts yields different final obligations. This is moral holonomy.',
        related: ['Moral Connection', 'Holonomy'] },
      { name: 'Holonomy',
        formal: 'The failure of parallel transport around a closed loop to return to the starting vector: Hol(gamma) = P_{gamma} - Id != 0 iff curvature != 0.',
        desc: 'If you transport an obligation around a closed loop in moral space — going through a sequence of moral situations and returning to the start — the obligation may have rotated. This rotation (holonomy) measures the path-dependence of moral reasoning: the order in which you consider moral factors changes the conclusion.',
        related: ['Parallel Transport', 'Curvature'] },
      { name: 'Geodesic',
        formal: 'A curve gamma in M satisfying the geodesic equation: nabla_{gamma\'} gamma\' = 0. The "straightest possible path" — the path of least moral resistance.',
        desc: 'Geodesics are the paths in moral space that are "locally optimal" — at each point, they go in the straightest possible direction given the curvature. A geodesic between two moral situations represents the morally smoothest transition. Different metrics yield different geodesics — what is "straight" depends on the ethical framework.',
        related: ['Moral Metric', 'A* Pathfinding'] },
    ],
    11: [
      { name: 'A* on Moral Manifold',
        formal: 'A* search with f(n) = g(n) + h(n), where g(n) is path cost (accumulated moral cost) and h(n) is the heuristic (estimated remaining cost). Applied to the discretized moral manifold.',
        desc: 'A* is a pathfinding algorithm that finds the optimal path by balancing known costs with estimated future costs. On the moral manifold, this models practical moral reasoning: g(n) represents the moral costs already incurred, and h(n) is our best estimate of the remaining moral cost to reach the goal state.',
        related: ['Geodesic', 'Moral Heuristics'] },
      { name: 'Moral Heuristics',
        formal: 'The heuristic function h(n) in A* search. Obligation vectors serve as heuristic functions, providing direction toward the goal. Deontological rules are pre-compiled heuristics.',
        desc: 'Deontological rules ("don\'t lie," "keep promises") are reinterpreted as pre-compiled heuristic functions for moral search. They provide quick, generally reliable estimates of which direction to go, without requiring full computation of the optimal path. This reconciles deontology and consequentialism as complementary search strategies.',
        related: ['A* on Moral Manifold', 'Obligation Vector'] },
      { name: 'Computational Intractability',
        formal: 'Exact moral reasoning on a 9-dimensional stratified manifold with a non-trivial metric is computationally intractable in general (NP-hard for discretized versions).',
        desc: 'Perfect moral reasoning — finding the truly optimal path through moral space considering all 9 dimensions, all boundaries, and all curvature effects — is computationally intractable. This is not a flaw but a theorem: it explains why moral reasoning is hard, why we need heuristics, and why reasonable people can disagree.',
        related: ['A* on Moral Manifold', 'Moral Heuristics'] },
    ],
    12: [
      { name: 'Bond Invariance Principle',
        formal: 'BIP: The moral evaluation of an action must be invariant under re-description of agents. Formally, a gauge symmetry: if phi is an agent-relabeling diffeomorphism, then S(phi(O), phi(I)) = S(O, I).',
        desc: 'The BIP states that the moral status of an action cannot change merely because we relabel the agents involved. "It\'s wrong when they do it but fine when we do it" violates BIP. This is formalized as a gauge symmetry — the same kind of symmetry that generates conservation laws in physics via Noether\'s theorem.',
        related: ['Noether for Ethics', 'Conservation of Harm'] },
      { name: "Noether's Theorem for Ethics",
        formal: 'If the moral Lagrangian L is invariant under a continuous symmetry (the BIP), then there exists a conserved current — the total harm H is conserved along any moral trajectory.',
        desc: 'Emmy Noether proved that every continuous symmetry of a physical system implies a conservation law (time invariance gives energy conservation, etc.). Applied to ethics: BIP symmetry implies that total harm is conserved. You cannot destroy harm by redescription, euphemism, or redistribution — you can only move it.',
        related: ['Bond Invariance Principle', 'Conservation of Harm'] },
      { name: 'Conservation of Harm',
        formal: 'dH/dt = 0 along any trajectory in M that preserves BIP. Total harm is a conserved quantity: it cannot be created or destroyed, only redistributed among dimensions and agents.',
        desc: 'The central result of the chapter. Harm is conserved like energy: euphemism does not reduce it (calling "torture" an "enhanced interrogation technique" changes nothing), re-description cannot redistribute it (calling pollution "externalities" does not make it disappear), and moral debt persists until discharged.',
        related: ["Noether's Theorem for Ethics", 'Four Consequences'] },
      { name: 'Four Consequences',
        formal: '(1) Euphemism does not reduce harm. (2) Harm is auditable. (3) Re-description cannot redistribute harm. (4) Moral debt persists until discharged.',
        desc: 'Four testable consequences of harm conservation: (1) Renaming harm does not reduce it, (2) Total harm along any trajectory can be computed and audited, (3) Moving harm between categories or agents does not reduce the total, (4) Deferred harm accumulates interest — you cannot escape it by ignoring it.',
        related: ['Conservation of Harm', 'Moral Debt'] },
      { name: 'D4 x U(1) Gauge Group',
        formal: 'The full gauge group of BIP is G = D4 x U(1)^H, where D4 is the dihedral group capturing Hohfeldian correlative/opposite symmetries and U(1)^H is the continuous phase invariance for each Hohfeldian position.',
        desc: 'The BIP gauge group has two parts. The discrete D4 component captures the 8-element symmetry of Hohfeldian positions (correlatives and opposites of the four pairs). The continuous U(1) captures phase invariance. This was revised from SU(2) after empirical CHSH experiments — a concrete example of the framework being corrected by data.',
        related: ['Bond Invariance Principle', 'Hohfeld as Gauge'] },
    ],
    13: [
      { name: 'Moral Superposition',
        formal: '|psi> = sum_i c_i |phi_i>, where |phi_i> are definite moral states and c_i are complex amplitudes. Before a decision is made, moral evaluation exists in superposition.',
        desc: 'Before a moral decision is made, the evaluation may genuinely exist in a superposition of states — not because we are ignorant, but because the moral fact itself is indeterminate. Deliberation is the process of preparing a measurement that will collapse this superposition to a definite moral state.',
        related: ['Moral Measurement', 'Interference'] },
      { name: 'Moral Measurement',
        formal: 'An observable A acting on the moral state |psi>. Measurement collapses the superposition: |psi> -> |phi_i> with probability |c_i|^2. The act of moral judgment is itself a measurement.',
        desc: 'Just as a quantum measurement collapses a superposition, making a moral judgment collapses moral superposition into a definite evaluation. This is not mere analogy — the mathematics is identical, and it explains why "looking at" a moral situation from different angles can yield genuinely different, incompatible evaluations.',
        related: ['Moral Superposition', 'Density Matrix'] },
      { name: 'Moral Interference',
        formal: 'When two moral framings are considered simultaneously, their amplitudes can constructively or destructively interfere, yielding probabilities that differ from the sum of individual probabilities.',
        desc: 'If you evaluate a situation from a utilitarian frame and a deontological frame separately, and then consider both simultaneously, the result is not simply the average. The framings can interfere — sometimes reinforcing (constructive interference) and sometimes canceling (destructive interference). This matches observed phenomena in moral psychology.',
        related: ['Moral Superposition', 'CHSH Inequality'] },
      { name: 'CHSH Inequality',
        formal: '|<A1*B1> + <A1*B2> + <A2*B1> - <A2*B2>| <= 2 classically. Violation (S > 2) indicates genuinely non-classical moral correlations.',
        desc: 'The CHSH (Clauser-Horne-Shimony-Holt) inequality is the key test: if moral reasoning is classical, correlations between different framings of the same situation are bounded by S <= 2. Violation indicates that moral cognition has genuinely quantum-like structure. The Dear Ethicist game is designed to test this empirically.',
        related: ['Bell Test', 'Dear Ethicist Game'] },
    ],
    14: [
      { name: 'Collective Moral Agency',
        formal: 'A collective agent A_coll with moral tensor T_coll that is not simply the sum of individual tensors: T_coll != sum_i T_i. Emergence: the collective has moral properties individuals lack.',
        desc: 'A corporation, a government, or an AI system can be a moral agent in its own right, with obligations and responsibilities that cannot be reduced to those of its individual members. The collective moral tensor captures emergent moral properties — the "character" of the institution that exceeds the sum of its parts.',
        related: ['Distributed Responsibility', 'AI as Collective'] },
      { name: 'Distributed Responsibility',
        formal: 'R_total = R_coll + sum_i R_i + R_residual, where R_residual is the responsibility gap: responsibility that belongs to the collective but cannot be assigned to any individual.',
        desc: 'In many institutional failures (financial crises, environmental disasters), no single individual bears full responsibility, yet the collective clearly does. The responsibility gap R_residual is a formal measure of this — the moral responsibility that exists at the collective level but cannot be decomposed into individual shares.',
        related: ['Collective Moral Agency', 'Moral Residue'] },
      { name: 'AI as Collective Agent',
        formal: 'An AI system with training data from N humans acts as a collective agent whose moral tensor aggregates the moral dispositions of its training distribution, potentially inheriting biases as dimensional distortions.',
        desc: 'Large language models aggregate the moral dispositions of millions of humans in their training data. This makes them collective moral agents in the geometric ethics sense — with emergent moral properties (including biases) that may not be traceable to any individual training example. Alignment is then a problem of collective moral agency.',
        related: ['Collective Moral Agency', 'AI Alignment'] },
    ],
    15: [
      { name: 'Moment of Contraction',
        formal: 'The map C: T^(1,1)M -> R, T^i_j -> S = T^i_j delta^j_i. The irreversible collapse from full tensor to scalar at the moment of decision.',
        desc: 'Every moral decision requires an eventual contraction — you must actually choose, and choosing means projecting the full tensor structure down to a scalar (yes/no, do/don\'t). The framework does not eliminate this moment but ensures you arrive at it with full awareness of what is being lost.',
        related: ['Scalar Collapse', 'Moral Residue'] },
      { name: 'Moral Residue',
        formal: 'R = T - S * (T/S). The tensor components lost in contraction. Even the "right" decision leaves residue — the moral weight of dimensions that were contracted away.',
        desc: 'When you make a decision, the dimensions you did not optimize for do not disappear. A doctor who triages correctly still carries the moral weight of the patients who waited. This residue is not guilt or failure — it is a mathematical fact about contraction. It explains moral distress even after correct decisions.',
        related: ['Moment of Contraction', 'Moral Injury'] },
      { name: 'Non-Commutativity',
        formal: 'In general, contracting first along dimension i then along j gives a different result than contracting first along j then along i: C_i(C_j(T)) != C_j(C_i(T)).',
        desc: 'The order in which you consider moral dimensions matters. Deciding about welfare first and then rights can yield a different outcome than deciding about rights first and then welfare. This non-commutativity is not a flaw but a structural feature of multi-dimensional moral reasoning.',
        related: ['Moment of Contraction', 'Holonomy'] },
      { name: 'Scalar Irrecoverability',
        formal: 'Theorem 15.1: Any continuous function f: R^n -> R (n >= 2) is non-injective. The information destroyed by projecting the moral tensor to a scalar is mathematically irrecoverable.',
        desc: 'This is the mathematical proof that scalar ethics is fundamentally inadequate. No continuous function from R^9 to R is one-to-one — infinitely many distinct moral tensors map to the same scalar value. No post-hoc analysis, no additional scalar, no clever encoding can recover what the projection destroys. The loss is provably permanent.',
        related: ['Scalar Collapse', 'Moment of Contraction'] },
    ],
    16: [
      { name: 'Three Types of Uncertainty',
        formal: '(1) Empirical uncertainty: uncertainty about facts. (2) Moral uncertainty: uncertainty about values. (3) Structural uncertainty: uncertainty about the framework itself.',
        desc: 'The framework distinguishes three fundamentally different types of uncertainty. Empirical uncertainty (what will happen?) is handled by probability theory. Moral uncertainty (which dimensions matter most?) is handled by the meta-metric. Structural uncertainty (is the framework itself correct?) is handled by the modesty conditions.',
        related: ['Moral Uncertainty', 'Meta-Metric'] },
      { name: 'Robust Obligations',
        formal: 'An obligation O is robust if it remains in the same half-space of TM for all admissible metrics g in G: for all g in G, g(O, n) > 0, where n is the boundary normal.',
        desc: 'Some obligations are robust — they hold regardless of which specific metric you use, as long as the metric is admissible. "Don\'t torture innocents" is robust because it points in the same direction under any reasonable moral metric. Identifying robust obligations is practically important for policy and AI alignment.',
        related: ['Admissible Metrics', 'Moral Uncertainty'] },
      { name: 'Residual Indeterminacy',
        formal: 'For some situations p in M, there exist admissible metrics g1, g2 such that the optimal actions under g1 and g2 are different. The framework correctly identifies these as genuinely indeterminate.',
        desc: 'The framework does not always yield a determinate answer, and this is by design. Some moral situations are genuinely indeterminate — reasonable frameworks disagree, and no amount of additional information resolves the disagreement. The framework formally identifies these cases rather than pretending to resolve them.',
        related: ['Moral Uncertainty', 'Three Types of Uncertainty'] },
    ],
    17: [
      { name: 'Dear Abby Corpus',
        formal: 'Analysis of 2,847 Dear Abby advice columns, coded for Hohfeldian positions and dimensional structure. Finds that natural moral reasoning uses tensor structure, not scalar evaluation.',
        desc: 'The Dear Abby corpus analysis examines real-world moral reasoning in advice columns. The coding reveals that people naturally reason in tensor terms — they distinguish between different dimensions (welfare, rights, justice) and different relational scales — even when they lack the formal vocabulary for it.',
        related: ['Hohfeld as Gauge', 'Bond Index'] },
      { name: 'Dear Ethicist Game',
        formal: 'An interactive experiment measuring Hohfeldian position correlations. Players assign normative positions to ethical dilemmas. CHSH correlations test whether moral reasoning violates classical bounds.',
        desc: 'The Dear Ethicist game is the primary empirical instrument. Players read ethical scenarios and assign Hohfeldian positions (Obligation, Claim, Liberty, No-right). The correlations between different framings of the same scenario can be used to compute the CHSH S-value and test whether moral cognition is genuinely non-classical.',
        related: ['CHSH Inequality', 'Bond Index'] },
      { name: 'Bond Index',
        formal: 'BI = (N_match - N_mismatch) / N_total, measuring the correlation between pairs of Hohfeldian assignments. Under D4 symmetry, correlative pairs should show BI close to 1.',
        desc: 'The Bond Index measures how well a respondent\'s moral judgments respect the correlative symmetry of Hohfeldian positions. A perfect score means every obligation has a matching claim, every liberty a matching no-right. The aggregate BI across many respondents tests whether moral reasoning has the D4 symmetry structure predicted by the framework.',
        related: ['Dear Ethicist Game', 'D4 Symmetry'] },
      { name: 'Cross-Lingual BIP',
        formal: 'BIP v10.16 experiments: 20,030 moral texts across 11 languages tested for deontic structure transfer. The obligation-permission axis transfers at 100% (model-mediated). Structural-to-surface ratio: 11.1x.',
        desc: 'The framework\'s dimensional structure predicts moral judgments 11.1 times better than surface linguistic features across 11 languages, confirming that the structure is real, not an artifact of English moral vocabulary. This cross-lingual invariance is strong evidence for the universality of the moral manifold.',
        related: ['Bond Invariance Principle', 'Nine Dimensions'] },
    ],
    18: [
      { name: 'Tensor-Valued Objectives',
        formal: 'Replace scalar reward R in R with tensor reward T in T^(1,1)M. The AI optimizes a tensor-valued objective, preserving directional information.',
        desc: 'Standard AI alignment gives the system a scalar reward to maximize. Geometric ethics says: give it a tensor-valued objective instead. The AI should not optimize a single number but maintain awareness of all 9 moral dimensions simultaneously, only contracting to a scalar at the moment of irreversible action.',
        related: ['Scalar Collapse', 'AI Alignment'] },
      { name: 'No Escape Theorem',
        formal: 'Theorem: For any AI system with a scalar objective function, there exists a moral situation in which the system necessarily violates at least one moral dimension. Scalar objectives are provably insufficient for alignment.',
        desc: 'The No Escape Theorem proves that scalar-objective AI systems will inevitably fail morally: any scalar objective can be Goodharted, any single-number reward can be gamed at the expense of unmeasured dimensions. This provides a formal argument for tensor-valued objectives in AI alignment.',
        related: ['Tensor-Valued Objectives', 'AI Alignment'] },
      { name: 'Alignment as Geodesic',
        formal: 'AI alignment is the problem of ensuring that the AI\'s trajectory through moral space follows a geodesic (or near-geodesic) path that respects all moral boundaries.',
        desc: 'Alignment is reframed geometrically: the AI should follow the geodesic — the path of minimal moral cost — while respecting all boundary strata (ethical red lines). Misalignment is a failure to follow the geodesic, either by ignoring dimensions (scalar collapse) or by crossing boundaries (boundary violation).',
        related: ['Geodesic', 'Moral Boundaries'] },
    ],
    19: [
      { name: 'ErisML',
        formal: 'Ethical Reasoning Integration and Specification Modeling Language. A domain-specific language for specifying moral situations, obligations, interests, metrics, and boundary conditions in geometric ethics terms.',
        desc: 'ErisML is the software implementation of geometric ethics — a modeling language that lets you specify moral situations formally. You define the manifold coordinates, the obligation vectors, the interest covectors, the metric, and the boundary conditions, and ErisML computes geodesics, checks boundary crossings, and evaluates satisfaction.',
        related: ['DEME Architecture', 'Norm Kernel'] },
      { name: 'DEME Architecture',
        formal: 'Decision Ethics Moral Engine. A four-layer architecture: (1) Fact Layer (empirical data), (2) Norm Layer (moral specifications in ErisML), (3) Compute Layer (geometric computations), (4) Decision Layer (contraction to action).',
        desc: 'DEME is the ethics engine — the computational system that evaluates moral situations. It separates facts from norms (the separation principle), computes geometric quantities on the moral manifold, and presents the full tensor structure to the decision-maker before contraction. It is designed for integration into AI systems.',
        related: ['ErisML', 'Separation Principle'] },
      { name: 'Norm Kernel',
        formal: 'The minimal, formally verified core of DEME that computes the moral metric, checks boundary conditions, and evaluates satisfaction. Designed for formal verification and audit.',
        desc: 'The Norm Kernel is the security-critical core of DEME — the minimal code path that must be trusted. It computes the metric, checks boundaries, and evaluates contraction. It is designed to be small enough for formal verification, ensuring that the moral computations are correct.',
        related: ['DEME Architecture', 'Bond Index'] },
      { name: 'Separation Principle',
        formal: 'Facts and norms must be maintained in separate layers with explicit interfaces. No empirical fact can entail a normative conclusion without passing through the norm layer (formalized Hume\'s guillotine).',
        desc: 'The separation principle enforces Hume\'s is/ought distinction architecturally: the fact layer cannot directly produce moral conclusions. All moral evaluation passes through the norm layer, where the metric, boundary conditions, and obligations are specified. This prevents the naturalistic fallacy at the system level.',
        related: ['DEME Architecture', 'ErisML'] },
    ],
    20: [
      { name: 'Bond Geodesic Equilibrium',
        formal: 'A market equilibrium where all agents follow geodesics on the economic-moral manifold. Generalizes Nash equilibrium to tensor-valued payoffs on stratified spaces.',
        desc: 'Standard game theory computes Nash equilibria using scalar payoffs. The Bond Geodesic Equilibrium uses tensor-valued payoffs on a moral manifold with boundaries, yielding richer equilibrium concepts. Some Nash equilibria are not geodesic equilibria (they cut corners across moral boundaries) and vice versa.',
        related: ['Geodesic', 'Game Theory'] },
      { name: '2008 Crisis as Manifold Failure',
        formal: 'The 2008 financial crisis reinterpreted as a cascading failure of the economic manifold: boundary crossings (CDO mislabeling), dimensional collapse (rating agency scalar scores), and metric failure (correlation breakdown).',
        desc: 'The financial crisis exemplifies every pathology the framework identifies. Rating agencies collapsed multi-dimensional risk to scalar scores (AAA ratings). CDO structuring crossed moral boundaries (mislabeling risk). And the assumed metric (Gaussian copula) failed catastrophically when correlations broke down — a metric failure.',
        related: ['Scalar Collapse', 'Moral Boundaries'] },
      { name: 'Prospect Theory',
        formal: 'Kahneman-Tversky prospect theory reinterpreted as a curvature effect on the moral manifold: the value function v(x) reflects the local curvature of the metric near a reference point.',
        desc: 'Loss aversion — the empirical finding that losses loom larger than gains — is reinterpreted as a curvature effect. The moral metric has higher curvature in the "loss" region than in the "gain" region, making small movements more costly near losses. This connects behavioral economics to the geometric framework.',
        related: ['Moral Metric', 'Curvature'] },
    ],
    21: [
      { name: 'Clinical Geodesic',
        formal: 'The optimal treatment path through the clinical moral manifold, respecting all boundary strata (consent boundaries, triage thresholds, resource constraints).',
        desc: 'In clinical ethics, the geodesic represents the morally optimal treatment trajectory — balancing patient welfare, autonomy (rights), and fair resource allocation (justice). Triage is explicit boundary-crossing: moving a patient from "treatable" to "expectant" crosses a boundary stratum.',
        related: ['Geodesic', 'Moral Boundaries'] },
      { name: 'QALY Irrecoverability',
        formal: 'Theorem: The Quality-Adjusted Life Year (QALY) is an irreversible scalar contraction of a tensor-valued health evaluation. Information lost in QALY computation cannot be recovered.',
        desc: 'QALYs collapse the multi-dimensional quality of life (mobility, cognition, pain, social function, emotional health) into a single number. The QALY Irrecoverability Theorem proves that two patients with identical QALYs can have completely different quality profiles — and no amount of additional QALY data resolves this.',
        related: ['Scalar Collapse', 'Tensor Hierarchy'] },
      { name: 'Geometric Informed Consent',
        formal: 'Informed consent as a boundary condition on the clinical manifold: the patient must be in the "informed" stratum before the treatment geodesic can proceed across the "consent" boundary.',
        desc: 'Informed consent is formalized as a boundary condition: the treatment path cannot cross the consent boundary unless the patient is in the "informed" stratum. This captures the idea that consent without information is not genuine consent — it is a violation of the boundary protocol.',
        related: ['Moral Boundaries', 'Semantic Gates'] },
      { name: 'Moral Injury',
        formal: 'Damage to an agent\'s moral manifold: the metric becomes distorted, geodesics become unreliable, and parallel transport develops pathological holonomy.',
        desc: 'Moral injury — the psychological damage from being forced to act against one\'s moral convictions — is formalized as manifold damage. The moral metric becomes distorted, making moral reasoning unreliable. This connects to PTSD in healthcare workers and the concept of moral residue from contraction.',
        related: ['Moral Residue', 'Moral Metric'] },
    ],
    22: [
      { name: 'Law as Geometry',
        formal: 'Legal systems as geometric structures on a normative manifold: statutes define boundary strata, precedent defines the metric, and legal reasoning is pathfinding.',
        desc: 'The law has natural geometric structure. Statutes create boundaries in legal space (this side is legal, that side is illegal). Precedent establishes the metric (how similar two cases are). Legal reasoning is pathfinding: given the current situation, what is the optimal path to a just resolution, respecting all boundary constraints?',
        related: ['A* on Moral Manifold', 'Whitney Stratification'] },
      { name: 'Hohfeldian Octad',
        formal: 'The 8 Hohfeldian positions (right, duty, privilege, no-right, power, liability, immunity, disability) organized by correlative and opposite relations with D4 dihedral symmetry.',
        desc: 'Hohfeld\'s 8 jural positions form a beautiful algebraic structure. Rights correlate with duties, privileges with no-rights, powers with liabilities, immunities with disabilities. The correlative and opposite relations generate a D4 symmetry group — the same group that describes the symmetries of a square.',
        related: ['D4 Symmetry', 'Gauge Theory'] },
      { name: 'Topological Constitutionality',
        formal: 'A constitution defines the topology of the legal manifold: which regions are connected, which boundaries are impassable, and what the fundamental group is. Constitutional amendment changes the topology.',
        desc: 'A constitution is not just a law — it defines the shape of legal space itself. Some legal paths are topologically forbidden (unconstitutional), not merely costly. Constitutional amendment is a topological change: it changes which paths are possible, not just which paths are optimal.',
        related: ['Whitney Stratification', 'Absorbing Strata'] },
    ],
    23: [
      { name: 'Market Microstructure',
        formal: 'Financial markets as a decision manifold with high-frequency dynamics. Order flow defines a vector field, the bid-ask spread is a metric property, and arbitrage is a geodesic.',
        desc: 'Financial markets map naturally onto the decision manifold. The bid-ask spread measures the "distance" between buying and selling — a metric property. Arbitrage is a geodesic (the shortest path to profit). Market-making is parallel transport of prices across the manifold.',
        related: ['Moral Manifold', 'Geodesic'] },
      { name: 'Flash Crash as Collapse',
        formal: 'The 2010 flash crash reinterpreted as a dimensional collapse: algorithmic trading collapsed the multi-dimensional market state to a single dimension (price), creating a singularity.',
        desc: 'The 2010 flash crash, where the Dow dropped 1000 points in minutes, is analyzed as a dimensional collapse. High-frequency algorithms reduced the multi-dimensional market state (liquidity, volatility, sentiment, fundamentals) to a single dimension (price), creating a singularity where the metric degenerated.',
        related: ['Scalar Collapse', 'Moral Singularities'] },
      { name: 'Option Pricing as Projection',
        formal: 'Black-Scholes option pricing is a scalar projection of a tensor-valued risk evaluation. The model\'s failures (volatility smile, fat tails) reflect the information lost in projection.',
        desc: 'The Black-Scholes formula reduces multi-dimensional risk to a single price — a scalar projection. Its well-known failures (the volatility smile, failure during crises) are exactly the pathologies predicted by the framework: scalar collapse loses directional risk information.',
        related: ['Scalar Collapse', 'Moral Metric'] },
    ],
    24: [
      { name: 'Euthyphro as Gauge',
        formal: 'The Euthyphro dilemma ("Is the good loved by the gods because it is good, or is it good because it is loved by the gods?") is a gauge ambiguity: the question asks whether the metric is given or chosen.',
        desc: 'Plato\'s ancient dilemma dissolves in geometric terms. "Is the good good because God commands it?" asks whether the moral metric is discovered (realism) or decreed (divine command theory). In gauge theory, this is a choice of gauge — and the physical/moral content is invariant under the choice. The dilemma is a gauge artifact.',
        related: ['Origin of the Metric', 'BIP Gauge Symmetry'] },
      { name: 'Theodicy as Projection',
        formal: 'The problem of evil (why does a good God allow suffering?) reinterpreted as a dimensional projection error: projecting the full 9D moral evaluation to a single "good/evil" dimension loses the structure that might resolve the problem.',
        desc: 'The problem of evil may be a problem of dimensional projection. When we ask "why does God allow evil?", we are projecting a 9-dimensional moral evaluation onto a single good/evil axis. The full tensor evaluation might show that what looks like "evil" in one dimension is compensated by structure in other dimensions — but we cannot see this through scalar lenses.',
        related: ['Scalar Collapse', 'Nine Dimensions'] },
      { name: 'Genesis 3:22',
        formal: '"And the LORD God said, Behold, the man is become as one of us, knowing good and evil." Reinterpreted as the acquisition of the moral metric — the ability to measure distances in moral space.',
        desc: 'The Genesis account of the Fall is reinterpreted: eating from the Tree of Knowledge of Good and Evil is acquiring the moral metric. Before the Fall, humans existed on the manifold but could not measure distances. After the Fall, they have the metric — and with it, the awareness of moral structure (and the burden of contraction).',
        related: ['Moral Metric', 'Origin of the Metric'] },
    ],
    25: [
      { name: 'Intergenerational Obligation',
        formal: 'Obligation vectors that extend across time: O(t, t\') in TM(t) connecting present moral situations to future ones. Climate obligations are vectors from the present manifold to the future manifold.',
        desc: 'Climate ethics involves obligations to future generations who do not yet exist. These are formalized as vectors from the present manifold to the future manifold — obligations that span time. The geometric framework captures the asymmetry: we can affect future generations, but they cannot affect us.',
        related: ['Obligation Vector', 'Discount Rate'] },
      { name: 'Discount Rate as Collapse',
        formal: 'The economic discount rate r collapses future moral dimensions: future welfare is weighted by e^{-rt}, causing distant future values to approach zero. This is dimensional collapse in the temporal direction.',
        desc: 'Standard cost-benefit analysis discounts future costs at a rate r, meaning costs 100 years from now are worth nearly nothing today. In geometric terms, this is dimensional collapse: the temporal dimension is being squeezed toward zero. This explains why standard economics undervalues climate action.',
        related: ['Scalar Collapse', 'Intergenerational Obligation'] },
      { name: 'Irreversible Boundary',
        formal: 'Species extinction as crossing an absorbing stratum: once a species is extinct, the moral manifold has permanently lost a degree of freedom. The boundary crossing is irreversible.',
        desc: 'Species extinction is the paradigmatic absorbing stratum. Once crossed, the biodiversity dimension has permanently shrunk — there is no returning. This gives formal content to the environmentalist intuition that extinction is categorically different from mere harm: it is an irreversible topology change.',
        related: ['Absorbing Strata', 'Moral Boundaries'] },
    ],
    26: [
      { name: 'Alignment as Geodesic Preservation',
        formal: 'AI alignment requires that the AI\'s decision trajectory approximate a geodesic on the moral manifold, preserving the tensor structure and respecting all boundary strata.',
        desc: 'The alignment problem is: how do we ensure AI systems make morally acceptable decisions? Geometrically: the AI should follow geodesics (optimal moral paths) while respecting boundaries (ethical red lines). Misalignment occurs when the AI deviates from the geodesic or crosses boundaries.',
        related: ['Geodesic', 'No Escape Theorem'] },
      { name: 'Algorithmic Bias as Projection',
        formal: 'Algorithmic bias occurs when a machine learning system\'s implicit metric projects certain moral dimensions to zero, making it blind to disparate impacts along those dimensions.',
        desc: 'When a hiring algorithm is biased against a demographic group, it has implicitly set the metric weight on that group\'s rights dimensions to zero — a projection that collapses those dimensions. Debiasing is then a problem of metric repair: adjusting the implicit metric to give appropriate weight to all 9 dimensions.',
        related: ['Scalar Collapse', 'Moral Metric'] },
      { name: 'Paperclip Maximizer',
        formal: 'The canonical AI safety scenario reinterpreted: a paperclip maximizer has undergone catastrophic dimensional collapse, reducing the entire 9D moral manifold to a single dimension (paperclip count).',
        desc: 'The paperclip maximizer thought experiment — an AI that converts the universe into paperclips — is the ultimate dimensional collapse. The AI has a 1-dimensional moral manifold (more paperclips = good) embedded in a 9-dimensional world. The No Escape Theorem predicts this will violate all other moral dimensions.',
        related: ['No Escape Theorem', 'Scalar Collapse'] },
    ],
    27: [
      { name: 'CRISPR as Manifold Modification',
        formal: 'Germline gene editing modifies the moral manifold itself: it changes the topology and metric of future moral space by altering the biological substrate of future agents.',
        desc: 'CRISPR germline editing does not just affect one patient — it changes the moral manifold for all future generations carrying the edit. This is not boundary crossing but manifold modification: the shape of future moral space itself is altered. This makes germline editing categorically different from somatic therapy.',
        related: ['Absorbing Strata', 'Intergenerational Obligation'] },
      { name: 'Double Consent Condition',
        formal: 'Research ethics requires consent from two distinct sources: the research subject (individual consent, boundary stratum) and the ethical review board (institutional consent, higher-order boundary).',
        desc: 'The double consent condition formalizes the two-layer boundary structure of research ethics. Individual consent establishes the first boundary condition; institutional review (IRB/ethics committee) establishes the second. Both boundaries must be satisfied — a subject cannot consent to unethical research, and an IRB cannot approve unconsented research.',
        related: ['Moral Boundaries', 'Whitney Stratification'] },
      { name: 'Neuroethics as Curvature',
        formal: 'Brain interventions that alter moral reasoning capacity change the curvature of the moral manifold for the affected agent, potentially altering which geodesics are accessible.',
        desc: 'Deep brain stimulation, psychoactive medication, and neural interfaces all alter the brain\'s moral reasoning capacity. In geometric terms, they change the curvature of the agent\'s moral manifold — making some moral paths easier (lower curvature) and others harder (higher curvature). This raises questions about moral responsibility under altered curvature.',
        related: ['Curvature', 'Moral Connection'] },
    ],
    28: [
      { name: 'War as Constrained Pathfinding',
        formal: 'Military ethics as A* pathfinding on a moral manifold with many boundary strata (laws of war, rules of engagement, proportionality constraints) and high-cost regions.',
        desc: 'In armed conflict, the commander seeks the "least bad" path — the geodesic that achieves the military objective while minimizing moral cost and respecting all boundary constraints (the Geneva Conventions, rules of engagement, proportionality). This is exactly the A* pathfinding problem on a constrained moral manifold.',
        related: ['A* on Moral Manifold', 'Proportionality'] },
      { name: 'Proportionality',
        formal: 'Multi-dimensional cost-benefit: the military advantage gained must be "proportional" to the civilian harm caused. In tensor terms, this is a metric-dependent comparison across different moral dimensions.',
        desc: 'Proportionality in just war theory asks whether the military gain justifies the civilian cost. In scalar terms, this is a simple comparison. In tensor terms, it is a metric-dependent comparison across incommensurable dimensions: military advantage (a security dimension) vs. civilian lives (a welfare dimension). The metric determines the exchange rate.',
        related: ['Moral Metric', 'Tensor Hierarchy'] },
      { name: 'Double Effect as Decomposition',
        formal: 'The doctrine of double effect decomposes an action\'s moral tensor into intended and foreseen components: T = T_intended + T_foreseen. Only T_intended is subject to deontological constraints.',
        desc: 'The doctrine of double effect says that causing harm as a foreseen side effect is morally different from intending harm as a means. In tensor terms, this is a decomposition of the moral tensor into two components. The intended component is subject to boundary constraints (deontological rules); the foreseen component is subject to proportionality (consequentialist weighing).',
        related: ['Tensor Hierarchy', 'Moral Boundaries'] },
      { name: 'Moral Injury in Combat',
        formal: 'Combat-induced moral injury as manifold damage: the soldier\'s moral metric becomes distorted by exposure to boundary crossings, creating pathological geodesics and persistent moral residue.',
        desc: 'Veterans\' moral injury — the deep psychological wound from participating in morally transgressive acts — is formalized as manifold damage. The moral metric is distorted by boundary crossings (killing, witnessing atrocities), creating warped geodesics: the veteran\'s moral reasoning becomes pathologically curved, requiring "manifold repair" (therapy).',
        related: ['Moral Injury', 'Absorbing Strata'] },
    ],
    29: [
      { name: 'Moral Field Equation',
        formal: 'An analogue of Einstein\'s field equation: G_ij = 8*pi*T_ij, where G_ij is the moral Einstein tensor (curvature) and T_ij is the moral stress-energy tensor (sources of moral obligation).',
        desc: 'An open problem: can we write a "moral field equation" that relates the curvature of moral space to the distribution of moral obligations, analogous to how Einstein\'s equation relates spacetime curvature to mass-energy? This would make the framework fully dynamic — obligations cause curvature, and curvature guides obligations.',
        related: ['Curvature', 'Moral Metric'] },
      { name: 'Torsion in Moral Space',
        formal: 'Open question: does the moral manifold have torsion (T(X,Y) = nabla_X Y - nabla_Y X - [X,Y] != 0)? Torsion would mean that moral space has a "twist" — parallel transport is path-dependent even locally.',
        desc: 'In Riemannian geometry, torsion is a property of the connection that makes parallelograms fail to close. If moral space has torsion, it would mean that even locally, the order of moral considerations matters — a deeper form of non-commutativity than that arising from curvature alone.',
        related: ['Moral Connection', 'Non-Commutativity'] },
      { name: 'Tensorial Interpretability',
        formal: 'Open problem: can we extract the implicit moral tensor from a trained AI system? If the AI\'s decision-making has tensor structure, can we identify the dimensions and metric it is using?',
        desc: 'If AI systems have implicit moral structures, we should be able to extract them — identify which moral dimensions the system tracks, what metric it uses, and where its boundaries are. This is "tensorial interpretability" — a geometric version of interpretable AI applied to moral reasoning.',
        related: ['AI as Collective Agent', 'Tensor-Valued Objectives'] },
      { name: 'Falsifiability',
        formal: 'The framework would be falsified by: (1) moral cognition provably scalar, (2) BIP violations being morally acceptable, (3) harm conservation failing empirically, (4) CHSH S < 2 in all moral experiments.',
        desc: 'The framework makes falsifiable predictions. If moral cognition turns out to be genuinely scalar (no directional structure), if BIP violations are sometimes morally acceptable, if harm can be genuinely destroyed by redescription, or if the CHSH inequality is never violated in moral experiments — the framework is wrong.',
        related: ['Conservation of Harm', 'CHSH Inequality'] },
    ],
    30: [
      { name: 'Return to the Border',
        formal: 'The book\'s argument comes full circle: the parable\'s "maybe" is the tensor that resists contraction. Not knowing whether something is "good" or "bad" is the correct moral state when the full tensor has not been contracted.',
        desc: 'The conclusion returns to the old man at the border. His "maybe" is not indecisiveness — it is the mathematical correct response when the full moral tensor has not been evaluated. Premature contraction to "good" or "bad" discards information. The wise response is to maintain the tensor.',
        related: ['Parable of the Horse', 'Moment of Contraction'] },
      { name: 'Ethics Is Not a Number',
        formal: 'The book\'s central thesis in one sentence: moral evaluation is inherently multi-dimensional (tensor-valued), and any reduction to a single number (scalar) destroys the structure that makes ethical reasoning possible.',
        desc: 'The final thesis: ethics is not a number. It is not a utility score, not a happiness index, not a cost-benefit ratio. It is a tensor — a multi-dimensional, context-dependent, direction-aware structure that lives on a curved, bounded, stratified manifold. Treating it as a number is not a simplification; it is a category error.',
        related: ['Scalar Collapse', 'Tensor Hierarchy'] },
      { name: 'The Geometry of Maybe',
        formal: '"Maybe" is not a hedge but a geometric position: the point on the manifold where the full tensor structure has been preserved, and where the information needed for contraction has not yet been acquired.',
        desc: 'The title of the final chapter. "Maybe" is the honest acknowledgment that the moral evaluation is not yet ready for contraction. The geometry of "maybe" is the geometry of the full tensor — rich, multi-dimensional, context-sensitive — before the irreversible collapse to a scalar decision.',
        related: ['Moral Uncertainty', 'Tensor Hierarchy'] },
    ],
  };

  // --- Build the modal overlay once ---
  const overlay = document.createElement('div');
  overlay.className = 'concept-modal-overlay';
  overlay.innerHTML =
    '<div class="concept-modal">' +
      '<button class="concept-modal-close" aria-label="Close">&times;</button>' +
      '<h3 class="concept-modal-title"></h3>' +
      '<div class="concept-chapter"></div>' +
      '<p class="concept-modal-desc"></p>' +
      '<div class="concept-formal"></div>' +
      '<div class="concept-related"></div>' +
    '</div>';
  document.body.appendChild(overlay);

  const modal = overlay.querySelector('.concept-modal');
  const modalTitle = modal.querySelector('.concept-modal-title');
  const modalChapter = modal.querySelector('.concept-chapter');
  const modalDesc = modal.querySelector('.concept-modal-desc');
  const modalFormal = modal.querySelector('.concept-formal');
  const modalRelated = modal.querySelector('.concept-related');

  function openConcept(chNum, concept) {
    modalTitle.textContent = concept.name;
    modalChapter.textContent = 'Chapter ' + chNum;
    modalDesc.textContent = concept.desc;
    modalFormal.textContent = concept.formal;

    // Build related links
    modalRelated.innerHTML = '';
    if (concept.related && concept.related.length) {
      const label = document.createElement('p');
      label.style.cssText = 'font-size:12px;color:var(--text-muted);margin:16px 0 8px;';
      label.textContent = 'Related concepts:';
      modalRelated.appendChild(label);
      const wrap = document.createElement('div');
      wrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;';
      concept.related.forEach(r => {
        const tag = document.createElement('span');
        tag.className = 'concept-tag';
        tag.textContent = r;
        tag.addEventListener('click', () => {
          // Find the related concept across all chapters
          for (const [ch, cList] of Object.entries(concepts)) {
            const found = cList.find(c => c.name === r);
            if (found) { openConcept(ch, found); return; }
          }
        });
        wrap.appendChild(tag);
      });
      modalRelated.appendChild(wrap);
    }

    overlay.classList.add('visible');
  }

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.classList.remove('visible');
  });
  modal.querySelector('.concept-modal-close').addEventListener('click', () => {
    overlay.classList.remove('visible');
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') overlay.classList.remove('visible');
  });

  // --- Inject concept tags into each chapter item ---
  const chapterItems = document.querySelectorAll('.chapter-item');
  chapterItems.forEach(item => {
    const numEl = item.querySelector('.ch-num');
    if (!numEl) return;
    const chNum = parseInt(numEl.textContent.trim());
    const chConcepts = concepts[chNum];
    if (!chConcepts) return;

    const tagsDiv = document.createElement('div');
    tagsDiv.className = 'chapter-concepts';
    chConcepts.forEach(c => {
      const tag = document.createElement('span');
      tag.className = 'concept-tag';
      tag.textContent = c.name;
      tag.addEventListener('click', (e) => {
        e.stopPropagation();
        openConcept(chNum, c);
      });
      tagsDiv.appendChild(tag);
    });

    const chInfo = item.querySelector('.ch-info');
    if (chInfo) chInfo.appendChild(tagsDiv);
  });
}
