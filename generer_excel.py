"""
Génération du fichier Excel — Étude comparative IFI
3 onglets : Hypothèses | Tableau comparatif | Annexe calculs
"""

import openpyxl
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter

# ==============================================================================
# PARAMÈTRES (identiques aux graphiques)
# ==============================================================================
VALEUR_MAISON     = 5_000_000
ABATTEMENT_RP     = 0.30
MONTANT_EMPRUNT   = 5_000_000
TAUX_EMPRUNT      = 0.04
DUREE_ANS         = 20
TAUX_PLACEMENT    = 0.05
CAPITAL_PLACE     = 5_000_000
APPRECIATION_IMMO = 0.025
BASE_IFI_FIXE     = VALEUR_MAISON * (1 - ABATTEMENT_RP)
IFI_SEUIL         = 1_300_000
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
    cumul = 0.0
    vm    = VALEUR_MAISON
    rows  = []
    for an in range(1, DUREE_ANS + 1):
        vm_fin = vm * (1 + APPRECIATION_IMMO)
        crd_d  = crd
        int_an = cap_an = 0.0
        for _ in range(12):
            i = crd * r; c = mens - i
            int_an += i; cap_an += c
            crd = max(0.0, crd - c)
        rdt    = cp * TAUX_PLACEMENT
        cp_fin = cp * (1 + TAUX_PLACEMENT)
        levier = rdt - int_an
        ifi_A  = calcul_ifi(BASE_IFI_FIXE)
        base_B = BASE_IFI_FIXE - crd
        ifi_B  = calcul_ifi(base_B)
        eco    = ifi_A - ifi_B
        flux   = levier + eco
        cumul  = cumul * (1 + TAUX_PLACEMENT) + flux
        fin_B  = cp_fin + cumul
        rows.append(dict(
            an=an, vm=vm, vm_fin=vm_fin,
            crd_d=crd_d, crd_fin=crd, int=int_an, cap=cap_an,
            rdt=rdt, cp=cp, cp_fin=cp_fin,
            levier=levier,
            ifi_A=ifi_A, base_B=base_B, ifi_B=ifi_B,
            eco=eco, flux=flux, cumul=cumul,
            fin_B=fin_B,
            pat_A=vm_fin,
            pat_B=vm_fin + fin_B,
        ))
        cp = cp_fin; vm = vm_fin
    return rows, mens

data, mens = calculer()

# ==============================================================================
# STYLES
# ==============================================================================
def fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def font(bold=False, color="000000", size=10, italic=False):
    return Font(bold=bold, color=color, size=size, italic=italic)

def align(h='center', v='center', wrap=False):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)

def border_thin():
    s = Side(style='thin', color='CBD5E1')
    return Border(left=s, right=s, top=s, bottom=s)

def border_medium_bottom():
    thin  = Side(style='thin',   color='CBD5E1')
    thick = Side(style='medium', color='64748B')
    return Border(left=thin, right=thin, top=thin, bottom=thick)

EUR = '#,##0 "€"'
EUR2 = '#,##0.00 "€"'
PCT = '0.00%'
NB2 = '#,##0.00'

# Couleurs
C_ROUGE_H  = '7F1D1D'
C_BLEU_H   = '1E3A5F'
C_VERT_H   = '14532D'
C_ROUGE_L  = 'FEF2F2'
C_ROUGE_LA = 'FEF9F9'
C_BLEU_L   = 'DBEAFE'
C_BLEU_LA  = 'EFF6FF'
C_VERT_L   = 'DCFCE7'
C_VERT_LA  = 'F0FDF4'
C_TOTAL    = '1E293B'
C_GRIS_L   = 'F1F5F9'
C_ORANGE   = 'FEE2E2'

# ==============================================================================
# CRÉATION DU CLASSEUR
# ==============================================================================
wb = openpyxl.Workbook()

# ==============================================================================
# ONGLET 1 — HYPOTHÈSES
# ==============================================================================
ws1 = wb.active
ws1.title = "Hypothèses"
ws1.sheet_view.showGridLines = False
ws1.column_dimensions['A'].width = 38
ws1.column_dimensions['B'].width = 22
ws1.column_dimensions['C'].width = 40

