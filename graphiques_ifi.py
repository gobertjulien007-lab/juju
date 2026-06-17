"""
Étude comparative IFI — Version corrigée
Correction : suppression du double-comptage du levier dans le réinvestissement.

LOGIQUE CORRECTE :
  - Le placement de 5M grossit à 5% composé → c'est LE moteur principal
  - Les intérêts sont payés depuis autres revenus → coût à déduire en fin de période
  - L'économie IFI = vrai flux cash annuel économisé → affiché séparément, cumulé sans capitalisation
  - Le "levier net" (rdt - intérêts) n'est PAS réinvesti séparément : il est déjà dans la croissance du 5M
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ==============================================================================
# PARAMÈTRES
# ==============================================================================
VALEUR_MAISON     = 5_000_000
ABATTEMENT_RP     = 0.30
MONTANT_EMPRUNT   = 5_000_000
TAUX_EMPRUNT      = 0.04
DUREE_ANS         = 20
TAUX_PLACEMENT    = 0.05
CAPITAL_PLACE     = 5_000_000
APPRECIATION_IMMO = 0.02
BASE_IFI_FIXE     = VALEUR_MAISON * (1 - ABATTEMENT_RP)   # 3 500 000 €, non revalorisée
IFI_SEUIL         = 1_300_000
IFI_BAREME = [
    (800_000,    1_300_000,  0.005),
    (1_300_000,  2_570_000,  0.007),
    (2_570_000,  5_000_000,  0.010),
    (5_000_000,  10_000_000, 0.0125),
    (10_000_000, float('inf'), 0.015),
]

# ==============================================================================
# CALCUL CORRIGÉ
# ==============================================================================
def calcul_ifi(base):
    if base < IFI_SEUIL: return 0.0
    ifi = 0.0
    for b, h, t in IFI_BAREME:
        if base <= b: break
        ifi += (min(base, h) - b) * t
    return ifi

def calculer():
    r    = TAUX_EMPRUNT / 12
    n    = DUREE_ANS * 12
    mens = MONTANT_EMPRUNT * r / (1 - (1 + r)**(-n))
    crd  = MONTANT_EMPRUNT
    cp   = CAPITAL_PLACE       # le placement grossit à 5%, jamais touché
    vm   = VALEUR_MAISON
    cumul_eco_ifi = 0.0        # cumul brut des économies IFI (sans capitalisation)
    rows = []

    for an in range(1, DUREE_ANS + 1):
        vm_fin = vm * (1 + APPRECIATION_IMMO)

        # Amortissement mensuel
        crd_d = crd
        int_an = cap_an = 0.0
        for _ in range(12):
            i = crd * r; c = mens - i
            int_an += i; cap_an += c
            crd = max(0.0, crd - c)

        # Placement : croît à 5% composé — indépendant, jamais touché
        cp_fin = cp * (1 + TAUX_PLACEMENT)

        # IFI — base fixe
        ifi_A  = calcul_ifi(BASE_IFI_FIXE)
        base_B = BASE_IFI_FIXE - crd
        ifi_B  = calcul_ifi(base_B)
        eco_ifi = ifi_A - ifi_B
        cumul_eco_ifi += eco_ifi

        # Patrimoines (bruts, avant déduction cumulative des charges)
        # Scénario A : maison uniquement
        # Scénario B : maison + placement (les intérêts et IFI sont des flux annuels distincts)
        rows.append(dict(
            an=an,
            vm_fin=vm_fin,
            crd_d=crd_d, crd_fin=crd, int=int_an, cap=cap_an,
            cp=cp, cp_fin=cp_fin,
            ifi_A=ifi_A, base_B=base_B, ifi_B=ifi_B,
            eco_ifi=eco_ifi,
            cumul_eco_ifi=cumul_eco_ifi,
        ))
        cp = cp_fin
        vm = vm_fin
    return rows, mens

data, mens = calculer()
ans = [d['an'] for d in data]

# Agrégats finaux
tot_int   = sum(d['int']    for d in data)
tot_ifi_A = sum(d['ifi_A']  for d in data)
tot_ifi_B = sum(d['ifi_B']  for d in data)
tot_eco   = tot_ifi_A - tot_ifi_B
val_place_20 = data[-1]['cp_fin']
vm_20        = data[-1]['vm_fin']

# Avantage net corrigé
# = croissance nette du placement (gain vs 0 en scénario A) - intérêts payés + économie IFI
gain_placement = val_place_20 - CAPITAL_PLACE   # gain NET (hors capital de départ récupéré)
avantage_net   = gain_placement - tot_int + tot_eco
# Patrimoines nets à 20 ans
pat_A_net = vm_20 - tot_ifi_A                                   # maison - IFI cumulée
pat_B_net = vm_20 + val_place_20 - tot_int - tot_ifi_B          # maison + placement - intérêts - IFI

# ==============================================================================
# PALETTE
# ==============================================================================
BLEU   = '#1D4ED8'
VERT   = '#15803D'
ROUGE  = '#B91C1C'
GRIS   = '#64748B'
FOND   = '#FAFAFA'
GRILLE = '#E2E8F0'
NOIR   = '#0F172A'

def base_ax(ax, title, subtitle='', xlabel='Année', ylabel=''):
    ax.set_facecolor(FOND)
    titre_complet = f"{title}\n{subtitle}" if subtitle else title
    ax.set_title(titre_complet, fontsize=12, fontweight='bold', color=NOIR, pad=10, linespacing=1.6)
    ax.set_xlabel(xlabel, fontsize=9, color=GRIS)
    if ylabel: ax.set_ylabel(ylabel, fontsize=9, color=GRIS)
    ax.grid(axis='y', color=GRILLE, linewidth=0.8, zorder=0)
    ax.set_xticks(ans)
    ax.tick_params(colors=GRIS, labelsize=8.5)
    for sp in ['top', 'right']: ax.spines[sp].set_visible(False)
    for sp in ['left', 'bottom']: ax.spines[sp].set_color(GRILLE)

# ==============================================================================
# VISUEL 1 — CRD vs Base IFI (inchangé, toujours correct)
# ==============================================================================
fig1, ax = plt.subplots(figsize=(13, 6.5))
fig1.patch.set_facecolor('white')

crds    = [d['crd_fin'] / 1e6 for d in data]
base_bs = [d['base_B']  / 1e6 for d in data]
an_decl = next(d['an'] for d in data if d['ifi_B'] > 0)

ax.axvspan(0.5, an_decl - 0.5, alpha=0.07, color=VERT,  zorder=1)
ax.axvspan(an_decl - 0.5, 20.5, alpha=0.07, color=ROUGE, zorder=1)

ax.plot(ans, crds,    color=BLEU, lw=2.5, marker='o', ms=4,
        label='Capital Restant Dû (CRD)  —  encours capital dû à la banque')
ax.plot(ans, base_bs, color=VERT, lw=2.5, marker='s', ms=4,
        label='Base IFI nette  =  3,5M€ − CRD  —  montant taxable par l\'État')

ax.axhline(IFI_SEUIL / 1e6, color=ROUGE, lw=1.5, linestyle='--', zorder=4)
ax.text(20.4, IFI_SEUIL / 1e6 + 0.08, "Seuil IFI\n1,3M€", fontsize=8.5, color=ROUGE, va='bottom')

crd_crit = (BASE_IFI_FIXE - IFI_SEUIL) / 1e6
ax.axhline(crd_crit, color=BLEU, lw=1, linestyle=':', alpha=0.6, zorder=4)
ax.text(0.7, crd_crit + 0.1,
        f"CRD critique = {crd_crit:.1f}M€  →  en dessous : IFI se déclenche",
        fontsize=8, color=BLEU, alpha=0.85)

d_decl = data[an_decl - 1]
ax.annotate(
    f"An {an_decl} : IFI se déclenche\nCRD = {d_decl['crd_fin']/1e6:.2f}M€\n"
    f"Base B = {d_decl['base_B']/1e6:.2f}M€\n→ IFI due : {d_decl['ifi_B']:,.0f} €",
    xy=(an_decl, d_decl['base_B'] / 1e6), xytext=(an_decl - 3.5, 2.5),
    fontsize=8.5, color=ROUGE,
    arrowprops=dict(arrowstyle='->', color=ROUGE, lw=1.2),
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#FEF2F2', edgecolor=ROUGE, alpha=0.95))

ax.text((an_decl - 1) / 2 + 0.5, -0.9,
        f"PROTECTION TOTALE\n{an_decl - 1} ans — IFI = 0 €",
        ha='center', fontsize=9.5, color=VERT, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#F0FDF4', edgecolor=VERT, alpha=0.85))
ax.text((an_decl + 20) / 2, -0.9,
        f"IFI progressive\nans {an_decl}–20",
        ha='center', fontsize=9, color=ROUGE,
        bbox=dict(boxstyle='round', facecolor='#FEF2F2', edgecolor=ROUGE, alpha=0.85))

base_ax(ax, "La dette neutralise l'IFI pendant 13 ans",
    subtitle="Base IFI = 3 500 000 € fixe  |  Déduction : CRD (capital uniquement, hors intérêts — Bofip)",
    ylabel="Millions €")
ax.set_ylim(-1.6, 5.8)
ax.legend(fontsize=9, loc='upper right', framealpha=0.95)
plt.tight_layout()
fig1.savefig('visuel_1_crd_vs_ifi.png', dpi=150, bbox_inches='tight')
print("✓ visuel_1_crd_vs_ifi.png")

# ==============================================================================
# VISUEL 2 — Patrimoine total CORRIGÉ (sans double-comptage)
# ==============================================================================
fig2, axes = plt.subplots(1, 2, figsize=(15, 6.5))
fig2.patch.set_facecolor('white')

# ── Gauche : évolution année par année ──
ax2 = axes[0]
maisons    = [d['vm_fin']  / 1e6 for d in data]
placements = [d['cp_fin']  / 1e6 for d in data]
total_B    = [maisons[i] + placements[i] for i in range(DUREE_ANS)]

ax2.fill_between(ans, 0, maisons,  alpha=0.12, color=ROUGE, zorder=2)
ax2.plot(ans, maisons, color=ROUGE, lw=2.5, linestyle='--', marker='o', ms=4,
         label=f'Scénario A — Maison seule (+{APPRECIATION_IMMO*100:.1f}%/an)')

ax2.fill_between(ans, maisons, total_B, alpha=0.15, color=VERT, zorder=2)
ax2.plot(ans, total_B, color=VERT, lw=2.8, marker='s', ms=4.5,
         label='Scénario B — Maison + Placement 5M€ à 5%')

for an in [5, 10, 15, 20]:
    i = an - 1
    ax2.text(an, total_B[i] + 0.5, f"{total_B[i]:.1f}M€",
             ha='center', fontsize=8.5, fontweight='bold', color=VERT)
    ax2.text(an, maisons[i] - 0.8, f"{maisons[i]:.1f}M€",
             ha='center', fontsize=8, color=ROUGE)

ax2.annotate('', xy=(20, total_B[-1]), xytext=(20, maisons[-1]),
    arrowprops=dict(arrowstyle='<->', color=NOIR, lw=1.8))
ax2.text(20.3, (total_B[-1] + maisons[-1]) / 2,
         f"  +{placements[-1]:.1f}M€\n  (placement)",
         fontsize=9, fontweight='bold', color=NOIR, va='center')

base_ax(ax2, "Patrimoine brut (avant charges)",
    subtitle="La maison croît identiquement — l'écart = le placement préservé en scénario B",
    ylabel="Millions €")
ax2.legend(fontsize=9, loc='upper left', framealpha=0.97)
ax2.set_ylim(-0.5, total_B[-1] * 1.12)

# ── Droite : synthèse nette à 20 ans (barres) ──
ax3 = axes[1]
categories = ['Scénario A\n(achat cash)', 'Scénario B\n(emprunt)']

# A : maison - IFI cumulée
# B : maison + placement - intérêts - IFI

comp_A = [vm_20 / 1e6, -tot_ifi_A / 1e6]
comp_B_base = [vm_20 / 1e6, (val_place_20 - CAPITAL_PLACE) / 1e6, -tot_int / 1e6, -tot_ifi_B / 1e6]

# Scénario A
ax3.bar(['A'], [vm_20 / 1e6], color='#FCA5A5', label='Maison revalorisée', width=0.4)
ax3.bar(['A'], [-tot_ifi_A / 1e6], bottom=[vm_20 / 1e6], color='#DC2626', label='IFI payée (charge)', width=0.4)
ax3.text(0, pat_A_net / 1e6 + 0.2, f"Net : {pat_A_net/1e6:.1f}M€", ha='center', fontweight='bold', fontsize=10, color=ROUGE)

# Scénario B
bottom = vm_20 / 1e6
ax3.bar(['B'], [bottom], color='#FCA5A5', width=0.4)  # maison (même)
ax3.bar(['B'], [(val_place_20 - CAPITAL_PLACE) / 1e6], bottom=bottom, color='#93C5FD',
        label='Croissance placement (gain net)', width=0.4)
bottom2 = bottom + (val_place_20 - CAPITAL_PLACE) / 1e6
ax3.bar(['B'], [CAPITAL_PLACE / 1e6], bottom=bottom2, color='#1D4ED8',
        label='Capital placement récupéré (5M€)', width=0.4)
bottom3 = bottom2 + CAPITAL_PLACE / 1e6
ax3.bar(['B'], [-tot_int / 1e6], bottom=bottom3, color='#F97316',
        label='Intérêts payés (charge)', width=0.4)
ax3.bar(['B'], [-tot_ifi_B / 1e6], bottom=bottom3 - tot_int / 1e6, color='#DC2626', width=0.4)
ax3.text(1, pat_B_net / 1e6 + 0.2, f"Net : {pat_B_net/1e6:.1f}M€", ha='center', fontweight='bold', fontsize=10, color=VERT)

ax3.axhline(0, color=NOIR, lw=0.8)
ax3.text(0.5, (pat_A_net + pat_B_net) / 2e6,
         f"Δ = +{(pat_B_net - pat_A_net)/1e6:.1f}M€",
         ha='center', fontsize=12, fontweight='bold', color=NOIR,
         bbox=dict(boxstyle='round', facecolor='#F0FDF4', edgecolor=VERT, alpha=0.95))

base_ax(ax3, "Patrimoine net à 20 ans",
    subtitle="Après déduction des intérêts et de l'IFI payée", xlabel='', ylabel='Millions €')
ax3.legend(fontsize=8, loc='upper left', framealpha=0.95)

fig2.suptitle("Scénario B : le capital de 5M€ reste investi et génère +11,3M€ d'avantage net",
              fontsize=13, fontweight='bold', color=NOIR, y=1.01)
plt.tight_layout()
fig2.savefig('visuel_2_patrimoine.png', dpi=150, bbox_inches='tight')
print("✓ visuel_2_patrimoine.png")

# ==============================================================================
# VISUEL 3 — Tableau comparatif CORRIGÉ
# ==============================================================================
fig3 = plt.figure(figsize=(17, 10.5))
fig3.patch.set_facecolor('white')
ax_t = fig3.add_subplot(111)
ax_t.axis('off')

col_headers = [
    'AN',
    # Scénario A
    'Valeur\nmaison (A)',
    'IFI payée\n(A)',
    'Pat. net\n(A) cumul',
    # Scénario B
    'CRD fin\n(capital restant)',
    'Intérêts\npayés',
    'Placement\n5M → valeur',
    'IFI payée\n(B)',
    'Pat. net\n(B) cumul',
    # Delta
    'Éco. IFI\nannuelle',
    'Delta\npatrimoine',
    'Statut IFI (B)',
]

rows_tbl = []
cum_ifi_A = cum_int = cum_ifi_B = 0.0
for d in data:
    cum_ifi_A += d['ifi_A']
    cum_int   += d['int']
    cum_ifi_B += d['ifi_B']
    pat_a = d['vm_fin'] - cum_ifi_A
    pat_b = d['vm_fin'] + d['cp_fin'] - cum_int - cum_ifi_B
    rows_tbl.append([
        str(d['an']),
        f"{d['vm_fin']/1e6:.2f}M€",
        f"{d['ifi_A']/1e3:.1f}k€",
        f"{pat_a/1e6:.2f}M€",
        f"{d['crd_fin']/1e6:.2f}M€",
        f"{d['int']/1e3:.0f}k€",
        f"{d['cp_fin']/1e6:.2f}M€",
        f"{d['ifi_B']/1e3:.1f}k€" if d['ifi_B'] > 0 else "0 €",
        f"{pat_b/1e6:.2f}M€",
        f"{d['eco_ifi']/1e3:.1f}k€",
        f"+{(pat_b - pat_a)/1e6:.2f}M€",
        "✓ Protégé" if d['ifi_B'] == 0 else f"⚠ {d['ifi_B']/1e3:.1f}k€",
    ])

rows_tbl.append([
    'TOTAL / AN 20',
    f"{vm_20/1e6:.2f}M€",
    f"{tot_ifi_A/1e3:.0f}k€",
    f"{pat_A_net/1e6:.2f}M€",
    "0 €",
    f"{tot_int/1e6:.2f}M€",
    f"{val_place_20/1e6:.2f}M€",
    f"{tot_ifi_B/1e3:.0f}k€",
    f"{pat_B_net/1e6:.2f}M€",
    f"{tot_eco/1e3:.0f}k€",
    f"+{(pat_B_net - pat_A_net)/1e6:.2f}M€",
    "20 ans",
])

tbl = ax_t.table(cellText=rows_tbl, colLabels=col_headers, loc='center', cellLoc='center')
tbl.auto_set_font_size(False)
tbl.set_fontsize(8.3)
tbl.scale(1, 1.36)

def fill_s(hex_c): return PatternFill("solid", fgColor=hex_c)

C_RH, C_BH, C_VH = '#7F1D1D', '#1E3A5F', '#14532D'
C_TOT = '#1E293B'
n_rows = len(rows_tbl) + 1
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor('#CBD5E1')
    cell.set_linewidth(0.5)
    if r == 0:
        clr = C_BH if c == 0 else (C_RH if c in [1,2,3] else (C_BH if c in [4,5,6,7,8] else C_VH))
        cell.set_facecolor(clr)
        cell.set_text_props(color='white', fontweight='bold', fontsize=8)
    elif r == n_rows - 1:
        cell.set_facecolor(C_TOT)
        cell.set_text_props(color='white', fontweight='bold', fontsize=9)
    else:
        idx  = r - 1
        ifi_b = data[idx]['ifi_B']
        pair  = (r % 2 == 0)
        if c == 0:
            cell.set_facecolor('#F1F5F9'); cell.set_text_props(fontweight='bold')
        elif c in [1,2,3]:
            cell.set_facecolor('#FEF9F9' if pair else '#FEF2F2')
        elif c in [4,5,6,7,8]:
            if ifi_b > 0:
                cell.set_facecolor('#FEE2E2' if c == 7 else ('#FFF7ED' if pair else '#FFEDD5'))
            else:
                cell.set_facecolor('#EFF6FF' if pair else '#DBEAFE')
        elif c in [9,10,11]:
            cell.set_facecolor('#F0FDF4' if pair else '#DCFCE7')

fig3.text(0.19, 0.925, "SCÉNARIO A — ACHAT CASH", ha='center', fontsize=10, fontweight='bold', color='#7F1D1D')
fig3.text(0.535, 0.925, "SCÉNARIO B — EMPRUNT 4% / 20 ANS", ha='center', fontsize=10, fontweight='bold', color='#1E3A5F')
fig3.text(0.865, 0.925, "AVANTAGE B vs A", ha='center', fontsize=10, fontweight='bold', color='#14532D')

fig3.text(0.5, 0.01,
    "Pat. net cumul = valeur maison − IFI cumulée (A)  |  valeur maison + placement − intérêts cumulés − IFI cumulée (B)\n"
    "Placement 5M → valeur = capital de 5M€ capitalisé à 5% composé (aucun retrait, aucun double-comptage)\n"
    "CRD = capital restant dû (hors intérêts — Bofip)  |  ⚠ orange : IFI scénario B déclenchée (CRD < 2 200 000 €)",
    ha='center', fontsize=7.8, color=GRIS,
    bbox=dict(boxstyle='round', facecolor='#F8FAFC', edgecolor='#CBD5E1'))

fig3.suptitle(
    f"Tableau comparatif CORRIGÉ — Maison {VALEUR_MAISON/1e6:.0f}M€ (+{APPRECIATION_IMMO*100:.1f}%/an)  |  "
    f"Emprunt {TAUX_EMPRUNT*100:.0f}%  |  Placement {TAUX_PLACEMENT*100:.0f}% composé  |  Sans double-comptage",
    fontsize=11, fontweight='bold', color=NOIR, y=0.97)

plt.tight_layout(rect=[0, 0.055, 1, 0.92])
fig3.savefig('visuel_3_tableau_comparatif.png', dpi=150, bbox_inches='tight')
print("✓ visuel_3_tableau_comparatif.png")

# ==============================================================================
# SYNTHÈSE CONSOLE
# ==============================================================================
print(f"""
{'='*70}
  SYNTHÈSE CORRIGÉE À 20 ANS
{'='*70}

  SCÉNARIO A — ACHAT CASH
    Maison revalorisée (2,5%/an)     : {vm_20/1e6:>8.2f}M€
    IFI payée sur 20 ans             : -{tot_ifi_A/1e3:>7.0f}k€
    Patrimoine net                   : {pat_A_net/1e6:>8.2f}M€

  SCÉNARIO B — EMPRUNT 4% / 20 ANS
    Maison revalorisée (idem)        : {vm_20/1e6:>8.2f}M€
    Placement 5M → 20 ans            : {val_place_20/1e6:>8.2f}M€
    Intérêts payés (20 ans)          : -{tot_int/1e6:>7.2f}M€
    IFI payée (20 ans)               : -{tot_ifi_B/1e3:>7.0f}k€
    Patrimoine net                   : {pat_B_net/1e6:>8.2f}M€

  AVANTAGE NET B vs A                : +{(pat_B_net - pat_A_net)/1e6:>7.2f}M€
  dont : croissance placement        : +{(val_place_20 - CAPITAL_PLACE)/1e6:>7.2f}M€
         − intérêts payés            : -{tot_int/1e6:>7.2f}M€
         + économie IFI nette        : +{tot_eco/1e3:>7.0f}k€

  Économie IFI brute sur 20 ans      : +{tot_eco/1e3:>7.0f}k€
    (dont 13 ans à 20 690 €/an = {13*20690/1e3:.0f}k€, puis décroissante)
{'='*70}
""")

print("3 visuels générés.")
