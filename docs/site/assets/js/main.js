/* ==========================================================================
   Geometric Ethics — Interactive Book Website
   Main JavaScript: Animations, Interactions, Visualizations
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initScrollAnimations();
  initParableTimeline();
  initDimensionWheel();
  initTensorHierarchy();
  initPartsAccordion();
  initHeroParticles();
  initObjectCards();
  initTheoremCards();
  initAppCards();
  initReadingPaths();
  initDemeArchitecture();
  initEquationHighlight();
  initConservationInteractive();
  initEpistemicCards();
  initGameDemo();
  initBellTestSlider();
});

/* --- Navigation --- */
function initNav() {
  const nav = document.getElementById('main-nav');
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');

  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 50);
  });

  if (toggle) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
    });
  }

  document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => links.classList.remove('open'));
  });

  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a');
  window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(section => {
      const top = section.offsetTop - 120;
      if (window.scrollY >= top) current = section.id;
    });
    navLinks.forEach(link => {
      link.style.color = link.getAttribute('href') === '#' + current
        ? 'var(--accent-light)' : '';
    });
  });
}

/* --- Scroll-triggered Animations --- */
function initScrollAnimations() {
  const elements = document.querySelectorAll('[data-aos]');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const delay = parseInt(entry.target.dataset.aosDelay) || 0;
        setTimeout(() => entry.target.classList.add('visible'), delay);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -60px 0px' });
  elements.forEach(el => observer.observe(el));
}

/* --- Parable Timeline --- */
function initParableTimeline() {
  const events = document.querySelectorAll('.timeline-event');
  if (!events.length) return;

  events.forEach(ev => {
    ev.addEventListener('click', () => {
      events.forEach(e => e.classList.remove('active'));
      ev.classList.add('active');
    });
  });

  let step = 0;
  setInterval(() => {
    step = (step + 1) % events.length;
    events.forEach(e => e.classList.remove('active'));
    events[step].classList.add('active');
  }, 4000);
}

