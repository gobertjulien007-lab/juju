"""
Génère graphique_ifi.xlsx — graphique IFI modifiable dans Excel
Onglet données + graphique natif Excel (titres/annotations éditables)
"""

import openpyxl
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.series import SeriesLabel
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils import get_column_letter

# ── Paramètres (reproduits pour autonomie du script)
MONTANT_EMPRUNT = 5_000_000
TAUX_EMPRUNT    = 0.04
DUREE_ANS       = 20
BASE_IFI_FIXE   = 3_500_000
IFI_SEUIL       = 1_300_000
IFI_BAREME = [
    (800_000,    1_300_000,  0.005),
    (1_300_000,  2_570_000,  0.007),
    (2_570_000,  5_000_000,  0.010),
    (5_000_000,  10_000_000, 0.0125),
    (10_000_000, float('inf'), 0.015),
]

def calcul_ifi(base):
    if base < IFI_SEUIL: return 0.0
    ifi = 0.0
    for b, h, t in IFI_BAREME:
        if base <= b: break
        ifi += (min(base, h) - b) * t
    return ifi

# ── Calcul amortissement mensuel
r    = TAUX_EMPRUNT / 12
n    = DUREE_ANS * 12
mens = MONTANT_EMPRUNT * r / (1 - (1 + r)**(-n))
crd  = MONTANT_EMPRUNT

rows = []
for an in range(1, DUREE_ANS + 1):
    for _ in range(12):
        i = crd * r
        crd = max(0.0, crd - (mens - i))
    base_B = BASE_IFI_FIXE - crd
    ifi_B  = calcul_ifi(base_B)
    rows.append(dict(
        an=an,
        crd=round(crd),
        base_B=round(base_B),
        seuil=IFI_SEUIL,
        crd_crit=BASE_IFI_FIXE - IFI_SEUIL,   # 2 200 000
        ifi_B=round(ifi_B),
    ))

# ── Trouver années clés
an_decl  = next(d['an'] for d in rows if d['ifi_B'] > 0)
an_crois = next(
    (rows[i+1]['an'] for i in range(len(rows)-1)
     if rows[i]['crd'] >= rows[i]['base_B'] and rows[i+1]['crd'] < rows[i+1]['base_B']),
    None
)

# ==============================================================================
# WORKBOOK
# ==============================================================================
wb = openpyxl.Workbook()

# ── Styles helpers
def fill(h):  return PatternFill("solid", fgColor=h.lstrip('#'))
def fnt(bold=False, color='000000', size=10):
    return Font(bold=bold, color=color.lstrip('#'), size=size)
def aln(h='center'):
    return Alignment(horizontal=h, vertical='center')
def brd():
    s = Side(style='thin', color='CBD5E1')
    return Border(left=s, right=s, top=s, bottom=s)

# ==============================================================================
# ONGLET 1 — DONNÉES (source du graphique)
# ==============================================================================
ws = wb.active
ws.title = "Données graphique"
ws.sheet_view.showGridLines = False

# En-têtes
headers = [
    ("Année",              "A"), ("CRD (M€)",            "B"),
    ("Base IFI nette (M€)","C"), ("Seuil IFI 1,3M€",    "D"),
    ("CRD critique 2,2M€", "E"), ("IFI due (€)",         "F"),
]
colors_h = ['#334155','#1E3A5F','#14532D','#7F1D1D','#1E3A5F','#7C3AED']
for col, ((h, _), bg) in enumerate(zip(headers, colors_h), 1):
    c = ws.cell(row=2, column=col, value=h)
    c.fill = fill(bg); c.font = fnt(bold=True, color='#FFFFFF', size=9)
    c.alignment = aln(); c.border = brd()
    ws.column_dimensions[get_column_letter(col)].width = 20

ws.row_dimensions[2].height = 24

# Titre
ws.merge_cells("A1:F1")
c = ws.cell(row=1, column=1, value="Données — Protection IFI par la dette (capital restant dû, Bofip)")
c.font = fnt(bold=True, size=12, color='#0F172A')
c.alignment = aln()
c.fill = fill('#F1F5F9')
ws.row_dimensions[1].height = 28

# Données
pair_bg  = '#EFF6FF'
impair_bg = '#F8FAFC'
EUR_FMT  = '#,##0'
MIL_FMT  = '#,##0.00'

for i, d in enumerate(rows):
    row = i + 3
    bg  = pair_bg if i % 2 == 0 else impair_bg
    # Marquer années clés
    if d['an'] == an_decl:   bg = '#FEF2F2'
    if an_crois and d['an'] == an_crois: bg = '#F5F3FF'

    vals = [
        d['an'],
        round(d['crd'] / 1e6, 3),
        round(d['base_B'] / 1e6, 3),
        round(IFI_SEUIL / 1e6, 3),
        round((BASE_IFI_FIXE - IFI_SEUIL) / 1e6, 3),
        d['ifi_B'],
    ]
    fmts = [None, MIL_FMT, MIL_FMT, MIL_FMT, MIL_FMT, EUR_FMT]
    for col, (v, fmt) in enumerate(zip(vals, fmts), 1):
        c = ws.cell(row=row, column=col, value=v)
        c.fill = fill(bg); c.border = brd()
        c.font = fnt(size=9)
        c.alignment = aln()
        if fmt: c.number_format = fmt
    ws.row_dimensions[row].height = 16

# ── Légende des années clés
leg_row = DUREE_ANS + 4
ws.merge_cells(f"A{leg_row}:F{leg_row}")
c = ws.cell(row=leg_row, column=1,
    value=f"🔴 An {an_decl} = déclenchement IFI (CRD passe sous 2,2M€)   |   "
          f"🟣 An {an_crois} = croisement CRD / Base IFI (CRD = Base = 1,75M€)   |   "
          f"Ces deux événements sont distincts")
