"""
3 visuels pédagogiques — Étude comparative IFI
Logique éditoriale : un message par visuel, zéro bruit.

Hypothèse appréciation immobilière :
  - Revalorisation bien : 2,5%/an (les deux scénarios en bénéficient identiquement)
  - Base IFI : FIXE à 3 500 000 € (valeur d'achat × 70%) — simplification pédagogique
    → on évite de complexifier l'IFI avec des projections de valeur incertaines
  - La revalorisation est intégrée uniquement dans le patrimoine total final
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# ==============================================================================
# PARAMÈTRES (modifiables)
# ==============================================================================
VALEUR_MAISON     = 5_000_000
ABATTEMENT_RP     = 0.30
MONTANT_EMPRUNT   = 5_000_000
TAUX_EMPRUNT      = 0.04
DUREE_ANS         = 20
TAUX_PLACEMENT    = 0.05
CAPITAL_PLACE     = 5_000_000
APPRECIATION_IMMO = 0.025          # revalorisation annuelle du bien (2,5%/an)

# Base IFI : FIXÉE à la valeur d'achat, pas revalorisée (choix pédagogique)
BASE_IFI_FIXE     = VALEUR_MAISON * (1 - ABATTEMENT_RP)   # 3 500 000 €

IFI_SEUIL  = 1_300_000
IFI_BAREME = [
    (800_000,    1_300_000,  0.005),
    (1_300_000,  2_570_000,  0.007),
    (2_570_000,  5_000_000,  0.010),
    (5_000_000,  10_000_000, 0.0125),
    (10_000_000, float('inf'), 0.015),
]

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
    r    = TAUX_EMPRUNT / 12
    n    = DUREE_ANS * 12
    mens = MONTANT_EMPRUNT * r / (1 - (1 + r)**(-n))
    crd  = MONTANT_EMPRUNT
    cp   = CAPITAL_PLACE
    cumul         = 0.0
    valeur_maison = VALEUR_MAISON   # croît à 2,5%/an — identique dans les deux scénarios
    rows = []

    for an in range(1, DUREE_ANS + 1):
        # Valeur du bien revalorisée (pour le patrimoine total, pas pour l'IFI)
        valeur_maison_fin = valeur_maison * (1 + APPRECIATION_IMMO)

        # Amortissement
        crd_d = crd
        int_an = cap_an = 0.0
        for _ in range(12):
            i = crd * r; c = mens - i
            int_an += i; cap_an += c
            crd = max(0.0, crd - c)

        # Placement
        rdt    = cp * TAUX_PLACEMENT
        cp_fin = cp * (1 + TAUX_PLACEMENT)
        levier = rdt - int_an

        # IFI — base FIXE (pas revalorisée : choix pédagogique)
        ifi_A  = calcul_ifi(BASE_IFI_FIXE)
        base_B = BASE_IFI_FIXE - crd
        ifi_B  = calcul_ifi(base_B)

        eco  = ifi_A - ifi_B
        flux = levier + eco
        cumul = cumul * (1 + TAUX_PLACEMENT) + flux

        # Patrimoines totaux (maison revalorisée + financier)
        # Scénario A : maison revalorisée uniquement (pas de financier)
        # Scénario B : maison revalorisée + placement + flux réinvestis
        pat_A_total = valeur_maison_fin                          # seule la maison
        pat_B_total = valeur_maison_fin + cp_fin + cumul         # maison + financier

        rows.append(dict(
            an=an,
            valeur_maison_fin=valeur_maison_fin,
            crd_d=crd_d, crd_fin=crd, int=int_an, cap=cap_an,
            rdt=rdt, cp=cp, cp_fin=cp_fin,
            levier=levier,
            ifi_A=ifi_A, base_B=base_B, ifi_B=ifi_B,
            eco=eco, flux=flux, cumul=cumul,
            pat_A_total=pat_A_total,
            pat_B_total=pat_B_total,
        ))
        cp = cp_fin
        valeur_maison = valeur_maison_fin
    return rows, mens

data, mens = calculer()
ans = [d['an'] for d in data]

# ==============================================================================
# PALETTE
# ==============================================================================
BLEU   = '#1D4ED8'
VERT   = '#15803D'
ROUGE  = '#B91C1C'
ORANGE = '#C2410C'
GRIS   = '#64748B'
FOND   = '#FAFAFA'
GRILLE = '#E2E8F0'
NOIR   = '#0F172A'

def base_ax(ax, title, subtitle='', xlabel='Année', ylabel=''):
    ax.set_facecolor(FOND)
    titre_complet = f"{title}\n{subtitle}" if subtitle else title
    ax.set_title(titre_complet, fontsize=12, fontweight='bold',
                 color=NOIR, pad=10, linespacing=1.6)
    ax.set_xlabel(xlabel, fontsize=9, color=GRIS)
    if ylabel: ax.set_ylabel(ylabel, fontsize=9, color=GRIS)
    ax.grid(axis='y', color=GRILLE, linewidth=0.8, zorder=0)
    ax.set_xticks(ans)
    ax.tick_params(colors=GRIS, labelsize=8.5)
    for sp in ['top', 'right']:
        ax.spines[sp].set_visible(False)
    for sp in ['left', 'bottom']:
        ax.spines[sp].set_color(GRILLE)

# ──────────────────────────────────────────────────────────────────────────────
# VISUEL 1 — CRD vs Base IFI nette : quand la dette cesse de protéger
# ──────────────────────────────────────────────────────────────────────────────
fig1, ax = plt.subplots(figsize=(13, 6.5))
fig1.patch.set_facecolor('white')

crds    = [d['crd_fin'] / 1e6 for d in data]
base_bs = [d['base_B']  / 1e6 for d in data]
seuil   = IFI_SEUIL / 1e6

# Trouver l'année de déclenchement
an_decl = next(d['an'] for d in data if d['ifi_B'] > 0)

# Zones
ax.axvspan(0.5, an_decl - 0.5, alpha=0.07, color=VERT,  zorder=1)
ax.axvspan(an_decl - 0.5, 20.5, alpha=0.07, color=ROUGE, zorder=1)

# Courbes
ax.plot(ans, crds,    color=BLEU,  lw=2.5, marker='o', ms=4,
        label='Capital Restant Dû (CRD)  —  encours en capital dû à la banque')
ax.plot(ans, base_bs, color=VERT,  lw=2.5, marker='s', ms=4,
        label='Base IFI nette  =  3,5M€ − CRD  —  montant taxable par l\'État')

# Seuil IFI
ax.axhline(seuil, color=ROUGE, lw=1.5, linestyle='--', zorder=4)
ax.text(20.4, seuil + 0.08, "Seuil IFI\n1,3M€", fontsize=8.5, color=ROUGE, va='bottom')

# Seuil CRD critique (3,5M − 1,3M = 2,2M)
crd_critique = (BASE_IFI_FIXE - IFI_SEUIL) / 1e6
ax.axhline(crd_critique, color=BLEU, lw=1, linestyle=':', alpha=0.6, zorder=4)
ax.text(0.7, crd_critique + 0.1,
        f"CRD critique = {crd_critique:.1f}M€  →  si CRD descend sous ce seuil, l'IFI se déclenche",
        fontsize=8, color=BLEU, alpha=0.85)

# Annotation déclenchement
d_decl = data[an_decl - 1]
ax.annotate(
    f"An {an_decl} : déclenchement IFI\nCRD = {d_decl['crd_fin']/1e6:.2f}M€\n"
    f"Base B = {d_decl['base_B']/1e6:.2f}M€ > 1,3M€\n→ IFI due : {d_decl['ifi_B']:,.0f} €",
    xy=(an_decl, d_decl['base_B'] / 1e6),
    xytext=(an_decl - 3.5, 2.5),
    fontsize=8.5, color=ROUGE,
    arrowprops=dict(arrowstyle='->', color=ROUGE, lw=1.2),
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#FEF2F2', edgecolor=ROUGE, alpha=0.95))

# Labels zones
ax.text((an_decl - 1) / 2 + 0.5, -0.9,
        f"PROTECTION TOTALE\n{an_decl - 1} ans — IFI = 0 €\ngrâce à la dette",
        ha='center', fontsize=9.5, color=VERT, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#F0FDF4', edgecolor=VERT, alpha=0.85))
ax.text((an_decl + 20) / 2, -0.9,
        f"IFI progressive\nans {an_decl} à 20\n(montants faibles)",
        ha='center', fontsize=9, color=ROUGE,
        bbox=dict(boxstyle='round', facecolor='#FEF2F2', edgecolor=ROUGE, alpha=0.85))

base_ax(ax,
    "La dette neutralise l'IFI pendant 13 ans",
    subtitle="Base IFI = 3 500 000 € (valeur d'achat × 70%)  —  Déduction : Capital Restant Dû (CRD, hors intérêts)",
    ylabel="Millions €")
ax.set_ylim(-1.6, 5.8)
ax.legend(fontsize=9, loc='upper right', framealpha=0.95)

plt.tight_layout()
fig1.savefig('visuel_1_crd_vs_ifi.png', dpi=150, bbox_inches='tight')
print("✓ visuel_1_crd_vs_ifi.png")

# ──────────────────────────────────────────────────────────────────────────────
# VISUEL 2 — Patrimoine total comparé (maison revalorisée + financier)
# ──────────────────────────────────────────────────────────────────────────────
fig2, ax = plt.subplots(figsize=(13, 6.5))
fig2.patch.set_facecolor('white')

# Données
maisons   = [d['valeur_maison_fin'] / 1e6 for d in data]   # commun aux deux scénarios
cp_fins   = [d['cp_fin']  / 1e6 for d in data]
cumuls    = [d['cumul']   / 1e6 for d in data]
fin_B     = [cp_fins[i] + cumuls[i] for i in range(DUREE_ANS)]
total_A   = maisons                                           # pas de financier
total_B   = [maisons[i] + fin_B[i] for i in range(DUREE_ANS)]

# Scénario A : maison seule (en croissance)
ax.fill_between(ans, 0, maisons, alpha=0.12, color=ROUGE, zorder=2)
ax.plot(ans, maisons, color=ROUGE, lw=2.5, linestyle='--', marker='o', ms=4,
        label=f'Scénario A — Maison revalorisée à {APPRECIATION_IMMO*100:.1f}%/an (seul actif)')

# Scénario B : maison + financier
ax.fill_between(ans, maisons, total_B, alpha=0.15, color=VERT, zorder=2)
ax.plot(ans, total_B, color=VERT, lw=2.8, marker='s', ms=4.5,
        label='Scénario B — Maison + Placement 5M€ + Flux réinvestis')

# Annotations milestones
for an in [5, 10, 15, 20]:
    i = an - 1
    ax.text(an, total_B[i] + 0.4, f"{total_B[i]:.1f}M€",
            ha='center', fontsize=8.5, fontweight='bold', color=VERT)
    ax.text(an, maisons[i] - 0.7, f"{maisons[i]:.1f}M€",
            ha='center', fontsize=8, color=ROUGE)

# Flèche delta à 20 ans
ax.annotate('', xy=(20, total_B[-1]), xytext=(20, maisons[-1]),
    arrowprops=dict(arrowstyle='<->', color=NOIR, lw=1.8))
delta_20 = total_B[-1] - maisons[-1]
ax.text(20.3, (total_B[-1] + maisons[-1]) / 2,
        f"Δ financier\n= {delta_20:.1f}M€",
        fontsize=10, fontweight='bold', color=NOIR, va='center')

# Encadré décomposition
val_maison_20 = data[-1]['valeur_maison_fin']
val_place_20  = data[-1]['cp_fin']
cumul_20      = data[-1]['cumul']
tot_int       = sum(d['int'] for d in data)
tot_ifi_A     = sum(d['ifi_A'] for d in data)
tot_ifi_B     = sum(d['ifi_B'] for d in data)

ax.text(0.02, 0.98,
    f"Patrimoine à 20 ans\n"
    f"{'─'*36}\n"
    f"SCÉNARIO A (cash)\n"
    f"  Maison (5M × 1,025²⁰)   : {val_maison_20/1e6:.2f}M€\n"
    f"  Financier                 :    0,00M€\n"
    f"  IFI payée (20 ans)        : −{tot_ifi_A/1e3:.0f}k€\n"
    f"  TOTAL NET                 : {(val_maison_20 - tot_ifi_A)/1e6:.2f}M€\n"
    f"{'─'*36}\n"
    f"SCÉNARIO B (emprunt)\n"
    f"  Maison (idem)             : {val_maison_20/1e6:.2f}M€\n"
    f"  Placement 5M → 20 ans    : {val_place_20/1e6:.2f}M€\n"
    f"  Flux réinvestis capitalisés: {cumul_20/1e6:.2f}M€\n"
    f"  Intérêts payés            : −{tot_int/1e6:.2f}M€\n"
    f"  IFI payée (20 ans)        : −{tot_ifi_B/1e3:.0f}k€\n"
    f"  TOTAL NET                 : {(val_maison_20 + val_place_20 + cumul_20 - tot_int - tot_ifi_B)/1e6:.2f}M€",
    transform=ax.transAxes, fontsize=8.5, va='top',
    fontfamily='monospace',
    bbox=dict(boxstyle='round,pad=0.6', facecolor='white', edgecolor='#CBD5E1', alpha=0.97))

base_ax(ax,
    "Patrimoine total à 20 ans : maison + actifs financiers",
    subtitle=f"La maison se revalorise à {APPRECIATION_IMMO*100:.1f}%/an dans les DEUX scénarios — l'écart vient uniquement du financier",
    ylabel="Millions €")
ax.legend(fontsize=9, loc='upper left', bbox_to_anchor=(0.02, 0.56), framealpha=0.97)
ax.set_ylim(-0.5, total_B[-1] * 1.1)

plt.tight_layout()
fig2.savefig('visuel_2_patrimoine.png', dpi=150, bbox_inches='tight')
print("✓ visuel_2_patrimoine.png")

# ──────────────────────────────────────────────────────────────────────────────
# VISUEL 3 — Tableau comparatif A / B / Delta
# ──────────────────────────────────────────────────────────────────────────────
fig3 = plt.figure(figsize=(17, 10.5))
fig3.patch.set_facecolor('white')
ax3 = fig3.add_subplot(111)
ax3.axis('off')

col_headers = [
    'AN',
    # Scénario A
    'Valeur\nmaison (A)',
    'IFI payée\n(A)',
    'Pat. total\n(A)',
    # Scénario B
    'CRD fin',
    'Intérêts\npayés',
    'IFI payée\n(B)',
    'Financier\n(B)',
    'Pat. total\n(B)',
    # Delta
    'Éco. IFI',
    'Delta\npatrimoine',
    'Statut IFI (B)',
]

rows_data = []
for d in data:
    fin_b     = d['cp_fin'] + d['cumul']
    pat_a_net = d['valeur_maison_fin']      # on affiche brut (IFI payée en charge courante)
    pat_b_net = d['valeur_maison_fin'] + fin_b
    delta_pat = pat_b_net - pat_a_net

    rows_data.append([
        str(d['an']),
        f"{d['valeur_maison_fin']/1e6:.2f}M€",
        f"{d['ifi_A']/1e3:.1f}k€",
        f"{pat_a_net/1e6:.2f}M€",
        f"{d['crd_fin']/1e6:.2f}M€",
        f"{d['int']/1e3:.0f}k€",
        f"{d['ifi_B']/1e3:.1f}k€" if d['ifi_B'] > 0 else "0 €",
        f"{fin_b/1e6:.2f}M€",
        f"{pat_b_net/1e6:.2f}M€",
        f"{d['eco']/1e3:.1f}k€",
        f"+{delta_pat/1e6:.2f}M€",
        "✓ Protégé" if d['ifi_B'] == 0 else f"⚠ {d['ifi_B']/1e3:.1f}k€",
    ])

# Ligne totaux / fin
tot_ifi_A  = sum(d['ifi_A'] for d in data)
tot_ifi_B  = sum(d['ifi_B'] for d in data)
tot_int    = sum(d['int']   for d in data)
tot_eco    = tot_ifi_A - tot_ifi_B
vm20       = data[-1]['valeur_maison_fin']
fin_b20    = data[-1]['cp_fin'] + data[-1]['cumul']

rows_data.append([
    'TOTAL / AN 20',
    f"{vm20/1e6:.2f}M€",
    f"{tot_ifi_A/1e3:.0f}k€",
    f"{vm20/1e6:.2f}M€",
    "remboursé",
    f"{tot_int/1e6:.2f}M€",
    f"{tot_ifi_B/1e3:.0f}k€",
    f"{fin_b20/1e6:.2f}M€",
    f"{(vm20+fin_b20)/1e6:.2f}M€",
    f"{tot_eco/1e3:.0f}k€",
    f"+{fin_b20/1e6:.2f}M€",
    "20 ans",
])

tbl = ax3.table(cellText=rows_data, colLabels=col_headers, loc='center', cellLoc='center')
tbl.auto_set_font_size(False)
tbl.set_fontsize(8.3)
tbl.scale(1, 1.36)

BLEU_H  = '#1E3A5F'
ROUGE_H = '#7F1D1D'
VERT_H  = '#14532D'
TOTAL_BG = '#1E293B'
n_rows = len(rows_data) + 1

for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor('#CBD5E1')
    cell.set_linewidth(0.5)

    if r == 0:
        if c == 0:
            cell.set_facecolor(BLEU_H)
        elif c in [1, 2, 3]:
            cell.set_facecolor(ROUGE_H)
        elif c in [4, 5, 6, 7, 8]:
            cell.set_facecolor(BLEU_H)
        elif c in [9, 10, 11]:
            cell.set_facecolor(VERT_H)
        cell.set_text_props(color='white', fontweight='bold', fontsize=8)

    elif r == n_rows - 1:
        cell.set_facecolor(TOTAL_BG)
        cell.set_text_props(color='white', fontweight='bold', fontsize=9)

    else:
        idx  = r - 1
        ifi_b = data[idx]['ifi_B']
        pair  = (r % 2 == 0)

        if c == 0:
            cell.set_facecolor('#F1F5F9')
            cell.set_text_props(fontweight='bold')
        elif c in [1, 2, 3]:
            cell.set_facecolor('#FEF9F9' if pair else '#FEF2F2')
        elif c in [4, 5, 6, 7, 8]:
            if ifi_b > 0 and c == 6:
                cell.set_facecolor('#FEE2E2')
            elif ifi_b > 0:
                cell.set_facecolor('#FFF7ED' if pair else '#FFEDD5')
            else:
                cell.set_facecolor('#EFF6FF' if pair else '#DBEAFE')
        elif c in [9, 10, 11]:
            cell.set_facecolor('#F0FDF4' if pair else '#DCFCE7')

# Titres de blocs au-dessus du tableau
fig3.text(0.215, 0.925, "SCÉNARIO A — ACHAT CASH",
          ha='center', fontsize=10, fontweight='bold', color='#7F1D1D')
fig3.text(0.545, 0.925, "SCÉNARIO B — EMPRUNT 4% / 20 ANS",
          ha='center', fontsize=10, fontweight='bold', color='#1E3A5F')
fig3.text(0.865, 0.925, "AVANTAGE B vs A",
          ha='center', fontsize=10, fontweight='bold', color='#14532D')

legend = (
    "  Valeur maison : 5 000 000 € × (1,025)ⁿ — identique dans les deux scénarios  •  "
    "IFI calculée sur base FIXE 3 500 000 € (valeur d'achat × 70%)  •  "
    "CRD = capital restant (hors intérêts, déductible IFI selon Bofip)\n"
    "  Financier (B) = Placement 5M capitalisé à 5% + flux réinvestis  •  "
    "Delta patrimoine = Patrimoine total B − Patrimoine total A  •  "
    "⚠ Lignes an 14–20 : IFI scénario B se déclenche progressivement"
)
fig3.text(0.5, 0.01, legend, ha='center', fontsize=7.8, color=GRIS,
    bbox=dict(boxstyle='round', facecolor='#F8FAFC', edgecolor='#CBD5E1'))

fig3.suptitle(
    "Tableau comparatif — Achat cash vs Emprunt amortissable  |  "
    f"Maison {VALEUR_MAISON/1e6:.0f}M€ revalorisée à {APPRECIATION_IMMO*100:.1f}%/an  |  "
    f"Emprunt {TAUX_EMPRUNT*100:.0f}%  |  Placement {TAUX_PLACEMENT*100:.0f}% composé",
    fontsize=11, fontweight='bold', color=NOIR, y=0.97)

plt.tight_layout(rect=[0, 0.055, 1, 0.92])
fig3.savefig('visuel_3_tableau_comparatif.png', dpi=150, bbox_inches='tight')
print("✓ visuel_3_tableau_comparatif.png")
print("\n3 visuels générés.")
