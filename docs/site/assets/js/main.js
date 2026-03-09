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
});

/* --- Navigation --- */
function initNav() {
  const nav = document.getElementById('main-nav');
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');

  // Scroll effect
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 50);
  });

  // Mobile toggle
  if (toggle) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
    });
  }

  // Close on link click
  document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => links.classList.remove('open'));
  });

  // Active link highlighting
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

/* --- Scroll-triggered Animations (replaces AOS library) --- */
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
  events.forEach(ev => {
    ev.addEventListener('click', () => {
      events.forEach(e => e.classList.remove('active'));
      ev.classList.add('active');
    });
  });

  // Auto-cycle
  let step = 0;
  setInterval(() => {
    step = (step + 1) % events.length;
    events.forEach(e => e.classList.remove('active'));
    events[step].classList.add('active');
  }, 4000);
}

/* --- Nine Dimensions Radial Chart --- */
function initDimensionWheel() {
  // ColorBrewer Dark2 colors for 9 dimensions
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

    // Axis line
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    Object.entries({ x1: cx, y1: cy, x2: ex, y2: ey, stroke: colors[i], 'stroke-width': 1.5, opacity: 0.4 })
      .forEach(([k, v]) => line.setAttribute(k, v));
    linesG.appendChild(line);

    // Value dot
    const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    Object.entries({ cx: px, cy: py, r: 5, fill: colors[i], cursor: 'pointer' })
      .forEach(([k, v]) => dot.setAttribute(k, v));
    dot.dataset.dim = i + 1;
    linesG.appendChild(dot);

    // Add pulse animation on hover
    dot.addEventListener('mouseenter', () => {
      dot.setAttribute('r', '8');
      highlightDimension(i + 1);
    });
    dot.addEventListener('mouseleave', () => dot.setAttribute('r', '5'));
    dot.addEventListener('click', () => highlightDimension(i + 1));

    // Label
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

  // Draw polygon
  polygon.setAttribute('points', points.join(' '));

  // Animate polygon on scroll
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

  // Dimension card interactivity
  function highlightDimension(dimNum) {
    document.querySelectorAll('.dim-card').forEach(card => {
      card.classList.toggle('active', parseInt(card.dataset.dim) === dimNum);
    });
    // Pulse the polygon vertex
    const angle = -Math.PI / 2 + (dimNum - 1) * angleStep;
    const px = cx + maxR * dims[dimNum - 1].value * Math.cos(angle);
    const py = cy + maxR * dims[dimNum - 1].value * Math.sin(angle);

    // Briefly increase the dot
    const dot = linesG.querySelectorAll('circle')[dimNum - 1];
    if (dot) {
      dot.setAttribute('r', '8');
      setTimeout(() => dot.setAttribute('r', '5'), 600);
    }
  }

  // Click handlers on dimension cards
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

      // Close all
      document.querySelectorAll('.part-item').forEach(i => i.classList.remove('open'));

      // Toggle clicked
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

  // ColorBrewer colors for particles
  const pColors = [
    'rgba(27,158,119,',   // teal
    'rgba(117,112,179,',  // purple
    'rgba(230,171,2,',    // gold
    'rgba(102,166,30,',   // green
    'rgba(141,160,203,',  // blue-purple
  ];

  // Create particles
  for (let i = 0; i < 50; i++) {
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() * 2 + 0.5,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      color: pColors[Math.floor(Math.random() * pColors.length)],
      alpha: Math.random() * 0.4 + 0.1
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

    // Draw connections between close particles
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(102,194,165,${0.08 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(animate);
  }
  animate();
}