/* --- Nine Dimensions Radial Chart --- */
function initDimensionWheel() {
  const colors = [
    '#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e',
    '#e6ab02', '#a6761d', '#666666', '#8da0cb'
  ];

  const dims = [
    { label: 'D₁ Welfare', short: 'Welfare', value: 0.85 },
    { label: 'D₂ Rights', short: 'Rights', value: 0.75 },
    { label: 'D₃ Justice', short: 'Justice', value: 0.80 },
    { label: 'D₄ Autonomy', short: 'Autonomy', value: 0.70 },
    { label: 'D₅ Privacy', short: 'Privacy', value: 0.60 },
    { label: 'D₆ Societal', short: 'Societal', value: 0.65 },
    { label: 'D₇ Virtue', short: 'Virtue', value: 0.72 },
    { label: 'D₈ Procedural', short: 'Procedural', value: 0.68 },
    { label: 'D₉ Epistemic', short: 'Epistemic', value: 0.55 }
  ];

  const cx = 250, cy = 250, maxR = 180;
  const linesG = document.getElementById('dim-lines');
  const labelsG = document.getElementById('dim-labels');
  const polygon = document.getElementById('dim-polygon');

  if (!linesG || !labelsG || !polygon) return;

  const n = dims.length;
  const angleStep = (2 * Math.PI) / n;
  const points = [];

  dims.forEach((dim, i) => {
    const angle = -Math.PI / 2 + i * angleStep;
    const ex = cx + maxR * Math.cos(angle);
    const ey = cy + maxR * Math.sin(angle);
    const px = cx + maxR * dim.value * Math.cos(angle);
    const py = cy + maxR * dim.value * Math.sin(angle);
    const lx = cx + (maxR + 24) * Math.cos(angle);
    const ly = cy + (maxR + 24) * Math.sin(angle);

    points.push(`${px},${py}`);

    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    Object.entries({ x1: cx, y1: cy, x2: ex, y2: ey, stroke: colors[i], 'stroke-width': 1.5, opacity: 0.4 })
      .forEach(([k, v]) => line.setAttribute(k, v));
    linesG.appendChild(line);

    const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    Object.entries({ cx: px, cy: py, r: 5, fill: colors[i], cursor: 'pointer' })
      .forEach(([k, v]) => dot.setAttribute(k, v));
    dot.dataset.dim = i + 1;
    linesG.appendChild(dot);

    dot.addEventListener('mouseenter', () => {
      dot.setAttribute('r', '8');
      highlightDimension(i + 1);
    });
    dot.addEventListener('mouseleave', () => dot.setAttribute('r', '5'));
    dot.addEventListener('click', () => highlightDimension(i + 1));

    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', lx);
    text.setAttribute('y', ly + 4);
    text.setAttribute('text-anchor', Math.cos(angle) < -0.1 ? 'end' : Math.cos(angle) > 0.1 ? 'start' : 'middle');
    text.setAttribute('fill', colors[i]);
    text.setAttribute('font-size', '11');
    text.setAttribute('font-family', 'Inter, sans-serif');
    text.setAttribute('font-weight', '500');
    text.textContent = dim.short;
    text.style.cursor = 'pointer';
    text.dataset.dim = i + 1;
    text.addEventListener('click', () => highlightDimension(i + 1));
    labelsG.appendChild(text);
  });

  polygon.setAttribute('points', points.join(' '));

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        polygon.style.transition = 'all 1s ease';
        polygon.setAttribute('fill', 'rgba(27,158,119,0.12)');
      }
    });
  }, { threshold: 0.3 });
  const dimSection = document.getElementById('dimensions');
  if (dimSection) observer.observe(dimSection);

  function highlightDimension(dimNum) {
    document.querySelectorAll('.dim-card').forEach(card => {
      card.classList.toggle('active', parseInt(card.dataset.dim) === dimNum);
    });
    const dot = linesG.querySelectorAll('circle')[dimNum - 1];
    if (dot) {
      dot.setAttribute('r', '8');
      setTimeout(() => dot.setAttribute('r', '5'), 600);
    }
  }

  document.querySelectorAll('.dim-card').forEach(card => {
    card.addEventListener('click', () => {
      highlightDimension(parseInt(card.dataset.dim));
    });
  });
}

/* --- Tensor Hierarchy Interactive --- */
function initTensorHierarchy() {
  const buttons = document.querySelectorAll('.level-btn');
  const levels = document.querySelectorAll('.h-level');

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const level = btn.dataset.level;
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      levels.forEach(l => {
        const id = l.id.replace('h-level-', '');
        if (id === level) {
          l.style.display = '';
          l.style.opacity = '0';
          l.classList.add('active');
          requestAnimationFrame(() => {
            l.style.transition = 'opacity 0.4s ease';
            l.style.opacity = '1';
          });
        } else {
          l.classList.remove('active');
          l.style.display = 'none';
        }
      });
    });
  });
}

/* --- Parts Accordion --- */
function initPartsAccordion() {
  document.querySelectorAll('.part-header').forEach(header => {
    header.addEventListener('click', () => {
      const item = header.closest('.part-item');
      const wasOpen = item.classList.contains('open');
      document.querySelectorAll('.part-item').forEach(i => i.classList.remove('open'));
      if (!wasOpen) item.classList.add('open');
    });
  });
}

/* --- Hero Floating Particles (Canvas) --- */
function initHeroParticles() {
  const hero = document.getElementById('hero');
  if (!hero) return;

  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:absolute;inset:0;z-index:0;pointer-events:none;';
  hero.insertBefore(canvas, hero.firstChild);

  const ctx = canvas.getContext('2d');
  let particles = [];
  let w, h;

  function resize() {
    w = canvas.width = hero.offsetWidth;
    h = canvas.height = hero.offsetHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const pColors = [
    'rgba(27,158,119,',
    'rgba(117,112,179,',
    'rgba(141,160,203,',
  ];

  for (let i = 0; i < 35; i++) {
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() * 1.5 + 0.5,
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.2,
      color: pColors[Math.floor(Math.random() * pColors.length)],
      alpha: Math.random() * 0.3 + 0.05
    });
  }

  function animate() {
    ctx.clearRect(0, 0, w, h);
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = w;
      if (p.x > w) p.x = 0;
      if (p.y < 0) p.y = h;
      if (p.y > h) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color + p.alpha + ')';
      ctx.fill();
    });

    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(102,194,165,${0.06 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(animate);
  }
  animate();
}

