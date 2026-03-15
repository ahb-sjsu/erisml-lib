/* ==========================================================================
   Geometric Methods — Interactive Demonstrations
   8 interactive SVG/Canvas visualizations for key concepts
   ========================================================================== */

const COLORS = {
  teal: '#1b9e77', tealLight: '#66c2a5', orange: '#d95f02',
  purple: '#7570b3', pink: '#e7298a', green: '#66a61e',
  gold: '#e6ab02', bg: '#0a1929', gridLine: 'rgba(102,194,165,0.12)',
  text: '#8fa4b8', textBright: '#e8ecf0'
};

const PALETTE = ['#1b9e77','#d95f02','#7570b3','#e7298a','#66a61e','#e6ab02','#a6761d','#66c2a5'];

// ============================================================================
// Utility functions
// ============================================================================

function createSVG(w, h, id) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  svg.setAttribute('id', id);
  svg.style.width = '100%';
  svg.style.height = 'auto';
  svg.style.userSelect = 'none';
  return svg;
}

function svgEl(tag, attrs) {
  const ns = 'http://www.w3.org/2000/svg';
  const el = document.createElementNS(ns, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
}

function makeDemoShell(title, icon, chapterId) {
  const container = document.createElement('div');
  container.className = 'demo-container';
  container.id = `demo-${chapterId}`;
  container.innerHTML = `
    <div class="demo-header">
      <span class="demo-icon">${icon}</span>
      <h4>${title}</h4>
      <span class="demo-badge">Interactive</span>
    </div>
    <div class="demo-body"></div>
  `;
  return container;
}

// ============================================================================
// Demo 1: Scalar Irrecoverability (Chapter 1)
// A 2D space with points; drag the projection angle to see info loss
// ============================================================================

function demoScalarIrrecoverability(container) {
  const W = 500, H = 400, cx = 200, cy = 200, R = 160;
  const shell = makeDemoShell('Scalar Irrecoverability Theorem', '\u{1F4CA}', 'ch1');
  const body = shell.querySelector('.demo-body');

  const canvasWrap = document.createElement('div');
  canvasWrap.className = 'demo-canvas-wrap';
  const svg = createSVG(W, H, 'svg-irrecoverability');
  canvasWrap.appendChild(svg);

  const controls = document.createElement('div');
  controls.className = 'demo-controls';
  controls.innerHTML = `
    <div class="demo-control-group">
      <label>Projection angle <span class="value-display" id="angle-val">45\u00B0</span></label>
      <input type="range" id="proj-angle" min="0" max="180" value="45" step="1">
    </div>
    <div class="demo-readout" id="irrecov-readout">
      Drag the slider to rotate the projection line.<br>
      Points with <span class="highlight">same color</span> on the line have different 2D positions but identical scalar projections.
    </div>
    <div class="demo-control-group">
      <label>Preset configurations</label>
      <div class="demo-btn-group">
        <button class="demo-btn" data-angle="45">45\u00B0</button>
        <button class="demo-btn" data-angle="0">Horizontal</button>
        <button class="demo-btn" data-angle="90">Vertical</button>
        <button class="demo-btn" data-angle="135">135\u00B0</button>
      </div>
    </div>
  `;

  body.appendChild(canvasWrap);
  body.appendChild(controls);

  // Points in 2D — chosen so some collapse under certain projections
  const points = [
    { x: 0.6, y: 0.3, label: 'A' },
    { x: -0.4, y: 0.7, label: 'B' },
    { x: -0.5, y: -0.5, label: 'C' },
    { x: 0.3, y: -0.6, label: 'D' },
    { x: 0.1, y: 0.8, label: 'E' },
    { x: -0.7, y: -0.1, label: 'F' },
    { x: 0.7, y: 0.6, label: 'G' },
  ];

  function render(angleDeg) {
    svg.innerHTML = '';
    const rad = angleDeg * Math.PI / 180;
    const dx = Math.cos(rad), dy = -Math.sin(rad);

    // Background grid
    for (let i = -4; i <= 4; i++) {
      svg.appendChild(svgEl('line', {
        x1: cx + i * 40, y1: cy - R, x2: cx + i * 40, y2: cy + R,
        stroke: COLORS.gridLine, 'stroke-width': 0.5
      }));
      svg.appendChild(svgEl('line', {
        x1: cx - R, y1: cy + i * 40, x2: cx + R, y2: cy + i * 40,
        stroke: COLORS.gridLine, 'stroke-width': 0.5
      }));
    }

    // Projection line
    svg.appendChild(svgEl('line', {
      x1: cx - dx * R, y1: cy + dy * R, x2: cx + dx * R, y2: cy - dy * R,
      stroke: COLORS.teal, 'stroke-width': 2, opacity: '0.6',
      'stroke-dasharray': '6,4'
    }));

    // Project and draw
    const projections = points.map((p, i) => {
      const px = p.x * R * 0.8, py = -p.y * R * 0.8;
      const dot = px * dx + py * (-dy);
      return { ...p, px, py, dot, i };
    });

    // Draw projection lines (whiskers)
    projections.forEach((p) => {
      const projX = cx + p.dot * dx;
      const projY = cy + p.dot * dy;
      svg.appendChild(svgEl('line', {
        x1: cx + p.px, y1: cy + p.py, x2: projX, y2: projY,
        stroke: PALETTE[p.i], 'stroke-width': 1, opacity: '0.3',
        'stroke-dasharray': '3,3'
      }));
    });

    // Draw projected points on line
    projections.forEach((p) => {
      const projX = cx + p.dot * dx;
      const projY = cy + p.dot * dy;
      svg.appendChild(svgEl('circle', {
        cx: projX, cy: projY, r: 5,
        fill: PALETTE[p.i], opacity: '0.7', stroke: '#0a1929', 'stroke-width': 1
      }));
    });

    // Draw 2D points
    projections.forEach((p) => {
      svg.appendChild(svgEl('circle', {
        cx: cx + p.px, cy: cy + p.py, r: 7,
        fill: PALETTE[p.i], stroke: '#e8ecf0', 'stroke-width': 1.5
      }));
      svg.appendChild(svgEl('text', {
        x: cx + p.px + 12, y: cy + p.py + 4,
        fill: COLORS.textBright, 'font-size': '11', 'font-family': 'JetBrains Mono, monospace'
      })).textContent = p.label;
    });

    // Angle label
    svg.appendChild(svgEl('text', {
      x: cx + dx * (R + 15), y: cy - dy * (R + 15) + 4,
      fill: COLORS.tealLight, 'font-size': '11', 'font-family': 'JetBrains Mono, monospace',
      'text-anchor': 'middle'
    })).textContent = `\u03D5`;

    // Check for near-collisions in projection
    projections.sort((a, b) => a.dot - b.dot);
    let collisions = 0;
    for (let i = 1; i < projections.length; i++) {
      if (Math.abs(projections[i].dot - projections[i - 1].dot) < 8) collisions++;
    }

    // Compute info loss metric
    const spread2D = points.reduce((s, p) => s + p.x * p.x + p.y * p.y, 0);
    const spread1D = projections.reduce((s, p) => s + p.dot * p.dot, 0) / (R * R * 0.64);
    const infoRetained = Math.min(100, Math.round(spread1D / spread2D * 100));

    const readout = shell.querySelector('#irrecov-readout');
    readout.innerHTML = `
      Projection: <span class="highlight">\u03D5 = ${angleDeg}\u00B0</span><br>
      Information retained: <span class="${infoRetained < 50 ? 'warn' : 'highlight'}">${infoRetained}%</span><br>
      Near-collisions: <span class="${collisions > 0 ? 'warn' : 'highlight'}">${collisions}</span> pairs<br>
      <span style="color:#5c7a94">Null space: ${7 - 1} = 6 degrees of freedom lost</span>
    `;
  }

  container.appendChild(shell);
  const slider = shell.querySelector('#proj-angle');
  const angleVal = shell.querySelector('#angle-val');
  slider.addEventListener('input', () => {
    angleVal.textContent = slider.value + '\u00B0';
    render(+slider.value);
  });
  shell.querySelectorAll('[data-angle]').forEach(btn => {
    btn.addEventListener('click', () => {
      slider.value = btn.dataset.angle;
      angleVal.textContent = btn.dataset.angle + '\u00B0';
      render(+btn.dataset.angle);
    });
  });
  render(45);
}


// ============================================================================
// Demo 2: Mahalanobis vs Euclidean Distance (Chapter 2)
// Interactive covariance matrix → contour comparison
// ============================================================================

function demoMahalanobis(container) {
  const W = 460, H = 460, cx = 230, cy = 230, scale = 80;
  const shell = makeDemoShell('Mahalanobis vs Euclidean Distance', '\u{1F534}', 'ch2');
  const body = shell.querySelector('.demo-body');

  const canvasWrap = document.createElement('div');
  canvasWrap.className = 'demo-canvas-wrap';
  const svg = createSVG(W, H, 'svg-mahalanobis');
  canvasWrap.appendChild(svg);

  const controls = document.createElement('div');
  controls.className = 'demo-controls';
  controls.innerHTML = `
    <div class="demo-control-group">
      <label>\u03C3\u2081\u2081 (variance dim 1) <span class="value-display" id="s11-val">1.0</span></label>
      <input type="range" id="s11" min="0.2" max="4" value="1" step="0.1">
    </div>
    <div class="demo-control-group">
      <label>\u03C3\u2082\u2082 (variance dim 2) <span class="value-display" id="s22-val">1.0</span></label>
      <input type="range" id="s22" min="0.2" max="4" value="1" step="0.1">
    </div>
    <div class="demo-control-group">
      <label>\u03C1 (correlation) <span class="value-display" id="rho-val">0.0</span></label>
      <input type="range" id="rho" min="-0.95" max="0.95" value="0" step="0.05">
    </div>
    <div class="demo-readout" id="maha-readout">
      <span class="highlight">Teal ellipses</span> = Mahalanobis contours<br>
      <span style="color:${COLORS.orange}">Orange circles</span> = Euclidean contours<br>
      Click anywhere to measure distance.
    </div>
    <div class="demo-control-group">
      <label>Presets</label>
      <div class="demo-btn-group">
        <button class="demo-btn" data-preset="iso">Isotropic</button>
        <button class="demo-btn" data-preset="aniso">Anisotropic</button>
        <button class="demo-btn" data-preset="corr">Correlated</button>
        <button class="demo-btn" data-preset="neg">Anti-corr</button>
      </div>
    </div>
  `;

  body.appendChild(canvasWrap);
  body.appendChild(controls);

  let clickPt = null;

  function render() {
    const s11 = +shell.querySelector('#s11').value;
    const s22 = +shell.querySelector('#s22').value;
    const rho = +shell.querySelector('#rho').value;
    const s12 = rho * Math.sqrt(s11 * s22);

    svg.innerHTML = '';

    // Grid
    for (let i = -5; i <= 5; i++) {
      svg.appendChild(svgEl('line', {
        x1: cx + i * scale, y1: 0, x2: cx + i * scale, y2: H,
        stroke: COLORS.gridLine, 'stroke-width': 0.5
      }));
      svg.appendChild(svgEl('line', {
        x1: 0, y1: cy + i * scale, x2: W, y2: cy + i * scale,
        stroke: COLORS.gridLine, 'stroke-width': 0.5
      }));
    }

    // Axes
    svg.appendChild(svgEl('line', { x1: 0, y1: cy, x2: W, y2: cy, stroke: COLORS.text, 'stroke-width': 1, opacity: '0.4' }));
    svg.appendChild(svgEl('line', { x1: cx, y1: 0, x2: cx, y2: H, stroke: COLORS.text, 'stroke-width': 1, opacity: '0.4' }));

    // Covariance matrix eigendecomposition for ellipse
    const trace = s11 + s22;
    const det = s11 * s22 - s12 * s12;
    const disc = Math.sqrt(Math.max(0, trace * trace / 4 - det));
    const lam1 = trace / 2 + disc;
    const lam2 = trace / 2 - disc;
    const angle = Math.atan2(s12, lam1 - s22);

    // Draw contours
    for (let r = 1; r <= 3; r++) {
      // Euclidean circles
      svg.appendChild(svgEl('circle', {
        cx, cy, r: r * scale,
        fill: 'none', stroke: COLORS.orange, 'stroke-width': 1,
        opacity: '0.3', 'stroke-dasharray': '4,4'
      }));

      // Mahalanobis ellipses
      const a = Math.sqrt(lam1) * r * scale;
      const b = Math.sqrt(Math.max(0.01, lam2)) * r * scale;
      const deg = -angle * 180 / Math.PI;
      svg.appendChild(svgEl('ellipse', {
        cx, cy, rx: a, ry: b,
        fill: 'none', stroke: COLORS.tealLight, 'stroke-width': 1.5,
        opacity: 0.7 - r * 0.15,
        transform: `rotate(${deg} ${cx} ${cy})`
      }));
    }

    // Center point
    svg.appendChild(svgEl('circle', { cx, cy, r: 4, fill: COLORS.teal }));

    // Clicked point
    if (clickPt) {
      const px = (clickPt.x - cx) / scale;
      const py = -(clickPt.y - cy) / scale;
      const dE = Math.sqrt(px * px + py * py);

      // Mahalanobis: d = sqrt( v^T Sigma^-1 v )
      const invDet = 1 / det;
      const dM = Math.sqrt(Math.max(0,
        invDet * (s22 * px * px - 2 * s12 * px * py + s11 * py * py)
      ));

      svg.appendChild(svgEl('circle', {
        cx: clickPt.x, cy: clickPt.y, r: 6,
        fill: COLORS.pink, stroke: '#e8ecf0', 'stroke-width': 1.5
      }));
      svg.appendChild(svgEl('line', {
        x1: cx, y1: cy, x2: clickPt.x, y2: clickPt.y,
        stroke: COLORS.pink, 'stroke-width': 1, 'stroke-dasharray': '4,3'
      }));

      const readout = shell.querySelector('#maha-readout');
      readout.innerHTML = `
        Point: (${px.toFixed(2)}, ${py.toFixed(2)})<br>
        Euclidean: <span style="color:${COLORS.orange}">${dE.toFixed(3)}</span><br>
        Mahalanobis: <span class="highlight">${dM.toFixed(3)}</span><br>
        Ratio: <span class="${dM/dE > 1.5 ? 'warn' : 'highlight'}">${(dM/dE).toFixed(2)}x</span>
      `;
    }

    // Matrix display
    svg.appendChild(svgEl('text', {
      x: 15, y: 25, fill: COLORS.text, 'font-size': '11',
      'font-family': 'JetBrains Mono, monospace'
    })).textContent = `\u03A3 = [${s11.toFixed(1)}, ${s12.toFixed(2)}; ${s12.toFixed(2)}, ${s22.toFixed(1)}]`;

    shell.querySelector('#s11-val').textContent = s11.toFixed(1);
    shell.querySelector('#s22-val').textContent = s22.toFixed(1);
    shell.querySelector('#rho-val').textContent = rho.toFixed(2);
  }

  container.appendChild(shell);

  svg.addEventListener('click', (e) => {
    const rect = svg.getBoundingClientRect();
    const scaleX = W / rect.width;
    clickPt = {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleX
    };
    render();
  });

  ['s11', 's22', 'rho'].forEach(id => {
    shell.querySelector(`#${id}`).addEventListener('input', render);
  });

  const presets = {
    iso:   { s11: 1, s22: 1, rho: 0 },
    aniso: { s11: 3, s22: 0.5, rho: 0 },
    corr:  { s11: 2, s22: 2, rho: 0.8 },
    neg:   { s11: 1.5, s22: 1.5, rho: -0.7 },
  };
  shell.querySelectorAll('[data-preset]').forEach(btn => {
    btn.addEventListener('click', () => {
      const p = presets[btn.dataset.preset];
      shell.querySelector('#s11').value = p.s11;
      shell.querySelector('#s22').value = p.s22;
      shell.querySelector('#rho').value = p.rho;
      render();
    });
  });

  render();
}


// ============================================================================
// Demo 3: Poincaré Disk (Chapter 3)
// Interactive hyperbolic space with geodesics
// ============================================================================

function demoPoincare(container) {
  const W = 480, H = 480, cx = 240, cy = 240, R = 200;
  const shell = makeDemoShell('Poincar\u00E9 Disk — Hyperbolic Geometry', '\u{1F30D}', 'ch3');
  const body = shell.querySelector('.demo-body');

  const canvasWrap = document.createElement('div');
  canvasWrap.className = 'demo-canvas-wrap';
  const svg = createSVG(W, H, 'svg-poincare');
  canvasWrap.appendChild(svg);

  const controls = document.createElement('div');
  controls.className = 'demo-controls';
  controls.innerHTML = `
    <div class="demo-readout" id="poincare-readout">
      Click inside the disk to place points.<br>
      Geodesics are drawn between consecutive pairs.<br>
      <span class="highlight">Notice:</span> distances grow rapidly near the boundary.
    </div>
    <div class="demo-control-group">
      <label>Actions</label>
      <div class="demo-btn-group">
        <button class="demo-btn" id="poincare-reset">Clear points</button>
        <button class="demo-btn" id="poincare-tree">Show tree</button>
        <button class="demo-btn" id="poincare-grid">Toggle grid</button>
      </div>
    </div>
  `;

  body.appendChild(canvasWrap);
  body.appendChild(controls);

  let points = [];
  let showGrid = true;
  const treePoints = [
    { x: 0, y: 0 },          // root
    { x: -0.3, y: -0.25 },   // L
    { x: 0.3, y: -0.25 },    // R
    { x: -0.55, y: -0.5 },   // LL
    { x: -0.15, y: -0.5 },   // LR
    { x: 0.15, y: -0.5 },    // RL
    { x: 0.55, y: -0.5 },    // RR
    { x: -0.72, y: -0.68 },  // LLL
    { x: -0.45, y: -0.68 },  // LLR
    { x: 0.45, y: -0.68 },   // RRL
    { x: 0.72, y: -0.68 },   // RRR
  ];
  const treeEdges = [[0,1],[0,2],[1,3],[1,4],[2,5],[2,6],[3,7],[3,8],[6,9],[6,10]];

  function hypDist(p1, p2) {
    const dx = p1.x - p2.x, dy = p1.y - p2.y;
    const n1sq = p1.x * p1.x + p1.y * p1.y;
    const n2sq = p2.x * p2.x + p2.y * p2.y;
    const num = dx * dx + dy * dy;
    const denom = (1 - n1sq) * (1 - n2sq);
    if (denom <= 0) return Infinity;
    return Math.acosh(1 + 2 * num / denom);
  }

  // Draw geodesic arc between two points in Poincaré disk
  function geodesicPath(p1, p2) {
    // If points are nearly collinear with origin, draw straight line
    const cross = p1.x * p2.y - p1.y * p2.x;
    if (Math.abs(cross) < 0.001) {
      return `M ${cx + p1.x * R} ${cy - p1.y * R} L ${cx + p2.x * R} ${cy - p2.y * R}`;
    }

    // Inversion-based geodesic calculation
    const d1 = p1.x * p1.x + p1.y * p1.y;
    const d2 = p2.x * p2.x + p2.y * p2.y;

    // Find the circle through p1, p2 orthogonal to unit circle
    const ax = p1.x, ay = p1.y, bx = p2.x, by = p2.y;
    const D = 2 * (ax * by - ay * bx);
    if (Math.abs(D) < 1e-10) {
      return `M ${cx + p1.x * R} ${cy - p1.y * R} L ${cx + p2.x * R} ${cy - p2.y * R}`;
    }

    const ux = (by * (ax * ax + ay * ay + 1) - ay * (bx * bx + by * by + 1)) / D;
    const uy = (ax * (bx * bx + by * by + 1) - bx * (ax * ax + ay * ay + 1)) / D;
    const r = Math.sqrt((ax - ux) * (ax - ux) + (ay - uy) * (ay - uy));

    // Convert to SVG coordinates
    const svgCx = cx + ux * R;
    const svgCy = cy - uy * R;
    const svgR = r * R;

    // Determine arc direction
    const a1 = Math.atan2(-(p1.y * R - (-uy * R)), p1.x * R - ux * R);
    const a2 = Math.atan2(-(p2.y * R - (-uy * R)), p2.x * R - ux * R);
    let da = a2 - a1;
    while (da > Math.PI) da -= 2 * Math.PI;
    while (da < -Math.PI) da += 2 * Math.PI;
    const sweep = da > 0 ? 1 : 0;
    const large = Math.abs(da) > Math.PI ? 1 : 0;

    return `M ${cx + p1.x * R} ${cy - p1.y * R} A ${svgR} ${svgR} 0 ${large} ${sweep} ${cx + p2.x * R} ${cy - p2.y * R}`;
  }

  function render() {
    svg.innerHTML = '';

    // Disk background
    svg.appendChild(svgEl('circle', {
      cx, cy, r: R, fill: 'rgba(10,25,41,0.9)', stroke: COLORS.tealLight,
      'stroke-width': 2
    }));

    // Hyperbolic grid (concentric circles at equal hyperbolic distances)
    if (showGrid) {
      for (let d = 0.5; d <= 3; d += 0.5) {
        const eucR = Math.tanh(d / 2) * R;
        svg.appendChild(svgEl('circle', {
          cx, cy, r: eucR, fill: 'none', stroke: COLORS.gridLine,
          'stroke-width': 0.5
        }));
      }
      // Radial lines
      for (let a = 0; a < Math.PI; a += Math.PI / 6) {
        svg.appendChild(svgEl('line', {
          x1: cx - Math.cos(a) * R, y1: cy - Math.sin(a) * R,
          x2: cx + Math.cos(a) * R, y2: cy + Math.sin(a) * R,
          stroke: COLORS.gridLine, 'stroke-width': 0.5
        }));
      }
    }

    // Draw geodesics between consecutive point pairs
    for (let i = 0; i < points.length - 1; i++) {
      const path = geodesicPath(points[i], points[i + 1]);
      svg.appendChild(svgEl('path', {
        d: path, fill: 'none', stroke: PALETTE[i % PALETTE.length],
        'stroke-width': 2, opacity: '0.8'
      }));
    }

    // Draw points
    points.forEach((p, i) => {
      const norm = Math.sqrt(p.x * p.x + p.y * p.y);
      svg.appendChild(svgEl('circle', {
        cx: cx + p.x * R, cy: cy - p.y * R, r: 6,
        fill: PALETTE[i % PALETTE.length], stroke: '#e8ecf0', 'stroke-width': 1.5
      }));
      svg.appendChild(svgEl('text', {
        x: cx + p.x * R + 10, y: cy - p.y * R + 4,
        fill: COLORS.textBright, 'font-size': '10',
        'font-family': 'JetBrains Mono, monospace'
      })).textContent = `\u2016x\u2016=${norm.toFixed(2)}`;
    });

    // Update readout
    const readout = shell.querySelector('#poincare-readout');
    if (points.length >= 2) {
      let info = `<span class="highlight">${points.length} points placed</span><br>`;
      for (let i = 0; i < points.length - 1; i++) {
        const d = hypDist(points[i], points[i + 1]);
        const euc = Math.sqrt((points[i].x - points[i+1].x)**2 + (points[i].y - points[i+1].y)**2);
        info += `d(${i+1},${i+2}): hyp=<span class="highlight">${d.toFixed(2)}</span> euc=${euc.toFixed(2)}<br>`;
      }
      readout.innerHTML = info;
    } else {
      readout.innerHTML = `${points.length} point(s). Click to add more.<br>Geodesics drawn between consecutive pairs.`;
    }
  }

  container.appendChild(shell);

  svg.addEventListener('click', (e) => {
    const rect = svg.getBoundingClientRect();
    const scaleX = W / rect.width;
    const mx = (e.clientX - rect.left) * scaleX - cx;
    const my = -((e.clientY - rect.top) * scaleX - cy);
    const px = mx / R, py = my / R;
    if (px * px + py * py < 0.95) {
      points.push({ x: px, y: py });
      render();
    }
  });

  shell.querySelector('#poincare-reset').addEventListener('click', () => { points = []; render(); });
  shell.querySelector('#poincare-tree').addEventListener('click', () => {
    points = [...treePoints];
    // Override render to draw tree edges
    render();
    treeEdges.forEach(([a, b]) => {
      const path = geodesicPath(treePoints[a], treePoints[b]);
      svg.appendChild(svgEl('path', {
        d: path, fill: 'none', stroke: COLORS.tealLight,
        'stroke-width': 1.5, opacity: '0.6'
      }));
    });
  });
  shell.querySelector('#poincare-grid').addEventListener('click', () => { showGrid = !showGrid; render(); });

  render();
}


// ============================================================================
// Demo 4: Persistent Homology (Chapter 5)
// Adjust epsilon to watch simplicial complex grow
// ============================================================================

function demoPersistence(container) {
  const W = 480, H = 400, cx = 240, cy = 200;
  const shell = makeDemoShell('Persistent Homology — Vietoris-Rips Complex', '\u{1F300}', 'ch5');
  const body = shell.querySelector('.demo-body');

  const canvasWrap = document.createElement('div');
  canvasWrap.className = 'demo-canvas-wrap';
  const svg = createSVG(W, H, 'svg-persistence');
  canvasWrap.appendChild(svg);

  const controls = document.createElement('div');
  controls.className = 'demo-controls';
  controls.innerHTML = `
    <div class="demo-control-group">
      <label>\u03B5 (scale) <span class="value-display" id="eps-val">0.30</span></label>
      <input type="range" id="eps-slider" min="0" max="1.5" value="0.3" step="0.01">
    </div>
    <div class="demo-readout" id="persist-readout">
      \u03B5 = 0.30<br>
      Components (H\u2080): ?<br>
      Loops (H\u2081): ?
    </div>
    <div class="demo-control-group">
      <label>Point cloud</label>
      <div class="demo-btn-group">
        <button class="demo-btn active" data-cloud="circle">Circle</button>
        <button class="demo-btn" data-cloud="figure8">Figure-8</button>
        <button class="demo-btn" data-cloud="clusters">Clusters</button>
        <button class="demo-btn" data-cloud="random">Random</button>
      </div>
    </div>
  `;

  body.appendChild(canvasWrap);
  body.appendChild(controls);

  // Generate point clouds
  function makeCircle(n, noise) {
    const pts = [];
    for (let i = 0; i < n; i++) {
      const t = (2 * Math.PI * i) / n;
      pts.push({
        x: Math.cos(t) + (Math.random() - 0.5) * noise,
        y: Math.sin(t) + (Math.random() - 0.5) * noise
      });
    }
    return pts;
  }

  function makeFigure8(n, noise) {
    const pts = [];
    for (let i = 0; i < n; i++) {
      const t = (2 * Math.PI * i) / n;
      const r = Math.cos(2 * t) > 0 ? 1 : -1;
      pts.push({
        x: Math.cos(t) * 0.7 + (Math.random() - 0.5) * noise,
        y: Math.sin(t) * Math.cos(t) * 1.2 + (Math.random() - 0.5) * noise
      });
    }
    return pts;
  }

  function makeClusters() {
    const pts = [];
    const centers = [[-0.8, 0.6], [0.8, 0.6], [0, -0.8]];
    centers.forEach(([cx, cy]) => {
      for (let i = 0; i < 8; i++) {
        pts.push({ x: cx + (Math.random() - 0.5) * 0.3, y: cy + (Math.random() - 0.5) * 0.3 });
      }
    });
    return pts;
  }

  function makeRandom(n) {
    const pts = [];
    for (let i = 0; i < n; i++) {
      pts.push({ x: (Math.random() - 0.5) * 2.2, y: (Math.random() - 0.5) * 1.8 });
    }
    return pts;
  }

  let cloudType = 'circle';
  let cloud = makeCircle(20, 0.15);
  const S = 130; // scale

  function dist(a, b) {
    return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
  }

  // Simple connected components via union-find
  function countComponents(pts, eps) {
    const parent = pts.map((_, i) => i);
    function find(i) { return parent[i] === i ? i : (parent[i] = find(parent[i])); }
    function union(a, b) { parent[find(a)] = find(b); }
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        if (dist(pts[i], pts[j]) <= eps) union(i, j);
      }
    }
    return new Set(pts.map((_, i) => find(i))).size;
  }

  // Count triangles (proxy for H1)
  function countTriangles(pts, eps) {
    let count = 0;
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        if (dist(pts[i], pts[j]) > eps) continue;
        for (let k = j + 1; k < pts.length; k++) {
          if (dist(pts[i], pts[k]) <= eps && dist(pts[j], pts[k]) <= eps) count++;
        }
      }
    }
    return count;
  }

  function render() {
    const eps = +shell.querySelector('#eps-slider').value;
    svg.innerHTML = '';

    // Draw filled triangles (2-simplices)
    for (let i = 0; i < cloud.length; i++) {
      for (let j = i + 1; j < cloud.length; j++) {
        if (dist(cloud[i], cloud[j]) > eps) continue;
        for (let k = j + 1; k < cloud.length; k++) {
          if (dist(cloud[i], cloud[k]) <= eps && dist(cloud[j], cloud[k]) <= eps) {
            svg.appendChild(svgEl('polygon', {
              points: `${cx+cloud[i].x*S},${cy-cloud[i].y*S} ${cx+cloud[j].x*S},${cy-cloud[j].y*S} ${cx+cloud[k].x*S},${cy-cloud[k].y*S}`,
              fill: COLORS.teal, opacity: '0.08', stroke: 'none'
            }));
          }
        }
      }
    }

    // Draw edges (1-simplices)
    for (let i = 0; i < cloud.length; i++) {
      for (let j = i + 1; j < cloud.length; j++) {
        const d = dist(cloud[i], cloud[j]);
        if (d <= eps) {
          svg.appendChild(svgEl('line', {
            x1: cx + cloud[i].x * S, y1: cy - cloud[i].y * S,
            x2: cx + cloud[j].x * S, y2: cy - cloud[j].y * S,
            stroke: COLORS.tealLight, 'stroke-width': 1, opacity: '0.5'
          }));
        }
      }
    }

    // Draw epsilon balls (faint)
    cloud.forEach(p => {
      svg.appendChild(svgEl('circle', {
        cx: cx + p.x * S, cy: cy - p.y * S, r: eps * S / 2,
        fill: COLORS.teal, opacity: '0.04', stroke: COLORS.teal,
        'stroke-width': 0.5, 'stroke-opacity': '0.15'
      }));
    });

    // Draw points
    cloud.forEach((p, i) => {
      svg.appendChild(svgEl('circle', {
        cx: cx + p.x * S, cy: cy - p.y * S, r: 4,
        fill: COLORS.tealLight, stroke: '#0a1929', 'stroke-width': 1
      }));
    });

    const nComp = countComponents(cloud, eps);
    const nTri = countTriangles(cloud, eps);
    const edges = (() => {
      let e = 0;
      for (let i = 0; i < cloud.length; i++)
        for (let j = i + 1; j < cloud.length; j++)
          if (dist(cloud[i], cloud[j]) <= eps) e++;
      return e;
    })();
    // Euler characteristic estimate for H1
    const chi = cloud.length - edges + nTri;
    const h1Est = Math.max(0, nComp - chi);

    shell.querySelector('#eps-val').textContent = eps.toFixed(2);
    shell.querySelector('#persist-readout').innerHTML = `
      \u03B5 = <span class="highlight">${eps.toFixed(2)}</span><br>
      Components (H\u2080): <span class="highlight">${nComp}</span><br>
      Loops (H\u2081): <span class="highlight">\u2248${h1Est}</span><br>
      Edges: ${edges} &middot; Triangles: ${nTri}
    `;
  }

  container.appendChild(shell);

  shell.querySelector('#eps-slider').addEventListener('input', render);

  const cloudGens = {
    circle: () => makeCircle(20, 0.15),
    figure8: () => makeFigure8(24, 0.12),
    clusters: () => makeClusters(),
    random: () => makeRandom(18)
  };

  shell.querySelectorAll('[data-cloud]').forEach(btn => {
    btn.addEventListener('click', () => {
      shell.querySelectorAll('[data-cloud]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      cloudType = btn.dataset.cloud;
      cloud = cloudGens[cloudType]();
      render();
    });
  });

  render();
}