def h_row(ws, row, label, value, note='', fmt=None):
    c_label = ws.cell(row=row, column=1, value=label)
    c_label.font      = font(size=10)
    c_label.alignment = align('left')
    c_label.border    = border_thin()
    c_label.fill      = fill('F8FAFC')

    c_val = ws.cell(row=row, column=2, value=value)
    c_val.font      = font(bold=True, size=10)
    c_val.alignment = align('right')
    c_val.border    = border_thin()
    if fmt: c_val.number_format = fmt

    c_note = ws.cell(row=row, column=3, value=note)
    c_note.font      = font(size=9, italic=True, color='64748B')
    c_note.alignment = align('left', wrap=True)
    c_note.border    = border_thin()
    c_note.fill      = fill('F8FAFC')

def h_section(ws, row, title, color):
    for c in range(1, 4):
        cell = ws.cell(row=row, column=c)
        cell.fill      = fill(color)
        cell.font      = font(bold=True, color='FFFFFF', size=11)
        cell.border    = border_thin()
    ws.cell(row=row, column=1).value     = title
    ws.cell(row=row, column=1).alignment = align('left')
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)

# Titre
ws1.merge_cells('A1:C1')
t = ws1['A1']
t.value     = "ÉTUDE COMPARATIVE IFI — HYPOTHÈSES DE TRAVAIL"
t.font      = font(bold=True, size=14, color='FFFFFF')
t.fill      = fill('0F172A')
t.alignment = align('center')
ws1.row_dimensions[1].height = 32

# En-têtes colonnes
for col, val in [(1, 'Paramètre'), (2, 'Valeur'), (3, 'Note explicative')]:
    c = ws1.cell(row=2, column=col, value=val)
    c.font      = font(bold=True, color='FFFFFF', size=10)
    c.fill      = fill('334155')
    c.alignment = align('center')
    c.border    = border_thin()
ws1.row_dimensions[2].height = 20

r = 3
h_section(ws1, r, "BIEN IMMOBILIER", '1E3A5F'); r += 1
h_row(ws1, r, "Valeur d'achat", VALEUR_MAISON, "Résidence principale", EUR); r += 1
h_row(ws1, r, "Abattement résidence principale", ABATTEMENT_RP, "30% prévu par la loi IFI", PCT); r += 1
h_row(ws1, r, "Base IFI (fixe)", BASE_IFI_FIXE,
      "Valeur d'achat × 70% — non revalorisée (choix pédagogique)", EUR); r += 1
h_row(ws1, r, "Revalorisation annuelle du bien", APPRECIATION_IMMO,
      "2,5%/an — intégrée uniquement dans le patrimoine total, pas dans l'IFI", PCT); r += 1

h_section(ws1, r, "EMPRUNT IMMOBILIER", '1E3A5F'); r += 1
h_row(ws1, r, "Montant emprunté", MONTANT_EMPRUNT, "100% du prix d'achat", EUR); r += 1
h_row(ws1, r, "Taux d'intérêt annuel fixe", TAUX_EMPRUNT, "Taux fixe sur toute la durée", PCT); r += 1
h_row(ws1, r, "Durée", DUREE_ANS, "années — prêt amortissable classique"); r += 1
h_row(ws1, r, "Mensualité", round(mens), "Capital + intérêts (calculé)", EUR); r += 1
h_row(ws1, r, "Annuité totale", round(mens * 12),
      "Payée depuis autres revenus du client → capital placé intouché", EUR); r += 1
h_row(ws1, r, "Service de la dette", "Autres revenus",
      "Le client n'utilise pas le placement pour rembourser"); r += 1

h_section(ws1, r, "PLACEMENT FINANCIER", '14532D'); r += 1
h_row(ws1, r, "Capital initial placé", CAPITAL_PLACE,
      "Équivalent du cash non dépensé en achat", EUR); r += 1
h_row(ws1, r, "Rendement annuel", TAUX_PLACEMENT,
      "5% composé — capitalisation en assurance-vie", PCT); r += 1
h_row(ws1, r, "Fiscalité sur le placement", 0,
      "0% pendant la capitalisation (enveloppe assurance-vie)", PCT); r += 1