/* ==========================================================================
   NEW INTERACTIVE FEATURES
   ========================================================================== */

/* --- Object Cards (click to expand/collapse formal definition) --- */
function initObjectCards() {
  document.querySelectorAll('.object-card').forEach(card => {
    card.style.cursor = 'pointer';
    const formal = card.querySelector('.object-formal');
    if (!formal) return;

    formal.style.maxHeight = '0';
    formal.style.overflow = 'hidden';
    formal.style.opacity = '0';
    formal.style.transition = 'max-height 0.35s ease, opacity 0.3s ease, padding-top 0.3s ease, margin-top 0.3s ease';
    formal.style.paddingTop = '0';
    formal.style.marginTop = '0';

    // Add hint
    const hint = document.createElement('span');
    hint.textContent = 'Click to explore';
    hint.style.cssText = 'display:block;font-size:11px;color:var(--text-muted);margin-top:8px;opacity:0.6;transition:opacity 0.2s';
    card.appendChild(hint);

    card.addEventListener('click', () => {
      const isOpen = card.classList.toggle('expanded');
      if (isOpen) {
        formal.style.maxHeight = '120px';
        formal.style.opacity = '1';
        formal.style.paddingTop = '8px';
        formal.style.marginTop = '4px';
        hint.style.opacity = '0';
      } else {
        formal.style.maxHeight = '0';
        formal.style.opacity = '0';
        formal.style.paddingTop = '0';
        formal.style.marginTop = '0';
        hint.style.opacity = '0.6';
      }
    });
  });
}

/* --- Theorem Cards (click to expand key insight) --- */
function initTheoremCards() {
  const details = {
    'Structured Pluralism': 'The partial order on admissible metrics means some genuine moral disagreements are geometrically irreducible \u2014 neither framework is "better." This is not relativism: the partial order still rules out many metrics. It is the mathematical formalization of reasonable pluralism.',
    'Conservation of Harm': 'BIP is a continuous symmetry of the moral Lagrangian. By Noether\u2019s theorem, this yields a conserved charge: harm. Four consequences flow directly: euphemism preserves total harm, harm is auditable across representations, re-description cannot redistribute harm between dimensions, and unresolved harm persists as moral debt.',
    'Gauge Group': 'D\u2084 has 8 elements mapping between Hohfeldian positions: Obligation \u2194 Claim (correlatives) and Liberty \u2194 No-claim (correlatives), plus their negations and compositions. Combined with U(1)\u2095 (harm phase rotation), this gives the maximal group preserving both jural structure and bounded total harm.',
    'No Escape Theorem': 'An AI system cannot find a description d\u2032 where moral constraints don\u2019t apply, because BIP guarantees E(d) = E(d\u2032) for all admissible re-descriptions. The four architectural requirements \u2014 canonicalization, grounded evaluation, structural audit, verification integrity \u2014 close all known escape routes.',
    'Non-Commutativity of Contraction': 'Contracting D\u2081 then D\u2082 \u2260 D\u2082 then D\u2081. Each contraction discards different dimensional information. This is why "which values do we simplify first?" is a substantive moral question, not a technical convenience. The order of moral simplification matters.',
    'Admissibility': 'Moral rules like "do not kill" and "keep your promises" never overestimate true cost to moral equilibrium. They may be suboptimal in edge cases (trolley problems), but they never make the search worse \u2014 they are guaranteed safe shortcuts. This is why evolution pre-compiled deontological rules into cognition.',
    'Intractability': 'Finding the exact moral geodesic on a 9-dimensional stratified manifold with boundaries is NP-hard in general. This explains why moral reasoning IS hard, and why we rely on heuristics: virtues, rules, intuitions, cultural norms. It is a feature of the problem, not a bug.'
  };

  document.querySelectorAll('.theorem-card').forEach(card => {
    const title = card.querySelector('h3');
    if (!title) return;
    const detail = details[title.textContent];
    if (!detail) return;

    card.style.cursor = 'pointer';

    const panel = document.createElement('div');
    panel.className = 'theorem-detail';
    panel.innerHTML = '<p>' + detail + '</p>';
    panel.style.cssText = 'max-height:0;overflow:hidden;opacity:0;transition:max-height 0.4s ease,opacity 0.3s ease;';
    card.appendChild(panel);

    // Click hint
    const hint = document.createElement('span');
    hint.textContent = 'Click for key insight \u2192';
    hint.className = 'theorem-hint';
    hint.style.cssText = 'display:block;font-size:11px;color:var(--text-muted);margin-top:8px;opacity:0.5;transition:opacity 0.2s';
    card.insertBefore(hint, panel);

    card.addEventListener('click', () => {
      const isOpen = card.classList.toggle('expanded');

      // Close others
      document.querySelectorAll('.theorem-card.expanded').forEach(c => {
        if (c !== card) {
          c.classList.remove('expanded');
          const p = c.querySelector('.theorem-detail');
          const h = c.querySelector('.theorem-hint');
          if (p) { p.style.maxHeight = '0'; p.style.opacity = '0'; }
          if (h) h.style.opacity = '0.5';
        }
      });

      if (isOpen) {
        panel.style.maxHeight = '300px';
        panel.style.opacity = '1';
        hint.style.opacity = '0';
      } else {
        panel.style.maxHeight = '0';
        panel.style.opacity = '0';
        hint.style.opacity = '0.5';
      }
    });
  });
}