c.font = fnt(size=9, color='#334155')
c.alignment = aln('left')
c.fill = fill('#F8FAFC')
ws.row_dimensions[leg_row].height = 20

# ==============================================================================
# GRAPHIQUE EXCEL NATIF
# ==============================================================================
chart = LineChart()
chart.title       = "Protection IFI par la dette : deux événements à distinguer"
chart.style       = 10
chart.y_axis.title = "Millions €"
chart.x_axis.title = "Année"
chart.height      = 14
chart.width       = 26
chart.y_axis.numFmt = '0.00'
chart.y_axis.scaling.min = -2.0
chart.y_axis.scaling.max = 5.5

data_rows = DUREE_ANS   # 20 lignes
start_row = 3
end_row   = start_row + data_rows - 1

def add_series(chart, ws, col, label, color_hex, width=28000, dash=None, marker_sym=None):
    from openpyxl.chart.series import Series, SeriesLabel
    from openpyxl.chart.data_source import NumDataSource, NumRef
    ref = Reference(ws, min_col=col, min_row=start_row, max_row=end_row)
    num_src = NumDataSource(numRef=NumRef(f=ref))
    s = Series(val=num_src, tx=SeriesLabel(v=label))
    s.graphicalProperties.line.solidFill = color_hex
    s.graphicalProperties.line.width = width
    if dash:
        s.graphicalProperties.line.dashDot = dash
    if marker_sym:
        s.marker.symbol = marker_sym
        s.marker.size = 5
        s.marker.graphicalProperties.solidFill = color_hex
        s.marker.graphicalProperties.line.solidFill = color_hex
    chart.series.append(s)

add_series(chart, ws, 2, "① CRD — Capital Restant Dû",         "1D4ED8", width=28000, marker_sym="circle")
add_series(chart, ws, 3, "② Base IFI nette = 3,5M€ − CRD",    "15803D", width=28000, marker_sym="square")
add_series(chart, ws, 4, "Seuil IFI = 1,3M€",                  "B91C1C", width=18000, dash="dash")
add_series(chart, ws, 5, "CRD critique = 2,2M€",               "1D4ED8", width=15000, dash="dot")

# Axe X — étiquettes = années (colonne A)
ref_cats = Reference(ws, min_col=1, min_row=start_row, max_row=end_row)
chart.set_categories(ref_cats)

# Placer le graphique dans l'onglet données
ws.add_chart(chart, "H2")

# ==============================================================================
# ONGLET 2 — NOTES D'ANNOTATION (pour que le client puisse les copier/coller)
# ==============================================================================
ws2 = wb.create_sheet("Notes & annotations")
ws2.sheet_view.showGridLines = False
ws2.column_dimensions['A'].width = 20
ws2.column_dimensions['B'].width = 60
ws2.column_dimensions['C'].width = 35

ws2.merge_cells("A1:C1")
c = ws2.cell(row=1, column=1, value="Annotations du graphique — à coller comme zones de texte dans Excel")
c.font = fnt(bold=True, size=12, color='#0F172A')
c.fill = fill('#F1F5F9')
c.alignment = aln()
ws2.row_dimensions[1].height = 28

notes = [
    ("Couleur", "Texte annotation", "Où la placer"),
    ("🔴 Rouge", f"An {an_decl} — IFI se déclenche\nCRD = {rows[an_decl-1]['crd']/1e6:.2f}M€ < 2,2M€\nBase taxable = {rows[an_decl-1]['base_B']/1e6:.2f}M€ > seuil 1,3M€",
     f"Sur la courbe bleue à l'an {an_decl}"),
    ("🟣 Violet", f"An {an_crois} — Croisement CRD = Base IFI\nCRD = Base = 1,75M€\n≠ déclenchement IFI (3 ans plus tard)",
     f"Sur le point de croisement an {an_crois}"),
    ("🟢 Vert", "ZONE VERTE — IFI = 0 €\n13 ans de protection totale\nÉconomie : 20 690 €/an",
     "Zone gauche, milieu bas"),
    ("🔴 Rouge clair", "ZONE ROUGE — IFI progressive\nAn 14 à 20\nTotal IFI payée : 81 000 €",
     "Zone droite, milieu bas"),
    ("Bleu pointillé", "CRD critique = 2,2M€\nEn dessous → IFI se déclenche",
     "À droite de la ligne pointillée bleue"),
    ("Rouge pointillé", "Seuil IFI = 1,3M€\n(art. 964 CGI — barème progressif)",
     "À droite de la ligne rouge"),
]

bgs_notes = ['#334155','#FEF2F2','#F5F3FF','#F0FDF4','#FFF1F2','#EFF6FF','#FEF2F2']
for i, (col, txt, pos) in enumerate(notes):
    row = i + 2
    bg  = bgs_notes[i] if i < len(bgs_notes) else '#F8FAFC'
    bold = (i == 0)
    for j, v in enumerate([col, txt, pos], 1):
        c = ws2.cell(row=row, column=j, value=v)
        c.fill = fill(bg)
        c.font = fnt(bold=bold, size=9)
        c.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        c.border = brd()
    ws2.row_dimensions[row].height = 50 if i > 0 else 20

# ==============================================================================
# SAVE
# ==============================================================================
wb.save("graphique_ifi.xlsx")
print("✓ graphique_ifi.xlsx généré")
print(f"  → An {an_decl}  : déclenchement IFI")
print(f"  → An {an_crois} : croisement des courbes CRD / Base IFI")
