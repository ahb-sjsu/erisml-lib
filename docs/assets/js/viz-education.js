/* ==========================================================================
   Geometric Education — Interactive Visualizations
   1. GPA Scalar Collapse: 8 learning dimensions collapsed to a single GPA
   2. Geodesic Learning Path: personalized vs standardized curriculum paths
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initGPACollapse();
  initGeodesicLearningPath();
});

/* ==========================================================================
   1. GPA SCALAR COLLAPSE — 8 learning dimensions collapsed to a scalar
   Three students with the same GPA but wildly different profiles.
   ========================================================================== */
function initGPACollapse() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const toc = section.querySelector('.toc-grid');
  if (!toc) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.innerHTML =
    '<h3 class="demo-title">GPA Scalar Collapse</h3>' +
    '<p class="demo-subtitle">Three students with the same GPA (3.5). Drag the slider to collapse 8 learning dimensions into one number.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="edu-gpa-canvas" width="520" height="380"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<label class="demo-slider-label">' +
        '<span>Collapse</span>' +
        '<input type="range" min="0" max="100" value="0" class="demo-slider" id="gpa-collapse-slider">' +
        '<span class="demo-val" id="gpa-collapse-val">Full Profile</span>' +
      '</label>' +
    '</div>';
  toc.parentNode.insertBefore(demo, toc.nextSibling);

  const canvas = document.getElementById('edu-gpa-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dims = ['Critical\nThinking','Creativity','Collab-\noration','Communi-\ncation','Math','Science','Art','Empathy'];
  const students = [
    { name: 'Student A — "The Analyst"',  color: '#1b9e77', vals: [0.95,0.40,0.50,0.55,0.95,0.90,0.20,0.55] },
    { name: 'Student B — "The Artist"',   color: '#d95f02', vals: [0.50,0.95,0.70,0.80,0.30,0.40,0.95,0.80] },
    { name: 'Student C — "The Leader"',   color: '#7570b3', vals: [0.70,0.55,0.95,0.90,0.50,0.55,0.45,0.80] },
  ];
  const N = dims.length, step = (Math.PI * 2) / N;

  function draw(collapse) {
    const w = canvas.width, h = canvas.height, t = collapse / 100;
    const cx = w / 2, cy = h / 2 - 10, maxR = 120;
    ctx.clearRect(0, 0, w, h);

    // Radar grid (fades with collapse)
    const go = Math.max(0, 1 - t * 1.5);
    if (go > 0) {
      for (let ring = 1; ring <= 4; ring++) {
        const r = (ring / 4) * maxR;
        ctx.strokeStyle = 'rgba(143,164,184,' + (0.15 * go) + ')';
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let i = 0; i <= N; i++) {
          const a = i * step - Math.PI / 2, px = cx + Math.cos(a) * r, py = cy + Math.sin(a) * r;
          i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.closePath(); ctx.stroke();
      }
      for (let i = 0; i < N; i++) {
        const a = i * step - Math.PI / 2;
        ctx.strokeStyle = 'rgba(143,164,184,' + (0.1 * go) + ')';
        ctx.beginPath(); ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(a) * maxR, cy + Math.sin(a) * maxR); ctx.stroke();
        const lr = maxR + 22, lx = cx + Math.cos(a) * lr, ly = cy + Math.sin(a) * lr;
        ctx.fillStyle = 'rgba(143,164,184,' + (0.8 * go) + ')';
        ctx.font = '9px Inter, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        dims[i].split('\n').forEach((ln, li, arr) => ctx.fillText(ln, lx, ly + li * 11 - (arr.length - 1) * 5));
      }
    }

    // Student radar polygons
    students.forEach((s) => {
      const avg = s.vals.reduce((a, b) => a + b, 0) / N;
      ctx.beginPath();
      for (let i = 0; i <= N; i++) {
        const idx = i % N, a = idx * step - Math.PI / 2;
        const v = s.vals[idx] * (1 - t) + avg * t, r = v * maxR;
        const px = cx + Math.cos(a) * r, py = cy + Math.sin(a) * r;
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.fillStyle = s.color + (t > 0.9 ? '40' : '20'); ctx.fill();
      ctx.strokeStyle = s.color + (t > 0.9 ? 'cc' : '99'); ctx.lineWidth = 2; ctx.stroke();
    });

    // Legend
    ctx.font = '11px Inter, sans-serif'; ctx.textAlign = 'left';
    students.forEach((s, i) => {
      const lx = 10 + i * 180;
      ctx.fillStyle = s.color; ctx.fillRect(lx, 8, 10, 10);
      ctx.fillStyle = '#e8ecf0'; ctx.fillText(s.name, lx + 14, 17);
    });

    // GPA label
    ctx.fillStyle = 'rgba(232,236,240,' + (0.3 + t * 0.7) + ')';
    ctx.font = '600 ' + (14 + t * 10) + 'px "JetBrains Mono", monospace';
    ctx.textAlign = 'center'; ctx.fillText('GPA: 3.5', cx, h - 30);
    if (t > 0.8) {
      ctx.fillStyle = '#d95f02'; ctx.font = '12px Inter, sans-serif';
      ctx.fillText('Same GPA. Three completely different learners.', cx, h - 10);
    }
    if (t > 0.95) {
      ctx.fillStyle = 'rgba(217,95,2,0.6)'; ctx.font = '10px Inter, sans-serif';
      ctx.fillText('The analyst, the artist, and the leader — indistinguishable.', cx, h);
    }
  }

  draw(0);
  document.getElementById('gpa-collapse-slider').addEventListener('input', function() {
    var v = parseInt(this.value);
    document.getElementById('gpa-collapse-val').textContent = v < 30 ? 'Full Profile' : v < 70 ? 'Collapsing...' : 'GPA Only';
    draw(v);
  });
}

