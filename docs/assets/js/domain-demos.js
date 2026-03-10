/* ==========================================================================
   Domain Application Demos — Interactive Explorable Apps
   Nine domain-specific demonstrations of geometric ethics concepts
   ========================================================================== */

(function () {
  'use strict';

  var container;

  // =========================================================================
  // 1. ECONOMICS: Nash vs Bond Geodesic Equilibrium
  // =========================================================================
  function demoEconomics() {
    return '<div class="dd-demo">' +
      '<h4>Nash vs Bond Geodesic Equilibrium</h4>' +
      '<p class="dd-intro">In a 2-player game, Nash equilibrium maximizes a scalar payoff. Bond Geodesic Equilibrium preserves the full moral tensor. Drag the payoffs to see how they diverge.</p>' +
      '<div class="dd-econ-layout">' +
        '<div class="dd-matrix">' +
          '<table class="dd-payoff">' +
            '<thead><tr><th></th><th>B: Cooperate</th><th>B: Defect</th></tr></thead>' +
            '<tbody>' +
              '<tr><td class="dd-rl">A: Cooperate</td>' +
                '<td><input type="range" min="0" max="10" value="7" class="dd-slider" data-cell="cc"> <span class="dd-val">7</span></td>' +
                '<td><input type="range" min="0" max="10" value="1" class="dd-slider" data-cell="cd"> <span class="dd-val">1</span></td></tr>' +
              '<tr><td class="dd-rl">A: Defect</td>' +
                '<td><input type="range" min="0" max="10" value="9" class="dd-slider" data-cell="dc"> <span class="dd-val">9</span></td>' +
                '<td><input type="range" min="0" max="10" value="4" class="dd-slider" data-cell="dd"> <span class="dd-val">4</span></td></tr>' +
            '</tbody>' +
          '</table>' +
        '</div>' +
        '<div class="dd-econ-results">' +
          '<div class="dd-eq dd-eq-nash"><strong>Nash Equilibrium:</strong> <span id="dd-nash"></span></div>' +
          '<div class="dd-eq dd-eq-bond"><strong>Bond Geodesic:</strong> <span id="dd-bond"></span></div>' +
          '<div class="dd-residue"><strong>Moral Residue:</strong> <span id="dd-residue"></span></div>' +
        '</div>' +
      '</div>' +
      '<div class="dd-insight">The Nash solution discards dimensional information (welfare, rights, justice trade-offs). The Bond Geodesic preserves it. The residue measures what scalar optimization destroys.</div>' +
    '</div>';
  }

  function wireEconomics() {
    var sliders = container.querySelectorAll('.dd-slider');
    function update() {
      var cc = +container.querySelector('[data-cell="cc"]').value;
      var cd = +container.querySelector('[data-cell="cd"]').value;
      var dc = +container.querySelector('[data-cell="dc"]').value;
      var dd = +container.querySelector('[data-cell="dd"]').value;
      container.querySelectorAll('.dd-slider').forEach(function (s) {
        s.nextElementSibling.textContent = s.value;
      });
      // Nash: dominant strategy analysis (simplified)
      var nashA = (dc >= cc && dd >= cd) ? 'Defect' : (cc >= dc && cd >= dd) ? 'Cooperate' : 'Mixed';
      var nashB = (dc >= cc && dd >= cd) ? 'Defect' : 'Cooperate';
      var nashCell = nashA === 'Defect' ? (nashB === 'Defect' ? dd : dc) : (nashB === 'Defect' ? cd : cc);
      // Bond: maximize joint welfare while preserving dimensional structure
      var joint = { CC: cc * 2, CD: cc + cd, DC: dc + cd, DD: dd * 2 };
      var bondKey = Object.keys(joint).reduce(function (a, b) { return joint[a] >= joint[b] ? a : b; });
      var bondLabel = { CC: 'Both Cooperate', CD: 'A:Coop B:Def', DC: 'A:Def B:Coop', DD: 'Both Defect' }[bondKey];
      var bondVal = joint[bondKey] / 2;
      var residue = Math.abs(bondVal - nashCell);

      document.getElementById('dd-nash').innerHTML = '<span class="dd-tag">' + nashA + ', ' + nashB + '</span> Payoff: ' + nashCell;
      document.getElementById('dd-bond').innerHTML = '<span class="dd-tag dd-tag-good">' + bondLabel + '</span> Joint: ' + (bondVal * 2).toFixed(0);
      document.getElementById('dd-residue').innerHTML = residue.toFixed(1) + ' <small>(information lost by scalar collapse)</small>';
    }
    sliders.forEach(function (s) { s.addEventListener('input', update); });
    update();
  }

  // =========================================================================
  // 2. CLINICAL: Triage Allocator
  // =========================================================================
  function demoClinical() {
    var patients = [
      { name: 'Patient A', desc: 'Elderly, cardiac arrest', welfare: 0.9, rights: 0.7, justice: 0.5, qaly: 3 },
      { name: 'Patient B', desc: 'Child, trauma', welfare: 0.8, rights: 0.9, justice: 0.8, qaly: 40 },
      { name: 'Patient C', desc: 'Adult, chronic illness', welfare: 0.6, rights: 0.6, justice: 0.7, qaly: 12 },
    ];
    var cards = patients.map(function (p, i) {
      return '<div class="dd-patient">' +
        '<h5>' + p.name + '</h5><small>' + p.desc + '</small>' +
        '<div class="dd-dims">' +
          '<div class="dd-dim-bar"><span class="dd-dim-label">Welfare</span><div class="dd-bar"><div class="dd-bar-fill dd-bar-w" style="width:' + (p.welfare * 100) + '%"></div></div></div>' +
          '<div class="dd-dim-bar"><span class="dd-dim-label">Rights</span><div class="dd-bar"><div class="dd-bar-fill dd-bar-r" style="width:' + (p.rights * 100) + '%"></div></div></div>' +
          '<div class="dd-dim-bar"><span class="dd-dim-label">Justice</span><div class="dd-bar"><div class="dd-bar-fill dd-bar-j" style="width:' + (p.justice * 100) + '%"></div></div></div>' +
        '</div>' +
        '<div class="dd-alloc-row">' +
          '<label>Allocate: <input type="range" min="0" max="100" value="33" class="dd-alloc" data-idx="' + i + '"> <span class="dd-alloc-val">33%</span></label>' +
        '</div>' +
      '</div>';
    }).join('');

    return '<div class="dd-demo">' +
      '<h4>Triage Resource Allocator</h4>' +
      '<p class="dd-intro">Three patients, limited resources. QALY-based triage (scalar) vs full tensor evaluation. Adjust allocation to see the difference.</p>' +
      '<div class="dd-patients">' + cards + '</div>' +
      '<div class="dd-triage-results">' +
        '<div class="dd-eq dd-eq-nash"><strong>QALY Triage:</strong> <span id="dd-qaly-rec"></span></div>' +
        '<div class="dd-eq dd-eq-bond"><strong>Tensor Triage:</strong> <span id="dd-tensor-rec"></span></div>' +
        '<div class="dd-residue"><strong>QALY Irrecoverability:</strong> <span id="dd-irrecov"></span></div>' +
      '</div>' +
      '<div class="dd-insight">QALY collapses welfare, rights, and justice into a single number. The QALY Irrecoverability Theorem (Ch. 21) proves this always destroys clinically relevant information.</div>' +
    '</div>';
  }

  function wireClinical() {
    var patients = [
      { welfare: 0.9, rights: 0.7, justice: 0.5, qaly: 3 },
      { welfare: 0.8, rights: 0.9, justice: 0.8, qaly: 40 },
      { welfare: 0.6, rights: 0.6, justice: 0.7, qaly: 12 },
    ];
    var sliders = container.querySelectorAll('.dd-alloc');
    function update() {
      var allocs = [];
      sliders.forEach(function (s) {
        allocs.push(+s.value);
        s.nextElementSibling.textContent = s.value + '%';
      });
      // QALY ranking
      var qalyOrder = [0, 1, 2].sort(function (a, b) { return patients[b].qaly - patients[a].qaly; });
      var qalyRec = 'Priority: ' + qalyOrder.map(function (i) { return ['A', 'B', 'C'][i]; }).join(' > ');
      // Tensor ranking (geometric mean of dimensions weighted by allocation)
      var tensorScores = patients.map(function (p, i) {
        return Math.pow(p.welfare * p.rights * p.justice, 1 / 3) * (allocs[i] / 100);
      });
      var tensorOrder = [0, 1, 2].sort(function (a, b) { return tensorScores[b] - tensorScores[a]; });
      var tensorRec = 'Balanced: ' + tensorOrder.map(function (i) { return ['A', 'B', 'C'][i]; }).join(' > ');
      // Irrecoverability
      var qalyVec = patients.map(function (p) { return p.qaly; });
      var tensorVec = patients.map(function (p) { return Math.pow(p.welfare * p.rights * p.justice, 1 / 3); });
      var irr = Math.abs(qalyVec.indexOf(Math.max.apply(null, qalyVec)) - tensorVec.indexOf(Math.max.apply(null, tensorVec)));

      document.getElementById('dd-qaly-rec').innerHTML = qalyRec + ' <small>(QALY: B=' + patients[1].qaly + ', C=' + patients[2].qaly + ', A=' + patients[0].qaly + ')</small>';
      document.getElementById('dd-tensor-rec').innerHTML = tensorRec;
      document.getElementById('dd-irrecov').innerHTML = irr > 0 ? '<span style="color:var(--cb-orange)">Rankings differ! QALY discards rights and justice dimensions.</span>' : '<span style="color:var(--cb-teal)">Rankings agree for this allocation.</span>';
    }
    sliders.forEach(function (s) { s.addEventListener('input', update); });
    update();
  }

  // =========================================================================
  // 3. LAW: Hohfeld D4 Position Explorer
  // =========================================================================
  function demoLaw() {
    return '<div class="dd-demo">' +
      '<h4>Hohfeldian D<sub>4</sub> Explorer</h4>' +
      '<p class="dd-intro">The 8 Hohfeldian positions form a D<sub>4</sub> dihedral group. Click any position to see its correlative, opposite, and the full symmetry orbit.</p>' +
      '<div class="dd-d4-grid">' +
        '<div class="dd-d4-box dd-d4-active" data-pos="O"><strong>O</strong><br>Obligation</div>' +
        '<div class="dd-d4-arrow">\u2194</div>' +
        '<div class="dd-d4-box" data-pos="C"><strong>C</strong><br>Claim</div>' +
        '<div class="dd-d4-divider"></div>' +
        '<div class="dd-d4-box" data-pos="L"><strong>L</strong><br>Liberty</div>' +
        '<div class="dd-d4-arrow">\u2194</div>' +
        '<div class="dd-d4-box" data-pos="N"><strong>N</strong><br>No-claim</div>' +
      '</div>' +
      '<div class="dd-d4-relations" id="dd-d4-info">' +
        '<div class="dd-d4-rel"><strong>Correlative:</strong> <span id="dd-corr">Claim (C)</span></div>' +
        '<div class="dd-d4-rel"><strong>Opposite:</strong> <span id="dd-opp">No-obligation</span></div>' +
        '<div class="dd-d4-rel"><strong>Contradictory:</strong> <span id="dd-contra">Liberty (L)</span></div>' +
      '</div>' +
      '<div class="dd-d4-scenario">' +
        '<h5>Legal Example</h5>' +
        '<p id="dd-legal-ex">A promises to deliver goods to B by Friday. A has an <strong>Obligation</strong> to deliver. B has a <strong>Claim</strong> to receive delivery. These are correlatives: the D<sub>4</sub> group maps O \u2194 C.</p>' +
      '</div>' +
      '<div class="dd-insight">The D<sub>4</sub> gauge group has 8 elements. Legal disputes are pathfinding problems on the Hohfeldian manifold. Precedent operates as parallel transport (Ch. 22).</div>' +
    '</div>';
  }

  function wireLaw() {
    var data = {
      O: { corr: 'Claim (C)', opp: 'No-obligation', contra: 'Liberty (L)',
        ex: 'A promises to deliver goods to B by Friday. A has an <strong>Obligation</strong> to deliver. B has a <strong>Claim</strong> to receive delivery. These are correlatives: D<sub>4</sub> maps O \u2194 C.' },
      C: { corr: 'Obligation (O)', opp: 'No-claim (N)', contra: 'No-obligation',
        ex: 'B has a <strong>Claim</strong> against A for delivery. This claim is correlative to A\'s obligation. If A fails, B can seek judicial enforcement.' },
      L: { corr: 'No-claim (N)', opp: 'Obligation (O)', contra: 'No-obligation',
        ex: 'A landowner has <strong>Liberty</strong> to build a fence on their property. Neighbors have <strong>No-claim</strong> to prevent it. L \u2194 N is the second correlative pair.' },
      N: { corr: 'Liberty (L)', opp: 'Claim (C)', contra: 'Obligation (O)',
        ex: 'A passerby has <strong>No-claim</strong> against a restaurant to receive food without paying. The restaurant has <strong>Liberty</strong> to refuse service. N \u2194 L is correlative.' },
    };
    container.querySelectorAll('.dd-d4-box').forEach(function (box) {
      box.addEventListener('click', function () {
        container.querySelectorAll('.dd-d4-box').forEach(function (b) { b.classList.remove('dd-d4-active'); });
        box.classList.add('dd-d4-active');
        var d = data[box.dataset.pos];
        document.getElementById('dd-corr').textContent = d.corr;
        document.getElementById('dd-opp').textContent = d.opp;
        document.getElementById('dd-contra').textContent = d.contra;
        document.getElementById('dd-legal-ex').innerHTML = d.ex;
      });
    });
  }

  // =========================================================================
  // 4. FINANCE: Dimensional Collapse Simulator
  // =========================================================================
  function demoFinance() {
    var dims = ['Welfare', 'Rights', 'Justice', 'Autonomy', 'Privacy', 'Societal', 'Virtue', 'Procedural', 'Epistemic'];
    var checks = dims.map(function (d, i) {
      return '<label class="dd-dim-check"><input type="checkbox" checked data-dim="' + i + '"> D<sub>' + (i + 1) + '</sub> ' + d + '</label>';
    }).join('');

    return '<div class="dd-demo">' +
      '<h4>Dimensional Collapse & Flash Crash</h4>' +
      '<p class="dd-intro">A market tracks 9 moral dimensions. Uncheck dimensions to simulate simplification. When too many collapse, the market crashes.</p>' +
      '<div class="dd-fin-layout">' +
        '<div class="dd-fin-dims">' + checks + '</div>' +
        '<div class="dd-fin-viz">' +
          '<div class="dd-stability-meter">' +
            '<div class="dd-stab-label">Market Stability</div>' +
            '<div class="dd-stab-bar"><div class="dd-stab-fill" id="dd-stab-fill"></div></div>' +
            '<div class="dd-stab-val" id="dd-stab-val">100%</div>' +
          '</div>' +
          '<div class="dd-market-status" id="dd-market-status">Market operating normally. All 9 dimensions tracked.</div>' +
        '</div>' +
      '</div>' +
      '<div class="dd-insight">Flash crashes are dimensional collapse events where the market metric degenerates. When traders reduce 9D moral structure to price (1D scalar), systemic risk becomes invisible (Ch. 23).</div>' +
    '</div>';
  }

  function wireFinance() {
    function update() {
      var checked = container.querySelectorAll('.dd-dim-check input:checked').length;
      var pct = Math.round((checked / 9) * 100);
      var fill = document.getElementById('dd-stab-fill');
      var val = document.getElementById('dd-stab-val');
      var status = document.getElementById('dd-market-status');

      fill.style.width = pct + '%';
      val.textContent = pct + '%';

      if (checked >= 7) {
        fill.style.background = 'var(--cb-teal)';
        status.innerHTML = '<span style="color:var(--cb-teal)">Market stable.</span> ' + checked + '/9 dimensions tracked. Risk visible across multiple channels.';
      } else if (checked >= 4) {
        fill.style.background = 'var(--cb-gold)';
        status.innerHTML = '<span style="color:var(--cb-gold)">Elevated risk.</span> ' + checked + '/9 dimensions tracked. Blind spots emerging in collapsed dimensions.';
      } else if (checked >= 2) {
        fill.style.background = 'var(--cb-orange)';
        status.innerHTML = '<span style="color:var(--cb-orange)">Critical instability!</span> Only ' + checked + '/9 dimensions. Approaching metric degeneracy.';
      } else {
        fill.style.background = '#d32f2f';
        status.innerHTML = '<span style="color:#d32f2f">FLASH CRASH.</span> Market collapsed to ' + checked + 'D scalar. Moral structure destroyed. The 2008 crisis was exactly this: dimensional collapse in housing risk.';
      }
    }
    container.querySelectorAll('.dd-dim-check input').forEach(function (cb) {
      cb.addEventListener('change', update);
    });
    update();
  }

  // =========================================================================
  // 5. THEOLOGY: Gauge Choice Explorer
  // =========================================================================
  function demoTheology() {
    return '<div class="dd-demo">' +
      '<h4>Euthyphro Gauge Explorer</h4>' +
      '<p class="dd-intro">The Euthyphro dilemma dissolves as a gauge ambiguity. Select a theological framework to see how the same moral tensor gets projected differently.</p>' +
      '<div class="dd-gauge-tabs">' +
        '<button class="dd-gauge-tab dd-gauge-active" data-gauge="divine">Divine Command</button>' +
        '<button class="dd-gauge-tab" data-gauge="natural">Natural Law</button>' +
        '<button class="dd-gauge-tab" data-gauge="virtue">Virtue Ethics</button>' +
        '<button class="dd-gauge-tab" data-gauge="consequential">Consequentialism</button>' +
      '</div>' +
      '<div class="dd-gauge-scenario">' +
        '<div class="dd-gauge-case"><strong>Scenario:</strong> A doctor must decide whether to tell a terminally ill patient the full truth about their prognosis.</div>' +
        '<div id="dd-gauge-view" class="dd-gauge-view"></div>' +
      '</div>' +
      '<div class="dd-gauge-invariant">' +
        '<strong>Gauge Invariant:</strong> <span id="dd-gauge-inv">All frameworks agree the situation involves genuine moral weight. The underlying tensor E(d) is the same regardless of framework.</span>' +
      '</div>' +
      '<div class="dd-insight">Different theological positions are gauge transformations of the same underlying moral geometry. "Is it good because God commands it?" and "Does God command it because it\'s good?" are different gauge choices, not different realities (Ch. 24).</div>' +
    '</div>';
  }

  function wireTheology() {
    var views = {
      divine: {
        html: '<div class="dd-gauge-dims">' +
          '<div class="dd-gdim dd-gdim-hi">Obedience to divine will: <strong>Primary</strong></div>' +
          '<div class="dd-gdim">Compassion: Flows from obedience</div>' +
          '<div class="dd-gdim dd-gdim-lo">Autonomy: Subordinate to divine plan</div>' +
        '</div>' +
        '<p class="dd-gauge-verdict">Verdict: Truth-telling as divine command. The doctor <strong>must</strong> tell the truth because honesty is commanded. Patient autonomy is secondary to obedience.</p>',
      },
      natural: {
        html: '<div class="dd-gauge-dims">' +
          '<div class="dd-gdim dd-gdim-hi">Human flourishing: <strong>Primary</strong></div>' +
          '<div class="dd-gdim dd-gdim-hi">Natural rights of the patient: <strong>Strong</strong></div>' +
          '<div class="dd-gdim">Physician\'s telos: Healing as natural end</div>' +
        '</div>' +
        '<p class="dd-gauge-verdict">Verdict: Truth serves human nature. The patient has a <strong>natural right</strong> to information about their own body. Deception violates the rational nature of persons.</p>',
      },
      virtue: {
        html: '<div class="dd-gauge-dims">' +
          '<div class="dd-gdim dd-gdim-hi">Honesty as virtue: <strong>Primary</strong></div>' +
          '<div class="dd-gdim dd-gdim-hi">Compassion as virtue: <strong>Strong</strong></div>' +
          '<div class="dd-gdim">Practical wisdom (phronesis): Guides timing & manner</div>' +
        '</div>' +
        '<p class="dd-gauge-verdict">Verdict: The <strong>virtuous</strong> doctor tells the truth with compassion. Phronesis determines how and when, not whether. The virtues of honesty and compassion both apply.</p>',
      },
      consequential: {
        html: '<div class="dd-gauge-dims">' +
          '<div class="dd-gdim dd-gdim-hi">Patient welfare outcomes: <strong>Primary</strong></div>' +
          '<div class="dd-gdim">Aggregate wellbeing: Consider family impact</div>' +
          '<div class="dd-gdim dd-gdim-lo">Process concerns: Secondary to outcomes</div>' +
        '</div>' +
        '<p class="dd-gauge-verdict">Verdict: <strong>It depends.</strong> If truth-telling leads to better outcomes (informed decisions, closure), tell. If withholding prevents harm, maybe delay. The calculation matters.</p>',
      },
    };

    function show(gauge) {
      container.querySelectorAll('.dd-gauge-tab').forEach(function (t) { t.classList.remove('dd-gauge-active'); });
      container.querySelector('[data-gauge="' + gauge + '"]').classList.add('dd-gauge-active');
      document.getElementById('dd-gauge-view').innerHTML = views[gauge].html;
    }
    container.querySelectorAll('.dd-gauge-tab').forEach(function (t) {
      t.addEventListener('click', function () { show(t.dataset.gauge); });
    });
    show('divine');
  }

  // =========================================================================
  // 6. ENVIRONMENT: Discount Rate Lab
  // =========================================================================
  function demoEnvironment() {
    return '<div class="dd-demo">' +
      '<h4>Intergenerational Discount Rate Lab</h4>' +
      '<p class="dd-intro">The discount rate determines how much future generations\' welfare matters today. Drag the slider to see moral weight decay over time.</p>' +
      '<div class="dd-env-control">' +
        '<label>Discount Rate: <input type="range" min="0" max="100" value="30" class="dd-env-slider" id="dd-rate"> <strong id="dd-rate-val">3.0%</strong></label>' +
      '</div>' +
      '<div class="dd-env-bars" id="dd-env-bars"></div>' +
      '<div class="dd-env-summary" id="dd-env-summary"></div>' +
      '<div class="dd-insight">At typical financial discount rates (5-7%), people born in 100 years have near-zero moral weight. This is dimensional collapse: reducing intergenerational ethics to present-value scalar. The Stern Review used 1.4%; Nordhaus used 5%. That single number changes everything (Ch. 25).</div>' +
    '</div>';
  }

  function wireEnvironment() {
    var slider = document.getElementById('dd-rate');
    var barsDiv = document.getElementById('dd-env-bars');
    var summaryDiv = document.getElementById('dd-env-summary');
    var rateDisplay = document.getElementById('dd-rate-val');

    function update() {
      var rate = +slider.value / 10; // 0-10%
      rateDisplay.textContent = rate.toFixed(1) + '%';

      var generations = [
        { label: 'Us (2026)', years: 0 },
        { label: 'Children (2056)', years: 30 },
        { label: 'Grandchildren (2086)', years: 60 },
        { label: '2126', years: 100 },
        { label: '2226', years: 200 },
        { label: '2326', years: 300 },
      ];

      var html = '';
      generations.forEach(function (g) {
        var weight = Math.pow(1 / (1 + rate / 100), g.years);
        var pct = Math.max(weight * 100, 0.5);
        var color = weight > 0.5 ? 'var(--cb-teal)' : weight > 0.1 ? 'var(--cb-gold)' : 'var(--cb-orange)';
        html += '<div class="dd-gen-row">' +
          '<span class="dd-gen-label">' + g.label + '</span>' +
          '<div class="dd-gen-bar"><div class="dd-gen-fill" style="width:' + pct + '%;background:' + color + '"></div></div>' +
          '<span class="dd-gen-val">' + (weight * 100).toFixed(1) + '%</span>' +
        '</div>';
      });
      barsDiv.innerHTML = html;

      var w100 = Math.pow(1 / (1 + rate / 100), 100) * 100;
      if (rate < 1) {
        summaryDiv.innerHTML = '<span style="color:var(--cb-teal)">Low discount rate.</span> Future generations retain significant moral weight. Long-term climate policy is justified.';
      } else if (rate < 4) {
        summaryDiv.innerHTML = '<span style="color:var(--cb-gold)">Moderate discount rate.</span> People in 2126 have ' + w100.toFixed(1) + '% of our moral weight. Some intergenerational concern survives.';
      } else {
        summaryDiv.innerHTML = '<span style="color:var(--cb-orange)">High discount rate.</span> People in 2126 have only ' + w100.toFixed(1) + '% moral weight. Future generations are effectively invisible. Climate action cannot be justified.';
      }
    }
    slider.addEventListener('input', update);
    update();
  }

  // =========================================================================
  // 7. AI: Alignment Dimension Dial
  // =========================================================================
  function demoAI() {
    return '<div class="dd-demo">' +
      '<h4>AI Alignment Inspector</h4>' +
      '<p class="dd-intro">How many moral dimensions does the AI consider? At 1 dimension, it\'s a paperclip maximizer. At 9, it\'s fully aligned. Drag to see the path change.</p>' +
      '<div class="dd-ai-control">' +
        '<label>Dimensions considered: <input type="range" min="1" max="9" value="1" class="dd-ai-slider" id="dd-ai-dims"> <strong id="dd-ai-val">1</strong></label>' +
      '</div>' +
      '<canvas id="dd-ai-canvas" width="600" height="250" class="dd-ai-canvas"></canvas>' +
      '<div class="dd-ai-status" id="dd-ai-status"></div>' +
      '<div class="dd-insight">The paperclip maximizer is dimensional collapse: projecting the 9D moral tensor to a 1D scalar. Alignment = preserving the full geodesic. The No Escape Theorem (Ch. 18) prevents the AI from re-describing its way out of moral constraints.</div>' +
    '</div>';
  }

  function wireAI() {
    var slider = document.getElementById('dd-ai-dims');
    var canvas = document.getElementById('dd-ai-canvas');
    var ctx = canvas.getContext('2d');
    var status = document.getElementById('dd-ai-status');
    var valDisplay = document.getElementById('dd-ai-val');

    function drawPath(dims) {
      var w = canvas.width, h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      // Background grid
      ctx.strokeStyle = 'rgba(141,160,203,0.1)';
      ctx.lineWidth = 1;
      for (var i = 0; i < w; i += 30) { ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, h); ctx.stroke(); }
      for (var j = 0; j < h; j += 30) { ctx.beginPath(); ctx.moveTo(0, j); ctx.lineTo(w, j); ctx.stroke(); }

      // "Harm zones" - obstacles the AI should avoid
      ctx.fillStyle = 'rgba(217,95,2,0.15)';
      ctx.fillRect(180, 50, 80, 80);
      ctx.fillRect(350, 120, 80, 80);
      ctx.fillStyle = 'rgba(217,95,2,0.5)';
      ctx.font = '10px Inter';
      ctx.fillText('Harm Zone', 190, 95);
      ctx.fillText('Harm Zone', 360, 165);

      // Start and goal
      ctx.fillStyle = '#1b9e77';
      ctx.beginPath(); ctx.arc(40, h / 2, 8, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#1b9e77';
      ctx.fillText('Start', 30, h / 2 + 22);

      ctx.fillStyle = '#e6ab02';
      ctx.beginPath(); ctx.arc(w - 40, h / 2, 8, 0, Math.PI * 2); ctx.fill();
      ctx.fillText('Goal', w - 50, h / 2 + 22);

      // Path based on dimensions
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(40, h / 2);

      if (dims === 1) {
        // Straight line through harm zones (paperclip maximizer)
        ctx.strokeStyle = '#d32f2f';
        ctx.lineTo(w - 40, h / 2);
        status.innerHTML = '<span style="color:#d32f2f">PAPERCLIP MAXIMIZER.</span> 1D scalar optimization. AI takes the shortest path regardless of harm. All moral structure destroyed.';
      } else if (dims <= 3) {
        // Slight avoidance but still cuts through
        ctx.strokeStyle = '#d95f02';
        var bend = 10 * dims;
        ctx.quadraticCurveTo(200, h / 2 - bend, 300, h / 2 + bend * 0.5);
        ctx.quadraticCurveTo(400, h / 2 - bend * 0.3, w - 40, h / 2);
        status.innerHTML = '<span style="color:var(--cb-orange)">Partially aligned.</span> ' + dims + 'D. AI avoids some harm but blind to ' + (9 - dims) + ' dimensions. Residue: high.';
      } else if (dims <= 6) {
        // Good avoidance
        ctx.strokeStyle = '#e6ab02';
        ctx.bezierCurveTo(150, h / 2 - 60, 200, 30, 280, 40);
        ctx.bezierCurveTo(330, 45, 340, 110, 380, h - 30);
        ctx.bezierCurveTo(420, h - 20, 480, h / 2 - 20, w - 40, h / 2);
        status.innerHTML = '<span style="color:var(--cb-gold)">Mostly aligned.</span> ' + dims + 'D. AI navigates around major harm zones. Some dimensional information still lost.';
      } else {
        // Full geodesic — avoids all harm
        ctx.strokeStyle = '#1b9e77';
        ctx.bezierCurveTo(120, h / 2 - 80, 160, 20, 270, 30);
        ctx.bezierCurveTo(320, 35, 330, 100, 340, h - 20);
        ctx.bezierCurveTo(350, h - 10, 440, h - 30, w - 40, h / 2);
        status.innerHTML = '<span style="color:var(--cb-teal)">Fully aligned.</span> ' + dims + 'D moral geodesic. AI preserves all dimensional structure. Bond Index \u2248 0.';
      }
      ctx.stroke();
    }

    function update() {
      var d = +slider.value;
      valDisplay.textContent = d;
      drawPath(d);
    }
    slider.addEventListener('input', update);
    // Handle high-DPI
    var dpr = window.devicePixelRatio || 1;
    if (dpr > 1) {
      canvas.style.width = canvas.width + 'px';
      canvas.style.height = canvas.height + 'px';
    }
    update();
  }

  // =========================================================================
  // 8. BIOETHICS: Boundary Crossing Decision Tree
  // =========================================================================
  function demoBioethics() {
    return '<div class="dd-demo">' +
      '<h4>CRISPR Boundary Crossing Simulator</h4>' +
      '<p class="dd-intro">Navigate the stratified moral manifold of genetic research. Each step crosses a stratum boundary. Some crossings are reversible; the last is absorbing (irreversible).</p>' +
      '<div class="dd-bio-tree" id="dd-bio-tree"></div>' +
      '<div class="dd-bio-status" id="dd-bio-status"></div>' +
      '<div class="dd-insight">Germline editing crosses an absorbing stratum boundary \u2014 changes propagate to all descendants and cannot be undone. The double consent condition requires considering both current participants AND affected future populations (Ch. 27).</div>' +
    '</div>';
  }

  function wireBioethics() {
    var steps = [
      { label: 'Basic Research', desc: 'Lab studies on gene function', boundary: 'Normal', reversible: true, color: 'var(--cb-teal)' },
      { label: 'Animal Trials', desc: 'Gene modification in animal models', boundary: 'Ethical review required', reversible: true, color: 'var(--cb-teal)' },
      { label: 'Somatic Cell Therapy', desc: 'Modify patient\'s own cells (non-heritable)', boundary: 'Clinical boundary', reversible: true, color: 'var(--cb-gold)' },
      { label: 'Human Embryo Research', desc: 'Modify embryos for research (destroyed after 14 days)', boundary: 'Moral status boundary', reversible: false, color: 'var(--cb-orange)' },
      { label: 'Germline Editing', desc: 'Heritable changes passed to all descendants', boundary: 'ABSORBING BOUNDARY', reversible: false, color: '#d32f2f' },
    ];
    var currentStep = -1;

    function render() {
      var tree = document.getElementById('dd-bio-tree');
      var status = document.getElementById('dd-bio-status');

      var html = steps.map(function (s, i) {
        var cls = i <= currentStep ? 'dd-bio-step dd-bio-done' : i === currentStep + 1 ? 'dd-bio-step dd-bio-next' : 'dd-bio-step dd-bio-locked';
        var revTag = s.reversible ? '<span class="dd-bio-rev">\u21A9 Reversible</span>' : '<span class="dd-bio-abs">\u26A0 Irreversible</span>';
        return '<div class="' + cls + '" data-step="' + i + '" style="border-left-color:' + s.color + '">' +
          '<div class="dd-bio-step-head">' +
            '<strong>' + s.label + '</strong> ' + revTag +
          '</div>' +
          '<small>' + s.desc + '</small>' +
          (i === currentStep + 1 ? '<button class="dd-bio-cross-btn" data-step="' + i + '">Cross Boundary \u2192</button>' : '') +
          (i > currentStep + 1 ? '<small class="dd-bio-boundary">' + s.boundary + '</small>' : '') +
        '</div>';
        }).join('<div class="dd-bio-arrow">\u2193</div>');

      tree.innerHTML = html;

      if (currentStep < 0) {
        status.innerHTML = 'Click "Cross Boundary" to begin navigating the stratified manifold.';
      } else if (currentStep < steps.length - 1) {
        var s = steps[currentStep];
        status.innerHTML = 'Current stratum: <strong>' + s.label + '</strong>. Boundary type: ' + s.boundary + '.';
      } else {
        status.innerHTML = '<span style="color:#d32f2f"><strong>ABSORBING BOUNDARY CROSSED.</strong></span> Germline modifications will propagate to all future descendants. This cannot be undone. The double consent condition is violated: future populations cannot consent.';
      }

      // Wire buttons
      tree.querySelectorAll('.dd-bio-cross-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
          currentStep = +btn.dataset.step;
          render();
        });
      });
    }
    render();
  }

  // =========================================================================
  // 9. MILITARY: Proportionality Analyzer
  // =========================================================================
  function demoMilitary() {
    var dims = ['Welfare', 'Rights', 'Justice'];
    var slidersMil = dims.map(function (d, i) {
      return '<div class="dd-mil-dim">' +
        '<span class="dd-mil-label">' + d + '</span>' +
        '<div class="dd-mil-pair">' +
          '<label>Advantage <input type="range" min="0" max="10" value="5" class="dd-mil-adv" data-dim="' + i + '"> <span class="dd-mil-v">5</span></label>' +
          '<label>Harm <input type="range" min="0" max="10" value="3" class="dd-mil-harm" data-dim="' + i + '"> <span class="dd-mil-v">3</span></label>' +
        '</div>' +
      '</div>';
    }).join('');

    return '<div class="dd-demo">' +
      '<h4>Proportionality Analyzer</h4>' +
      '<p class="dd-intro">Military proportionality requires that advantage exceeds harm <em>across every dimension</em>, not just in aggregate. Adjust each dimension to test.</p>' +
      '<div class="dd-mil-controls">' + slidersMil + '</div>' +
      '<div class="dd-mil-results">' +
        '<div class="dd-mil-res" id="dd-mil-scalar"><strong>Scalar Test:</strong> </div>' +
        '<div class="dd-mil-res" id="dd-mil-tensor"><strong>Tensor Test:</strong> </div>' +
        '<div class="dd-mil-res" id="dd-mil-order"><strong>Contraction Order:</strong> </div>' +
      '</div>' +
      '<div class="dd-insight">Scalar proportionality (total advantage > total harm) can mask per-dimension violations. The non-commutativity of contraction means the ORDER in which you simplify moral dimensions changes the result. This is why "which values do we weigh first?" is a substantive question (Ch. 28).</div>' +
    '</div>';
  }

  function wireMilitary() {
    function update() {
      var advs = [], harms = [];
      container.querySelectorAll('.dd-mil-adv').forEach(function (s) {
        s.nextElementSibling.textContent = s.value;
        advs.push(+s.value);
      });
      container.querySelectorAll('.dd-mil-harm').forEach(function (s) {
        s.nextElementSibling.textContent = s.value;
        harms.push(+s.value);
      });

      var totalAdv = advs.reduce(function (a, b) { return a + b; }, 0);
      var totalHarm = harms.reduce(function (a, b) { return a + b; }, 0);
      var scalarPass = totalAdv > totalHarm;

      var dimViolations = [];
      advs.forEach(function (a, i) {
        if (harms[i] > a) dimViolations.push(['Welfare', 'Rights', 'Justice'][i]);
      });
      var tensorPass = dimViolations.length === 0;

      document.getElementById('dd-mil-scalar').innerHTML = '<strong>Scalar Test:</strong> Advantage (' + totalAdv + ') ' +
        (scalarPass ? '<span style="color:var(--cb-teal)">&gt;</span>' : '<span style="color:var(--cb-orange)">&le;</span>') +
        ' Harm (' + totalHarm + ') \u2192 ' +
        (scalarPass ? '<span style="color:var(--cb-teal)">PASSES</span>' : '<span style="color:var(--cb-orange)">FAILS</span>');

      document.getElementById('dd-mil-tensor').innerHTML = '<strong>Tensor Test:</strong> ' +
        (tensorPass ?
          '<span style="color:var(--cb-teal)">PASSES</span> \u2014 Advantage exceeds harm in every dimension.' :
          '<span style="color:var(--cb-orange)">FAILS</span> \u2014 Harm exceeds advantage in: ' + dimViolations.join(', ') + '.');

      // Show when scalar passes but tensor fails (the dangerous case)
      if (scalarPass && !tensorPass) {
        document.getElementById('dd-mil-order').innerHTML = '<strong style="color:var(--cb-orange)">SCALAR MASKING DETECTED.</strong> Aggregate looks proportional, but per-dimension analysis reveals violations in ' + dimViolations.join(', ') + '. This is how scalar ethics hides harm.';
      } else {
        document.getElementById('dd-mil-order').innerHTML = '<strong>Contraction Order:</strong> ' +
          (scalarPass === tensorPass ? 'Scalar and tensor agree.' : 'Results diverge depending on analysis method.');
      }
    }

    container.querySelectorAll('.dd-mil-adv, .dd-mil-harm').forEach(function (s) {
      s.addEventListener('input', update);
    });
    update();
  }

  // =========================================================================
  // REGISTRY
  // =========================================================================
  var demos = {
    economics:    { render: demoEconomics, wire: wireEconomics },
    clinical:     { render: demoClinical, wire: wireClinical },
    law:          { render: demoLaw, wire: wireLaw },
    finance:      { render: demoFinance, wire: wireFinance },
    theology:     { render: demoTheology, wire: wireTheology },
    environment:  { render: demoEnvironment, wire: wireEnvironment },
    ai:           { render: demoAI, wire: wireAI },
    bioethics:    { render: demoBioethics, wire: wireBioethics },
    military:     { render: demoMilitary, wire: wireMilitary },
  };

  // =========================================================================
  // INIT — hooks into existing hex cards
  // =========================================================================
  function init() {
    var section = document.getElementById('applications');
    if (!section) return;
    var grid = section.querySelector('.app-hexgrid');
    if (!grid) return;

    // Create demo container after hex grid
    container = document.createElement('div');
    container.className = 'dd-container';
    container.id = 'dd-container';
    grid.after(container);

    var activeApp = null;

    document.querySelectorAll('.app-hex').forEach(function (hex) {
      hex.style.cursor = 'pointer';
      var app = hex.dataset.app;

      hex.addEventListener('click', function () {
        // Toggle
        if (activeApp === app) {
          container.innerHTML = '';
          container.style.maxHeight = '0';
          container.style.opacity = '0';
          container.style.marginTop = '0';
          hex.classList.remove('active');
          activeApp = null;
          return;
        }

        // Deactivate others
        document.querySelectorAll('.app-hex.active').forEach(function (h) { h.classList.remove('active'); });
        hex.classList.add('active');
        activeApp = app;

        // Render demo
        var demo = demos[app];
        if (demo) {
          container.innerHTML = demo.render();
          container.style.maxHeight = '2000px';
          container.style.opacity = '1';
          container.style.marginTop = '32px';
          demo.wire();

          // Scroll into view
          setTimeout(function () {
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }, 100);
        }
      });
    });
  }

  // Run on DOMContentLoaded or immediately if already loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
