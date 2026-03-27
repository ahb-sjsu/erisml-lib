/* ==========================================================================
   Geometric AI — Interactive Visualizations
   1. Reward Scalar Collapse: multi-dimensional values collapsed to scalar
   2. Sycophancy Manifold: user pressure pulls AI response from truth
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initRewardScalarCollapse();
  initSycophancyManifold();
});

/* ==========================================================================
   1. REWARD SCALAR COLLAPSE — 8 value dimensions collapsed to a scalar
   Two AI systems with same reward score but dangerously different profiles.
   ========================================================================== */
function initRewardScalarCollapse() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const toc = section.querySelector('.toc-grid');
  if (!toc) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.innerHTML =
    '<h3 class="demo-title">Reward Scalar Collapse</h3>' +
    '<p class="demo-subtitle">Two AI systems with the same reward score. Drag the slider to collapse 8 value dimensions into one number.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="ai-reward-canvas" width="520" height="340"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<label class="demo-slider-label">' +
        '<span>Collapse</span>' +
        '<input type="range" min="0" max="100" value="0" class="demo-slider" id="reward-collapse-slider">' +
        '<span class="demo-val" id="reward-collapse-val">Value Manifold</span>' +
      '</label>' +
    '</div>';

  toc.parentNode.insertBefore(demo, toc.nextSibling);

  const canvas = document.getElementById('ai-reward-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const dimNames = ['Helpful', 'Honest', 'Harmless', 'Creative', 'Accurate', 'Empathic', 'Fair', 'Robust'];
  const dimColors = ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#8da0cb'];
  const N = dimNames.length;

  // AI-A: helpful and creative but dishonest and unfair
  const aiA = [0.95, 0.20, 0.55, 0.90, 0.35, 0.70, 0.25, 0.60]; // avg ~0.5625
  // AI-B: honest and fair but less helpful and creative
  const aiB = [0.30, 0.90, 0.75, 0.25, 0.80, 0.40, 0.85, 0.25]; // avg ~0.5625

  function draw(collapse) {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const t = collapse / 100;

    const cx1 = w / 4;
    const cx2 = 3 * w / 4;
    const cy = h / 2 - 10;
    const maxR = 110;

    const avgA = aiA.reduce((a, b) => a + b, 0) / N;
    const avgB = aiB.reduce((a, b) => a + b, 0) / N;

    // Labels
    ctx.fillStyle = '#e8ecf0';
    ctx.font = '600 14px "Crimson Pro", serif';
    ctx.textAlign = 'center';
    ctx.fillText('AI System A', cx1, 20);
    ctx.fillText('AI System B', cx2, 20);

    // Draw radar chart for one AI system
    function drawRadar(cx, values, avg) {
      const angleStep = (2 * Math.PI) / N;

      // Draw axis lines and labels (fade with collapse)
      if (t < 0.85) {
        const labelAlpha = 1 - t * 1.1;
        for (let i = 0; i < N; i++) {
          const angle = i * angleStep - Math.PI / 2;
          const ex = cx + Math.cos(angle) * maxR;
          const ey = cy + Math.sin(angle) * maxR;
          ctx.strokeStyle = 'rgba(88,120,150,' + (0.25 * labelAlpha) + ')';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.lineTo(ex, ey);
          ctx.stroke();

          // Dim labels
          const lx = cx + Math.cos(angle) * (maxR + 16);
          const ly = cy + Math.sin(angle) * (maxR + 16);
          ctx.fillStyle = 'rgba(143,164,184,' + labelAlpha + ')';
          ctx.font = '9px Inter, sans-serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(dimNames[i], lx, ly);
        }

        // Reference circles
        for (let ring = 0.25; ring <= 1.0; ring += 0.25) {
          ctx.strokeStyle = 'rgba(88,120,150,' + (0.1 * labelAlpha) + ')';
          ctx.beginPath();
          ctx.arc(cx, cy, maxR * ring, 0, Math.PI * 2);
          ctx.stroke();
        }
      }

      // Interpolate values toward average (collapse)
      const collapsedVals = values.map(v => v * (1 - t) + avg * t);

      // Draw filled polygon
      ctx.beginPath();
      for (let i = 0; i < N; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const r = collapsedVals[i] * maxR;
        const px = cx + Math.cos(angle) * r;
        const py = cy + Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();

      if (t < 0.95) {
        // Colored fill with gradient-like effect
        ctx.fillStyle = 'rgba(27,158,119,' + (0.15 * (1 - t) + 0.05) + ')';
        ctx.fill();
        ctx.strokeStyle = 'rgba(27,158,119,' + (0.7 * (1 - t) + 0.15) + ')';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Draw individual value dots on polygon vertices
      for (let i = 0; i < N; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const r = collapsedVals[i] * maxR;
        const px = cx + Math.cos(angle) * r;
        const py = cy + Math.sin(angle) * r;
        const dotAlpha = (1 - t);
        if (dotAlpha > 0.05) {
          ctx.fillStyle = dimColors[i];
          ctx.globalAlpha = dotAlpha;
          ctx.beginPath();
          ctx.arc(px, py, 4, 0, Math.PI * 2);
          ctx.fill();
          ctx.globalAlpha = 1;
        }
      }

      // When fully collapsed, draw a single circle (the scalar)
      if (t > 0.5) {
        const scalarAlpha = (t - 0.5) * 2;
        ctx.strokeStyle = 'rgba(136,153,170,' + scalarAlpha + ')';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(cx, cy, avg * maxR, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = 'rgba(136,153,170,' + (scalarAlpha * 0.1) + ')';
        ctx.fill();
      }
    }

    drawRadar(cx1, aiA, avgA);
    drawRadar(cx2, aiB, avgB);

    // Reward scores
    ctx.fillStyle = t > 0.5 ? '#e8ecf0' : '#5c7a94';
    ctx.font = '600 16px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    ctx.fillText('R = ' + avgA.toFixed(3), cx1, h - 20);
    ctx.fillText('R = ' + avgB.toFixed(3), cx2, h - 20);

    // Divider
    ctx.strokeStyle = 'rgba(102,194,165,0.2)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(w / 2, 10);
    ctx.lineTo(w / 2, h - 10);
    ctx.stroke();
    ctx.setLineDash([]);

    // Warning at high collapse
    if (t > 0.8) {
      ctx.fillStyle = '#d95f02';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Same reward. A is helpful but dishonest. B is honest but unhelpful.', w / 2, h - 4);
    }
  }

  draw(0);

  document.getElementById('reward-collapse-slider').addEventListener('input', function() {
    const v = parseInt(this.value);
    document.getElementById('reward-collapse-val').textContent =
      v < 25 ? 'Value Manifold' : v < 60 ? 'Collapsing...' : v < 90 ? 'Nearly Scalar' : 'Scalar Reward';
    draw(v);
  });
}

/* ==========================================================================
   2. SYCOPHANCY MANIFOLD — User pressure pulls AI response from truth
   on a curved manifold. Shows drift along a geodesic away from truth.
   ========================================================================== */
function initSycophancyManifold() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const prev = section.querySelectorAll('.scalar-tensor-demo');
  const anchor = prev[prev.length - 1];
  if (!anchor) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.style.marginTop = '32px';
  demo.innerHTML =
    '<h3 class="demo-title">Sycophancy Manifold</h3>' +
    '<p class="demo-subtitle">User pressure pulls the AI response away from truth along a curved geodesic. Watch the drift in real-time.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="ai-sycophancy-canvas" width="520" height="340"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<label class="demo-slider-label">' +
        '<span>User Pressure</span>' +
        '<input type="range" min="0" max="100" value="0" class="demo-slider" id="sycophancy-slider">' +
        '<span class="demo-val" id="sycophancy-val">None</span>' +
      '</label>' +
      '<div style="display:flex;gap:24px;justify-content:center;margin-top:8px;font-size:12px;color:var(--text-secondary)">' +
        '<span style="color:#1b9e77">Truth (fixed)</span>' +
        '<span style="color:#d95f02">AI Response (drifting)</span>' +
        '<span style="color:#7570b3">Geodesic path</span>' +
      '</div>' +
    '</div>';

  anchor.parentNode.insertBefore(demo, anchor.nextSibling);

  const canvas = document.getElementById('ai-sycophancy-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // Manifold parameters
  const w = canvas.width, h = canvas.height;
  const manifoldCx = w * 0.45;
  const manifoldCy = h * 0.48;
  const manifoldRx = 180;
  const manifoldRy = 120;

  // Truth position (fixed point on manifold)
  const truthAngle = -0.4;
  const truthX = manifoldCx + manifoldRx * 0.45 * Math.cos(truthAngle);
  const truthY = manifoldCy + manifoldRy * 0.35 * Math.sin(truthAngle) - 20;

  // "What user wants to hear" — target of sycophantic drift
  const userWantAngle = 2.2;
  const userWantX = manifoldCx + manifoldRx * 0.7 * Math.cos(userWantAngle);
  const userWantY = manifoldCy + manifoldRy * 0.65 * Math.sin(userWantAngle) + 10;

  function draw(pressure) {
    ctx.clearRect(0, 0, w, h);
    const t = pressure / 100;

    // Draw manifold surface (elliptical region with curvature lines)
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(manifoldCx, manifoldCy, manifoldRx, manifoldRy, 0, 0, Math.PI * 2);
    const grad = ctx.createRadialGradient(manifoldCx, manifoldCy, 20, manifoldCx, manifoldCy, manifoldRx);
    grad.addColorStop(0, 'rgba(20,37,54,0.7)');
    grad.addColorStop(1, 'rgba(20,37,54,0.2)');
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.strokeStyle = 'rgba(88,120,150,0.3)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.restore();

    // Curvature grid lines on manifold (showing it's curved)
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(manifoldCx, manifoldCy, manifoldRx, manifoldRy, 0, 0, Math.PI * 2);
    ctx.clip();

    ctx.strokeStyle = 'rgba(88,120,150,0.1)';
    ctx.lineWidth = 1;
    // Curved horizontal lines
    for (let i = -3; i <= 3; i++) {
      ctx.beginPath();
      for (let x = -manifoldRx; x <= manifoldRx; x += 4) {
        const normX = x / manifoldRx;
        const curve = Math.sqrt(Math.max(0, 1 - normX * normX));
        const yOff = i * 30 + normX * normX * 15;
        const px = manifoldCx + x;
        const py = manifoldCy + yOff;
        if (x === -manifoldRx) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();
    }
    // Curved vertical lines
    for (let i = -4; i <= 4; i++) {
      ctx.beginPath();
      for (let y = -manifoldRy; y <= manifoldRy; y += 4) {
        const normY = y / manifoldRy;
        const xOff = i * 35 + normY * normY * 12;
        const px = manifoldCx + xOff;
        const py = manifoldCy + y;
        if (y === -manifoldRy) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();
    }
    ctx.restore();

    // Compute AI response position along curved geodesic
    // Use a quadratic Bezier to simulate geodesic curvature
    const ctrlX = manifoldCx + manifoldRx * 0.1;
    const ctrlY = manifoldCy - manifoldRy * 0.25;
    const aiX = (1 - t) * (1 - t) * truthX + 2 * (1 - t) * t * ctrlX + t * t * userWantX;
    const aiY = (1 - t) * (1 - t) * truthY + 2 * (1 - t) * t * ctrlY + t * t * userWantY;

    // Draw the geodesic path (full arc, faded)
    ctx.strokeStyle = 'rgba(117,112,179,0.25)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    for (let s = 0; s <= 1; s += 0.01) {
      const px = (1 - s) * (1 - s) * truthX + 2 * (1 - s) * s * ctrlX + s * s * userWantX;
      const py = (1 - s) * (1 - s) * truthY + 2 * (1 - s) * s * ctrlY + s * s * userWantY;
      if (s === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw the traversed portion of geodesic (solid, bright)
    if (t > 0.01) {
      ctx.strokeStyle = 'rgba(117,112,179,0.7)';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      for (let s = 0; s <= t; s += 0.005) {
        const px = (1 - s) * (1 - s) * truthX + 2 * (1 - s) * s * ctrlX + s * s * userWantX;
        const py = (1 - s) * (1 - s) * truthY + 2 * (1 - s) * s * ctrlY + s * s * userWantY;
        if (s === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();
    }

    // Draw "what user wants to hear" zone
    ctx.fillStyle = 'rgba(217,95,2,0.08)';
    ctx.beginPath();
    ctx.arc(userWantX, userWantY, 25, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = 'rgba(217,95,2,0.3)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = 'rgba(217,95,2,0.5)';
    ctx.font = '9px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('User wants', userWantX, userWantY + 35);
    ctx.fillText('to hear', userWantX, userWantY + 46);

    // Draw truth point
    ctx.fillStyle = '#1b9e77';
    ctx.beginPath();
    ctx.arc(truthX, truthY, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#1b9e77';
    ctx.font = '600 11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('TRUTH', truthX, truthY - 14);

    // Draw AI response point
    ctx.fillStyle = '#d95f02';
    ctx.beginPath();
    ctx.arc(aiX, aiY, 6, 0, Math.PI * 2);
    ctx.fill();
    // Pulsing glow when drifting
    if (t > 0.1) {
      ctx.fillStyle = 'rgba(217,95,2,' + (0.15 * t) + ')';
      ctx.beginPath();
      ctx.arc(aiX, aiY, 12 + t * 6, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.fillStyle = '#d95f02';
    ctx.font = '600 11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('AI', aiX, aiY - 14);

    // Draw connecting line from truth to AI (shows distance)
    if (t > 0.02) {
      ctx.strokeStyle = 'rgba(233,114,76,0.4)';
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 3]);
      ctx.beginPath();
      ctx.moveTo(truthX, truthY);
      ctx.lineTo(aiX, aiY);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Metrics panel (right side)
    const metricX = w - 90;
    const metricY = 40;

    // Geodesic distance from truth (not Euclidean — grows nonlinearly on curved manifold)
    // On a Poincare-like manifold, distance grows faster as you approach the boundary
    const eucDist = Math.sqrt((aiX - truthX) ** 2 + (aiY - truthY) ** 2);
    const maxDist = Math.sqrt((userWantX - truthX) ** 2 + (userWantY - truthY) ** 2);
    const normDist = eucDist / maxDist;
    // Manifold curvature amplifies distance nonlinearly
    const geodesicDist = Math.tanh(normDist * 2.5) / Math.tanh(2.5);

    const userSatisfaction = t;
    // Sycophancy index: ratio of drift-toward-user vs truth-holding
    const sycophancyIdx = t > 0.01 ? geodesicDist * userSatisfaction : 0;

    ctx.fillStyle = 'rgba(20,37,54,0.8)';
    ctx.fillRect(metricX - 55, metricY - 10, 115, 100);
    ctx.strokeStyle = 'rgba(88,120,150,0.3)';
    ctx.lineWidth = 1;
    ctx.strokeRect(metricX - 55, metricY - 10, 115, 100);

    ctx.fillStyle = '#8fa4b8';
    ctx.font = '600 9px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('METRICS', metricX + 2, metricY + 4);

    // Distance from truth
    ctx.fillStyle = geodesicDist > 0.6 ? '#d95f02' : '#1b9e77';
    ctx.font = '600 12px "JetBrains Mono", monospace';
    ctx.fillText(geodesicDist.toFixed(3), metricX + 2, metricY + 24);
    ctx.fillStyle = '#8fa4b8';
    ctx.font = '9px Inter, sans-serif';
    ctx.fillText('Truth Distance', metricX + 2, metricY + 36);

    // User satisfaction
    ctx.fillStyle = '#e6ab02';
    ctx.font = '600 12px "JetBrains Mono", monospace';
    ctx.fillText(userSatisfaction.toFixed(3), metricX + 2, metricY + 54);
    ctx.fillStyle = '#8fa4b8';
    ctx.font = '9px Inter, sans-serif';
    ctx.fillText('User Satisfaction', metricX + 2, metricY + 66);

    // Sycophancy index
    ctx.fillStyle = sycophancyIdx > 0.4 ? '#e7298a' : '#7570b3';
    ctx.font = '600 12px "JetBrains Mono", monospace';
    ctx.fillText(sycophancyIdx.toFixed(3), metricX + 2, metricY + 84);
    ctx.fillStyle = '#8fa4b8';
    ctx.font = '9px Inter, sans-serif';
    ctx.fillText('Sycophancy Index', metricX + 2, metricY + 96);

    // Insight text at high pressure
    if (t > 0.6) {
      ctx.fillStyle = '#e7298a';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Curvature amplifies drift: small pressure, large deviation.', w / 2, h - 8);
    } else if (t > 0.25) {
      ctx.fillStyle = '#7570b3';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('AI drifts along geodesic away from truth.', w / 2, h - 8);
    }
  }

  draw(0);

  document.getElementById('sycophancy-slider').addEventListener('input', function() {
    const v = parseInt(this.value);
    document.getElementById('sycophancy-val').textContent =
      v < 15 ? 'None' : v < 40 ? 'Mild' : v < 70 ? 'Strong' : 'Extreme';
    draw(v);
  });
}