/* ==========================================================================
   2. GEODESIC LEARNING PATH — Personalized vs standardized curriculum
   A learner navigates a 2D knowledge manifold with varying difficulty.
   ========================================================================== */
function initGeodesicLearningPath() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const prev = section.querySelectorAll('.scalar-tensor-demo');
  const anchor = prev[prev.length - 1];
  if (!anchor) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.style.marginTop = '32px';
  demo.innerHTML =
    '<h3 class="demo-title">Geodesic Learning Path</h3>' +
    '<p class="demo-subtitle">A knowledge manifold with varying difficulty. The standardized path ignores the terrain; the personalized geodesic adapts.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="edu-geodesic-canvas" width="520" height="340"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">' +
        '<button class="btn btn-secondary" id="edu-standard-btn">Standard Path</button>' +
        '<button class="btn btn-secondary" id="edu-personal-btn">Personalized Path</button>' +
        '<button class="btn btn-secondary" id="edu-reset-btn">Reset</button>' +
      '</div>' +
      '<div style="display:flex;gap:24px;justify-content:center;margin-top:8px;font-size:12px;color:var(--text-secondary)">' +
        '<span style="color:#66c2a5">Easy (strengths)</span>' +
        '<span style="color:#e6ab02">Moderate</span>' +
        '<span style="color:#d95f02">Hard (weaknesses)</span>' +
      '</div>' +
    '</div>';
  anchor.parentNode.insertBefore(demo, anchor.nextSibling);

  const canvas = document.getElementById('edu-geodesic-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const cols = 52, rows = 34, cW = canvas.width / cols, cH = canvas.height / rows;

  // Build difficulty terrain — hard blobs (weaknesses) and easy zones (strengths)
  var terrain = [], hardBlobs = [
    { cx:20, cy:10, r:7, i:0.9, label:'Abstract\nAlgebra' },
    { cx:35, cy:20, r:6, i:0.85, label:'Formal\nProofs' },
    { cx:15, cy:22, r:5, i:0.7, label:'Statistics' },
    { cx:40, cy:8,  r:5, i:0.6, label:'Topology' }
  ], easyBlobs = [
    { cx:8, cy:8, r:6, i:0.1 }, { cx:30, cy:28, r:5, i:0.1 },
    { cx:45, cy:15, r:4, i:0.15 }, { cx:10, cy:30, r:5, i:0.1 }
  ];
  for (var y = 0; y < rows; y++) {
    terrain[y] = [];
    for (var x = 0; x < cols; x++) {
      var v = 0.3;
      hardBlobs.forEach(function(b) {
        var d = Math.sqrt((x-b.cx)*(x-b.cx)+(y-b.cy)*(y-b.cy));
        if (d < b.r) { var f = 1-d/b.r; v = Math.max(v, b.i*f*f); }
      });
      easyBlobs.forEach(function(b) {
        var d = Math.sqrt((x-b.cx)*(x-b.cx)+(y-b.cy)*(y-b.cy));
        if (d < b.r) { var f = 1-d/b.r; v = Math.min(v, b.i+(1-f)*v); }
      });
      terrain[y][x] = v;
    }
  }

  var start = { x:2, y:2 }, goal = { x:49, y:31 };

  // Standard path: straight line ignoring terrain
  var standardPath = [];
  for (var i = 0; i <= 100; i++) {
    var f = i/100;
    standardPath.push({ px: start.x+(goal.x-start.x)*f, py: start.y+(goal.y-start.y)*f });
  }

  // Personalized path: A* weighted by terrain difficulty
  function computeGeodesic() {
    var open = [], closed = {}, from = {}, g = {};
    function k(x,y) { return x+','+y; }
    function h(x,y) { return Math.abs(x-goal.x)+Math.abs(y-goal.y); }
    var sk = k(start.x,start.y); g[sk] = 0;
    open.push({ x:start.x, y:start.y, f:h(start.x,start.y) });
    var dirs = [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]];
    while (open.length > 0) {
      var bi = 0;
      for (var i = 1; i < open.length; i++) { if (open[i].f < open[bi].f) bi = i; }
      var cur = open.splice(bi, 1)[0], ck = k(cur.x, cur.y);
      if (cur.x === goal.x && cur.y === goal.y) {
        var path = [], pk = ck;
        while (pk) { var p = pk.split(','); path.unshift({px:+p[0],py:+p[1]}); pk = from[pk]; }
        return path;
      }
      closed[ck] = true;
      for (var d = 0; d < 8; d++) {
        var nx = cur.x+dirs[d][0], ny = cur.y+dirs[d][1];
        if (nx<0||nx>=cols||ny<0||ny>=rows) continue;
        var nk = k(nx,ny);
        if (closed[nk]) continue;
        var mc = (dirs[d][0]&&dirs[d][1]) ? 1.414 : 1, tc = 1+terrain[ny][nx]*8;
        var tg = (g[ck]||0)+mc*tc;
        if (g[nk]===undefined||tg<g[nk]) {
          g[nk]=tg; from[nk]=ck; var fv=tg+h(nx,ny);
          var found=false;
          for (var oi=0;oi<open.length;oi++) { if(open[oi].x===nx&&open[oi].y===ny){open[oi].f=fv;found=true;break;} }
          if (!found) open.push({x:nx,y:ny,f:fv});
        }
      }
    }
    return [{px:start.x,py:start.y},{px:goal.x,py:goal.y}];
  }
  var personalizedPath = computeGeodesic();

  var animTimer = null, drawnStd = [], drawnPer = [];

  function tColor(v) {
    if (v < 0.25) { var f=v/0.25; return 'rgb('+Math.round(20+f*80)+','+Math.round(60+(1-f)*80)+','+Math.round(54+(1-f)*40)+')'; }
    if (v < 0.5)  { var f=(v-0.25)/0.25; return 'rgb('+Math.round(100+f*80)+','+Math.round(120-f*30)+','+Math.round(50-f*20)+')'; }
    var f=(v-0.5)/0.5; return 'rgb('+Math.round(180+f*37)+','+Math.round(90-f*45)+','+Math.round(30-f*28)+')';
  }

  function drawScene() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (var y = 0; y < rows; y++)
      for (var x = 0; x < cols; x++) { ctx.fillStyle = tColor(terrain[y][x]); ctx.fillRect(x*cW, y*cH, cW+0.5, cH+0.5); }

    // Blob labels
    ctx.font = '9px Inter, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    hardBlobs.forEach(function(b) {
      ctx.fillStyle = 'rgba(232,236,240,0.6)';
      b.label.split('\n').forEach((ln,li,arr) => ctx.fillText(ln, b.cx*cW+cW/2, b.cy*cH+li*11-(arr.length-1)*5));
    });

    // Standard path (dashed white)
    if (drawnStd.length > 1) {
      ctx.strokeStyle = 'rgba(232,236,240,0.9)'; ctx.lineWidth = 3; ctx.setLineDash([6,4]);
      ctx.beginPath(); ctx.moveTo(drawnStd[0].px*cW+cW/2, drawnStd[0].py*cH+cH/2);
      for (var i=1;i<drawnStd.length;i++) ctx.lineTo(drawnStd[i].px*cW+cW/2, drawnStd[i].py*cH+cH/2);
      ctx.stroke(); ctx.setLineDash([]);
      var ms = drawnStd[drawnStd.length>>1];
      ctx.fillStyle='rgba(232,236,240,0.85)'; ctx.font='10px "JetBrains Mono",monospace';
      ctx.fillText('Standard', ms.px*cW+cW/2, ms.py*cH-8);
    }
    // Personalized path (solid teal)
    if (drawnPer.length > 1) {
      ctx.strokeStyle = '#1b9e77'; ctx.lineWidth = 3; ctx.setLineDash([]);
      ctx.beginPath(); ctx.moveTo(drawnPer[0].px*cW+cW/2, drawnPer[0].py*cH+cH/2);
      for (var i=1;i<drawnPer.length;i++) ctx.lineTo(drawnPer[i].px*cW+cW/2, drawnPer[i].py*cH+cH/2);
      ctx.stroke();
      var mp = drawnPer[Math.floor(drawnPer.length*0.4)];
      ctx.fillStyle='#1b9e77'; ctx.font='10px "JetBrains Mono",monospace';
      ctx.fillText('Personalized', mp.px*cW+cW/2, mp.py*cH-8);
    }

    // Start & goal markers
    ctx.fillStyle='#66c2a5'; ctx.beginPath();
    ctx.arc(start.x*cW+cW/2, start.y*cH+cH/2, 6, 0, Math.PI*2); ctx.fill();
    ctx.fillStyle='#e8ecf0'; ctx.font='600 9px Inter, sans-serif'; ctx.textAlign='center';
    ctx.fillText('START', start.x*cW+cW/2, start.y*cH-8);
    ctx.fillStyle='#e7298a'; ctx.beginPath();
    ctx.arc(goal.x*cW+cW/2, goal.y*cH+cH/2, 6, 0, Math.PI*2); ctx.fill();
    ctx.fillStyle='#e8ecf0'; ctx.fillText('GOAL', goal.x*cW+cW/2, goal.y*cH-8);

    // Status text
    if (drawnStd.length>1 && drawnPer.length>1) {
      ctx.fillStyle='#1b9e77'; ctx.font='12px Inter, sans-serif'; ctx.textAlign='center';
      ctx.fillText('The geodesic avoids weak areas. Same destination, less struggle.', canvas.width/2, canvas.height-6);
    } else if (drawnStd.length>1) {
      ctx.fillStyle='#d95f02'; ctx.font='12px Inter, sans-serif'; ctx.textAlign='center';
      ctx.fillText('Standard path cuts through difficult terrain. One size fits all.', canvas.width/2, canvas.height-6);
    }
  }

  function animatePath(path, target) {
    if (animTimer) clearInterval(animTimer);
    target.length = 0;
    var idx = 0, step = Math.max(1, Math.floor(path.length / 80));
    animTimer = setInterval(function() {
      if (idx >= path.length) {
        clearInterval(animTimer); animTimer = null;
        for (var i=target.length;i<path.length;i++) target.push(path[i]);
        drawScene(); return;
      }
      target.push(path[idx]); idx += step; drawScene();
    }, 25);
  }

  drawScene();
  document.getElementById('edu-standard-btn').addEventListener('click', function() { animatePath(standardPath, drawnStd); });
  document.getElementById('edu-personal-btn').addEventListener('click', function() { animatePath(personalizedPath, drawnPer); });
  document.getElementById('edu-reset-btn').addEventListener('click', function() {
    if (animTimer) clearInterval(animTimer); animTimer=null; drawnStd=[]; drawnPer=[]; drawScene();
  });
}