/* --- Application Cards (click to expand domain detail) --- */
function initAppCards() {
  const details = {
    economics: {
      title: 'Geometric Economics',
      chapter: 20,
      detail: 'The Bond Geodesic Equilibrium replaces Nash equilibrium with geodesic paths on the moral manifold. The 2008 financial crisis is analyzed as a manifold failure where the metric collapsed. Prospect theory\u2019s reference-dependence is a gauge choice.'
    },
    clinical: {
      title: 'Geometric Clinical Ethics',
      chapter: 21,
      detail: 'The QALY Irrecoverability Theorem: converting quality-adjusted life-years to a scalar necessarily destroys clinically relevant information. Triage as optimal pathfinding on the emergency stratum of the moral manifold.'
    },
    law: {
      title: 'Geometric Jurisprudence',
      chapter: 22,
      detail: 'The Hohfeldian octad (O, C, L, N and their opposites) forms a D\u2084 gauge symmetry group. Legal disputes become A* pathfinding problems. Constitutional law provides topological constraints. Precedent operates as parallel transport.'
    },
    finance: {
      title: 'Geometric Finance',
      chapter: 23,
      detail: 'Flash crashes are dimensional collapse events where the market metric degenerates. Option pricing as scalar projection loses hedging structure. Market microstructure analyzed on the decision manifold.'
    },
    theology: {
      title: 'Geometric Theology',
      chapter: 24,
      detail: 'The Euthyphro dilemma dissolves as a gauge ambiguity \u2014 different gauge choices correspond to different theological positions on the same underlying moral geometry. Theodicy analyzed as dimensional projection failure.'
    },
    environment: {
      title: 'Geometric Environmental Ethics',
      chapter: 25,
      detail: 'Climate change as intergenerational obligation across temporal boundaries. The discount rate controversy is dimensional collapse \u2014 reducing future welfare to a present scalar. Species extinction as irreversible boundary crossing.'
    },
    ai: {
      title: 'Geometric AI Ethics',
      chapter: 26,
      detail: 'The paperclip maximizer is dimensional collapse: an AI projecting the full moral tensor to a single scalar. Alignment = geodesic preservation. Algorithmic bias as scalar projection. The No Escape Theorem prevents circumvention via re-framing.'
    },
    bioethics: {
      title: 'Geometric Bioethics',
      chapter: 27,
      detail: 'CRISPR as irreversible boundary crossing: germline editing crosses an absorbing stratum. Research ethics requires the double consent condition \u2014 both current participants AND affected future populations must be considered.'
    },
    military: {
      title: 'Geometric Military Ethics',
      chapter: 28,
      detail: 'Proportionality as multi-dimensional cost-benefit on the moral manifold. The doctrine of double effect as decomposition into intended and unintended dimensional components. Moral injury formalized as manifold damage.'
    }
  };

  const section = document.getElementById('applications');
  if (!section) return;
  const container = section.querySelector('.container');

  const detailPanel = document.createElement('div');
  detailPanel.className = 'app-detail-panel';
  detailPanel.style.cssText = 'max-height:0;overflow:hidden;opacity:0;transition:max-height 0.4s ease,opacity 0.3s ease,margin-top 0.3s ease;margin-top:0;';
  container.appendChild(detailPanel);

  document.querySelectorAll('.app-hex').forEach(hex => {
    hex.style.cursor = 'pointer';
    const app = hex.dataset.app;

    hex.addEventListener('click', () => {
      const wasActive = hex.classList.contains('active');

      document.querySelectorAll('.app-hex.active').forEach(h => h.classList.remove('active'));

      if (wasActive) {
        detailPanel.style.maxHeight = '0';
        detailPanel.style.opacity = '0';
        detailPanel.style.marginTop = '0';
        return;
      }

      hex.classList.add('active');
      const info = details[app];
      if (info) {
        detailPanel.innerHTML =
          '<div class="app-detail-inner">' +
            '<h4>' + info.title + ' <span class="app-ch-badge">Chapter ' + info.chapter + '</span></h4>' +
            '<p>' + info.detail + '</p>' +
          '</div>';
        detailPanel.style.maxHeight = '300px';
        detailPanel.style.opacity = '1';
        detailPanel.style.marginTop = '28px';
      }
    });
  });
}