// ============================================================================
// Demo 5: Pareto Frontier (Chapter 8)
// Click to add configurations, frontier auto-highlights
// ============================================================================

function demoPareto(container) {
  const W = 480, H = 400;
  const pad = { l: 60, r: 30, t: 30, b: 50 };
  const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;
  const shell = makeDemoShell('Pareto Frontier Explorer', '\u{1F4C8}', 'ch8');
  const body = shell.querySelector('.demo-body');

  const canvasWrap = document.createElement('div');
  canvasWrap.className = 'demo-canvas-wrap';
  const svg = createSVG(W, H, 'svg-pareto');
  canvasWrap.appendChild(svg);

  const controls = document.createElement('div');
  controls.className = 'demo-controls';
  controls.innerHTML = `
    <div class="demo-readout" id="pareto-readout">
      Click in the plot to add configurations.<br>
      <span class="highlight">Teal points</span> = Pareto-optimal (non-dominated)<br>
      <span style="color:${COLORS.text}">Gray points</span> = dominated
    </div>
    <div class="demo-control-group">
      <div class="demo-btn-group">
        <button class="demo-btn" id="pareto-defect">Defect prediction</button>
        <button class="demo-btn" id="pareto-reset">Clear</button>
      </div>
    </div>
  `;

  body.appendChild(canvasWrap);
  body.appendChild(controls);

  // x = num_dimensions (1-5), y = MAE (lower is better)
  let configs = [
    { x: 1, y: 3.8, label: '{Complexity}' },
    { x: 2, y: 2.1, label: '{Cmplx, Proc}' },
    { x: 3, y: 1.7, label: '{Cmplx, Proc, Size}' },
    { x: 5, y: 1.5, label: 'All' },
    { x: 2, y: 3.2, label: '{Size, Halst}' },
    { x: 1, y: 5.1, label: '{OO}' },
    { x: 3, y: 2.5, label: '{Size, OO, Halst}' },
    { x: 4, y: 1.6, label: '{Cmplx, Proc, Size, Halst}' },
  ];

  function paretoFrontier(pts) {
    const sorted = [...pts].sort((a, b) => a.x - b.x || a.y - b.y);
    const frontier = [];
    let minY = Infinity;
    for (const p of sorted) {
      if (p.y < minY) {
        frontier.push(p);
        minY = p.y;
      }
    }
    return frontier;
  }

  function toSvg(p) {
    const xRange = 6, yRange = 6;
    return {
      sx: pad.l + (p.x / xRange) * pw,
      sy: pad.t + (p.y / yRange) * ph
    };
  }

  function render() {
    svg.innerHTML = '';
    const xRange = 6, yRange = 6;

    // Axes
    svg.appendChild(svgEl('line', {
      x1: pad.l, y1: pad.t, x2: pad.l, y2: H - pad.b,
      stroke: COLORS.text, 'stroke-width': 1
    }));
    svg.appendChild(svgEl('line', {
      x1: pad.l, y1: H - pad.b, x2: W - pad.r, y2: H - pad.b,
      stroke: COLORS.text, 'stroke-width': 1
    }));

    // Axis labels
    svg.appendChild(svgEl('text', {
      x: W / 2, y: H - 8, fill: COLORS.text, 'font-size': '12',
      'font-family': 'Inter, sans-serif', 'text-anchor': 'middle'
    })).textContent = 'Number of dimensions (k)';
    svg.appendChild(svgEl('text', {
      x: 14, y: H / 2, fill: COLORS.text, 'font-size': '12',
      'font-family': 'Inter, sans-serif', 'text-anchor': 'middle',
      transform: `rotate(-90 14 ${H/2})`
    })).textContent = 'MAE (lower is better)';

    // Grid & tick marks
    for (let x = 1; x <= 5; x++) {
      const sx = pad.l + (x / xRange) * pw;
      svg.appendChild(svgEl('line', { x1: sx, y1: pad.t, x2: sx, y2: H - pad.b, stroke: COLORS.gridLine, 'stroke-width': 0.5 }));
      svg.appendChild(svgEl('text', { x: sx, y: H - pad.b + 18, fill: COLORS.text, 'font-size': '10', 'text-anchor': 'middle', 'font-family': 'JetBrains Mono' })).textContent = x;
    }
    for (let y = 0; y <= 5; y++) {
      const sy = pad.t + (y / yRange) * ph;
      svg.appendChild(svgEl('line', { x1: pad.l, y1: sy, x2: W - pad.r, y2: sy, stroke: COLORS.gridLine, 'stroke-width': 0.5 }));
      svg.appendChild(svgEl('text', { x: pad.l - 8, y: sy + 4, fill: COLORS.text, 'font-size': '10', 'text-anchor': 'end', 'font-family': 'JetBrains Mono' })).textContent = y.toFixed(1);
    }

    const frontier = paretoFrontier(configs);
    const frontierSet = new Set(frontier);

    // Dominated region shading
    if (frontier.length >= 2) {
      let pathD = '';
      const sorted = [...frontier].sort((a, b) => a.x - b.x);
      sorted.forEach((p, i) => {
        const { sx, sy } = toSvg(p);
        if (i === 0) pathD += `M ${pad.l} ${sy} L ${sx} ${sy}`;
        else pathD += ` L ${sx} ${sy}`;
      });
      const last = toSvg(sorted[sorted.length - 1]);
      pathD += ` L ${last.sx} ${H - pad.b} L ${pad.l} ${H - pad.b} Z`;
      svg.appendChild(svgEl('path', {
        d: pathD, fill: COLORS.teal, opacity: '0.06'
      }));
    }

    // Frontier line
    if (frontier.length >= 2) {
      const sorted = [...frontier].sort((a, b) => a.x - b.x);
      let d = sorted.map((p, i) => {
        const { sx, sy } = toSvg(p);
        // Step function style
        if (i === 0) return `M ${sx} ${sy}`;
        const prev = toSvg(sorted[i-1]);
        return `L ${sx} ${prev.sy} L ${sx} ${sy}`;
      }).join(' ');
      svg.appendChild(svgEl('path', {
        d, fill: 'none', stroke: COLORS.teal, 'stroke-width': 2
      }));
    }

    // Points
    configs.forEach(p => {
      const { sx, sy } = toSvg(p);
      const isF = frontierSet.has(p);
      svg.appendChild(svgEl('circle', {
        cx: sx, cy: sy, r: isF ? 7 : 5,
        fill: isF ? COLORS.teal : COLORS.text,
        stroke: isF ? '#e8ecf0' : 'none', 'stroke-width': isF ? 1.5 : 0,
        opacity: isF ? '1' : '0.4'
      }));
      if (p.label && isF) {
        svg.appendChild(svgEl('text', {
          x: sx + 10, y: sy - 8, fill: COLORS.tealLight, 'font-size': '9',
          'font-family': 'JetBrains Mono, monospace'
        })).textContent = p.label;
      }
    });

    shell.querySelector('#pareto-readout').innerHTML = `
      Configurations: <span class="highlight">${configs.length}</span><br>
      Pareto-optimal: <span class="highlight">${frontier.length}</span><br>
      Dominated: ${configs.length - frontier.length}<br>
      <span style="color:#5c7a94">Click to add. Lower MAE + fewer dims = better.</span>
    `;
  }

  container.appendChild(shell);

  svg.addEventListener('click', (e) => {
    const rect = svg.getBoundingClientRect();
    const scaleX = W / rect.width;
    const mx = (e.clientX - rect.left) * scaleX;
    const my = (e.clientY - rect.top) * scaleX;
    if (mx < pad.l || mx > W - pad.r || my < pad.t || my > H - pad.b) return;
    const x = ((mx - pad.l) / pw) * 6;
    const y = ((my - pad.t) / ph) * 6;
    configs.push({ x: Math.round(x), y: +y.toFixed(2) });
    render();
  });

  shell.querySelector('#pareto-reset').addEventListener('click', () => { configs = []; render(); });
  shell.querySelector('#pareto-defect').addEventListener('click', () => {
    configs = [
      { x: 1, y: 3.8, label: '{Complexity}' }, { x: 2, y: 2.1, label: '{Cmplx, Proc}' },
      { x: 3, y: 1.7, label: '{Cmplx, Proc, Size}' }, { x: 5, y: 1.5, label: 'All' },
      { x: 2, y: 3.2, label: '{Size, Halst}' }, { x: 1, y: 5.1, label: '{OO}' },
      { x: 3, y: 2.5, label: '{Size, OO, Halst}' }, { x: 4, y: 1.6 },
    ];
    render();
  });

  render();
}


