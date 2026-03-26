"""Generate publication-quality figures for JRU paper."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUT = Path(r'C:\source\erisml-lib\docs\papers\paper4-variable-loss-aversion\figures')
OUT.mkdir(exist_ok=True)

# Journal style
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# ═══════════════════════════════════════════════════════════════
# FIGURE 1: Lambda vs Dimensions (the key prediction)
# ═══════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(5.5, 3.8))

# Theoretical curve
d = np.linspace(1, 14, 200)
lam = np.sqrt(d)
ax.plot(d, lam, color='#b7410e', linewidth=2.2, label=r'Geometric: $\lambda = \sqrt{d}$', zorder=5)

# CPT constant
ax.axhline(y=2.25, color='#4a90d9', linewidth=1.5, linestyle='--', alpha=0.8, label=r'CPT: $\lambda = 2.25$ (constant)')

# Horowitz & McConnell range
ax.axhspan(1.0, 3.5, alpha=0.06, color='#805ad5', zorder=0)
ax.annotate('H&M 2002\nmeta-analytic\nrange', xy=(12.5, 2.25), fontsize=7.5, color='#805ad5',
            ha='center', va='center', style='italic')

# Data points
points = [
    (1, 1.00, 'Pure\ncash', '#2ca02c', 'o'),
    (2, 1.63, 'Commodity', '#2ca02c', 's'),
    (3, 1.91, 'Gift', '#2ca02c', 'D'),
    (5, 2.22, 'Standard\n(KT 1992)', '#d62728', '^'),
    (12.5, 3.53, 'Heirloom', '#7b2d8e', 'p'),
]

for d_val, lam_val, label, color, marker in points:
    ax.scatter(d_val, lam_val, s=80, c=color, marker=marker, zorder=10,
              edgecolors='white', linewidths=0.8)
    offset_y = 0.18 if d_val != 5 else -0.25
    offset_x = 0
    if d_val == 12.5: offset_y = 0.25
    if d_val == 1: offset_x = 0.4; offset_y = -0.2
    ax.annotate(label, (d_val + offset_x, lam_val + offset_y),
               fontsize=7.5, ha='center', va='bottom', color=color, fontweight='600')

# Match point annotation
ax.annotate('', xy=(5, 2.25), xytext=(5, 2.22),
           arrowprops=dict(arrowstyle='<->', color='#999', lw=0.8))
ax.annotate(r'$\Delta = 0.03$', xy=(5.6, 2.235), fontsize=7, color='#999')

ax.set_xlabel('Active evaluative dimensions ($d$)')
ax.set_ylabel(r'Loss aversion coefficient ($\lambda$)')
ax.set_xlim(0, 14.5)
ax.set_ylim(0.5, 4.2)
ax.legend(loc='upper left', framealpha=0.95, edgecolor='#ddd')
ax.set_xticks([1, 2, 3, 5, 7, 9, 12.5])
ax.set_xticklabels(['1', '2', '3', '5', '7', '9', '12.5'])

fig.savefig(OUT / 'fig1_lambda_vs_dimensions.png')
fig.savefig(OUT / 'fig1_lambda_vs_dimensions.svg')
plt.close()
print('Figure 1: lambda vs dimensions')


# ═══════════════════════════════════════════════════════════════
# FIGURE 2: Dimensional activation diagram (gain vs loss)
# ═══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(6, 3.2), gridspec_kw={'wspace': 0.4})

dims = ['Consequences\n($a_1$)', 'Rights\n($a_2$)', 'Fairness\n($a_3$)',
        'Autonomy\n($a_4$)', 'Trust\n($a_5$)', 'Social\n($a_6$)',
        'Identity\n($a_7$)', 'Legitimacy\n($a_8$)', 'Epistemic\n($a_9$)']

# Panel A: Gain
ax = axes[0]
gain_active = [1, 0, 0, 0, 0, 0, 0, 0, 0]
colors_gain = ['#2ca02c' if a else '#e8e8e8' for a in gain_active]
bars = ax.barh(range(9), [0.8 if a else 0.15 for a in gain_active], color=colors_gain,
               edgecolor=['#1a7a1a' if a else '#ccc' for a in gain_active], linewidth=0.8)
ax.set_yticks(range(9))
ax.set_yticklabels(dims, fontsize=7.5)
ax.set_xlim(0, 1)
ax.set_xticks([])
ax.set_title('(a) Monetary Gain of $\\delta$', fontsize=10, fontweight='600', pad=8)
ax.invert_yaxis()
ax.text(0.5, 8.8, '$d_{gain} = 1$', fontsize=10, fontweight='700', color='#2ca02c',
        ha='center', transform=ax.get_yaxis_transform())

# Panel B: Loss (heirloom)
ax = axes[1]
loss_active = [1, 1, 1, 0, 1, 1, 1, 0, 1]
colors_loss = ['#d62728' if a else '#e8e8e8' for a in loss_active]
bars = ax.barh(range(9), [0.8 if a else 0.15 for a in loss_active], color=colors_loss,
               edgecolor=['#a01010' if a else '#ccc' for a in loss_active], linewidth=0.8)
ax.set_yticks(range(9))
ax.set_yticklabels(dims, fontsize=7.5)
ax.set_xlim(0, 1)
ax.set_xticks([])
ax.set_title('(b) Loss of Heirloom ($-\\delta$)', fontsize=10, fontweight='600', pad=8)
ax.invert_yaxis()
ax.text(0.5, 8.8, '$d_{loss} = 7$', fontsize=10, fontweight='700', color='#d62728',
        ha='center', transform=ax.get_yaxis_transform())

# Add arrows and formula below
fig.text(0.5, -0.02,
         r'$\lambda = \sqrt{d_{loss} \,/\, d_{gain}} = \sqrt{7\,/\,1} = 2.65$',
         fontsize=11, ha='center', fontweight='600', color='#b7410e')

fig.savefig(OUT / 'fig2_dimensional_activation.png')
fig.savefig(OUT / 'fig2_dimensional_activation.svg')
plt.close()
print('Figure 2: dimensional activation')


# ═══════════════════════════════════════════════════════════════
# FIGURE 3: Cross-cultural predictions vs observed
# ═══════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(5.5, 3.5))

populations = ['Machiguenga', 'Hadza', 'Tsimane', 'US students',
               'Europe avg', 'Au (PNG)', 'Lamalera']
predicted = [36, 36, 36, 37, 37, 37, 38]
observed  = [26, 27, 32, 42, 44, 44, 57]

x = np.arange(len(populations))
width = 0.35

bars1 = ax.bar(x - width/2, predicted, width, color='#b7410e', alpha=0.85,
               label='Predicted (frozen $\\Sigma$)', edgecolor='white', linewidth=0.5)
bars2 = ax.bar(x + width/2, observed, width, color='#4a90d9', alpha=0.85,
               label='Observed', edgecolor='white', linewidth=0.5)

# Error annotations
for i in range(len(populations)):
    err = abs(predicted[i] - observed[i])
    y_max = max(predicted[i], observed[i])
    ax.annotate(f'{err:.0f}%', (x[i], y_max + 1.5), fontsize=7, ha='center',
               color='#666', fontweight='500')

ax.set_ylabel('Ultimatum offer (%)')
ax.set_xticks(x)
ax.set_xticklabels(populations, rotation=35, ha='right', fontsize=8)
ax.set_ylim(0, 65)
ax.legend(loc='upper left', framealpha=0.95, edgecolor='#ddd')

# MAE annotation
ax.annotate('Cross-cultural MAE = 8.8%\n(zero cultural parameters)',
           xy=(0.98, 0.95), xycoords='axes fraction',
           fontsize=8.5, ha='right', va='top',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='#fef3ed', edgecolor='#b7410e', alpha=0.9),
           fontweight='600', color='#b7410e')

fig.savefig(OUT / 'fig3_cross_cultural.png')
fig.savefig(OUT / 'fig3_cross_cultural.svg')
plt.close()
print('Figure 3: cross-cultural')


# ═══════════════════════════════════════════════════════════════
# FIGURE 4: Geometric intuition — gain vs loss paths on manifold
# ═══════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(4.5, 4.5))

# Draw 2D projection of attribute space
ax.set_xlim(-0.5, 4.5)
ax.set_ylim(-0.5, 4.5)
ax.set_aspect('equal')
ax.set_xlabel('Monetary dimension ($a_1$)', fontsize=10)
ax.set_ylabel('Fairness dimension ($a_3$)', fontsize=10)

# Origin point (current state)
ax.scatter(2, 2, s=120, c='#333', marker='o', zorder=10)
ax.annotate('Current\nstate', (2, 1.6), fontsize=8, ha='center', color='#333', fontweight='600')

# Gain path (horizontal — only monetary)
ax.annotate('', xy=(3.5, 2), xytext=(2.15, 2),
           arrowprops=dict(arrowstyle='->', color='#2ca02c', lw=2.5))
ax.annotate('Gain: $+\\delta$\n(1 dimension)', (3.6, 2.05), fontsize=8,
           color='#2ca02c', fontweight='600', va='center')

# Loss path (diagonal — monetary + fairness)
ax.annotate('', xy=(0.7, 0.7), xytext=(1.88, 1.88),
           arrowprops=dict(arrowstyle='->', color='#d62728', lw=2.5))
ax.annotate('Loss: $-\\delta$\n(2 dimensions)', (0.1, 0.5), fontsize=8,
           color='#d62728', fontweight='600', va='center')

# Length annotations
gain_len = 1.5
loss_len = np.sqrt(1.3**2 + 1.3**2)
ax.annotate(f'|gain| = {gain_len:.1f}', (2.8, 2.3), fontsize=7.5, color='#2ca02c', style='italic')
ax.annotate(f'|loss| = {loss_len:.1f}', (1.0, 1.6), fontsize=7.5, color='#d62728', style='italic')
ax.annotate(f'$\\lambda$ = {loss_len/gain_len:.2f} = $\\sqrt{{2}}$', (0.5, 3.5), fontsize=11,
           color='#b7410e', fontweight='700',
           bbox=dict(boxstyle='round,pad=0.3', facecolor='#fef3ed', edgecolor='#b7410e'))

# Grid
ax.grid(True, alpha=0.15)
ax.set_title('Geometric Intuition: Why Losses Loom Larger', fontsize=10, fontweight='600', pad=10)

fig.savefig(OUT / 'fig4_geometric_intuition.png')
fig.savefig(OUT / 'fig4_geometric_intuition.svg')
plt.close()
print('Figure 4: geometric intuition')

print(f'\nAll figures saved to {OUT}')
