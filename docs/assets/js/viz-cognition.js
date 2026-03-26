/* ==========================================================================
   Geometric Cognition — Interactive Visualizations
   1. Model Signatures radar chart (cognitive profiles)
   2. IQ Collapse (cognitive dimensions to scalar)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initModelSignatures();
  initIQCollapse();
});

/* ==========================================================================
   1. MODEL SIGNATURES — Radar chart comparing cognitive profiles
   Toggle between models to see different geometric signatures.
   ========================================================================== */
function initModelSignatures() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const toc = section.querySelector('.toc-grid');
  if (!toc) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.innerHTML =
    '<h3 class="demo-title">Cognitive Geometric Signatures</h3>' +
    '<p class="demo-subtitle">Each model has a distinct cognitive profile. Toggle to compare signatures across 5 axes.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="radar-canvas" width="420" height="380"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">' +
        '<button class="btn btn-secondary" id="radar-claude" style="border-color:#1b9e77;color:#1b9e77">Claude Opus</button>' +
        '<button class="btn btn-secondary" id="radar-gemini" style="border-color:#d95f02;color:#d95f02">Gemini Flash</button>' +
        '<button class="btn btn-secondary" id="radar-gpt" style="border-color:#7570b3;color:#7570b3">GPT-4o</button>' +
        '<button class="btn btn-secondary" id="radar-human" style="border-color:#e6ab02;color:#e6ab02">Human Expert</button>' +
        '<button class="btn btn-secondary" id="radar-all">Show All</button>' +
      '</div>' +
    '</div>';

  toc.parentNode.insertBefore(demo, toc.nextSibling);

  const canvas = document.getElementById('radar-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const axes = ['Attention', 'Learning', 'Metacognition', 'Executive', 'Social Cog.'];
  const n = axes.length;
  const cx = 210, cy = 190, maxR = 140;
  const angleStep = (2 * Math.PI) / n;

  const models = {
    claude:  { vals: [0.92, 0.85, 0.88, 0.90, 0.78], color: '#1b9e77', name: 'Claude Opus' },
    gemini:  { vals: [0.88, 0.90, 0.65, 0.82, 0.60], color: '#d95f02', name: 'Gemini Flash' },
    gpt:     { vals: [0.85, 0.82, 0.75, 0.88, 0.72], color: '#7570b3', name: 'GPT-4o' },
    human:   { vals: [0.70, 0.75, 0.90, 0.65, 0.95], color: '#e6ab02', name: 'Human Expert' },
  };

  let activeModels = new Set(['claude']);
  let animProgress = {};

  function getPoint(i, v) {
    const angle = -Math.PI / 2 + i * angleStep;
    return {
      x: cx + maxR * v * Math.cos(angle),
      y: cy + maxR * v * Math.sin(angle)
    };
  }

  function draw() {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Draw concentric rings
    for (let ring = 0.2; ring <= 1.0; ring += 0.2) {
      ctx.strokeStyle = 'rgba(102,194,165,0.1)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const p = getPoint(i % n, ring);
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }
      ctx.closePath();
      ctx.stroke();
    }

    // Draw axis lines and labels
    for (let i = 0; i < n; i++) {
      const p = getPoint(i, 1.0);
      ctx.strokeStyle = 'rgba(102,194,165,0.2)';
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(p.x, p.y);
      ctx.stroke();

      // Labels
      const lp = getPoint(i, 1.18);
      ctx.fillStyle = '#8fa4b8';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(axes[i], lp.x, lp.y);
    }

    // Draw model polygons
    for (const [key, model] of Object.entries(models)) {
      if (!activeModels.has(key)) continue;
      const prog = animProgress[key] || 1;

      // Fill
      ctx.fillStyle = model.color + '20';
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const p = getPoint(i % n, model.vals[i % n] * prog);
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }
      ctx.closePath();
      ctx.fill();

      // Stroke
      ctx.strokeStyle = model.color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const p = getPoint(i % n, model.vals[i % n] * prog);
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }
      ctx.closePath();
      ctx.stroke();

      // Dots
      for (let i = 0; i < n; i++) {
        const p = getPoint(i, model.vals[i] * prog);
        ctx.fillStyle = model.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Legend
    let legendY = h - 20;
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'left';
    let legendX = 10;
    for (const [key, model] of Object.entries(models)) {
      if (!activeModels.has(key)) continue;
      ctx.fillStyle = model.color;
      ctx.fillRect(legendX, legendY - 8, 10, 10);
      ctx.fillStyle = '#8fa4b8';
      ctx.fillText(model.name, legendX + 14, legendY);
      legendX += ctx.measureText(model.name).width + 30;
    }
  }

  function animateModel(key) {
    animProgress[key] = 0;
    function step() {
      animProgress[key] = Math.min(1, (animProgress[key] || 0) + 0.04);
      draw();
      if (animProgress[key] < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  draw();

  function setModel(key) {
    activeModels = new Set([key]);
    animateModel(key);
  }

  document.getElementById('radar-claude').addEventListener('click', () => setModel('claude'));
  document.getElementById('radar-gemini').addEventListener('click', () => setModel('gemini'));
  document.getElementById('radar-gpt').addEventListener('click', () => setModel('gpt'));
  document.getElementById('radar-human').addEventListener('click', () => setModel('human'));
  document.getElementById('radar-all').addEventListener('click', () => {
    activeModels = new Set(['claude', 'gemini', 'gpt', 'human']);
    for (const key of activeModels) animateModel(key);
  });
}

/* ==========================================================================
   2. IQ COLLAPSE — Cognitive dimensions collapsed to a single number
   Shows how one IQ number hides the rich cognitive profile.
   ========================================================================== */
function initIQCollapse() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const prev = section.querySelectorAll('.scalar-tensor-demo');
  const anchor = prev[prev.length - 1];
  if (!anchor) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.style.marginTop = '32px';
  demo.innerHTML =
    '<h3 class="demo-title">The IQ Trap: Scalar Collapse of Cognition</h3>' +
    '<p class="demo-subtitle">Two minds with the same IQ score. Drag sliders to reshape the profiles and watch IQ stay the same.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="iq-canvas" width="520" height="300"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<label class="demo-slider-label">' +
        '<span>Collapse</span>' +
        '<input type="range" min="0" max="100" value="0" class="demo-slider" id="iq-collapse-slider">' +
        '<span class="demo-val" id="iq-collapse-val">Tensor</span>' +
      '</label>' +
    '</div>';

  anchor.parentNode.insertBefore(demo, anchor.nextSibling);

  const canvas = document.getElementById('iq-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const dimNames = ['Verbal', 'Spatial', 'Memory', 'Speed', 'Reason', 'Exec', 'Social'];
  const dimColors = ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d'];

  // Two minds with same average but very different profiles
  const mindA = [0.95, 0.40, 0.70, 0.55, 0.85, 0.60, 0.75]; // Verbal-analytical
  const mindB = [0.45, 0.90, 0.80, 0.70, 0.50, 0.75, 0.70]; // Spatial-memory

  function draw(collapse) {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const t = collapse / 100;
    const barW = 24, gap = 8;
    const maxH = 180;
    const baseY = h - 50;
    const groupW = dimNames.length * (barW + gap);
    const offA = (w / 2 - groupW) / 2;
    const offB = w / 2 + (w / 2 - groupW) / 2;

    const avgA = mindA.reduce((a, b) => a + b) / mindA.length;
    const avgB = mindB.reduce((a, b) => a + b) / mindB.length;
    const iqA = Math.round(avgA * 50 + 75);
    const iqB = Math.round(avgB * 50 + 75);

    ctx.fillStyle = '#e8ecf0';
    ctx.font = '600 14px "Crimson Pro", serif';
    ctx.textAlign = 'center';
    ctx.fillText('Mind A: Verbal-Analytical', w / 4, 22);
    ctx.fillText('Mind B: Spatial-Memory', 3 * w / 4, 22);

    for (let i = 0; i < dimNames.length; i++) {
      const vA = mindA[i] * (1 - t) + avgA * t;
      const vB = mindB[i] * (1 - t) + avgB * t;

      const xA = offA + i * (barW + gap);
      const xB = offB + i * (barW + gap);

      ctx.fillStyle = t < 1 ? dimColors[i] + '33' : 'transparent';
      ctx.fillRect(xA, baseY - maxH, barW, maxH);
      ctx.fillRect(xB, baseY - maxH, barW, maxH);

      ctx.fillStyle = t < 0.95 ? dimColors[i] : '#8899aa';
      ctx.fillRect(xA, baseY - vA * maxH, barW, vA * maxH);
      ctx.fillRect(xB, baseY - vB * maxH, barW, vB * maxH);

      if (t < 0.75) {
        ctx.fillStyle = `rgba(143,164,184,${1 - t})`;
        ctx.font = '8px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(dimNames[i], xA + barW / 2, baseY + 12);
        ctx.fillText(dimNames[i], xB + barW / 2, baseY + 12);
      }
    }

    ctx.font = '600 16px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillStyle = t > 0.5 ? '#e8ecf0' : '#5c7a94';
    ctx.fillText('IQ: ' + iqA, w / 4, baseY + 32);
    ctx.fillText('IQ: ' + iqB, 3 * w / 4, baseY + 32);

    if (t > 0.8) {
      ctx.fillStyle = '#d95f02';
      ctx.font = '12px Inter, sans-serif';
      ctx.fillText('Same IQ. Completely different minds.', w / 2, baseY + 52);
    }

    ctx.strokeStyle = 'rgba(102,194,165,0.2)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(w / 2, 10);
    ctx.lineTo(w / 2, h - 10);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  draw(0);

  document.getElementById('iq-collapse-slider').addEventListener('input', function() {
    const v = parseInt(this.value);
    document.getElementById('iq-collapse-val').textContent = v < 30 ? 'Tensor' : v < 70 ? 'Collapsing...' : 'Scalar';
    draw(v);
  });
}
