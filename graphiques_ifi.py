"""
3 visuels pédagogiques — Étude comparative IFI
Logique éditoriale : un message par visuel, zéro bruit.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np

# ==============================================================================
# PARAMÈTRES (modifiables)
# ==============================================================================
VALEUR_MAISON   = 5_000_000
ABATTEMENT_RP   = 0.30
MONTANT_EMPRUNT = 5_000_000
TAUX_EMPRUNT    = 0.04
DUREE_ANS       = 20
TAUX_PLACEMENT  = 0.05
CAPITAL_PLACE   = 5_000_000
IFI_SEUIL       = 1_300_000
IFI_BAREME = [
    (800_000,    1_300_000,  0.005),
    (1_300_000,  2_570_000,  0.007),
    (2_570_000,  5_000_000,  0.010),
    (5_000_000,  10_000_000, 0.0125),
    (10_000_000, float('inf'), 0.015),
]
BASE_IFI_MAISON = VALEUR_MAISON * (1 - ABATTEMENT_RP)

# ==============================================================================
# CALCUL
# ==============================================================================
def calcul_ifi(base):
    if base < IFI_SEUIL: return 0.0
    ifi = 0.0
    for b, h, t in IFI_BAREME:
        if base <= b: break
        ifi += (min(base, h) - b) * t
    return ifi

def calculer():
    r = TAUX_EMPRUNT / 12
    n = DUREE_ANS * 12
    mens = MONTANT_EMPRUNT * r / (1 - (1 + r)**(-n))
    crd = MONTANT_EMPRUNT
    cp = CAPITAL_PLACE
    cumul = 0.0
    rows = []
    for an in range(1, DUREE_ANS + 1):
        crd_d = crd
        int_an = cap_an = 0.0
        for _ in range(12):
            i = crd * r; c = mens - i
            int_an += i; cap_an += c
            crd = max(0.0, crd - c)
        rdt = cp * TAUX_PLACEMENT
        cp_fin = cp * (1 + TAUX_PLACEMENT)
        levier = rdt - int_an
        ifi_A = calcul_ifi(BASE_IFI_MAISON)
        base_B = BASE_IFI_MAISON - crd
        ifi_B = calcul_ifi(base_B)
        eco = ifi_A - ifi_B
        flux = levier + eco
        cumul = cumul * (1 + TAUX_PLACEMENT) + flux
        rows.append(dict(an=an, crd_d=crd_d, crd_fin=crd, int=int_an, cap=cap_an,
                         rdt=rdt, cp=cp, cp_fin=cp_fin,
                         levier=levier, ifi_A=ifi_A, base_B=base_B, ifi_B=ifi_B,
                         eco=eco, flux=flux, cumul=cumul))
        cp = cp_fin
    return rows, mens

data, mens = calculer()
ans = [d['an'] for d in data]

# Palette sobre
BLEU   = '#1D4ED8'
VERT   = '#15803D'
ROUGE  = '#B91C1C'
GRIS   = '#64748B'
FOND   = '#FAFAFA'
GRILLE = '#E2E8F0'
NOIR   = '#0F172A'

def base_ax(ax, title, subtitle='', xlabel='Année', ylabel=''):
    ax.set_facecolor(FOND)
    if subtitle:
        ax.set_title(f"{title}\n{subtitle}", fontsize=12, fontweight='bold',
                     color=NOIR, pad=10, linespacing=1.5)
    else:
        ax.set_title(title, fontsize=12, fontweight='bold', color=NOIR, pad=10)
    ax.set_xlabel(xlabel, fontsize=9, color=GRIS)
    if ylabel: ax.set_ylabel(ylabel, fontsize=9, color=GRIS)
    ax.grid(axis='y', color=GRILLE, linewidth=0.8, zorder=0)
    ax.set_xticks(ans)
    ax.tick_params(colors=GRIS, labelsize=8.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRILLE)
    ax.spines['bottom'].set_color(GRILLE)

# ──────────────────────────────────────────────────────────────────────────────
# VISUEL 1 — CRD vs Base IFI : quand la protection prend fin
# ──────────────────────────────────────────────────────────────────────────────
fig1, ax = plt.subplots(figsize=(13, 6))
fig1.patch.set_facecolor('white')

crds    = [d['crd_fin'] / 1e6 for d in data]
base_bs = [d['base_B']  / 1e6 for d in data]
seuil   = IFI_SEUIL / 1e6   # 1.3M

# Zone protégée (base_B < 1.3M)
ax.axvspan(0.5, 13.5, alpha=0.07, color=VERT, zorder=1)
ax.axvspan(13.5, 20.5, alpha=0.07, color=ROUGE, zorder=1)

# Courbes
ax.plot(ans, crds,    color=BLEU,  lw=2.5, marker='o', ms=4, label='Capital Restant Dû (CRD)  — ce que la banque peut encore réclamer')
ax.plot(ans, base_bs, color=VERT,  lw=2.5, marker='s', ms=4, label='Base IFI nette  =  3,5M€ − CRD  — ce que l\'État peut taxer')

# Seuil de déclenchement
ax.axhline(seuil, color=ROUGE, lw=1.5, linestyle='--', zorder=4)
ax.text(20.3, seuil + 0.05, "Seuil IFI\n1,3M€", fontsize=8.5, color=ROUGE, va='bottom')

# Seuil CRD critique
ax.axhline(2.2, color=BLEU, lw=1, linestyle=':', zorder=4, alpha=0.6)
ax.text(0.7, 2.25, "CRD critique = 2,2M€\n(si CRD < 2,2M€ → base B > 1,3M€ → IFI due)", fontsize=8, color=BLEU, alpha=0.8)

# Annotation croisement
ax.annotate("An 14 : la dette\nne couvre plus l'IFI\nBase B = 1,56M€ > 1,3M€",
    xy=(14, base_bs[13]), xytext=(11.5, 2.3),
    fontsize=8.5, color=ROUGE,
    arrowprops=dict(arrowstyle='->', color=ROUGE, lw=1.2),
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#FEF2F2', edgecolor=ROUGE, alpha=0.95))

# Labels de zone
ax.text(7, -0.8, "PROTECTION TOTALE\n13 ans — IFI = 0 €\ngrâce à la dette",
        ha='center', fontsize=9.5, color=VERT, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#F0FDF4', edgecolor=VERT, alpha=0.85))
ax.text(17, -0.8, "IFI partielle\nans 14 à 20\nmontants faibles",
        ha='center', fontsize=9, color=ROUGE,
        bbox=dict(boxstyle='round', facecolor='#FEF2F2', edgecolor=ROUGE, alpha=0.85))

base_ax(ax,
    "La dette protège de l'IFI pendant 13 ans",
    subtitle="Le Capital Restant Dû (CRD) maintient la base taxable sous le seuil de 1,3M€",
    ylabel="Millions €")
ax.set_ylim(-1.4, 5.8)
ax.legend(fontsize=9, loc='upper right', framealpha=0.95)

plt.tight_layout()
fig1.savefig('visuel_1_crd_vs_ifi.png', dpi=150, bbox_inches='tight')
print("✓ visuel_1_crd_vs_ifi.png")

# ──────────────────────────────────────────────────────────────────────────────
# VISUEL 2 — Accumulation du patrimoine financier
# ──────────────────────────────────────────────────────────────────────────────
fig2, ax = plt.subplots(figsize=(13, 6))
fig2.patch.set_facecolor('white')

cp_fins  = [d['cp_fin']  / 1e6 for d in data]
cumuls   = [d['cumul']   / 1e6 for d in data]
totaux_B = [cp_fins[i] + cumuls[i] for i in range(DUREE_ANS)]

# Scénario A : toujours 0
ax.axhline(0, color=ROUGE, lw=2, linestyle='--', zorder=4, label='Scénario A — Achat CASH\nPatrimoine financier = 0 € (les 5M€ sont dans la maison)')

# Placement 5M
ax.fill_between(ans, 0, cp_fins, alpha=0.10, color=BLEU, zorder=2)
ax.plot(ans, cp_fins, color=BLEU, lw=2, linestyle='-.', marker='o', ms=3.5,
        label='Scénario B — Placement 5M€ capitalisé à 5%', zorder=3)

# Total B
ax.fill_between(ans, cp_fins, totaux_B, alpha=0.18, color=VERT, zorder=2)
ax.plot(ans, totaux_B, color=VERT, lw=2.8, marker='s', ms=4.5,
        label='Scénario B — Total (placement + flux réinvestis)', zorder=3)

# Annotations clés
for an in [5, 10, 15, 20]:
    i = an - 1
    ax.text(an, totaux_B[i] + 0.35, f"{totaux_B[i]:.1f}M€",
            ha='center', fontsize=8.5, fontweight='bold', color=VERT)

ax.annotate(f"An 20\n+{totaux_B[-1]:.1f}M€\nde patrimoine\nfinancier",
    xy=(20, totaux_B[-1]), xytext=(17, totaux_B[-1] - 4),
    fontsize=9.5, fontweight='bold', color=VERT,
    arrowprops=dict(arrowstyle='->', color=VERT, lw=1.3),
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#F0FDF4', edgecolor=VERT, alpha=0.95))

# Delta final
ax.annotate('', xy=(20, totaux_B[-1]), xytext=(20, 0),
    arrowprops=dict(arrowstyle='<->', color=NOIR, lw=1.5))
ax.text(20.25, totaux_B[-1] / 2, f"Δ = {totaux_B[-1]:.1f}M€",
        fontsize=10, fontweight='bold', color=NOIR, va='center')

# Encadré décomposition
ax.text(0.02, 0.97,
    f"Décomposition à 20 ans (scénario B) :\n"
    f"  Placement 5M€ → {data[-1]['cp_fin']/1e6:.1f}M€  (×{data[-1]['cp_fin']/CAPITAL_PLACE:.1f})\n"
    f"  Flux réinvestis capitalisés : {data[-1]['cumul']/1e6:.1f}M€\n"
    f"  Total : {totaux_B[-1]:.1f}M€\n\n"
    f"Coût des intérêts (20 ans) : −{sum(d['int'] for d in data)/1e6:.1f}M€\n"
    f"Avantage net vs cash : +{totaux_B[-1] - sum(d['int'] for d in data)/1e6:.1f}M€",
    transform=ax.transAxes, fontsize=9, va='top',
    bbox=dict(boxstyle='round,pad=0.6', facecolor='#F0F9FF', edgecolor=BLEU, alpha=0.97))

base_ax(ax,
    "Scénario B : le capital de 5M€ reste investi et fructifie",
    subtitle="Scénario A : ce même capital est immobilisé dans la maison — zéro rendement",
    ylabel="Millions €")
ax.legend(fontsize=9, loc='upper left', bbox_to_anchor=(0.02, 0.67), framealpha=0.95)
ax.set_ylim(-1, 26)

plt.tight_layout()
fig2.savefig('visuel_2_patrimoine.png', dpi=150, bbox_inches='tight')
print("✓ visuel_2_patrimoine.png")

# ──────────────────────────────────────────────────────────────────────────────
# VISUEL 3 — Tableau comparatif A vs B vs Delta (style présentation)
# ──────────────────────────────────────────────────────────────────────────────
fig3 = plt.figure(figsize=(16, 10))
fig3.patch.set_facecolor('white')
ax3 = fig3.add_subplot(111)
ax3.axis('off')

# En-têtes de colonnes
col_headers = [
    'AN',
    # Scénario A
    'IFI\npayée (A)',
    'Patrimoine\nfinancier (A)',
    # Scénario B
    'CRD fin\n(capital restant)',
    'Intérêts\npayés',
    'IFI\npayée (B)',
    'Patrimoine\nfinancier (B)',
    # Delta
    'Économie\nIFI',
    'Avantage\ncumulé',
    'Statut IFI (B)',
]

rows_data = []
cumul_interets = 0
for d in data:
    cumul_interets += d['int']
    pat_B = d['cp_fin'] + d['cumul']
    rows_data.append([
        str(d['an']),
        f"{d['ifi_A']/1e3:.1f}k€",
        "0 €",
        f"{d['crd_fin']/1e6:.2f}M€",
        f"{d['int']/1e3:.0f}k€",
        f"{d['ifi_B']/1e3:.1f}k€" if d['ifi_B'] > 0 else "0 €",
        f"{pat_B/1e6:.2f}M€",
        f"{d['eco']/1e3:.1f}k€",
        f"{d['cumul']/1e6:.2f}M€",
        "✓ Protégé" if d['ifi_B'] == 0 else f"⚠ IFI {d['ifi_B']/1e3:.1f}k€",
    ])

# Ligne totaux
tot_ifi_A = sum(d['ifi_A'] for d in data)
tot_ifi_B = sum(d['ifi_B'] for d in data)
tot_int   = sum(d['int']   for d in data)
tot_eco   = tot_ifi_A - tot_ifi_B
pat_B_20  = data[-1]['cp_fin'] + data[-1]['cumul']

rows_data.append([
    'TOTAL',
    f"{tot_ifi_A/1e3:.0f}k€",
    "0 €",
    "—",
    f"{tot_int/1e6:.2f}M€",
    f"{tot_ifi_B/1e3:.0f}k€",
    f"{pat_B_20/1e6:.1f}M€",
    f"{tot_eco/1e3:.0f}k€",
    f"{data[-1]['cumul']/1e6:.1f}M€",
    "20 ans",
])

tbl = ax3.table(
    cellText=rows_data,
    colLabels=col_headers,
    loc='center',
    cellLoc='center'
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(8.5)
tbl.scale(1, 1.38)

# Couleurs de colonne par bloc
BLEU_HEADER  = '#1E3A5F'
ROUGE_HEADER = '#7F1D1D'
VERT_HEADER  = '#14532D'
BLEU_COL     = '#EFF6FF'
ROUGE_COL    = '#FEF2F2'
VERT_COL     = '#F0FDF4'
TOTAL_BG     = '#1E293B'

n_rows = len(rows_data) + 1  # +1 pour header

for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor('#CBD5E1')
    cell.set_linewidth(0.5)

    if r == 0:
        # En-têtes avec code couleur par bloc
        if c == 0:
            cell.set_facecolor(BLEU_HEADER); cell.set_text_props(color='white', fontweight='bold', fontsize=8)
        elif c in [1, 2]:
            cell.set_facecolor(ROUGE_HEADER); cell.set_text_props(color='white', fontweight='bold', fontsize=8)
        elif c in [3, 4, 5, 6]:
            cell.set_facecolor(BLEU_HEADER);  cell.set_text_props(color='white', fontweight='bold', fontsize=8)
        elif c in [7, 8, 9]:
            cell.set_facecolor(VERT_HEADER);  cell.set_text_props(color='white', fontweight='bold', fontsize=8)

    elif r == n_rows - 1:
        # Ligne totaux
        cell.set_facecolor(TOTAL_BG)
        cell.set_text_props(color='white', fontweight='bold', fontsize=9)

    else:
        an_idx = r - 1
        ifi_b_val = data[an_idx]['ifi_B']
        pair = (r % 2 == 0)

        if c == 0:
            cell.set_facecolor('#F1F5F9'); cell.set_text_props(fontweight='bold')
        elif c in [1, 2]:
            cell.set_facecolor('#FEF9F9' if pair else ROUGE_COL)
        elif c in [3, 4, 5, 6]:
            if ifi_b_val > 0:
                cell.set_facecolor('#FEF2F2' if c in [5] else ('#FFF7ED' if pair else '#FFF0E0'))
            else:
                cell.set_facecolor(BLEU_COL if pair else '#E0EEFF')
        elif c in [7, 8, 9]:
            cell.set_facecolor(VERT_COL if pair else '#D1FAE5')

# Bloc de légende sous le tableau
legend_text = (
    "  SCÉNARIO A (rouge) : achat cash — 5M€ immobilisés dans la maison, 0 patrimoine financier, IFI payée tous les ans à 20 690 €\n"
    "  SCÉNARIO B (bleu)  : emprunt 4% / 20 ans — 5M€ investis à 5%, IFI = 0 € pendant 13 ans grâce à la dette (CRD > 2,2M€)\n"
    "  DELTA    (vert)    : Économie IFI + flux réinvestis capitalisés à 5% = avantage cumulé du scénario B sur A\n"
    "  CRD = Capital Restant Dû (encours en capital uniquement, hors intérêts — seul montant déductible IFI selon le Bofip)"
)
fig3.text(0.5, 0.01, legend_text, ha='center', fontsize=8, color=GRIS,
    bbox=dict(boxstyle='round', facecolor='#F8FAFC', edgecolor='#CBD5E1'))

# Titres des blocs
fig3.text(0.245, 0.93, "SCÉNARIO A — ACHAT CASH",
    ha='center', fontsize=10, fontweight='bold', color='#7F1D1D')
fig3.text(0.555, 0.93, "SCÉNARIO B — EMPRUNT 4% / 20 ANS",
    ha='center', fontsize=10, fontweight='bold', color='#1E3A5F')
fig3.text(0.84, 0.93, "AVANTAGE B vs A",
    ha='center', fontsize=10, fontweight='bold', color='#14532D')

fig3.suptitle(
    "Tableau comparatif — Achat cash vs Emprunt amortissable\n"
    f"Résidence principale {VALEUR_MAISON/1e6:.0f}M€  |  Emprunt {MONTANT_EMPRUNT/1e6:.0f}M€ à {TAUX_EMPRUNT*100:.0f}%  |  Placement à {TAUX_PLACEMENT*100:.0f}% composé",
    fontsize=12, fontweight='bold', color=NOIR, y=0.97)

plt.tight_layout(rect=[0, 0.06, 1, 0.92])
fig3.savefig('visuel_3_tableau_comparatif.png', dpi=150, bbox_inches='tight')
print("✓ visuel_3_tableau_comparatif.png")
print("\n3 visuels générés.")