/* --- Reading Paths (click to navigate to chapters) --- */
function initReadingPaths() {
  document.querySelectorAll('.path-card').forEach(card => {
    card.style.cursor = 'pointer';
    const chapters = Array.from(card.querySelectorAll('.path-ch')).map(el => parseInt(el.textContent));

    // Add hint
    const hint = document.createElement('span');
    hint.textContent = 'Click to highlight chapters \u2192';
    hint.style.cssText = 'display:block;font-size:11px;color:var(--text-muted);margin-top:12px;opacity:0.5';
    card.appendChild(hint);

    card.addEventListener('click', () => {
      const partsSection = document.getElementById('parts');
      if (!partsSection) return;

      partsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

      setTimeout(() => {
        // Clear previous highlights
        document.querySelectorAll('.chapter-item.highlighted').forEach(ch => ch.classList.remove('highlighted'));

        document.querySelectorAll('.part-item').forEach(item => {
          const chapterItems = item.querySelectorAll('.chapter-item');
          let hasMatch = false;

          chapterItems.forEach(ch => {
            const num = parseInt(ch.querySelector('.ch-num')?.textContent);
            if (chapters.includes(num)) {
              hasMatch = true;
              ch.classList.add('highlighted');
            }
          });

          if (hasMatch) item.classList.add('open');
        });

        // Clear highlights after 6 seconds
        setTimeout(() => {
          document.querySelectorAll('.chapter-item.highlighted').forEach(ch => {
            ch.classList.remove('highlighted');
          });
        }, 6000);
      }, 600);
    });
  });
}