// ============================================================================
// Demo 6: MRI Perturbation Visualization (Chapter 9)
// Animated perturbation cloud with histogram
// ============================================================================

function demoMRI(container) {
  const W = 480, H = 360;
  const shell = makeDemoShell('Model Robustness Index (MRI)', '\u{1F9EA}', 'ch9');
  const body = shell.querySelector('.demo-body');

  const canvasWrap = document.createElement('div');
  canvasWrap.className = 'demo-canvas-wrap';
  const canvas = document.createElement('canvas');
  canvas.width = W * 2; canvas.height = H * 2;
  canvas.style.width = '100%'; canvas.style.height = 'auto';
  canvasWrap.appendChild(canvas);

  const controls = document.createElement('div');
  controls.className = 'demo-controls';
  controls.innerHTML = `
    <div class="demo-control-group">
      <label>Perturbation scale <span class="value-display" id="mri-scale-val">0.30</span></label>
      <input type="range" id="mri-scale" min="0.05" max="1.0" value="0.3" step="0.01">
    </div>
    <div class="demo-control-group">
      <label>Samples <span class="value-display" id="mri-n-val">300</span></label>
      <input type="range" id="mri-n" min="50" max="1000" value="300" step="50">
    </div>
    <div class="demo-readout" id="mri-readout">
      Click "Run" to generate perturbations.
    </div>
    <div class="demo-btn-group">
      <button class="demo-btn" id="mri-run">Run perturbations</button>
      <button class="demo-btn" id="mri-animate">Animate</button>
    </div>
  `;

  body.appendChild(canvasWrap);
  body.appendChild(controls);
  container.appendChild(shell);

  const ctx = canvas.getContext('2d');
  let animId = null;

  function computeMRI(deviations) {
    const sorted = [...deviations].sort((a, b) => a - b);
    const mean = deviations.reduce((s, v) => s + v, 0) / deviations.length;
    const p75 = sorted[Math.floor(sorted.length * 0.75)];
    const p95 = sorted[Math.floor(sorted.length * 0.95)];
    return { mean, p75, p95, mri: 0.5 * mean + 0.3 * p75 + 0.2 * p95 };
  }

  function drawState(deviations, highlight) {
    const dpr = 2;
    ctx.clearRect(0, 0, W * dpr, H * dpr);
    ctx.save();
    ctx.scale(dpr, dpr);

    // Left: scatter of perturbation points
    const scatterW = W * 0.45, scatterH = H - 40;
    const scX = 30, scY = 20;

    ctx.fillStyle = 'rgba(10,25,41,0.8)';
    ctx.fillRect(scX, scY, scatterW, scatterH);
    ctx.strokeStyle = COLORS.gridLine;
    ctx.strokeRect(scX, scY, scatterW, scatterH);

    // Axes cross
    const ocx = scX + scatterW / 2, ocy = scY + scatterH / 2;
    ctx.strokeStyle = 'rgba(102,194,165,0.2)';
    ctx.beginPath();
    ctx.moveTo(ocx, scY); ctx.lineTo(ocx, scY + scatterH);
    ctx.moveTo(scX, ocy); ctx.lineTo(scX + scatterW, ocy);
    ctx.stroke();

    // Baseline
    ctx.fillStyle = COLORS.teal;
    ctx.beginPath();
    ctx.arc(ocx, ocy, 5, 0, Math.PI * 2);
    ctx.fill();

    // Perturbation dots
    const maxDev = Math.max(1, ...deviations) * 1.2;
    const n = highlight || deviations.length;
    for (let i = 0; i < n; i++) {
      const angle = (i / deviations.length) * Math.PI * 2 + Math.random() * 0.3;
      const r = deviations[i] / maxDev * (scatterW / 2 - 10);
      const px = ocx + Math.cos(angle) * r;
      const py = ocy + Math.sin(angle) * r;
      const alpha = deviations[i] > computeMRI(deviations).p95 ? 0.9 : 0.4;
      ctx.fillStyle = deviations[i] > computeMRI(deviations).p95
        ? COLORS.orange : COLORS.tealLight;
      ctx.globalAlpha = alpha;
      ctx.beginPath();
      ctx.arc(px, py, 2.5, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    // Right: histogram
    const histX = scX + scatterW + 30, histW = W - histX - 20, histH = scatterH;
    const histY = scY;
    const nBins = 20;
    const bins = new Array(nBins).fill(0);
    const binW = maxDev / nBins;
    for (let i = 0; i < n; i++) {
      const b = Math.min(nBins - 1, Math.floor(deviations[i] / binW));
      bins[b]++;
    }
    const maxBin = Math.max(1, ...bins);

    // Draw bins
    const barW = histW / nBins;
    const { mean, p75, p95, mri } = computeMRI(deviations);
    for (let i = 0; i < nBins; i++) {
      const barH = (bins[i] / maxBin) * (histH - 20);
      const bx = histX + i * barW;
      const by = histY + histH - barH;
      const val = (i + 0.5) * binW;
      ctx.fillStyle = val > p95 ? COLORS.orange : val > p75 ? COLORS.gold : COLORS.tealLight;
      ctx.globalAlpha = 0.7;
      ctx.fillRect(bx, by, barW - 1, barH);
    }
    ctx.globalAlpha = 1;

    // Percentile lines
    const drawLine = (val, color, label) => {
      const lx = histX + (val / maxDev) * histW;
      if (lx > histX && lx < histX + histW) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 3]);
        ctx.beginPath();
        ctx.moveTo(lx, histY);
        ctx.lineTo(lx, histY + histH);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = color;
        ctx.font = '10px JetBrains Mono';
        ctx.fillText(label, lx + 3, histY + 12);
      }
    };
    drawLine(mean, COLORS.tealLight, 'mean');
    drawLine(p75, COLORS.gold, 'P75');
    drawLine(p95, COLORS.orange, 'P95');

    // Labels
    ctx.fillStyle = COLORS.text;
    ctx.font = '10px JetBrains Mono';
    ctx.fillText('Perturbation cloud', scX, scY - 5);
    ctx.fillText('Deviation histogram', histX, histY - 5);
    ctx.fillText('\u03C9 (deviation)', histX + histW / 2 - 30, histY + histH + 15);

    ctx.restore();

    // Update readout
    shell.querySelector('#mri-readout').innerHTML = `
      Mean \u03C9: <span class="highlight">${mean.toFixed(3)}</span><br>
      P75: <span style="color:${COLORS.gold}">${p75.toFixed(3)}</span><br>
      P95: <span class="warn">${p95.toFixed(3)}</span><br>
      <strong>MRI = <span class="highlight">${mri.toFixed(3)}</span></strong><br>
      <span style="color:#5c7a94">= 0.5\u00B7mean + 0.3\u00B7P75 + 0.2\u00B7P95</span>
    `;
  }

  function generate() {
    const scale = +shell.querySelector('#mri-scale').value;
    const n = +shell.querySelector('#mri-n').value;
    const devs = [];
    for (let i = 0; i < n; i++) {
      // Log-normal perturbation model
      const z1 = Math.sqrt(-2 * Math.log(Math.random())) * Math.cos(2 * Math.PI * Math.random());
      const z2 = Math.sqrt(-2 * Math.log(Math.random())) * Math.cos(2 * Math.PI * Math.random());
      const dev = Math.abs(z1 * scale) + Math.abs(z2 * scale * 0.5);
      devs.push(dev);
    }
    return devs;
  }

  let currentDevs = generate();
  drawState(currentDevs);

  shell.querySelector('#mri-run').addEventListener('click', () => {
    if (animId) { cancelAnimationFrame(animId); animId = null; }
    currentDevs = generate();
    drawState(currentDevs);
  });

  shell.querySelector('#mri-animate').addEventListener('click', () => {
    if (animId) { cancelAnimationFrame(animId); animId = null; return; }
    currentDevs = generate();
    let frame = 0;
    const total = currentDevs.length;
    function step() {
      frame = Math.min(total, frame + Math.ceil(total / 60));
      drawState(currentDevs, frame);
      if (frame < total) animId = requestAnimationFrame(step);
      else animId = null;
    }
    step();
  });

  ['mri-scale', 'mri-n'].forEach(id => {
    shell.querySelector(`#${id}`).addEventListener('input', () => {
      shell.querySelector(`#${id}-val`).textContent =
        id === 'mri-scale' ? (+shell.querySelector(`#${id}`).value).toFixed(2) : shell.querySelector(`#${id}`).value;
    });
  });
}