h_section(ws1, r, "BARÈME IFI 2024", '7C3AED'); r += 1
for b, h, t in IFI_BAREME:
    note = f"Taux {t*100:.2f}% appliqué de {b:,.0f} € à {h:,.0f} €".replace('inf', '∞')
    h_row(ws1, r, f"  {b/1e3:,.0f}k€ → {h/1e3 if h < 1e10 else '∞':}k€",
          f"{t*100:.2f}%", note)
    r += 1
h_row(ws1, r, "Seuil de déclenchement", IFI_SEUIL,
      "Si patrimoine net < 1,3M€ → IFI = 0. Si ≥ 1,3M€ → IFI calculée dès 800k€ (effet rétroactif)", EUR)
r += 1

h_section(ws1, r, "RÈGLE DE DÉDUCTION IFI (Bofip BOI-PAT-IFI-20-30-30)", '7C3AED'); r += 1
h_row(ws1, r, "Dette déductible", "Capital Restant Dû (CRD)",
      "Encours en CAPITAL uniquement — les intérêts ne sont PAS déductibles"); r += 1
h_row(ws1, r, "Base IFI nette (scénario B)", "Base IFI fixe − CRD fin d'année",
      "3 500 000 € − CRD. IFI déclenchée si cette base ≥ 1 300 000 €"); r += 1

ws1.row_dimensions[1].height = 32
for row in ws1.iter_rows():
    for cell in row:
        if cell.row > 1:
            ws1.row_dimensions[cell.row].height = 18

# ==============================================================================
# ONGLET 2 — TABLEAU COMPARATIF
# ==============================================================================
ws2 = wb.create_sheet("Tableau comparatif")
ws2.sheet_view.showGridLines = False

# Titre
ws2.merge_cells('A1:M1')
t2 = ws2['A1']
t2.value     = "TABLEAU COMPARATIF — ACHAT CASH (A) vs EMPRUNT 4% / 20 ANS (B)"
t2.font      = font(bold=True, size=13, color='FFFFFF')
t2.fill      = fill('0F172A')
t2.alignment = align('center')
ws2.row_dimensions[1].height = 30

# Sous-titre blocs
blocs = [
    (1, 1, "AN",               '334155'),
    (2, 4, "SCÉNARIO A — ACHAT CASH",          C_ROUGE_H),
    (5, 9, "SCÉNARIO B — EMPRUNT 4% / 20 ANS", C_BLEU_H),
    (10, 13, "AVANTAGE B vs A",                C_VERT_H),
]
for c_start, c_end, label, color in blocs:
    ws2.merge_cells(start_row=2, start_column=c_start, end_row=2, end_column=c_end)
    cell = ws2.cell(row=2, column=c_start)
    cell.value     = label
    cell.font      = font(bold=True, color='FFFFFF', size=10)
    cell.fill      = fill(color)
    cell.alignment = align('center')
    for c in range(c_start, c_end + 1):
        ws2.cell(row=2, column=c).border = border_thin()
ws2.row_dimensions[2].height = 20

# En-têtes colonnes
headers = [
    "Année",
    "Valeur maison\n(2,5%/an)",
    "IFI payée\n(A)",
    "Patrimoine\ntotal (A)",
    "CRD fin\n(capital restant)",
    "Intérêts\npayés",
    "IFI payée\n(B)",
    "Patrimoine\nfinancier (B)",
    "Patrimoine\ntotal (B)",
    "Économie\nIFI",
    "Flux\nréinvesti",
    "Delta\npatrimoine",
    "Statut IFI (B)",
]
col_colors = [
    '334155',
    C_ROUGE_H, C_ROUGE_H, C_ROUGE_H,
    C_BLEU_H, C_BLEU_H, C_BLEU_H, C_BLEU_H, C_BLEU_H,
    C_VERT_H, C_VERT_H, C_VERT_H, C_VERT_H,
]
for c, (hdr, clr) in enumerate(zip(headers, col_colors), 1):
    cell = ws2.cell(row=3, column=c, value=hdr)
    cell.font      = font(bold=True, color='FFFFFF', size=9)
    cell.fill      = fill(clr)
    cell.alignment = align('center', wrap=True)
    cell.border    = border_thin()
ws2.row_dimensions[3].height = 36

# Largeurs colonnes
col_widths = [6, 16, 14, 16, 16, 14, 14, 18, 18, 14, 14, 16, 16]
for i, w in enumerate(col_widths, 1):
    ws2.column_dimensions[get_column_letter(i)].width = w