/* --- DEME Architecture (click layers for detail) --- */
function initDemeArchitecture() {
  const layerInfo = [
    { y: 10, name: 'Layer 7: Application', detail: 'Domain-specific modules (healthcare, finance, legal) that consume DEME evaluations and translate them into domain actions and recommendations.' },
    { y: 65, name: 'Layer 6: Governance Profile', detail: 'Selects which moral metric g\u03bc\u03bd to use. Different profiles encode different ethical frameworks \u2014 utilitarian, deontological, virtue-based, or custom blends.' },
    { y: 120, name: 'Layer 5: ErisML Specification', detail: 'The modeling language that translates natural-language policies into formal tensor specifications. Bridges human intent and mathematical structure.' },
    { y: 175, name: 'Layer 4: Translation Layer', detail: 'Policy modules that convert ErisML specs into executable DEME evaluation pipelines. Maps specification to computation.' },
    { y: 230, name: 'Layer 3: DEME Ethics Engine', detail: 'Core evaluation engine. Takes EthicalFacts, applies Ethics Modules, performs tensor contraction, computes the Bond Index, returns structured Judgements.' },
    { y: 285, name: 'Layer 2: Norm Kernel', detail: 'Formally verified automaton enforcing hard ethical constraints \u2014 the "thou shalt not" rules that cannot be overridden by any higher layer. The safety floor.' },
    { y: 340, name: 'Layer 1: Tensor Runtime', detail: 'Geometric primitives: manifold operations, tensor algebra, parallel transport, geodesic computation, stratification logic. The mathematical substrate.' }
  ];

  const vizContainer = document.querySelector('.architecture-viz');
  const svg = document.querySelector('.deme-svg');
  if (!vizContainer || !svg) return;

  // Create tooltip
  const tooltip = document.createElement('div');
  tooltip.className = 'deme-tooltip';
  vizContainer.style.position = 'relative';
  vizContainer.appendChild(tooltip);

  const rects = svg.querySelectorAll('rect');
  rects.forEach(rect => {
    const ry = parseFloat(rect.getAttribute('y'));
    const info = layerInfo.find(l => Math.abs(l.y - ry) < 5);
    if (!info) return;

    rect.style.cursor = 'pointer';
    rect.addEventListener('mouseenter', () => {
      rect.setAttribute('stroke-width', '3');
    });
    rect.addEventListener('mouseleave', () => {
      rect.setAttribute('stroke-width', rect.getAttribute('y') === '230' ? '2' : '1.5');
    });
    rect.addEventListener('click', (e) => {
      e.stopPropagation();
      tooltip.innerHTML =
        '<h4>' + info.name + '</h4>' +
        '<p>' + info.detail + '</p>';
      tooltip.classList.add('visible');
    });
  });

  document.addEventListener('click', (e) => {
    if (!tooltip.contains(e.target)) {
      tooltip.classList.remove('visible');
    }
  });
}

/* --- Equation Step-Through --- */
function initEquationHighlight() {
  const terms = document.querySelectorAll('.eq-term');
  const formula = document.querySelector('.eq-main');
  if (!terms.length || !formula) return;

  let active = -1;
  let autoCycleId;

  terms.forEach((term, i) => {
    term.style.cursor = 'pointer';
    term.style.transition = 'all 0.3s ease';
    term.style.padding = '12px';
    term.style.borderRadius = '8px';
    term.style.border = '1px solid transparent';

    term.addEventListener('click', () => {
      clearInterval(autoCycleId);
      active = active === i ? -1 : i;
      terms.forEach((t, j) => {
        t.style.background = j === active ? 'rgba(27,158,119,0.1)' : 'transparent';
        t.style.borderColor = j === active ? 'var(--border-medium)' : 'transparent';
      });
    });
  });

  // Auto-cycle to hint at interactivity
  let step = 0;
  autoCycleId = setInterval(() => {
    if (active !== -1) return;
    terms.forEach((t, j) => {
      t.style.background = j === step ? 'rgba(27,158,119,0.06)' : 'transparent';
      t.style.borderColor = j === step ? 'var(--border-subtle)' : 'transparent';
    });
    step = (step + 1) % terms.length;
  }, 2500);
}

