"""
Graphiques pédagogiques — Étude comparative IFI
À valider avant construction Excel
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ==============================================================================
# PARAMÈTRES MODIFIABLES (variables d'entrée)
# ==============================================================================
VALEUR_MAISON   = 5_000_000
ABATTEMENT_RP   = 0.30
MONTANT_EMPRUNT = 5_000_000
TAUX_EMPRUNT    = 0.04
DUREE_ANS       = 20
TAUX_PLACEMENT  = 0.05
CAPITAL_PLACE   = 5_000_000
IFI_SEUIL       = 1_300_000
IFI_BAREME      = [
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
    if base < IFI_SEUIL:
        return 0.0
    ifi = 0.0
    for (b, h, t) in IFI_BAREME:
        if base <= b: break
        ifi += (min(base, h) - b) * t
    return ifi

def calculer_modele():
    r = TAUX_EMPRUNT / 12
    n = DUREE_ANS * 12
    mens = MONTANT_EMPRUNT * r / (1 - (1 + r)**(-n))
    crd = MONTANT_EMPRUNT
    annees = []
    capital_place = CAPITAL_PLACE
    cumul = 0.0
    for an in range(1, DUREE_ANS + 1):
        crd_d = crd
        int_an = cap_an = 0.0
        for _ in range(12):
            i = crd * r
            c = mens - i
            int_an += i; cap_an += c
            crd = max(0.0, crd - c)
        rdt = capital_place * TAUX_PLACEMENT
        cp_fin = capital_place * (1 + TAUX_PLACEMENT)
        levier = rdt - int_an
        ifi_A = calcul_ifi(BASE_IFI_MAISON)
        base_B = BASE_IFI_MAISON - crd
        ifi_B = calcul_ifi(base_B)
        eco = ifi_A - ifi_B
        flux = levier + eco
        cumul = cumul * (1 + TAUX_PLACEMENT) + flux
        annees.append({
            'an': an, 'crd_fin': crd, 'int': int_an,
            'rdt': rdt, 'levier': levier,
            'ifi_A': ifi_A, 'base_B': base_B, 'ifi_B': ifi_B,
            'eco': eco, 'flux': flux, 'cumul': cumul,
            'cp_debut': capital_place, 'cp_fin': cp_fin,
        })
        capital_place = cp_fin
    return annees, mens

data, mensualite = calculer_modele()
ans = [d['an'] for d in data]

# Couleurs
C_BLEU    = '#2563EB'
C_VERT    = '#16A34A'
C_ROUGE   = '#DC2626'
C_ORANGE  = '#EA580C'
C_VIOLET  = '#7C3AED'
C_GRIS    = '#6B7280'
C_JAUNE   = '#D97706'
C_FOND    = '#F8FAFC'
C_GRILLE  = '#E2E8F0'

def style_ax(ax, title, xlabel='Année', ylabel=''):
    ax.set_facecolor(C_FOND)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=12, color='#1E293B')
    ax.set_xlabel(xlabel, fontsize=10, color=C_GRIS)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, color=C_GRIS)
    ax.grid(axis='y', color=C_GRILLE, linewidth=0.8)
    ax.set_xticks(ans)
    ax.tick_params(colors=C_GRIS, labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for sp in ['left','bottom']:
        ax.spines[sp].set_color(C_GRILLE)

def fmt_m(v):
    """Formate en millions avec 1 décimale."""
    return f"{v/1e6:.1f}M€"

def fmt_k(v):
    return f"{v/1e3:.0f}k€"

# ==============================================================================
# FIGURE 1 — COMPOSITION DU FLUX ANNUEL RÉINVESTI
# ==============================================================================
fig1, ax = plt.subplots(figsize=(14, 6))
fig1.patch.set_facecolor('white')

leviers = [d['levier']/1e3 for d in data]
ecos    = [d['eco']/1e3    for d in data]
flux    = [d['flux']/1e3   for d in data]

bars1 = ax.bar(ans, leviers, color=C_BLEU,   label='Composante 1 — Effet de levier net\n(Rendement 5% − Intérêts 4%)', zorder=3)
bars2 = ax.bar(ans, ecos,    bottom=leviers,  color=C_VERT,  label='Composante 2 — Économie IFI\n(IFI cash − IFI emprunt)', zorder=3)

# Annotation valeur totale sur quelques années clés
for i in [0, 4, 9, 12, 13, 19]:
    ax.text(ans[i], flux[i] + 8, f"{flux[i]:.0f}k",
            ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1E293B')

# Zone IFI déclenchée
ax.axvspan(13.5, 20.5, alpha=0.06, color=C_ROUGE, zorder=1)
ax.text(14.2, max(flux)*0.85, "IFI en scénario B\nse déclenche (an 14)",
        fontsize=8.5, color=C_ROUGE, style='italic')

# Ligne repère 70k€
ax.axhline(70, color=C_JAUNE, linestyle='--', linewidth=1.2, zorder=4)
ax.text(1.2, 73, "~70k€ (estimation initiale an 1)", fontsize=8, color=C_JAUNE)

style_ax(ax,
    "Flux annuel réinvesti = Effet de levier + Économie IFI\n"
    "(ce flux est capitalisé à 5%/an dans l'assurance-vie)",
    ylabel="k€ / an")
ax.legend(loc='upper left', fontsize=9, framealpha=0.9)

# Encadré pédagogique
ax.text(0.98, 0.05,
    "Lecture : chaque barre = ce que la stratégie d'emprunt\n"
    "génère EN PLUS vs achat cash, année par année.\n"
    "→ Bleu = gain financier (placement 5% > prêt 4%)\n"
    "→ Vert = IFI non payée grâce à la dette\n"
    "→ Les deux sont reinvestis à 5% composé",
    transform=ax.transAxes, fontsize=8.5, va='bottom', ha='right',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#EFF6FF', edgecolor=C_BLEU, alpha=0.9))

plt.tight_layout()
fig1.savefig('graphique_1_flux_annuel.png', dpi=150, bbox_inches='tight')
print("✓ graphique_1_flux_annuel.png")

# ==============================================================================
# FIGURE 2 — DÉCLENCHEMENT PROGRESSIF DE L'IFI
# ==============================================================================
fig2, axes = plt.subplots(1, 2, figsize=(14, 6))
fig2.patch.set_facecolor('white')

# ── Gauche : évolution CRD vs seuil de déclenchement ──
ax2 = axes[0]
crds   = [d['crd_fin']/1e6 for d in data]
base_b = [d['base_B']/1e6  for d in data]

ax2.fill_between(ans, crds, alpha=0.15, color=C_BLEU)
ax2.plot(ans, crds, color=C_BLEU, linewidth=2.5, marker='o', ms=5, label='Capital Restant Dû (CRD)')
ax2.fill_between(ans, base_b, alpha=0.12, color=C_VERT)
ax2.plot(ans, base_b, color=C_VERT, linewidth=2.5, marker='s', ms=5, label='Base IFI nette (3,5M − CRD)')

seuil_crd = 2.2
ax2.axhline(seuil_crd, color=C_ROUGE, linestyle='--', linewidth=1.5, zorder=4)
ax2.text(1, seuil_crd + 0.05, "CRD seuil = 2,2M€\n(IFI se déclenche si CRD < 2,2M€)", fontsize=8, color=C_ROUGE)

ax2.axhline(1.3, color=C_ORANGE, linestyle=':', linewidth=1.2)
ax2.text(14.5, 1.35, "Seuil IFI = 1,3M€", fontsize=8, color=C_ORANGE)

# Annotation an 14
ax2.annotate("An 14 :\nCRD = 1,94M€\nBase B = 1,56M€\n→ IFI = 4 344 €",
    xy=(14, base_b[13]), xytext=(16, 0.3),
    fontsize=8, color=C_ROUGE,
    arrowprops=dict(arrowstyle='->', color=C_ROUGE, lw=1.2),
    bbox=dict(boxstyle='round', facecolor='#FEF2F2', edgecolor=C_ROUGE, alpha=0.9))

# Zone protégée
ax2.axvspan(0.5, 13.5, alpha=0.05, color=C_VERT, zorder=1)
ax2.text(7, 0.15, "13 ans sans IFI", ha='center', fontsize=9, color=C_VERT, fontweight='bold')

style_ax(ax2,
    "Déclenchement IFI — Scénario B\n"
    "Base IFI nette = 3 500 000 € − CRD fin d'année",
    ylabel="Millions €")
ax2.legend(fontsize=8.5, loc='upper right')
ax2.set_ylim(-1.8, 5.5)

# ── Droite : montant IFI payé chaque année (A vs B) ──
ax3 = axes[1]
ifi_A_vals = [d['ifi_A']/1e3 for d in data]
ifi_B_vals = [d['ifi_B']/1e3 for d in data]

ax3.fill_between(ans, ifi_A_vals, alpha=0.12, color=C_ROUGE, label='IFI Scénario A (cash)')
ax3.plot(ans, ifi_A_vals, color=C_ROUGE, linewidth=2.5, linestyle='--', label='IFI Scénario A (cash)\n→ 20 690 €/an fixe')

ax3.fill_between(ans, ifi_B_vals, alpha=0.2, color=C_VERT)
ax3.plot(ans, ifi_B_vals, color=C_VERT, linewidth=2.5, marker='o', ms=5, label='IFI Scénario B (emprunt)')

# Annotation zone économie
ax3.annotate('', xy=(13, 20.69), xytext=(13, 0),
    arrowprops=dict(arrowstyle='<->', color=C_VERT, lw=1.5))
ax3.text(13.3, 10, "20 690 €\néconomisés\nchaque année\npendant 13 ans",
         fontsize=8, color=C_VERT)

# Total encadré
total_A = sum(d['ifi_A'] for d in data)
total_B = sum(d['ifi_B'] for d in data)
ax3.text(0.04, 0.92,
    f"Total IFI A (20 ans) : {total_A/1e3:,.0f}k€\n"
    f"Total IFI B (20 ans) : {total_B/1e3:,.0f}k€\n"
    f"Économie nette        : {(total_A-total_B)/1e3:,.0f}k€",
    transform=ax3.transAxes, fontsize=9, va='top',
    bbox=dict(boxstyle='round', facecolor='#F0FDF4', edgecolor=C_VERT, alpha=0.95))

style_ax(ax3, "IFI payée chaque année\nScénario A (cash) vs Scénario B (emprunt)", ylabel="k€")
ax3.legend(fontsize=8.5, loc='center right')

fig2.suptitle("Déclenchement progressif de l'IFI — Pourquoi la dette protège pendant 13 ans",
              fontsize=13, fontweight='bold', color='#1E293B', y=1.01)
plt.tight_layout()
fig2.savefig('graphique_2_ifi_declenchement.png', dpi=150, bbox_inches='tight')
print("✓ graphique_2_ifi_declenchement.png")

# ==============================================================================
# FIGURE 3 — ACCUMULATION DU PATRIMOINE FINANCIER
# ==============================================================================
fig3, ax = plt.subplots(figsize=(14, 7))
fig3.patch.set_facecolor('white')

cp_fins   = [d['cp_fin']/1e6   for d in data]
cumuls    = [d['cumul']/1e6    for d in data]
total_B_w = [cp_fins[i] + cumuls[i] for i in range(DUREE_ANS)]

ax.fill_between(ans, cp_fins, alpha=0.18, color=C_BLEU)
ax.fill_between(ans, cp_fins, total_B_w, alpha=0.18, color=C_VERT)

ax.plot(ans, cp_fins,   color=C_BLEU,  linewidth=2.5, label='Valeur placement 5M€ capitalisé', marker='o', ms=4)
ax.plot(ans, total_B_w, color=C_VIOLET, linewidth=2.5, label='Total patrimoine financier B\n(placement + flux réinvestis)', marker='s', ms=4)

# Scénario A = 0 tout le temps (l'argent est dans la maison)
ax.axhline(0, color=C_ROUGE, linestyle='--', linewidth=1.5, label='Scénario A (cash) — patrimoine financier = 0')

# Annotations clés
for an, label in [(5,5), (10,10), (15,15), (20,20)]:
    i = an - 1
    ax.annotate(f"An {an}\n{fmt_m(data[i]['cp_fin'])}",
        xy=(an, cp_fins[i]),
        xytext=(an - 0.3, cp_fins[i] - 1.5),
        fontsize=7.5, ha='center', color=C_BLEU)

ax.annotate(f"An 20\nTotal : {fmt_m(data[-1]['cp_fin'] + data[-1]['cumul'])}",
    xy=(20, total_B_w[-1]),
    xytext=(17.5, total_B_w[-1] + 0.5),
    fontsize=9, fontweight='bold', color=C_VIOLET,
    arrowprops=dict(arrowstyle='->', color=C_VIOLET, lw=1.2))

# Décomposition finale
ax.text(0.02, 0.96,
    f"Décomposition patrimoine financier à 20 ans (scénario B) :\n"
    f"  • Placement 5M → {fmt_m(data[-1]['cp_fin'])}   (×{data[-1]['cp_fin']/CAPITAL_PLACE:.2f})\n"
    f"  • Flux réinvestis capitalisés : {fmt_m(data[-1]['cumul'])}\n"
    f"  • TOTAL : {fmt_m(data[-1]['cp_fin'] + data[-1]['cumul'])}\n\n"
    f"Scénario A (cash) : 0 € de patrimoine financier\n"
    f"→ Delta : +{fmt_m(data[-1]['cp_fin'] + data[-1]['cumul'])}",
    transform=ax.transAxes, fontsize=9, va='top',
    bbox=dict(boxstyle='round', facecolor='#EFF6FF', edgecolor=C_BLEU, alpha=0.95))

style_ax(ax,
    "Accumulation du patrimoine financier sur 20 ans\n"
    "Scénario B : le capital de 5M€ est préservé et investi plutôt qu'immobilisé dans la maison",
    ylabel="Millions €")
ax.legend(fontsize=9, loc='upper left', bbox_to_anchor=(0.02, 0.72))

plt.tight_layout()
fig3.savefig('graphique_3_patrimoine.png', dpi=150, bbox_inches='tight')
print("✓ graphique_3_patrimoine.png")

# ==============================================================================
# FIGURE 4 — SYNTHÈSE PÉDAGOGIQUE : D'OÙ VIENT L'AVANTAGE ?
# ==============================================================================
fig4, axes4 = plt.subplots(1, 2, figsize=(14, 6))
fig4.patch.set_facecolor('white')

# ── Gauche : Waterfall de l'avantage net ──
ax4 = axes4[0]

gain_place  = (data[-1]['cp_fin'] - CAPITAL_PLACE) / 1e6
gain_cumul  = data[-1]['cumul'] / 1e6
cout_int    = -sum(d['int'] for d in data) / 1e6
eco_ifi     = sum(d['eco'] for d in data) / 1e6
total       = gain_place + gain_cumul + cout_int + eco_ifi

labels   = ['[1] Croissance\nplacement 5M', '[2] Flux\nréinvestis', '[3] Intérêts\npayés', '[4] Économie\nIFI', 'AVANTAGE\nNET TOTAL']
valeurs  = [gain_place, gain_cumul, cout_int, eco_ifi, total]
couleurs = [C_BLEU, C_VERT, C_ROUGE, C_VERT, C_VIOLET]

bases = [0, gain_place, gain_place + gain_cumul, gain_place + gain_cumul + cout_int, 0]
for i, (l, v, b, c) in enumerate(zip(labels, valeurs, bases, couleurs)):
    ax4.bar(i, v, bottom=b, color=c, alpha=0.85, width=0.6, zorder=3)
    sign = '+' if v >= 0 else ''
    ax4.text(i, b + v + (0.1 if v >= 0 else -0.6),
             f"{sign}{v:.1f}M€", ha='center', va='bottom' if v >= 0 else 'top',
             fontsize=10, fontweight='bold', color='#1E293B')

ax4.axhline(0, color='#CBD5E1', linewidth=1)
style_ax(ax4,
    "D'où vient l'avantage net de 15,3M€ ?\nDécomposition des 4 moteurs",
    xlabel='', ylabel='Millions €')
ax4.set_xticks(range(5))
ax4.set_xticklabels(labels, fontsize=9)

# ── Droite : Camembert de répartition des gains ──
ax5 = axes4[1]
positifs = [gain_place, gain_cumul, abs(cout_int), eco_ifi]
plabels  = ['Croissance\nplacement', 'Flux\nréinvestis', 'Coût\nintérêts\n(à déduire)', 'Économie\nIFI']
pcouleurs = [C_BLEU, C_VERT, C_ROUGE, C_JAUNE]

# Pie sur les gains bruts seulement
gains_bruts = [gain_place, gain_cumul, eco_ifi]
glabels = ['Croissance placement\n5M€ → 13,3M€', 'Flux réinvestis\ncapitalisés', 'Économie IFI\n20 ans']
gcouleurs = [C_BLEU, C_VERT, C_JAUNE]

wedges, texts, autotexts = ax5.pie(
    gains_bruts, labels=glabels, colors=gcouleurs,
    autopct='%1.0f%%', startangle=90,
    pctdistance=0.75, labeldistance=1.12,
    wedgeprops=dict(edgecolor='white', linewidth=2))

for at in autotexts:
    at.set_fontsize(10)
    at.set_fontweight('bold')
    at.set_color('white')
for t in texts:
    t.set_fontsize(9)

ax5.set_title(
    "Répartition des gains bruts\n(avant déduction des 2,3M€ d'intérêts)",
    fontsize=12, fontweight='bold', color='#1E293B', pad=15)

total_gains = sum(gains_bruts)
ax5.text(0, -1.55,
    f"Gains bruts = {total_gains:.1f}M€  −  Intérêts = {abs(cout_int):.1f}M€  =  Avantage net {total:.1f}M€",
    ha='center', fontsize=9.5, color='#1E293B',
    bbox=dict(boxstyle='round', facecolor='#F8FAFF', edgecolor=C_VIOLET, alpha=0.95))

fig4.suptitle("Synthèse — Avantage financier de l'emprunt vs achat cash à 20 ans",
              fontsize=14, fontweight='bold', color='#1E293B', y=1.02)
plt.tight_layout()
fig4.savefig('graphique_4_synthese.png', dpi=150, bbox_inches='tight')
print("✓ graphique_4_synthese.png")

# ==============================================================================
# FIGURE 5 — TABLEAU RÉCAPITULATIF VISUEL (style présentation client)
# ==============================================================================
fig5, ax = plt.subplots(figsize=(16, 9))
fig5.patch.set_facecolor('white')
ax.set_facecolor('white')
ax.axis('off')

col_labels = ['An', 'CRD fin\n(capital restant)', 'Intérêts\npayés', 'Placement\n(valeur fin)',
               'Levier net\n(rdt − int.)', 'IFI cash\n(scén. A)', 'IFI\nemprunt (B)', 'Éco. IFI',
               'Flux\nréinvesti', 'Cumul\ncapitalisé']

rows = []
for d in data:
    rows.append([
        str(d['an']),
        f"{d['crd_fin']/1e6:.2f}M€",
        f"{d['int']/1e3:.0f}k€",
        f"{d['cp_fin']/1e6:.2f}M€",
        f"{d['levier']/1e3:.0f}k€",
        f"{d['ifi_A']/1e3:.1f}k€",
        f"{d['ifi_B']/1e3:.1f}k€" if d['ifi_B'] > 0 else "—",
        f"{d['eco']/1e3:.1f}k€",
        f"{d['flux']/1e3:.0f}k€",
        f"{d['cumul']/1e6:.2f}M€",
    ])

tbl = ax.table(
    cellText=rows,
    colLabels=col_labels,
    loc='center',
    cellLoc='center'
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(8.5)
tbl.scale(1, 1.35)

# Mise en forme
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor('#CBD5E1')
    if r == 0:
        cell.set_facecolor('#1E3A5F')
        cell.set_text_props(color='white', fontweight='bold', fontsize=8)
    elif r > 0 and rows[r-1][6] != '—':   # lignes avec IFI déclenchée
        bg = '#FEF2F2' if c == 6 else ('#FFF7ED' if c in [7, 8] else ('#F0F9FF' if r % 2 == 0 else 'white'))
        cell.set_facecolor(bg)
    elif r % 2 == 0:
        cell.set_facecolor('#F0F9FF')
    else:
        cell.set_facecolor('white')

# Légende sous le tableau
ax.text(0.5, 0.02,
    "CRD = Capital Restant Dû (déductible IFI, hors intérêts)  •  "
    "Levier net = Rendement 5% − Intérêts 4%  •  "
    "Flux réinvesti = Levier net + Économie IFI  •  "
    "Cumul = flux capitalisés à 5%\n"
    "⚠ Lignes en rouge (an 14–20) = IFI se déclenche en scénario B car CRD < 2 200 000 €",
    transform=ax.transAxes, ha='center', fontsize=8, color=C_GRIS,
    bbox=dict(boxstyle='round', facecolor='#F8FAFC', edgecolor=C_GRILLE))

ax.set_title("Tableau de bord — Étude comparative IFI sur 20 ans\n"
             f"Résidence principale {VALEUR_MAISON/1e6:.0f}M€ | Emprunt {MONTANT_EMPRUNT/1e6:.0f}M€ à {TAUX_EMPRUNT*100:.0f}% | Placement à {TAUX_PLACEMENT*100:.0f}%",
             fontsize=13, fontweight='bold', color='#1E293B', pad=15)

plt.tight_layout()
fig5.savefig('graphique_5_tableau_client.png', dpi=150, bbox_inches='tight')
print("✓ graphique_5_tableau_client.png")
print("\nTous les graphiques générés.")