# Données
for idx, d in enumerate(data):
    row = 4 + idx
    an  = d['an']
    pair = (idx % 2 == 0)
    ifi_b_active = d['ifi_B'] > 0

    ra  = fill(C_ROUGE_LA  if pair else C_ROUGE_L)
    rb  = fill(C_BLEU_LA   if pair else C_BLEU_L)
    rvo = fill('FFF7ED'    if pair else 'FFEDD5')  # orange pour IFI B active
    rv  = fill(C_VERT_LA   if pair else C_VERT_L)
    rg  = fill(C_GRIS_L)
    ri  = fill(C_ORANGE)   # IFI B déclenchée

    row_data = [
        (an,           '0',    rg),
        (d['vm_fin'],  EUR,    ra),
        (d['ifi_A'],   EUR,    ra),
        (d['pat_A'],   EUR,    ra),
        (d['crd_fin'], EUR,    rvo if ifi_b_active else rb),
        (d['int'],     EUR,    rvo if ifi_b_active else rb),
        (d['ifi_B'],   EUR,    ri  if ifi_b_active else rb),
        (d['fin_B'],   EUR,    rvo if ifi_b_active else rb),
        (d['pat_B'],   EUR,    rvo if ifi_b_active else rb),
        (d['eco'],     EUR,    rv),
        (d['flux'],    EUR,    rv),
        (d['pat_B'] - d['pat_A'], EUR, rv),
        ("✓ Protégé" if not ifi_b_active else f"⚠ IFI due", '0', rv),
    ]
    for c, (val, fmt, bg) in enumerate(row_data, 1):
        cell = ws2.cell(row=row, column=c, value=val)
        cell.fill      = bg
        cell.border    = border_thin()
        cell.alignment = align('center')
        cell.font      = font(size=9)
        if fmt != '0': cell.number_format = fmt
    ws2.row_dimensions[row].height = 17

# Ligne totaux
tot_row = 4 + DUREE_ANS
totals = [
    ("TOTAL / AN 20", '0'),
    (data[-1]['vm_fin'],    EUR),
    (sum(d['ifi_A'] for d in data), EUR),
    (data[-1]['pat_A'],     EUR),
    (0,                     EUR),   # CRD = 0 en fin
    (sum(d['int'] for d in data),   EUR),
    (sum(d['ifi_B'] for d in data), EUR),
    (data[-1]['fin_B'],     EUR),
    (data[-1]['pat_B'],     EUR),
    (sum(d['eco'] for d in data),   EUR),
    (sum(d['flux'] for d in data),  EUR),
    (data[-1]['pat_B'] - data[-1]['pat_A'], EUR),
    ("20 ans", '0'),
]
for c, (val, fmt) in enumerate(totals, 1):
    cell = ws2.cell(row=tot_row, column=c, value=val)
    cell.fill      = fill(C_TOTAL)
    cell.font      = font(bold=True, color='FFFFFF', size=9)
    cell.alignment = align('center')
    cell.border    = border_thin()
    if fmt != '0': cell.number_format = fmt
ws2.row_dimensions[tot_row].height = 20

# Note de bas de page
note_row = tot_row + 2
ws2.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=13)
note_cell = ws2.cell(row=note_row, column=1,
    value="Base IFI fixe = 3 500 000 € (valeur achat × 70%, non revalorisée — choix pédagogique)  •  "
          "CRD = capital restant dû (hors intérêts, seul montant déductible selon Bofip)  •  "
          "Patrimoine financier B = Placement 5M capitalisé à 5% + flux réinvestis  •  "
          "⚠ Lignes orange : IFI scénario B se déclenche (CRD < 2 200 000 €)")
note_cell.font      = font(size=8, italic=True, color='64748B')
note_cell.alignment = align('left', wrap=True)
note_cell.fill      = fill('F8FAFC')
ws2.row_dimensions[note_row].height = 28

# ==============================================================================
# ONGLET 3 — ANNEXE CALCULS
# ==============================================================================
ws3 = wb.create_sheet("Annexe — Calculs détaillés")
ws3.sheet_view.showGridLines = False