/* --- Conservation of Harm Interactive --- */
function initConservationInteractive() {
  const consequences = document.querySelectorAll('.consequence');
  const svg = document.querySelector('.noether-svg');

  consequences.forEach(c => {
    c.style.cursor = 'pointer';
    c.style.transition = 'all 0.3s ease';
    c.style.padding = '12px';
    c.style.borderRadius = '8px';

    c.addEventListener('click', () => {
      const wasActive = c.classList.contains('active');
      consequences.forEach(cc => {
        cc.classList.remove('active');
        cc.style.background = 'transparent';
      });

      if (!wasActive) {
        c.classList.add('active');
        c.style.background = 'rgba(27,158,119,0.06)';

        // Pulse the SVG center
        if (svg) {
          const center = svg.querySelector('circle[r="40"]');
          if (center) {
            center.style.transition = 'r 0.3s ease';
            center.setAttribute('r', '46');
            setTimeout(() => center.setAttribute('r', '40'), 400);
          }
        }
      }
    });
  });
}

/* --- Epistemic Cards (click to expand examples) --- */
function initEpistemicCards() {
  const examples = {
    'Definition / Modeling choice': 'Examples: The 9 moral dimensions, the Whitney stratification model, the choice of smooth manifold topology, the Hohfeldian position types. These are the framework\u2019s architectural choices \u2014 useful but not uniquely determined by the data.',
    'Theorem (conditional)': 'Examples: Conservation of Harm (Thm 12.1), No Escape (Thm 18.1), Structured Pluralism (Thm 9.2). Each is rigorous mathematics \u2014 but the real question is whether its premises hold in the world.',
    'Empirical result (preliminary / robust)': 'Examples: BIP violation rates in the Dear Abby corpus (robust \u2014 51K letters), order effects in moral judgment (robust \u2014 replicated), Bell inequality violation (preliminary \u2014 open question).',
    'Speculation / Extension': 'Examples: Connections to Orch-OR consciousness theory, the moral field equation, torsion in moral space, category-theoretic reformulation. Flagged honestly as speculative \u2014 directions for future research.'
  };

  document.querySelectorAll('.epistemic-card').forEach(card => {
    const tag = card.querySelector('.tag')?.textContent;
    const example = examples[tag];
    if (!example) return;

    card.style.cursor = 'pointer';
    card.style.transition = 'border-color 0.3s ease';

    const detail = document.createElement('div');
    detail.className = 'epistemic-detail';
    detail.innerHTML = '<p>' + example + '</p>';
    detail.style.cssText = 'max-height:0;overflow:hidden;opacity:0;transition:max-height 0.35s ease,opacity 0.3s ease;';
    card.appendChild(detail);

    card.addEventListener('click', () => {
      const isOpen = card.classList.toggle('expanded');
      if (isOpen) {
        detail.style.maxHeight = '200px';
        detail.style.opacity = '1';
        card.style.borderColor = 'var(--border-medium)';
      } else {
        detail.style.maxHeight = '0';
        detail.style.opacity = '0';
        card.style.borderColor = '';
      }
    });
  });
}