// ============================================================================
// Demo 7: D4 Group Actions (Chapter 13)
// Interactive grid transformation with all 8 D4 elements
// ============================================================================

function demoD4(container) {
  const shell = makeDemoShell('D\u2084 Dihedral Group Actions', '\u{1F504}', 'ch13');
  const body = shell.querySelector('.demo-body');

  const canvasWrap = document.createElement('div');
  canvasWrap.className = 'demo-canvas-wrap';
  canvasWrap.style.display = 'flex';
  canvasWrap.style.flexDirection = 'column';
  canvasWrap.style.alignItems = 'center';
  canvasWrap.style.gap = '12px';

  // A 5x5 colored grid
  const N = 5;
  const gridColors = [
    ['#1b9e77','#1b9e77','#d95f02','#0a1929','#0a1929'],
    ['#0a1929','#1b9e77','#d95f02','#0a1929','#0a1929'],
    ['#0a1929','#0a1929','#d95f02','#0a1929','#0a1929'],
    ['#0a1929','#0a1929','#d95f02','#7570b3','#0a1929'],
    ['#0a1929','#0a1929','#d95f02','#7570b3','#7570b3'],
  ];

  let currentGrid = gridColors.map(r => [...r]);

  const gridEl = document.createElement('div');
  gridEl.className = 'demo-grid';
  gridEl.style.gridTemplateColumns = `repeat(${N}, 1fr)`;

  for (let r = 0; r < N; r++) {
    for (let c = 0; c < N; c++) {
      const cell = document.createElement('div');
      cell.className = 'demo-grid-cell';
      cell.id = `d4-cell-${r}-${c}`;
      gridEl.appendChild(cell);
    }
  }
  canvasWrap.appendChild(gridEl);

  const statusEl = document.createElement('div');
  statusEl.style.cssText = 'font-family:JetBrains Mono,monospace; font-size:0.78rem; color:#8fa4b8; text-align:center;';
  statusEl.id = 'd4-status';
  statusEl.textContent = 'Identity (e)';
  canvasWrap.appendChild(statusEl);

  const controls = document.createElement('div');
  controls.className = 'demo-controls';
  controls.innerHTML = `
    <div class="demo-control-group">
      <label>Rotations</label>
      <div class="demo-btn-group">
        <button class="demo-btn d4-btn" data-op="e">e (identity)</button>
        <button class="demo-btn d4-btn" data-op="r90">r\u2080\u2089\u2080</button>
        <button class="demo-btn d4-btn" data-op="r180">r\u2081\u2088\u2080</button>
        <button class="demo-btn d4-btn" data-op="r270">r\u2082\u2087\u2080</button>
      </div>
    </div>
    <div class="demo-control-group">
      <label>Reflections</label>
      <div class="demo-btn-group">
        <button class="demo-btn d4-btn" data-op="sh">s\u2095 (horiz)</button>
        <button class="demo-btn d4-btn" data-op="sv">s\u1D65 (vert)</button>
        <button class="demo-btn d4-btn" data-op="sd1">s\u2081 (diag \u2572)</button>
        <button class="demo-btn d4-btn" data-op="sd2">s\u2082 (diag \u2571)</button>
      </div>
    </div>
    <div class="demo-readout">
      |D\u2084| = <span class="highlight">8</span> elements<br>
      4 rotations + 4 reflections<br>
      Each transforms the grid while preserving spatial relationships.<br>
      <span style="color:#5c7a94">ARC-AGI puzzles have natural D\u2084 symmetry.</span>
    </div>
    <div class="demo-btn-group">
      <button class="demo-btn" id="d4-reset">Reset</button>
      <button class="demo-btn" id="d4-random">Random orbit</button>
    </div>
  `;

  body.appendChild(canvasWrap);
  body.appendChild(controls);

  function applyOp(grid, op) {
    const n = grid.length;
    const out = Array.from({ length: n }, () => Array(n).fill('#0a1929'));
    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        let nr, nc;
        switch (op) {
          case 'e': nr = r; nc = c; break;
          case 'r90': nr = c; nc = n - 1 - r; break;
          case 'r180': nr = n - 1 - r; nc = n - 1 - c; break;
          case 'r270': nr = n - 1 - c; nc = r; break;
          case 'sh': nr = n - 1 - r; nc = c; break;
          case 'sv': nr = r; nc = n - 1 - c; break;
          case 'sd1': nr = c; nc = r; break;
          case 'sd2': nr = n - 1 - c; nc = n - 1 - r; break;
          default: nr = r; nc = c;
        }
        out[nr][nc] = grid[r][c];
      }
    }
    return out;
  }

  const opLabels = {
    e: 'Identity (e)', r90: 'Rotation 90\u00B0', r180: 'Rotation 180\u00B0', r270: 'Rotation 270\u00B0',
    sh: 'Reflection \u2194 horizontal', sv: 'Reflection \u2195 vertical',
    sd1: 'Reflection \u2572 main diagonal', sd2: 'Reflection \u2571 anti-diagonal'
  };

  function renderGrid() {
    for (let r = 0; r < N; r++) {
      for (let c = 0; c < N; c++) {
        const cell = document.getElementById(`d4-cell-${r}-${c}`);
        if (cell) cell.style.backgroundColor = currentGrid[r][c];
      }
    }
  }

  container.appendChild(shell);

  shell.querySelectorAll('.d4-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const op = btn.dataset.op;
      currentGrid = applyOp(gridColors, op);
      shell.querySelector('#d4-status').textContent = opLabels[op];
      renderGrid();
    });
  });

  shell.querySelector('#d4-reset').addEventListener('click', () => {
    currentGrid = gridColors.map(r => [...r]);
    shell.querySelector('#d4-status').textContent = 'Identity (e)';
    renderGrid();
  });

  shell.querySelector('#d4-random').addEventListener('click', () => {
    const ops = ['e', 'r90', 'r180', 'r270', 'sh', 'sv', 'sd1', 'sd2'];
    let i = 0;
    const cycle = () => {
      const op = ops[i % ops.length];
      currentGrid = applyOp(gridColors, op);
      shell.querySelector('#d4-status').textContent = opLabels[op];
      renderGrid();
      i++;
      if (i < ops.length) setTimeout(cycle, 400);
    };
    cycle();
  });

  renderGrid();
}