ws3.merge_cells('A1:J1')
t3 = ws3['A1']
t3.value     = "ANNEXE — DÉTAIL DES CALCULS ANNÉE PAR ANNÉE"
t3.font      = font(bold=True, size=13, color='FFFFFF')
t3.fill      = fill('0F172A')
t3.alignment = align('center')
ws3.row_dimensions[1].height = 30

# Explication des formules
formulas = [
    ("FORMULE", "EXPRESSION", "EXPLICATION"),
    ("Mensualité",
     f"= {MONTANT_EMPRUNT:,.0f} × (4%/12) / [1 − (1 + 4%/12)^(−240)]",
     f"= {mens:,.0f} €/mois  →  {mens*12:,.0f} €/an"),
    ("CRD fin d'année N",
     "= CRD début − Σ(capital mensuel remboursé sur 12 mois)",
     "Encours en capital uniquement. Les intérêts = charge, pas ajoutés au solde."),
    ("Rendement placement",
     "= Valeur placement début d'année × 5%",
     "La valeur grossit chaque année : 5M × 1,05^N"),
    ("Effet de levier net",
     "= Rendement placement − Intérêts payés dans l'année",
     "An 1 : 250 000 − 196 967 = 53 033 €. Croissant car intérêts baissent, placement grossit."),
    ("Base IFI scénario A",
     f"= {VALEUR_MAISON:,.0f} × (1 − 30%) = {BASE_IFI_FIXE:,.0f} € fixe",
     "Non revalorisée pour simplifier. IFI A = 20 690 €/an constant."),
    ("Base IFI scénario B",
     f"= {BASE_IFI_FIXE:,.0f} € − CRD fin d'année",
     "Négative les premières années → pas d'IFI. IFI se déclenche quand base ≥ 1 300 000 €."),
    ("IFI calculée",
     "Barème progressif à partir de 800 000 € (si seuil 1 300 000 € atteint)",
     "Effet rétroactif : dès que base ≥ 1,3M€, on recalcule depuis 800k€."),
    ("Économie IFI",
     "= IFI scénario A − IFI scénario B",
     "Positive tant que IFI B < IFI A. Décroît après an 14 quand IFI B se déclenche."),
    ("Flux réinvesti",
     "= Effet de levier net + Économie IFI",
     "Somme des deux bénéfices annuels, capitalisée à 5%."),
    ("Cumul réinvesti",
     "= Cumul(N−1) × 1,05 + Flux(N)",
     "Capitalisation à 5% : le stock grossit chaque année avant d'ajouter le flux de l'année."),
    ("Valeur maison",
     f"= {VALEUR_MAISON:,.0f} × (1 + 2,5%)^N",
     "Revalorisation identique dans les deux scénarios → n'impacte pas le delta financier."),
    ("Patrimoine total A",
     "= Valeur maison revalorisée",
     "Pas de financier en scénario A (5M immobilisés dans l'achat)."),
    ("Patrimoine total B",
     "= Valeur maison revalorisée + Placement 5M capitalisé + Cumul réinvesti",
     "Les 3 composantes financières s'ajoutent à la même maison qu'en scénario A."),
    ("Delta patrimoine",
     "= Patrimoine total B − Patrimoine total A",
     "= avantage net annuel du scénario B. Croît régulièrement jusqu'à ~+20M€ à an 20."),
]

for r_idx, row_data in enumerate(formulas):
    row = r_idx + 3
    colors = ['1E3A5F', '334155', '334155'] if r_idx == 0 else [C_GRIS_L, 'FFFFFF', 'F0F9FF']
    bolds  = [True, True, True] if r_idx == 0 else [True, False, False]
    ftcols = ['FFFFFF', 'FFFFFF', 'FFFFFF'] if r_idx == 0 else ['0F172A', '0F172A', '1D4ED8']
    for c, (val, clr, bld, ftc) in enumerate(zip(row_data, colors, bolds, ftcols), 1):
        cell = ws3.cell(row=row, column=c, value=val)
        cell.fill      = fill(clr)
        cell.font      = font(bold=bld, color=ftc, size=9)
        cell.alignment = align('left', 'center', wrap=True)
        cell.border    = border_thin()
    ws3.row_dimensions[row].height = 32 if r_idx == 0 else 40