/* --- Dear Ethicist Game Demo (functional mini-game) --- */
function initGameDemo() {
  const choicesDiv = document.querySelector('.game-choices');
  if (!choicesDiv) return;

  const positions = ['O', 'C', 'L', 'N'];
  const labels = { O: 'Obligation', C: 'Claim', L: 'Liberty', N: 'No-claim' };

  let neighborChoice = null;
  let writerChoice = null;

  choicesDiv.innerHTML =
    '<div class="choice-row">' +
      '<span class="choice-label">Neighbor\u2019s position:</span>' +
      '<div class="choice-buttons" data-party="neighbor">' +
        positions.map(p =>
          '<button class="choice-btn" data-choice="' + p + '">' + p + ' <small>' + labels[p] + '</small></button>'
        ).join('') +
      '</div>' +
    '</div>' +
    '<div class="choice-row">' +
      '<span class="choice-label">Writer\u2019s claim:</span>' +
      '<div class="choice-buttons" data-party="writer">' +
        positions.map(p =>
          '<button class="choice-btn" data-choice="' + p + '">' + p + ' <small>' + labels[p] + '</small></button>'
        ).join('') +
      '</div>' +
    '</div>' +
    '<div class="game-result" style="padding:12px 0 0;display:none">' +
      '<div class="game-result-inner">' +
        '<p class="result-text"></p>' +
      '</div>' +
    '</div>';

  function updateResult() {
    const result = choicesDiv.querySelector('.game-result');
    const text = choicesDiv.querySelector('.result-text');
    const inner = choicesDiv.querySelector('.game-result-inner');
    if (!neighborChoice || !writerChoice) {
      result.style.display = 'none';
      return;
    }

    result.style.display = 'block';

    const isCorrelative =
      (neighborChoice === 'O' && writerChoice === 'C') ||
      (neighborChoice === 'C' && writerChoice === 'O') ||
      (neighborChoice === 'L' && writerChoice === 'N') ||
      (neighborChoice === 'N' && writerChoice === 'L');

    if (isCorrelative) {
      text.innerHTML =
        '<strong style="color:var(--cb-teal)">Correlative symmetry holds.</strong> ' +
        neighborChoice + ' \u2194 ' + writerChoice + ' is a valid Hohfeldian correlative pair. Bond Index contribution: 0 (perfect structural consistency).';
      inner.className = 'game-result-inner result-good';
    } else {
      const violation = (0.3 + Math.random() * 0.5).toFixed(2);
      text.innerHTML =
        '<strong style="color:var(--cb-orange)">' + neighborChoice + ' \u2194 ' + writerChoice + '</strong>' +
        ' is not a correlative pair. The Hohfeldian correlatives are O\u2194C and L\u2194N. ' +
        'Bond Index contribution: ' + violation + ' (structural violation detected).';
      inner.className = 'game-result-inner result-warn';
    }
  }

  choicesDiv.querySelectorAll('.choice-buttons').forEach(group => {
    const party = group.dataset.party;
    group.querySelectorAll('.choice-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        group.querySelectorAll('.choice-btn').forEach(b => b.classList.remove('active-choice'));
        btn.classList.add('active-choice');

        if (party === 'neighbor') neighborChoice = btn.dataset.choice;
        if (party === 'writer') writerChoice = btn.dataset.choice;

        updateResult();
      });
    });
  });
}

/* --- Bell Test Interactive Slider --- */
function initBellTestSlider() {
  const bellViz = document.querySelector('.bell-viz');
  const bellSvg = document.querySelector('.bell-svg');
  if (!bellViz || !bellSvg) return;

  const controls = document.createElement('div');
  controls.className = 'bell-controls';
  controls.innerHTML =
    '<div class="bell-slider-row">' +
      '<span class="bell-slider-label">Observed S value:</span>' +
      '<input type="range" min="0" max="320" value="210" class="bell-slider">' +
      '<span class="bell-s-display">S = 2.10</span>' +
    '</div>' +
    '<p class="bell-verdict"></p>';
  bellViz.appendChild(controls);

  const slider = controls.querySelector('.bell-slider');
  const display = controls.querySelector('.bell-s-display');
  const verdict = controls.querySelector('.bell-verdict');

  function updateBell(value) {
    const s = value / 100;
    display.textContent = 'S = ' + s.toFixed(2);

    if (s <= 2) {
      verdict.innerHTML = '<span style="color:var(--cb-orange)">Within classical bound (|S| \u2264 2).</span> Moral reasoning appears classical \u2014 no quantum structure detected.';
      display.style.color = 'var(--cb-orange)';
    } else if (s <= 2.83) {
      verdict.innerHTML = '<span style="color:var(--cb-purple)">Classical bound violated!</span> Evidence for quantum-like superposition and interference in moral deliberation.';
      display.style.color = 'var(--cb-purple)';
    } else {
      verdict.innerHTML = '<span style="color:var(--text-muted)">Exceeds Tsirelson bound (2\u221A2 \u2248 2.83).</span> This would violate quantum mechanics itself \u2014 check experimental design.';
      display.style.color = 'var(--text-muted)';
    }
  }

  slider.addEventListener('input', () => updateBell(parseInt(slider.value)));
  updateBell(210);
}
