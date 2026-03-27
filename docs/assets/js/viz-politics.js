/* ==========================================================================
   Geometric Politics — Interactive Visualizations
   1. Left-Right Collapse: 8 political dimensions collapsed to 1D axis
   2. Gerrymandering Manifold Surgery: same voters, different outcomes
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initLeftRightCollapse();
  initGerrymanderingSurgery();
});

/* ==========================================================================
   1. LEFT-RIGHT COLLAPSE — 8 political dimensions collapsed to scalar
   Two voters at the same left-right position with different profiles.
   ========================================================================== */
function initLeftRightCollapse() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const toc = section.querySelector('.toc-grid');
  if (!toc) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.innerHTML =
    '<h3 class="demo-title">Left-Right Scalar Collapse</h3>' +
    '<p class="demo-subtitle">Two voters land at the same spot on the left-right axis. Drag the slider to collapse 8 dimensions into one number.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="pol-collapse-canvas" width="520" height="340"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<label class="demo-slider-label">' +
        '<span>Collapse</span>' +
        '<input type="range" min="0" max="100" value="0" class="demo-slider" id="pol-collapse-slider">' +
        '<span class="demo-val" id="pol-collapse-val">Full Spectrum</span>' +
      '</label>' +
    '</div>';

  toc.parentNode.insertBefore(demo, toc.nextSibling);

  const canvas = document.getElementById('pol-collapse-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const dims = ['Economic', 'Social', 'Foreign', 'Environ', 'Civil Lib', 'Immigr', 'Health', 'Educ'];
  const dimColors = ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#8da0cb'];

  // Voter A: libertarian-ish — free market, socially liberal, non-interventionist
  // Voter B: communitarian — regulated market, socially conservative, hawkish
  // Both average to ~0.50 on a 0=Left 1=Right scale
  const voterA = [0.85, 0.20, 0.15, 0.30, 0.90, 0.40, 0.25, 0.95]; // avg ~0.50
  const voterB = [0.25, 0.80, 0.85, 0.70, 0.10, 0.60, 0.75, 0.05]; // avg ~0.51

  function draw(collapse) {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const t = collapse / 100;

    const cx = w / 2;
    const cy = 155;
    const maxR = 110;

    const avgA = voterA.reduce((a, b) => a + b, 0) / voterA.length;
    const avgB = voterB.reduce((a, b) => a + b, 0) / voterB.length;

    // Labels
    ctx.fillStyle = '#e8ecf0';
    ctx.font = '600 14px "Crimson Pro", serif';
    ctx.textAlign = 'center';

    if (t < 0.85) {
      // --- Radar chart mode ---
      ctx.fillText('Voter A (Libertarian-ish)', w / 4, 20);
      ctx.fillText('Voter B (Communitarian)', 3 * w / 4, 20);

      var cxA = w / 4, cxB = 3 * w / 4;
      var cyR = cy;
      var rMax = 90;

      // Draw both radar charts
      drawRadar(ctx, cxA, cyR, rMax, voterA, dimColors, dims, t, '#1b9e77');
      drawRadar(ctx, cxB, cyR, rMax, voterB, dimColors, dims, t, '#d95f02');

      // Divider
      ctx.strokeStyle = 'rgba(102,194,165,0.2)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(w / 2, 10);
      ctx.lineTo(w / 2, h - 60);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    if (t >= 0.85) {
      // --- Left-right axis mode ---
      var axisY = cy + 20;
      var axisLeft = 60;
      var axisRight = w - 60;
      var axisLen = axisRight - axisLeft;

      // Draw axis line
      ctx.strokeStyle = '#5c7a94';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(axisLeft, axisY);
      ctx.lineTo(axisRight, axisY);
      ctx.stroke();

      // Tick marks and labels
      ctx.fillStyle = '#8fa4b8';
      ctx.font = '11px Inter, sans-serif';
      ctx.textAlign = 'center';
      for (var i = 0; i <= 10; i++) {
        var tx = axisLeft + (i / 10) * axisLen;
        ctx.beginPath();
        ctx.moveTo(tx, axisY - 4);
        ctx.lineTo(tx, axisY + 4);
        ctx.stroke();
      }
      ctx.fillText('Left', axisLeft, axisY + 22);
      ctx.fillText('Right', axisRight, axisY + 22);
      ctx.fillText('Center', axisLeft + axisLen / 2, axisY + 22);

      // Plot voters — they overlap
      var posA = axisLeft + avgA * axisLen;
      var posB = axisLeft + avgB * axisLen;

      ctx.fillStyle = '#1b9e77';
      ctx.beginPath();
      ctx.arc(posA, axisY - 16, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#e8ecf0';
      ctx.font = '600 11px Inter, sans-serif';
      ctx.fillText('A', posA, axisY - 12);

      ctx.fillStyle = '#d95f02';
      ctx.beginPath();
      ctx.arc(posB, axisY + 16, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#e8ecf0';
      ctx.fillText('B', posB, axisY + 20);

      ctx.fillStyle = '#e8ecf0';
      ctx.font = '600 14px "Crimson Pro", serif';
      ctx.fillText('Both voters: "Center"', w / 2, 30);

      ctx.fillStyle = '#d95f02';
      ctx.font = '12px Inter, sans-serif';
      ctx.fillText('Same position. Opposite beliefs.', w / 2, axisY + 50);
      ctx.fillText('The left-right axis destroyed 7 dimensions of information.', w / 2, axisY + 68);
    }

    // Scores
    ctx.fillStyle = t > 0.5 ? '#e8ecf0' : '#5c7a94';
    ctx.font = '600 14px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('L-R score: ' + avgA.toFixed(2), w / 4, h - 16);
    ctx.fillText('L-R score: ' + avgB.toFixed(2), 3 * w / 4, h - 16);
  }

  function drawRadar(ctx, cx, cy, r, values, colors, labels, t, accentColor) {
    var n = values.length;
    var angleStep = (Math.PI * 2) / n;

    // Background web
    for (var ring = 1; ring <= 4; ring++) {
      var rr = (ring / 4) * r;
      ctx.strokeStyle = 'rgba(92,122,148,0.15)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (var i = 0; i <= n; i++) {
        var angle = -Math.PI / 2 + i * angleStep;
        var px = cx + Math.cos(angle) * rr;
        var py = cy + Math.sin(angle) * rr;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();
    }

    // Spokes and labels
    for (var i = 0; i < n; i++) {
      var angle = -Math.PI / 2 + i * angleStep;
      var sx = cx + Math.cos(angle) * r;
      var sy = cy + Math.sin(angle) * r;
      ctx.strokeStyle = 'rgba(92,122,148,0.2)';
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(sx, sy);
      ctx.stroke();

      // Labels fade with collapse
      if (t < 0.7) {
        var lx = cx + Math.cos(angle) * (r + 16);
        var ly = cy + Math.sin(angle) * (r + 16);
        ctx.fillStyle = 'rgba(143,164,184,' + (1 - t * 1.3) + ')';
        ctx.font = '9px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(labels[i], lx, ly);
      }
    }

    // Average value (what everything collapses to)
    var avg = values.reduce((a, b) => a + b, 0) / values.length;

    // Data polygon
    ctx.beginPath();
    for (var i = 0; i < n; i++) {
      var angle = -Math.PI / 2 + i * angleStep;
      // Interpolate between actual value and average (collapse)
      var v = values[i] * (1 - t) + avg * t;
      var pr = v * r;
      var px = cx + Math.cos(angle) * pr;
      var py = cy + Math.sin(angle) * pr;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fillStyle = accentColor + '22';
    ctx.fill();
    ctx.strokeStyle = accentColor + 'cc';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Dimension dots
    for (var i = 0; i < n; i++) {
      var angle = -Math.PI / 2 + i * angleStep;
      var v = values[i] * (1 - t) + avg * t;
      var pr = v * r;
      var px = cx + Math.cos(angle) * pr;
      var py = cy + Math.sin(angle) * pr;
      ctx.fillStyle = (t < 0.85) ? colors[i] : '#8899aa';
      ctx.beginPath();
      ctx.arc(px, py, 3, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.textBaseline = 'alphabetic';
  }

  draw(0);

  document.getElementById('pol-collapse-slider').addEventListener('input', function() {
    var v = parseInt(this.value);
    document.getElementById('pol-collapse-val').textContent = v < 30 ? 'Full Spectrum' : v < 70 ? 'Collapsing...' : 'Left-Right Only';
    draw(v);
  });
}

/* ==========================================================================
   2. GERRYMANDERING MANIFOLD SURGERY — Same voters, different outcomes
   Interactive grid of blue/red dots with district boundaries.
   ========================================================================== */
function initGerrymanderingSurgery() {
  const section = document.querySelector('.book-index');
  if (!section) return;
  const prev = section.querySelectorAll('.scalar-tensor-demo');
  const anchor = prev[prev.length - 1];
  if (!anchor) return;

  const demo = document.createElement('div');
  demo.className = 'scalar-tensor-demo';
  demo.style.marginTop = '32px';
  demo.innerHTML =
    '<h3 class="demo-title">Gerrymandering as Manifold Surgery</h3>' +
    '<p class="demo-subtitle">Same 200 voters, different district cuts. Click a button to see how boundary surgery changes outcomes.</p>' +
    '<div class="demo-canvas-row">' +
      '<canvas id="gerry-canvas" width="520" height="380"></canvas>' +
    '</div>' +
    '<div class="demo-controls">' +
      '<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">' +
        '<button class="btn btn-secondary" id="gerry-fair-btn">Fair Districts</button>' +
        '<button class="btn btn-secondary" id="gerry-red-btn">Red Gerrymander</button>' +
        '<button class="btn btn-secondary" id="gerry-blue-btn">Blue Gerrymander</button>' +
        '<button class="btn btn-secondary" id="gerry-reset-btn">No Districts</button>' +
      '</div>' +
      '<div style="display:flex;gap:24px;justify-content:center;margin-top:8px;font-size:12px;color:var(--text-secondary)">' +
        '<span style="color:#4a9ede">Blue voters: <span id="gerry-blue-count">0</span></span>' +
        '<span style="color:#de4a4a">Red voters: <span id="gerry-red-count">0</span></span>' +
        '<span id="gerry-result" style="color:#e8ecf0;font-weight:600"></span>' +
      '</div>' +
    '</div>';

  anchor.parentNode.insertBefore(demo, anchor.nextSibling);

  const canvas = document.getElementById('gerry-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // Grid setup: 20 columns x 10 rows = 200 voters
  const gridCols = 20;
  const gridRows = 10;
  const totalVoters = gridCols * gridRows;
  const cellW = canvas.width / gridCols;
  const cellH = (canvas.height - 40) / gridRows;
  const offsetY = 20;

  // Generate a voter map: slightly more blue overall (55/45 split)
  // with geographic clustering
  var voters = [];
  var seed = 42;
  function seededRandom() {
    seed = (seed * 16807 + 0) % 2147483647;
    return (seed - 1) / 2147483646;
  }

  // Create clusters: left side leans blue, right side leans red, some mixing
  for (var row = 0; row < gridRows; row++) {
    for (var col = 0; col < gridCols; col++) {
      var blueBias = 0.55; // slight overall blue lean
      // Geographic gradient: left more blue, right more red
      blueBias += (10 - col) * 0.025;
      // Some vertical clustering
      if (row >= 3 && row <= 6 && col >= 8 && col <= 14) blueBias -= 0.15; // red pocket in center
      if (row <= 2 && col <= 6) blueBias += 0.15; // blue stronghold top-left
      if (row >= 7 && col >= 15) blueBias -= 0.2; // red stronghold bottom-right

      var isBlue = seededRandom() < Math.max(0.1, Math.min(0.9, blueBias));
      voters.push(isBlue ? 'B' : 'R');
    }
  }

  var blueTotal = voters.filter(v => v === 'B').length;
  var redTotal = totalVoters - blueTotal;

  document.getElementById('gerry-blue-count').textContent = blueTotal;
  document.getElementById('gerry-red-count').textContent = redTotal;

  // District definitions: 5 districts of 40 voters each (4 cols x 10 rows or various shapes)
  // Each district is an array of [col, row] pairs.

  function makeVerticalStripes() {
    // 5 vertical districts, each 4 columns wide
    var districts = [];
    for (var d = 0; d < 5; d++) {
      var cells = [];
      for (var row = 0; row < gridRows; row++) {
        for (var col = d * 4; col < (d + 1) * 4; col++) {
          cells.push([col, row]);
        }
      }
      districts.push(cells);
    }
    return districts;
  }

  function makeRedGerrymander() {
    // Pack blue voters into 2 districts, spread red advantage across 3
    // District 0: leftmost 2 cols (blue stronghold) + top 2 rows of cols 2-3
    // District 1: cols 2-5 middle rows (another blue-packed)
    // Districts 2,3,4: remaining — red wins each narrowly
    var districts = [[], [], [], [], []];
    for (var row = 0; row < gridRows; row++) {
      for (var col = 0; col < gridCols; col++) {
        var idx = row * gridCols + col;
        // Pack blue into districts 0 and 1
        if (col <= 3 && row <= 4) {
          districts[0].push([col, row]);
        } else if (col <= 3 && row > 4) {
          districts[1].push([col, row]);
        } else if (col >= 4 && col <= 9) {
          // Split remaining columns to spread red advantage
          if (row <= 4) {
            districts[2].push([col, row]);
          } else {
            districts[3].push([col, row]);
          }
        } else {
          districts[4].push([col, row]);
        }
      }
    }
    return districts;
  }

  function makeBlueGerrymander() {
    // Spread blue voters across 4 districts for narrow wins, sacrifice 1
    var districts = [[], [], [], [], []];
    for (var row = 0; row < gridRows; row++) {
      for (var col = 0; col < gridCols; col++) {
        // Horizontal snake: alternate direction per pair of rows
        if (row <= 1) {
          // Rows 0-1: split into left/right halves
          if (col <= 9) districts[0].push([col, row]);
          else districts[1].push([col, row]);
        } else if (row <= 3) {
          if (col <= 9) districts[1].push([col, row]);
          else districts[0].push([col, row]);
        } else if (row <= 5) {
          if (col <= 9) districts[2].push([col, row]);
          else districts[3].push([col, row]);
        } else if (row <= 7) {
          if (col <= 9) districts[3].push([col, row]);
          else districts[2].push([col, row]);
        } else {
          // Rows 8-9: sacrifice district
          districts[4].push([col, row]);
        }
      }
    }
    return districts;
  }

  var currentDistricts = null;

  var districtColors = [
    'rgba(102,194,165,0.35)',
    'rgba(252,141,98,0.35)',
    'rgba(141,160,203,0.35)',
    'rgba(231,138,195,0.35)',
    'rgba(166,216,84,0.35)'
  ];

  var districtBorders = [
    '#66c2a5',
    '#fc8d62',
    '#8da0cb',
    '#e78ac3',
    '#a6d854'
  ];

  function drawGrid() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Build district membership map for border drawing
    var districtMap = {};
    if (currentDistricts) {
      for (var d = 0; d < currentDistricts.length; d++) {
        for (var c = 0; c < currentDistricts[d].length; c++) {
          var cell = currentDistricts[d][c];
          districtMap[cell[0] + ',' + cell[1]] = d;
        }
      }
    }

    // Draw district backgrounds
    if (currentDistricts) {
      for (var d = 0; d < currentDistricts.length; d++) {
        for (var c = 0; c < currentDistricts[d].length; c++) {
          var cell = currentDistricts[d][c];
          ctx.fillStyle = districtColors[d];
          ctx.fillRect(cell[0] * cellW, offsetY + cell[1] * cellH, cellW, cellH);
        }
      }
    }

    // Draw voters as dots
    for (var row = 0; row < gridRows; row++) {
      for (var col = 0; col < gridCols; col++) {
        var idx = row * gridCols + col;
        var cx = col * cellW + cellW / 2;
        var cy = offsetY + row * cellH + cellH / 2;
        var isBlue = voters[idx] === 'B';

        ctx.fillStyle = isBlue ? '#4a9ede' : '#de4a4a';
        ctx.beginPath();
        ctx.arc(cx, cy, Math.min(cellW, cellH) * 0.3, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Draw district borders (thick lines between cells of different districts)
    if (currentDistricts) {
      ctx.lineWidth = 3;
      for (var row = 0; row < gridRows; row++) {
        for (var col = 0; col < gridCols; col++) {
          var d = districtMap[col + ',' + row];
          if (d === undefined) continue;

          var x = col * cellW;
          var y = offsetY + row * cellH;

          // Right neighbor
          if (col < gridCols - 1) {
            var dRight = districtMap[(col + 1) + ',' + row];
            if (dRight !== d) {
              ctx.strokeStyle = '#e8ecf0';
              ctx.beginPath();
              ctx.moveTo(x + cellW, y);
              ctx.lineTo(x + cellW, y + cellH);
              ctx.stroke();
            }
          }
          // Bottom neighbor
          if (row < gridRows - 1) {
            var dBottom = districtMap[col + ',' + (row + 1)];
            if (dBottom !== d) {
              ctx.strokeStyle = '#e8ecf0';
              ctx.beginPath();
              ctx.moveTo(x, y + cellH);
              ctx.lineTo(x + cellW, y + cellH);
              ctx.stroke();
            }
          }
          // Left edge
          if (col === 0) {
            ctx.strokeStyle = '#e8ecf0';
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x, y + cellH);
            ctx.stroke();
          }
          // Top edge
          if (row === 0) {
            ctx.strokeStyle = '#e8ecf0';
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x + cellW, y);
            ctx.stroke();
          }
          // Right edge of grid
          if (col === gridCols - 1) {
            ctx.strokeStyle = '#e8ecf0';
            ctx.beginPath();
            ctx.moveTo(x + cellW, y);
            ctx.lineTo(x + cellW, y + cellH);
            ctx.stroke();
          }
          // Bottom edge of grid
          if (row === gridRows - 1) {
            ctx.strokeStyle = '#e8ecf0';
            ctx.beginPath();
            ctx.moveTo(x, y + cellH);
            ctx.lineTo(x + cellW, y + cellH);
            ctx.stroke();
          }
        }
      }
    }

    // Draw district labels and compute results
    if (currentDistricts) {
      var blueSeats = 0;
      var redSeats = 0;
      for (var d = 0; d < currentDistricts.length; d++) {
        var dBlue = 0;
        var dRed = 0;
        var sumX = 0, sumY = 0;
        for (var c = 0; c < currentDistricts[d].length; c++) {
          var cell = currentDistricts[d][c];
          var idx = cell[1] * gridCols + cell[0];
          if (voters[idx] === 'B') dBlue++;
          else dRed++;
          sumX += cell[0] * cellW + cellW / 2;
          sumY += offsetY + cell[1] * cellH + cellH / 2;
        }
        var centX = sumX / currentDistricts[d].length;
        var centY = sumY / currentDistricts[d].length;

        var winner = dBlue > dRed ? 'B' : 'R';
        if (winner === 'B') blueSeats++;
        else redSeats++;

        // District label at centroid
        ctx.fillStyle = winner === 'B' ? '#4a9ede' : '#de4a4a';
        ctx.font = '600 12px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('D' + (d + 1) + ': ' + dBlue + 'B/' + dRed + 'R', centX, centY - 14);
      }

      // Result display
      var resultEl = document.getElementById('gerry-result');
      resultEl.textContent = 'Seats: Blue ' + blueSeats + ' — Red ' + redSeats;
      resultEl.style.color = blueSeats > redSeats ? '#4a9ede' : blueSeats < redSeats ? '#de4a4a' : '#e8ecf0';

      // Info text at top
      ctx.fillStyle = '#8fa4b8';
      ctx.font = '11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'alphabetic';
      ctx.fillText('5 districts \u00b7 ' + totalVoters + ' voters \u00b7 ' + blueTotal + ' blue \u00b7 ' + redTotal + ' red \u00b7 Same voters, different cuts', canvas.width / 2, 14);
    } else {
      document.getElementById('gerry-result').textContent = '';
      ctx.fillStyle = '#8fa4b8';
      ctx.font = '11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'alphabetic';
      ctx.fillText(totalVoters + ' voters \u00b7 ' + blueTotal + ' blue \u00b7 ' + redTotal + ' red \u00b7 Choose a districting plan below', canvas.width / 2, 14);
    }

    ctx.textBaseline = 'alphabetic';
  }

  drawGrid();

  document.getElementById('gerry-fair-btn').addEventListener('click', function() {
    currentDistricts = makeVerticalStripes();
    drawGrid();
  });

  document.getElementById('gerry-red-btn').addEventListener('click', function() {
    currentDistricts = makeRedGerrymander();
    drawGrid();
  });

  document.getElementById('gerry-blue-btn').addEventListener('click', function() {
    currentDistricts = makeBlueGerrymander();
    drawGrid();
  });

  document.getElementById('gerry-reset-btn').addEventListener('click', function() {
    currentDistricts = null;
    drawGrid();
  });
}