ws3.column_dimensions['A'].width = 22
ws3.column_dimensions['B'].width = 50
ws3.column_dimensions['C'].width = 58

# Tableau numérique de vérification
sep_row = len(formulas) + 5
ws3.merge_cells(start_row=sep_row, start_column=1, end_row=sep_row, end_column=10)
sep_cell = ws3.cell(row=sep_row, column=1,
    value="TABLEAU DE VÉRIFICATION NUMÉRIQUE — TOUTES LES VALEURS INTERMÉDIAIRES")
sep_cell.font      = font(bold=True, size=11, color='FFFFFF')
sep_cell.fill      = fill('0F172A')
sep_cell.alignment = align('center')
ws3.row_dimensions[sep_row].height = 24

annexe_headers = [
    "An", "CRD début", "Intérêts", "Capital\nremb.", "CRD fin",
    "Rdt\nplacement", "Levier\nnet", "IFI (A)", "IFI (B)", "Éco IFI",
    "Flux\nréinvesti", "Cumul\n5%", "Valeur\nmaison",
]
for c, hdr in enumerate(annexe_headers, 1):
    cell = ws3.cell(row=sep_row + 1, column=c, value=hdr)
    cell.font      = font(bold=True, color='FFFFFF', size=9)
    cell.fill      = fill('334155')
    cell.alignment = align('center', wrap=True)
    cell.border    = border_thin()
ws3.row_dimensions[sep_row + 1].height = 32

for idx, d in enumerate(data):
    row = sep_row + 2 + idx
    pair = (idx % 2 == 0)
    bg = fill('F8FAFC') if pair else fill('FFFFFF')
    bg_ifi = fill('FEE2E2') if d['ifi_B'] > 0 else bg

    vals = [
        (d['an'],       '0',  fill(C_GRIS_L)),
        (d['crd_d'],    EUR,  bg),
        (d['int'],      EUR,  bg),
        (d['cap'],      EUR,  bg),
        (d['crd_fin'],  EUR,  bg),
        (d['rdt'],      EUR,  bg),
        (d['levier'],   EUR,  bg),
        (d['ifi_A'],    EUR,  bg),
        (d['ifi_B'],    EUR,  bg_ifi),
        (d['eco'],      EUR,  bg),
        (d['flux'],     EUR,  bg),
        (d['cumul'],    EUR,  bg),
        (d['vm_fin'],   EUR,  bg),
    ]
    for c, (val, fmt, bg_c) in enumerate(vals, 1):
        cell = ws3.cell(row=row, column=c, value=val)
        cell.fill      = bg_c
        cell.font      = font(size=9)
        cell.alignment = align('center')
        cell.border    = border_thin()
        if fmt != '0': cell.number_format = fmt
    ws3.row_dimensions[row].height = 17

# Largeurs annexe
for i, w in enumerate([6, 14, 13, 13, 14, 14, 13, 13, 13, 12, 13, 14, 14], 1):
    ws3.column_dimensions[get_column_letter(i)].width = w

# ==============================================================================
# SAUVEGARDE
# ==============================================================================
filename = "etude_ifi_cash_vs_emprunt.xlsx"
wb.save(filename)
print(f"✓ Fichier Excel généré : {filename}")