// ============================================================================
// Demo 8: Bond Geodesic Pathfinding (Chapter 6)
// A* on a 2D space with moral boundary regions
// ============================================================================

function demoBondGeodesic(container) {
  const W = 480, H = 400;
  const shell = makeDemoShell('Bond Geodesic — Pathfinding with Moral Boundaries', '\u{1F6E4}', 'ch6');
  const body = shell.querySelector('.demo-body');

  const canvasWrap = document.createElement('div');
  canvasWrap.className = 'demo-canvas-wrap';
  const canvas = document.createElement('canvas');
  canvas.width = W * 2; canvas.height = H * 2;
  canvas.style.width = '100%'; canvas.style.height = 'auto';
  canvas.style.cursor = 'crosshair';
  canvasWrap.appendChild(canvas);

  const controls = document.createElement('div');
  controls.className = 'demo-controls';
  controls.innerHTML = `
    <div class="demo-control-group">
      <label>Boundary penalty <span class="value-display" id="penalty-val">5.0</span></label>
      <input type="range" id="penalty-slider" min="0" max="20" value="5" step="0.5">
    </div>
    <div class="demo-readout" id="geo-readout">
      <span style="color:${COLORS.orange}">Orange zone</span> = deception boundary<br>
      <span style="color:${COLORS.pink}">Pink zone</span> = coercion boundary<br>
      <span style="color:${COLORS.tealLight}">Teal path</span> = Bond Geodesic<br>
      <span style="color:${COLORS.text}">Gray path</span> = Euclidean shortest<br>
      Click to set start (1st) and goal (2nd).
    </div>
    <div class="demo-btn-group">
      <button class="demo-btn" id="geo-reset">Reset</button>
      <button class="demo-btn" id="geo-preset">Ultimatum game</button>
    </div>
  `;

  body.appendChild(canvasWrap);
  body.appendChild(controls);
  container.appendChild(shell);

  const ctx = canvas.getContext('2d');
  const dpr = 2;

  // Boundary zones (circles representing moral constraints)
  const zones = [
    { x: 200, y: 160, r: 60, color: COLORS.orange, label: 'Deception', penalty: 1 },
    { x: 340, y: 250, r: 50, color: COLORS.pink, label: 'Coercion', penalty: 1 },
    { x: 120, y: 300, r: 45, color: COLORS.purple, label: 'Exploitation', penalty: 1 },
  ];

  let startPt = { x: 60, y: 80 };
  let goalPt = { x: 420, y: 350 };
  let clickCount = 0;

  function costAt(x, y, penalty) {
    let cost = 1;
    for (const z of zones) {
      const d = Math.sqrt((x - z.x) ** 2 + (y - z.y) ** 2);
      if (d < z.r) {
        cost += penalty * (1 - d / z.r);
      } else if (d < z.r * 1.5) {
        cost += penalty * 0.3 * (1 - (d - z.r) / (z.r * 0.5));
      }
    }
    return cost;
  }

  // Simple grid-based A*
  function findPath(start, goal, penalty) {
    const step = 8;
    const cols = Math.ceil(W / step), rows = Math.ceil(H / step);
    const toIdx = (r, c) => r * cols + c;
    const sr = Math.floor(start.y / step), sc = Math.floor(start.x / step);
    const gr = Math.floor(goal.y / step), gc = Math.floor(goal.x / step);

    const dist = new Float32Array(rows * cols).fill(Infinity);
    const prev = new Int32Array(rows * cols).fill(-1);
    dist[toIdx(sr, sc)] = 0;

    // Priority queue (simple sorted array for small grids)
    const open = [{ r: sr, c: sc, f: 0 }];
    const closed = new Set();

    const dirs = [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [-1, 1], [1, -1], [1, 1]];

    while (open.length > 0) {
      open.sort((a, b) => a.f - b.f);
      const cur = open.shift();
      const idx = toIdx(cur.r, cur.c);
      if (closed.has(idx)) continue;
      closed.add(idx);

      if (cur.r === gr && cur.c === gc) break;

      for (const [dr, dc] of dirs) {
        const nr = cur.r + dr, nc = cur.c + dc;
        if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
        const nIdx = toIdx(nr, nc);
        if (closed.has(nIdx)) continue;

        const moveCost = (Math.abs(dr) + Math.abs(dc) > 1 ? 1.414 : 1) * step;
        const cx = nc * step + step / 2, cy = nr * step + step / 2;
        const edgeCost = moveCost * costAt(cx, cy, penalty);
        const newDist = dist[idx] + edgeCost;

        if (newDist < dist[nIdx]) {
          dist[nIdx] = newDist;
          prev[nIdx] = idx;
          const h = Math.sqrt((nr - gr) ** 2 + (nc - gc) ** 2) * step;
          open.push({ r: nr, c: nc, f: newDist + h });
        }
      }
    }

    // Reconstruct path
    const path = [];
    let ci = toIdx(gr, gc);
    while (ci !== -1) {
      const r = Math.floor(ci / cols), c = ci % cols;
      path.unshift({ x: c * step + step / 2, y: r * step + step / 2 });
      ci = prev[ci];
    }
    return { path, cost: dist[toIdx(gr, gc)] };
  }

  function render() {
    const penalty = +shell.querySelector('#penalty-slider').value;
    ctx.clearRect(0, 0, W * dpr, H * dpr);
    ctx.save();
    ctx.scale(dpr, dpr);

    // Background cost field
    const imgData = ctx.createImageData(W, H);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const c = costAt(x, y, penalty);
        const idx = (y * W + x) * 4;
        if (c > 1.5) {
          // In a boundary zone — tint with zone color
          const intensity = Math.min(1, (c - 1) / penalty * 0.6);
          let zoneColor = zones.find(z => {
            const d = Math.sqrt((x - z.x) ** 2 + (y - z.y) ** 2);
            return d < z.r * 1.5;
          });
          if (zoneColor) {
            const hex = zoneColor.color;
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            imgData.data[idx] = 10 + r * intensity * 0.5;
            imgData.data[idx + 1] = 22 + g * intensity * 0.5;
            imgData.data[idx + 2] = 34 + b * intensity * 0.5;
          } else {
            imgData.data[idx] = 10; imgData.data[idx + 1] = 25; imgData.data[idx + 2] = 41;
          }
        } else {
          imgData.data[idx] = 10; imgData.data[idx + 1] = 22; imgData.data[idx + 2] = 34;
        }
        imgData.data[idx + 3] = 255;
      }
    }
    ctx.putImageData(imgData, 0, 0);

    // Zone labels
    zones.forEach(z => {
      ctx.strokeStyle = z.color;
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.4;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.arc(z.x, z.y, z.r, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.globalAlpha = 1;

      ctx.fillStyle = z.color;
      ctx.globalAlpha = 0.6;
      ctx.font = '10px JetBrains Mono';
      ctx.textAlign = 'center';
      ctx.fillText(z.label, z.x, z.y + 4);
      ctx.globalAlpha = 1;
    });

    // Euclidean straight line
    ctx.strokeStyle = COLORS.text;
    ctx.lineWidth = 1.5;
    ctx.globalAlpha = 0.4;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(startPt.x, startPt.y);
    ctx.lineTo(goalPt.x, goalPt.y);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;

    // Bond Geodesic (A* path)
    const { path, cost } = findPath(startPt, goalPt, penalty);
    if (path.length > 1) {
      ctx.strokeStyle = COLORS.tealLight;
      ctx.lineWidth = 2.5;
      ctx.shadowColor = COLORS.teal;
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.moveTo(path[0].x, path[0].y);
      for (let i = 1; i < path.length; i++) ctx.lineTo(path[i].x, path[i].y);
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    // Euclidean cost
    const eucCost = Math.sqrt((goalPt.x - startPt.x) ** 2 + (goalPt.y - startPt.y) ** 2);
    const { cost: eucPenCost } = findPath(startPt, goalPt, 0);

    // Start & goal
    ctx.fillStyle = COLORS.green;
    ctx.beginPath(); ctx.arc(startPt.x, startPt.y, 7, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = COLORS.textBright;
    ctx.font = '10px JetBrains Mono';
    ctx.textAlign = 'left';
    ctx.fillText('Start', startPt.x + 10, startPt.y + 4);

    ctx.fillStyle = COLORS.pink;
    ctx.beginPath(); ctx.arc(goalPt.x, goalPt.y, 7, 0, Math.PI * 2); ctx.fill();
    ctx.fillText('Goal', goalPt.x + 10, goalPt.y + 4);

    ctx.restore();

    shell.querySelector('#penalty-val').textContent = penalty.toFixed(1);
    shell.querySelector('#geo-readout').innerHTML = `
      Euclidean distance: <span style="color:${COLORS.text}">${eucCost.toFixed(0)}</span><br>
      Bond Geodesic cost: <span class="highlight">${cost.toFixed(0)}</span><br>
      Detour ratio: <span class="${cost/eucCost > 1.5 ? 'warn' : 'highlight'}">${(cost / eucCost).toFixed(2)}x</span><br>
      <span style="color:#5c7a94">Penalty = ${penalty.toFixed(1)}. Higher penalty \u2192 longer detour.</span>
    `;
  }

  canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width * W;
    const y = (e.clientY - rect.top) / rect.height * H;
    if (clickCount % 2 === 0) {
      startPt = { x, y };
    } else {
      goalPt = { x, y };
    }
    clickCount++;
    render();
  });

  shell.querySelector('#penalty-slider').addEventListener('input', render);
  shell.querySelector('#geo-reset').addEventListener('click', () => {
    startPt = { x: 60, y: 80 }; goalPt = { x: 420, y: 350 }; clickCount = 0;
    render();
  });
  shell.querySelector('#geo-preset').addEventListener('click', () => {
    startPt = { x: 50, y: 60 }; goalPt = { x: 440, y: 340 };
    shell.querySelector('#penalty-slider').value = 8;
    render();
  });

  render();
}


