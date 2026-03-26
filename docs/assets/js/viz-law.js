/* ==========================================================================
   Geometric Law — Interactive Visualizations
   1. Hohfeldian Square with D4 group transformations
   2. Gauge Violation in sentencing disparities
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initHohfeldianSquare();
  initGaugeViolation();
});

/* ==========================================================================
   1. HOHFELDIAN SQUARE — Animated D4 group transformations
   Click rotation (r) or reflection (s) to transform the square.
   ========================================================================== */
function initHohfeldianSquare() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const toc = section.querySelector('.toc-grid');
  if (!toc) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.innerHTML =
    '<h3 class="demo-title">The Hohfeldian Square: D<sub>4</sub> Symmetry</h3>' +
    '<p class="demo-subtitle">Click r (rotate 90 degrees) or s (reflect) to apply D<sub>4</sub> group transformations. Watch the legal positions transform.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="hohfeld-canvas" width="420" height="380"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">' +
        '<button class="btn btn-secondary" id="hohfeld-rotate">r (Rotate 90&deg;)</button>' +
        '<button class="btn btn-secondary" id="hohfeld-reflect">s (Reflect)</button>' +
        '<button class="btn btn-secondary" id="hohfeld-reset">Reset (e)</button>' +
      '</div>' +
      '<div style="text-align:center;margin-top:8px;font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--text-secondary)">' +
        'Current: <span id="hohfeld-state" style="color:#1b9e77">e (identity)</span> &mdash; ' +
        'Transforms applied: <span id="hohfeld-count" style="color:#d95f02">0</span>' +
      '</div>' +
    '</div>';

  toc.parentNode.insertBefore(demo, toc.nextSibling);

  const canvas = document.getElementById('hohfeld-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // The four positions of the first Hohfeldian square
  const basePositions = ['Right', 'Duty', 'No-Right', 'Liberty'];
  const colors = ['#1b9e77', '#d95f02', '#7570b3', '#e6ab02'];

  // D4 group: track rotation count (0-3) and reflection state
  let rotation = 0;
  let reflected = false;
  let transformCount = 0;
  let animProgress = 1;
  let prevIndices = [0, 1, 2, 3];
  let currIndices = [0, 1, 2, 3];

  function getIndices() {
    let idx = [0, 1, 2, 3];
    // Apply rotation
    for (let r = 0; r < rotation; r++) {
      idx = [idx[3], idx[0], idx[1], idx[2]];
    }
    // Apply reflection (swap across vertical)
    if (reflected) {
      idx = [idx[1], idx[0], idx[3], idx[2]];
    }
    return idx;
  }

  function getStateName() {
    if (rotation === 0 && !reflected) return 'e (identity)';
    if (rotation === 1 && !reflected) return 'r';
    if (rotation === 2 && !reflected) return 'r\u00B2';
    if (rotation === 3 && !reflected) return 'r\u00B3';
    if (rotation === 0 && reflected) return 's';
    if (rotation === 1 && reflected) return 'sr';
    if (rotation === 2 && reflected) return 'sr\u00B2';
    if (rotation === 3 && reflected) return 'sr\u00B3';
    return '?';
  }

  // Corner positions on canvas (TL, TR, BR, BL)
  const cx = 210, cy = 185;
  const sz = 120;
  const corners = [
    { x: cx - sz, y: cy - sz }, // TL = 0
    { x: cx + sz, y: cy - sz }, // TR = 1
    { x: cx + sz, y: cy + sz }, // BR = 2
    { x: cx - sz, y: cy + sz }, // BL = 3
  ];

  function draw() {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const idx = currIndices;
    const pidx = prevIndices;
    const t = Math.min(1, animProgress);
    const ease = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;

    // Draw edges
    ctx.strokeStyle = 'rgba(102,194,165,0.3)';
    ctx.lineWidth = 1.5;
    for (let i = 0; i < 4; i++) {
      const j = (i + 1) % 4;
      ctx.beginPath();
      ctx.moveTo(corners[i].x, corners[i].y);
      ctx.lineTo(corners[j].x, corners[j].y);
      ctx.stroke();
    }
    // Diagonals (correlative relations)
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = 'rgba(217,95,2,0.2)';
    ctx.beginPath();
    ctx.moveTo(corners[0].x, corners[0].y);
    ctx.lineTo(corners[2].x, corners[2].y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(corners[1].x, corners[1].y);
    ctx.lineTo(corners[3].x, corners[3].y);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw edge labels
    ctx.fillStyle = '#5c7a94';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('correlative', cx, cy - sz - 10);
    ctx.fillText('correlative', cx, cy + sz + 18);
    ctx.save();
    ctx.translate(cx - sz - 14, cy);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('opposite', 0, 0);
    ctx.restore();
    ctx.save();
    ctx.translate(cx + sz + 14, cy);
    ctx.rotate(Math.PI / 2);
    ctx.fillText('opposite', 0, 0);
    ctx.restore();

    // Draw position labels at corners with animation
    for (let c = 0; c < 4; c++) {
      const posIdx = idx[c];
      ctx.fillStyle = colors[posIdx];
      ctx.font = '600 16px "Crimson Pro", serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      // Animate: fade in
      ctx.globalAlpha = ease;
      ctx.fillText(basePositions[posIdx], corners[c].x, corners[c].y);
      ctx.globalAlpha = 1;

      // Draw dot
      ctx.beginPath();
      ctx.arc(corners[c].x, corners[c].y - 20, 5, 0, Math.PI * 2);
      ctx.fillStyle = colors[posIdx];
      ctx.fill();
    }

    // Group element display
    ctx.fillStyle = '#e8ecf0';
    ctx.font = '14px "Crimson Pro", serif';
    ctx.textAlign = 'center';
    ctx.fillText('D\u2084 = \u27E8r, s | r\u2074 = s\u00B2 = e, srs = r\u207B\u00B9\u27E9', cx, h - 20);
  }

  function animateTo(newIdx) {
    prevIndices = [...currIndices];
    currIndices = newIdx;
    animProgress = 0;
    function step() {
      animProgress += 0.06;
      draw();
      if (animProgress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  draw();

  document.getElementById('hohfeld-rotate').addEventListener('click', () => {
    rotation = (rotation + 1) % 4;
    transformCount++;
    animateTo(getIndices());
    document.getElementById('hohfeld-state').textContent = getStateName();
    document.getElementById('hohfeld-count').textContent = transformCount;
  });

  document.getElementById('hohfeld-reflect').addEventListener('click', () => {
    reflected = !reflected;
    transformCount++;
    animateTo(getIndices());
    document.getElementById('hohfeld-state').textContent = getStateName();
    document.getElementById('hohfeld-count').textContent = transformCount;
  });

  document.getElementById('hohfeld-reset').addEventListener('click', () => {
    rotation = 0;
    reflected = false;
    transformCount = 0;
    animateTo(getIndices());
    document.getElementById('hohfeld-state').textContent = getStateName();
    document.getElementById('hohfeld-count').textContent = '0';
  });
}

/* ==========================================================================
   2. GAUGE VIOLATION — Sentencing disparities
   Identical cases with different demographics. Slider reveals gauge variance.
   ========================================================================== */
function initGaugeViolation() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const prev = section.querySelectorAll('.scalar-tensor-demo');
  const anchor = prev[prev.length - 1];
  if (!anchor) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.style.marginTop = '32px';
  demo.innerHTML =
    '<h3 class="demo-title">Gauge Violation in Sentencing</h3>' +
    '<p class="demo-subtitle">Same crime, same circumstances. Slider reveals how demographic factors create gauge-variant sentencing.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="gauge-canvas" width="520" height="300"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<label class="demo-slider-label">' +
        '<span>Gauge Bias</span>' +
        '<input type="range" min="0" max="100" value="0" class="demo-slider" id="gauge-slider">' +
        '<span class="demo-val" id="gauge-val">0%</span>' +
      '</label>' +
      '<div style="display:flex;gap:12px;justify-content:center;margin-top:8px">' +
        '<button class="btn btn-secondary" id="gauge-invariant-btn">Show Gauge-Invariant</button>' +
        '<button class="btn btn-secondary" id="gauge-variant-btn">Show Gauge-Variant</button>' +
      '</div>' +
    '</div>';

  anchor.parentNode.insertBefore(demo, anchor.nextSibling);

  const canvas = document.getElementById('gauge-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const caseDims = ['Severity', 'Intent', 'Priors', 'Circum.', 'Impact'];
  const caseVals = [0.7, 0.8, 0.3, 0.5, 0.6]; // Same for both defendants
  let biasLevel = 0;
  let showMode = 'neutral'; // 'neutral', 'invariant', 'variant'

  function drawGauge() {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const bias = biasLevel / 100;
    const barW = 30, gap = 12;
    const maxH = 160;
    const baseY = h - 60;
    const groupW = caseDims.length * (barW + gap);

    // Two defendants
    const offsetA = (w / 2 - groupW) / 2 + 10;
    const offsetB = w / 2 + (w / 2 - groupW) / 2 + 10;

    // Titles
    ctx.fillStyle = '#e8ecf0';
    ctx.font = '600 14px "Crimson Pro", serif';
    ctx.textAlign = 'center';
    ctx.fillText('Defendant A', w / 4, 22);
    ctx.fillText('Defendant B', 3 * w / 4, 22);

    // Identical case factors
    ctx.fillStyle = '#5c7a94';
    ctx.font = '11px Inter, sans-serif';
    ctx.fillText('Same offense, same facts', w / 4, 40);
    ctx.fillText('Same offense, same facts', 3 * w / 4, 40);

    const colors = ['#1b9e77', '#d95f02', '#7570b3', '#e6ab02', '#66a61e'];

    // Sentencing modifier from gauge violation
    let sentenceA = 0, sentenceB = 0;

    for (let i = 0; i < caseDims.length; i++) {
      const v = caseVals[i];
      // Defendant A: no bias applied
      const vA = v;
      // Defendant B: bias distorts the evaluation
      const vB = showMode === 'variant' ? Math.min(1, v + bias * (0.15 + i * 0.05)) : v;

      const bHA = vA * maxH;
      const bHB = vB * maxH;
      const xA = offsetA + i * (barW + gap);
      const xB = offsetB + i * (barW + gap);

      sentenceA += vA;
      sentenceB += vB;

      // Draw bars
      ctx.fillStyle = colors[i] + '33';
      ctx.fillRect(xA, baseY - maxH, barW, maxH);
      ctx.fillRect(xB, baseY - maxH, barW, maxH);

      ctx.fillStyle = colors[i];
      ctx.fillRect(xA, baseY - bHA, barW, bHA);
      ctx.fillRect(xB, baseY - bHB, barW, bHB);

      // Labels
      ctx.fillStyle = '#8fa4b8';
      ctx.font = '9px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(caseDims[i], xA + barW / 2, baseY + 14);
      ctx.fillText(caseDims[i], xB + barW / 2, baseY + 14);
    }

    // Sentence results
    const sentA = (sentenceA / caseDims.length * 10).toFixed(1);
    const sentB = (sentenceB / caseDims.length * 10).toFixed(1);

    ctx.font = '600 14px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#1b9e77';
    ctx.fillText('Sentence: ' + sentA + ' yrs', w / 4, baseY + 36);
    ctx.fillStyle = sentA !== sentB ? '#d95f02' : '#1b9e77';
    ctx.fillText('Sentence: ' + sentB + ' yrs', 3 * w / 4, baseY + 36);

    // Gauge status
    const isInvariant = Math.abs(parseFloat(sentA) - parseFloat(sentB)) < 0.1;
    ctx.font = '12px Inter, sans-serif';
    if (isInvariant) {
      ctx.fillStyle = '#1b9e77';
      ctx.fillText('Gauge-INVARIANT: S(A) = S(B)', w / 2, baseY + 56);
    } else {
      ctx.fillStyle = '#d95f02';
      ctx.fillText('Gauge-VARIANT: S(A) \u2260 S(B) \u2014 Violation!', w / 2, baseY + 56);
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

  drawGauge();

  document.getElementById('gauge-slider').addEventListener('input', function() {
    biasLevel = parseInt(this.value);
    document.getElementById('gauge-val').textContent = biasLevel + '%';
    if (showMode === 'variant') drawGauge();
  });

  document.getElementById('gauge-invariant-btn').addEventListener('click', () => {
    showMode = 'invariant';
    drawGauge();
  });

  document.getElementById('gauge-variant-btn').addEventListener('click', () => {
    showMode = 'variant';
    drawGauge();
  });
}