# ==============================================================================
# DRAFT EMAIL (texte brut)
# ==============================================================================
email = f"""
================================================================================
  DRAFT EMAIL — ÉTUDE COMPARATIVE IFI
================================================================================

Objet : Étude comparative — Achat cash vs financement bancaire | Résidence principale 5M€

Bonjour [Prénom],

Suite à notre échange, veuillez trouver ci-joint l'étude comparative que nous
avons préparée pour vous aider à prendre votre décision.

────────────────────────────────────────────────────────────────────────────────
  LA QUESTION
────────────────────────────────────────────────────────────────────────────────

Vous envisagez l'acquisition de votre résidence principale pour 5 000 000 €.
Vous disposez des fonds pour acheter cash. La question est simple :
est-il financièrement préférable d'acheter cash ou de recourir à un emprunt ?

────────────────────────────────────────────────────────────────────────────────
  LES HYPOTHÈSES RETENUES
────────────────────────────────────────────────────────────────────────────────

  Maison               : 5 000 000 € (résidence principale, Paris)
  Revalorisation immo  : +2,5%/an → 8,2M€ à 20 ans
  Emprunt              : 5 000 000 € à 4% fixe sur 20 ans
                         Mensualité : {mens:,.0f} €/mois
  Placement            : 5 000 000 € en assurance-vie à 5% composé, 0% fiscalité
  Service de la dette  : vos autres revenus — le placement n'est jamais touché
  Base IFI             : 3 500 000 € fixe (5M€ × 70%, abattement RP 30%)

────────────────────────────────────────────────────────────────────────────────
  LES 3 EFFETS CLÉ DU FINANCEMENT BANCAIRE
────────────────────────────────────────────────────────────────────────────────

  1. PROTECTION IFI PENDANT 13 ANS
     La dette vient en déduction de votre base taxable IFI.
     Tant que le Capital Restant Dû (CRD) dépasse 2 200 000 €,
     votre base nette reste sous le seuil de 1 300 000 € → IFI = 0 €.
     Économie : 20 690 €/an pendant 13 ans = 268 970 € économisés.
     (L'IFI reprend progressivement à partir de l'an 14, mais reste très faible)

  2. EFFET DE LEVIER FINANCIER
     En conservant vos 5M€ investis à 5% pendant que vous empruntez à 4%,
     vous générez un gain net dès l'an 1 :
       → An 1 : 250 000 € (rdt) − 196 967 € (intérêts) = 53 033 € de gain net
       → Ce gain augmente chaque année (le placement grossit, les intérêts baissent)
       → An 20 : 631 738 € − 7 757 € = 623 981 € de gain net

  3. CAPITALISATION DES GAINS
     L'ensemble de ces gains (levier + IFI économisée) est réinvesti à 5%/an.
     Au bout de 20 ans, ce compte de capitalisation atteint {data[-1]['cumul']/1e6:.1f}M€.

────────────────────────────────────────────────────────────────────────────────
  RÉSULTAT À 20 ANS
────────────────────────────────────────────────────────────────────────────────

  SCÉNARIO A — ACHAT CASH
    Maison revalorisée              : {data[-1]['vm_fin']/1e6:.2f}M€
    Patrimoine financier            :  0,00M€
    IFI payée sur 20 ans            : −{sum(d['ifi_A'] for d in data)/1e3:.0f}k€
    ─────────────────────────────────────────
    PATRIMOINE NET TOTAL            : {(data[-1]['vm_fin'] - sum(d['ifi_A'] for d in data))/1e6:.2f}M€

  SCÉNARIO B — EMPRUNT 4% / 20 ANS
    Maison revalorisée              : {data[-1]['vm_fin']/1e6:.2f}M€  (identique)
    Placement 5M€ → 20 ans          : {data[-1]['cp_fin']/1e6:.2f}M€
    Flux réinvestis capitalisés     : {data[-1]['cumul']/1e6:.2f}M€
    Intérêts payés (20 ans)         : −{sum(d['int'] for d in data)/1e6:.2f}M€
    IFI payée sur 20 ans            : −{sum(d['ifi_B'] for d in data)/1e3:.0f}k€
    ─────────────────────────────────────────
    PATRIMOINE NET TOTAL            : {(data[-1]['vm_fin'] + data[-1]['cp_fin'] + data[-1]['cumul'] - sum(d['int'] for d in data) - sum(d['ifi_B'] for d in data))/1e6:.2f}M€

  AVANTAGE NET DU FINANCEMENT      : +{(data[-1]['cp_fin'] + data[-1]['cumul'] - sum(d['int'] for d in data) + sum(d['ifi_A'] for d in data) - sum(d['ifi_B'] for d in data))/1e6:.2f}M€

────────────────────────────────────────────────────────────────────────────────

Vous trouverez en pièce jointe le fichier Excel détaillant :
  • Onglet 1 : toutes les hypothèses (modifiables)
  • Onglet 2 : le tableau comparatif année par année
  • Onglet 3 : le détail de chaque calcul pour vérification

Je reste bien entendu disponible pour échanger sur ces résultats et affiner
les paramètres selon votre situation.

Bien cordialement,
[Votre nom]
================================================================================
"""

with open("draft_email.txt", "w", encoding="utf-8") as f:
    f.write(email)
print("✓ Draft email généré : draft_email.txt")
print(email)