// ============================================================================
// Injection system — inserts demos after specific headings
// ============================================================================

const DEMO_MAP = {
  'chapter-01-why-geometry': {
    fn: demoScalarIrrecoverability,
    after: '1.1'  // After "The Limitations of Scalar Metrics"
  },
  'chapter-02-mahalanobis-distance': {
    fn: demoMahalanobis,
    after: '2.1'  // After "From Euclidean to Mahalanobis" or first heading
  },
  'chapter-03-hyperbolic-geometry': {
    fn: demoPoincare,
    after: '3.1'  // After "Why Hyperbolic Space"
  },
  'chapter-05-topological-data-analysis': {
    fn: demoPersistence,
    after: '5.3'  // After "Persistent Homology"
  },
  'chapter-06-pathfinding-on-manifolds': {
    fn: demoBondGeodesic,
    after: '6.4'  // After "The Bond Geodesic"
  },
  'chapter-08-pareto-optimization': {
    fn: demoPareto,
    after: '8.2'  // After "Why Scalarization Fails"
  },
  'chapter-09-adversarial-robustness': {
    fn: demoMRI,
    after: '9.2'  // After "The MRI Formulation"
  },
  'chapter-13-group-theoretic-augmentation': {
    fn: demoD4,
    after: '13.2'  // After "The Dihedral Group D4"
  }
};

function injectDemos(chapterId, contentElement) {
  const config = DEMO_MAP[chapterId];
  if (!config) return;

  // Find the target heading (h2 containing the section number)
  const headings = contentElement.querySelectorAll('h2');
  let targetHeading = null;

  for (const h of headings) {
    if (h.textContent.includes(config.after)) {
      targetHeading = h;
      break;
    }
  }

  if (!targetHeading) {
    // Fallback: insert after the first h2
    targetHeading = headings[0];
  }

  if (targetHeading) {
    // Find the next sibling that is another h2 (insert before it)
    let insertBefore = targetHeading.nextElementSibling;
    while (insertBefore && insertBefore.tagName !== 'H2') {
      insertBefore = insertBefore.nextElementSibling;
    }

    const wrapper = document.createElement('div');
    if (insertBefore) {
      contentElement.insertBefore(wrapper, insertBefore);
    } else {
      // Insert after the last element of this section
      contentElement.appendChild(wrapper);
    }
    config.fn(wrapper);
  }
}

// Expose globally
window.injectDemos = injectDemos;
