"""
Génération Excel — Étude comparative IFI (version corrigée, sans double-comptage)
3 onglets : Hypothèses | Tableau comparatif | Annexe calculs
"""

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
APPRECIATION_IMMO = 0.02           # 2%/an
BASE_IFI_FIXE     = VALEUR_MAISON * (1 - ABATTEMENT_RP)   # 3 500 000 €
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
    cp   = CAPITAL_PLACE
    vm   = VALEUR_MAISON
    rows = []
    cum_ifi_A = cum_int = cum_ifi_B = cumul_eco_ifi = 0.0

    for an in range(1, DUREE_ANS + 1):
        vm_fin = vm * (1 + APPRECIATION_IMMO)
        crd_d  = crd
        int_an = cap_an = 0.0
        for _ in range(12):
            i = crd * r; c = mens - i
            int_an += i; cap_an += c
            crd = max(0.0, crd - c)

        cp_fin = cp * (1 + TAUX_PLACEMENT)
        ifi_A  = calcul_ifi(BASE_IFI_FIXE)
        base_B = BASE_IFI_FIXE - crd
        ifi_B  = calcul_ifi(base_B)
        eco    = ifi_A - ifi_B

        cum_ifi_A     += ifi_A
        cum_int       += int_an
        cum_ifi_B     += ifi_B
        cumul_eco_ifi += eco

        pat_A = vm_fin - cum_ifi_A
        pat_B = vm_fin + cp_fin - cum_int - cum_ifi_B

        rows.append(dict(
            an=an, vm=vm, vm_fin=vm_fin,
            crd_d=crd_d, crd_fin=crd, int=int_an, cap=cap_an,
            cp=cp, cp_fin=cp_fin,
            ifi_A=ifi_A, base_B=base_B, ifi_B=ifi_B,
            eco=eco, cumul_eco_ifi=cumul_eco_ifi,
            pat_A=pat_A, pat_B=pat_B,
            cum_ifi_A=cum_ifi_A, cum_int=cum_int, cum_ifi_B=cum_ifi_B,
        ))
        cp = cp_fin; vm = vm_fin
    return rows, mens

data, mens = calculer()

tot_int   = sum(d['int']   for d in data)
tot_ifi_A = sum(d['ifi_A'] for d in data)
tot_ifi_B = sum(d['ifi_B'] for d in data)
tot_eco   = tot_ifi_A - tot_ifi_B
vm_20     = data[-1]['vm_fin']
cp_20     = data[-1]['cp_fin']
pat_A_net = data[-1]['pat_A']
pat_B_net = data[-1]['pat_B']
avantage  = pat_B_net - pat_A_net

# ==============================================================================
# STYLES
# ==============================================================================
EUR  = '#,##0 €'
EUR2 = '#,##0.00 €'
PCT  = '0.00%'
NB   = '#,##0'

def fill(h): return PatternFill("solid", fgColor=h.lstrip('#'))
def fnt(bold=False, color="000000", size=10, italic=False):
    return Font(bold=bold, color=color.lstrip('#'), size=size, italic=italic)
def aln(h='center', v='center', wrap=False):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)
def brd():
    s = Side(style='thin', color='CBD5E1')
    return Border(left=s, right=s, top=s, bottom=s)

C = dict(
    rouge_h='#7F1D1D', bleu_h='#1E3A5F', vert_h='#14532D', noir='#0F172A',
    rouge_l='#FEF2F2', rouge_la='#FEF9F9',
    bleu_l='#DBEAFE',  bleu_la='#EFF6FF',
    vert_l='#DCFCE7',  vert_la='#F0FDF4',
    gris_l='#F1F5F9',  total='#1E293B',
    orange='#FEE2E2',  orange_l='#FFF7ED', orange_la='#FFEDD5',
    header2='#334155', fond='#F8FAFC', violet='#7C3AED',
)

def set_cell(ws, row, col, value, fmt=None, bg=None, bold=False, color='#000000',
             size=10, h='center', wrap=False, italic=False, border=True):
    c = ws.cell(row=row, column=col, value=value)
    if bg:    c.fill      = fill(bg)
    if border: c.border   = brd()
    c.font      = fnt(bold=bold, color=color, size=size, italic=italic)
    c.alignment = aln(h=h, wrap=wrap)
    if fmt:   c.number_format = fmt
    return c

def title_row(ws, row, text, ncols, bg, color='#FFFFFF', size=13, height=30):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    c = set_cell(ws, row, 1, text, bg=bg, bold=True, color=color, size=size)
    ws.row_dimensions[row].height = height

def bloc_header(ws, row, col_start, col_end, text, bg):
    ws.merge_cells(start_row=row, start_column=col_start, end_row=row, end_column=col_end)
    c = set_cell(ws, row, col_start, text, bg=bg, bold=True, color='#FFFFFF', size=10)
    for col in range(col_start, col_end + 1):
        ws.cell(row=row, column=col).border = brd()

# ==============================================================================
# CLASSEUR
# ==============================================================================
wb = openpyxl.Workbook()

# ──────────────────────────────────────────────────────────────────────────────
# ONGLET 1 — HYPOTHÈSES
# ──────────────────────────────────────────────────────────────────────────────
ws1 = wb.active
ws1.title = "Hypothèses"
ws1.sheet_view.showGridLines = False
ws1.column_dimensions['A'].width = 40
ws1.column_dimensions['B'].width = 24
ws1.column_dimensions['C'].width = 55

title_row(ws1, 1, "ÉTUDE COMPARATIVE IFI — HYPOTHÈSES DE TRAVAIL", 3, C['noir'])

for col, txt in [(1,'Paramètre'), (2,'Valeur'), (3,'Note explicative')]:
    set_cell(ws1, 2, col, txt, bg=C['header2'], bold=True, color='#FFFFFF')
ws1.row_dimensions[2].height = 20

def section(row, txt, bg):
    ws1.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    set_cell(ws1, row, 1, txt, bg=bg, bold=True, color='#FFFFFF', size=11, h='left')
    for c in range(1, 4): ws1.cell(row=row, column=c).border = brd()
    ws1.row_dimensions[row].height = 22

def param(row, lbl, val, note='', fmt=None):
    set_cell(ws1, row, 1, lbl, bg=C['fond'], h='left')
    c = set_cell(ws1, row, 2, val, bg='#FFFFFF', bold=True, h='right')
    if fmt: c.number_format = fmt
    set_cell(ws1, row, 3, note, bg=C['fond'], italic=True, color='#64748B', size=9, h='left', wrap=True)
    ws1.row_dimensions[row].height = 18

r = 3
section(r, "BIEN IMMOBILIER", C['bleu_h']); r+=1
param(r, "Valeur d'achat",                 VALEUR_MAISON,     "Résidence principale", EUR); r+=1
param(r, "Abattement résidence principale", ABATTEMENT_RP,     "30% prévu par la loi IFI", PCT); r+=1
param(r, "Base IFI (fixe, non revalorisée)", BASE_IFI_FIXE,
      "5M€ × 70%. Non revalorisée = choix pédagogique (évite projections incertaines)", EUR); r+=1
param(r, "Revalorisation du bien",          APPRECIATION_IMMO,
      "2%/an. Identique dans les deux scénarios → n'impacte pas le delta financier", PCT); r+=1

section(r, "EMPRUNT IMMOBILIER", C['bleu_h']); r+=1
param(r, "Montant emprunté",                MONTANT_EMPRUNT,   "100% du prix d'achat", EUR); r+=1
param(r, "Taux d'intérêt annuel fixe",      TAUX_EMPRUNT,      "Taux fixe, toute durée", PCT); r+=1
param(r, "Durée",                           DUREE_ANS,         "ans — prêt amortissable classique"); r+=1
param(r, "Mensualité (calculée)",           round(mens),
      f"= {MONTANT_EMPRUNT:,.0f} × (4%/12) / [1−(1+4%/12)^−240]. Calculée en mensuel (240 mois).", EUR); r+=1
param(r, "Annuité totale",                  round(mens*12),    "Payée depuis autres revenus du client", EUR); r+=1
param(r, "Service de la dette",             "Autres revenus",
      "Le placement de 5M€ n'est JAMAIS touché pour rembourser le prêt"); r+=1
param(r, "Total intérêts sur 20 ans",       round(tot_int),
      "Coût réel du crédit. Déduit du patrimoine final en scénario B.", EUR); r+=1

section(r, "PLACEMENT FINANCIER", C['vert_h']); r+=1
param(r, "Capital initial placé",           CAPITAL_PLACE,
      "Les 5M€ que le client n'a pas dépensés (car il emprunte)", EUR); r+=1
param(r, "Rendement annuel",                TAUX_PLACEMENT,
      "5% composé. Capitalisé en assurance-vie, sans fiscalité pendant la durée.", PCT); r+=1
param(r, "Fiscalité sur le placement",      "0%",
      "Pas de prélèvements pendant la capitalisation (enveloppe AV)"); r+=1
param(r, "Valeur du placement à 20 ans",    round(cp_20),
      f"= 5 000 000 × (1,05)^20 = {cp_20/1e6:.2f}M€", EUR); r+=1

section(r, "LOGIQUE DE CALCUL (correction double-comptage)", C['violet']); r+=1
param(r, "Moteur 1 — Placement",
      "+8,27M€ net",
      "Le 5M€ grossit à 5%/an → 13,27M€. Gain net = 13,27M€ − 5M€ = 8,27M€"); r+=1
param(r, "Moteur 2 — Coût crédit",
      "−2,27M€",
      "Total intérêts payés sur 20 ans (calculé mensuellement sur 240 mois)"); r+=1
param(r, "Moteur 3 — Économie IFI",
      f"+{tot_eco/1e3:.0f}k€",
      f"IFI évitée 13 ans (20 690€/an) + faible IFI ans 14-20. Total : {tot_eco/1e3:.0f}k€"); r+=1
param(r, "⚠ Levier net NON réinvesti séparément", "Supprimé",
      "Rendement 5M − Intérêts = déjà dans la croissance du 5M. Réinvestir séparément = double-comptage."); r+=1
param(r, "AVANTAGE NET TOTAL",              round(avantage),
      f"= +8,27M€ − 2,27M€ + {tot_eco/1e3:.0f}k€ = +{avantage/1e6:.2f}M€", EUR); r+=1

section(r, "BARÈME IFI 2024 (Bofip BOI-PAT-IFI-20-30-30)", C['violet']); r+=1
for b, h, t in IFI_BAREME:
    lbl  = f"  {b/1e3:,.0f}k€ → {'∞' if h > 1e9 else f'{h/1e3:,.0f}k€'}"
    note = (f"Déductible IFI : Capital Restant Dû uniquement (hors intérêts). "
            f"Seuil déclenchement : 1 300 000 €. Assiette rétroactive à 800 000 €.")
    param(r, lbl, f"{t*100:.2f}%", note if b == 800_000 else ""); r+=1

# ──────────────────────────────────────────────────────────────────────────────
# ONGLET 2 — TABLEAU COMPARATIF
# ──────────────────────────────────────────────────────────────────────────────
ws2 = wb.create_sheet("Tableau comparatif")
ws2.sheet_view.showGridLines = False

title_row(ws2, 1, "TABLEAU COMPARATIF — ACHAT CASH (A) vs EMPRUNT 4% / 20 ANS (B)", 13, C['noir'])

bloc_header(ws2, 2,  1,  1,  "AN",                             C['header2'])
bloc_header(ws2, 2,  2,  4,  "SCÉNARIO A — ACHAT CASH",        C['rouge_h'])
bloc_header(ws2, 2,  5,  9,  "SCÉNARIO B — EMPRUNT 4% / 20 ANS", C['bleu_h'])
bloc_header(ws2, 2, 10, 13,  "AVANTAGE B vs A",                C['vert_h'])
ws2.row_dimensions[2].height = 22

headers = [
    "Année",
    "Valeur maison\n(+2%/an)", "IFI payée\n(A)", "Pat. net cumulé\n(A)",
    "CRD fin\n(capital restant)", "Intérêts\npayés", "Placement 5M€\n(valeur)", "IFI payée\n(B)", "Pat. net cumulé\n(B)",
    "Éco. IFI\nannuelle", "Cumul éco.\nIFI", "Delta\npatrimoine", "Statut IFI (B)",
]
hdr_bg = [C['header2']] + [C['rouge_h']]*3 + [C['bleu_h']]*5 + [C['vert_h']]*4
for col, (h, bg) in enumerate(zip(headers, hdr_bg), 1):
    set_cell(ws2, 3, col, h, bg=bg, bold=True, color='#FFFFFF', size=9, wrap=True)
ws2.row_dimensions[3].height = 38

col_w = [6, 16, 13, 17, 17, 13, 17, 13, 17, 13, 13, 16, 15]
for i, w in enumerate(col_w, 1):
    ws2.column_dimensions[get_column_letter(i)].width = w

for idx, d in enumerate(data):
    row  = 4 + idx
    pair = (idx % 2 == 0)
    ifi_b_on = d['ifi_B'] > 0

    ra  = C['rouge_la'] if pair else C['rouge_l']
    rb  = C['bleu_la']  if pair else C['bleu_l']
    ro  = C['orange_la'] if pair else C['orange_l']
    rv  = C['vert_la']  if pair else C['vert_l']

    cells = [
        (d['an'],       NB,    C['gris_l'],  False),
        (d['vm_fin'],   EUR,   ra,            False),
        (d['ifi_A'],    EUR,   ra,            False),
        (d['pat_A'],    EUR,   ra,            True),
        (d['crd_fin'],  EUR,   ro if ifi_b_on else rb, False),
        (d['int'],      EUR,   ro if ifi_b_on else rb, False),
        (d['cp_fin'],   EUR,   ro if ifi_b_on else rb, False),
        (d['ifi_B'],    EUR,   C['orange'] if ifi_b_on else rb, False),
        (d['pat_B'],    EUR,   ro if ifi_b_on else rb, True),
        (d['eco'],      EUR,   rv,            False),
        (d['cumul_eco_ifi'], EUR, rv,         False),
        (d['pat_B'] - d['pat_A'], EUR, rv,    True),
        ("✓ Protégé" if not ifi_b_on else f"⚠ IFI {d['ifi_B']/1e3:.1f}k€", None, rv, False),
    ]
    for col, (val, fmt, bg, bld) in enumerate(cells, 1):
        set_cell(ws2, row, col, val, fmt=fmt, bg=bg, bold=bld, size=9)
    ws2.row_dimensions[row].height = 17

# Ligne totaux
tot_row = 4 + DUREE_ANS
totals = [
    ("TOTAL / AN 20", None),
    (vm_20,           EUR),
    (tot_ifi_A,       EUR),
    (pat_A_net,       EUR),
    (0,               EUR),
    (tot_int,         EUR),
    (cp_20,           EUR),
    (tot_ifi_B,       EUR),
    (pat_B_net,       EUR),
    (tot_eco,         EUR),
    (tot_eco,         EUR),
    (avantage,        EUR),
    ("20 ans",        None),
]
for col, (val, fmt) in enumerate(totals, 1):
    set_cell(ws2, tot_row, col, val, fmt=fmt, bg=C['total'], bold=True, color='#FFFFFF', size=9)
ws2.row_dimensions[tot_row].height = 22

# Note bas de page
note_r = tot_row + 2
ws2.merge_cells(start_row=note_r, start_column=1, end_row=note_r, end_column=13)
set_cell(ws2, note_r, 1,
    "Pat. net cumulé = valeur maison − IFI cumulée (A) | maison + placement − intérêts cumulés − IFI cumulée (B)  •  "
    "Placement = 5M€ × (1,05)^N, jamais touché, aucun double-comptage  •  "
    "CRD = capital restant dû (hors intérêts, seul montant déductible IFI — Bofip)  •  "
    "⚠ Orange : IFI scénario B déclenchée (CRD < 2 200 000 €)",
    bg=C['fond'], italic=True, color='#64748B', size=8, h='left', wrap=True)
ws2.row_dimensions[note_r].height = 28

# ──────────────────────────────────────────────────────────────────────────────
# ONGLET 3 — ANNEXE CALCULS
# ──────────────────────────────────────────────────────────────────────────────
ws3 = wb.create_sheet("Annexe — Calculs détaillés")
ws3.sheet_view.showGridLines = False
title_row(ws3, 1, "ANNEXE — FORMULES ET DÉTAIL DES CALCULS", 3, C['noir'])

formulas = [
    ("FORMULE / CONCEPT",           "EXPRESSION MATHÉMATIQUE",
     "EXPLICATION PÉDAGOGIQUE"),
    ("Mensualité (méthode mensuelle)",
     f"= {MONTANT_EMPRUNT:,.0f} × (4%÷12) ÷ [1−(1+4%÷12)^−240]",
     f"= {mens:,.0f} €/mois. Calculé sur 240 mois (pas 20 ans) → plus précis car le prêt est mensuel."),
    ("Capital Restant Dû (CRD)",
     "CRD fin mois = CRD début − (mensualité − intérêts du mois)",
     "Les intérêts = CRD × 4%/12. Ne s'ajoutent PAS au CRD. Chaque mois, le capital diminue."),
    ("Intérêts annuels",
     "= Σ(CRD début de chaque mois × 4%/12) sur 12 mois",
     f"An 1 : {data[0]['int']:,.0f} € (pas 200 000 € car le capital décroît mois par mois). An 20 : {data[-1]['int']:,.0f} €."),
    ("Déduction IFI (Bofip)",
     "Base IFI nette = 3 500 000 € − CRD fin d'année",
     "Seul le CAPITAL restant est déductible. Les intérêts ne le sont pas. Base fixe (non revalorisée)."),
    ("Déclenchement IFI scénario B",
     "IFI due si base nette ≥ 1 300 000 €  ↔  CRD < 2 200 000 €",
     f"3 500 000 − 1 300 000 = 2 200 000 €. Franchi à l'an {next(d['an'] for d in data if d['ifi_B']>0)}."),
    ("IFI calculée (barème progressif)",
     "Si base ≥ 1,3M€ : IFI = 0,5%×(base−800k) + 0,7%×(base−1,3M) + ...",
     "Assiette rétroactive à 800 000 € dès que le seuil 1 300 000 € est atteint."),
    ("Croissance du placement",
     f"Valeur(N) = {CAPITAL_PLACE:,.0f} × (1,05)^N",
     f"An 20 : {cp_20:,.0f} €. C'est le moteur principal. Le capital n'est jamais touché."),
    ("⚠ Levier net = PAS un flux séparé",
     "Rdt placement − Intérêts = déjà dans la croissance du 5M",
     "Erreur fréquente : réinvestir ce surplus séparément crée un double-comptage. On ne le fait pas."),
    ("Économie IFI (seul vrai flux additionnel)",
     "= IFI(A) − IFI(B)  →  ~20 690 €/an les 13 premières années",
     "Ce cash est réellement économisé vs scénario A. Affiché en cumul brut (sans recapitalisation)."),
    ("Patrimoine net A",
     "= Valeur maison(N) − Σ IFI(A) payée depuis an 1",
     "Pas de patrimoine financier en scénario A (5M€ immobilisés dans la maison)."),
    ("Patrimoine net B",
     "= Valeur maison(N) + Placement(N) − Σ intérêts − Σ IFI(B)",
     "Les charges cumulatives (intérêts, IFI) sont déduites au fil des années."),
    ("Avantage net B vs A",
     f"= Pat.B − Pat.A  →  +{avantage/1e6:.2f}M€ à 20 ans",
     f"= Croissance placement ({(cp_20-CAPITAL_PLACE)/1e6:.2f}M€) − Intérêts ({tot_int/1e6:.2f}M€) + Éco.IFI ({tot_eco/1e3:.0f}k€)"),
]

ws3.column_dimensions['A'].width = 28
ws3.column_dimensions['B'].width = 52
ws3.column_dimensions['C'].width = 60

for ridx, row_data in enumerate(formulas):
    row = ridx + 3
    if ridx == 0:
        bgs   = [C['bleu_h'], C['bleu_h'], C['bleu_h']]
        bolds = [True, True, True]
        colors= ['#FFFFFF', '#FFFFFF', '#FFFFFF']
    else:
        bgs   = [C['gris_l'], '#FFFFFF', '#EFF6FF']
        bolds = [True, False, False]
        colors= ['#0F172A', '#0F172A', '#1D4ED8']
    for col, (val, bg, bld, clr) in enumerate(zip(row_data, bgs, bolds, colors), 1):
        set_cell(ws3, row, col, val, bg=bg, bold=bld, color=clr, size=9, h='left', wrap=True)
    ws3.row_dimensions[row].height = 38

# Tableau de vérification numérique
sep = len(formulas) + 4
ws3.merge_cells(start_row=sep, start_column=1, end_row=sep, end_column=13)
set_cell(ws3, sep, 1,
    "TABLEAU DE VÉRIFICATION NUMÉRIQUE — Toutes les valeurs intermédiaires année par année",
    bg=C['noir'], bold=True, color='#FFFFFF', size=11)
ws3.row_dimensions[sep].height = 24

v_headers = ["An","CRD début","Intérêts","Capital remb.","CRD fin",
             "Rdt placement","IFI (A)","IFI (B)","Éco. IFI",
             "Valeur maison","Placement (val)","Pat. net A","Pat. net B"]
for col, h in enumerate(v_headers, 1):
    set_cell(ws3, sep+1, col, h, bg=C['header2'], bold=True, color='#FFFFFF', size=9, wrap=True)
ws3.row_dimensions[sep+1].height = 32

for idx, d in enumerate(data):
    row  = sep + 2 + idx
    pair = (idx % 2 == 0)
    bg   = C['fond'] if pair else '#FFFFFF'
    bg_b = C['orange'] if d['ifi_B'] > 0 else bg

    vals = [
        (d['an'],       NB,  C['gris_l']),
        (d['crd_d'],    EUR, bg),
        (d['int'],      EUR, bg),
        (d['cap'],      EUR, bg),
        (d['crd_fin'],  EUR, bg),
        (d['cp_fin'],   EUR, bg),
        (d['ifi_A'],    EUR, bg),
        (d['ifi_B'],    EUR, bg_b),
        (d['eco'],      EUR, bg),
        (d['vm_fin'],   EUR, bg),
        (d['cp_fin'],   EUR, bg),
        (d['pat_A'],    EUR, bg),
        (d['pat_B'],    EUR, bg),
    ]
    for col, (val, fmt, bg_c) in enumerate(vals, 1):
        set_cell(ws3, row, col, val, fmt=fmt, bg=bg_c, size=9)
    ws3.row_dimensions[row].height = 17

for i, w in enumerate([5,14,13,14,14,14,13,13,13,14,14,14,14], 1):
    ws3.column_dimensions[get_column_letter(i)].width = w

# ==============================================================================
# SAUVEGARDE
# ==============================================================================
fname = "etude_ifi_cash_vs_emprunt.xlsx"
wb.save(fname)
print(f"✓ Excel généré : {fname}")

# ==============================================================================
# DRAFT EMAIL
# ==============================================================================
email = f"""Objet : Étude comparative — Achat cash vs financement bancaire | Résidence principale 5M€

Bonjour [Prénom],

Suite à notre échange, veuillez trouver ci-joint l'étude comparative préparée pour vous.

──────────────────────────────────────────────────────────────────
LA QUESTION
──────────────────────────────────────────────────────────────────

Vous envisagez l'acquisition de votre résidence principale pour 5 000 000 €.
Vous disposez des liquidités pour acheter cash. La question est :
est-il financièrement plus pertinent d'acheter cash ou de recourir à un emprunt ?

──────────────────────────────────────────────────────────────────
LES HYPOTHÈSES RETENUES
──────────────────────────────────────────────────────────────────

  Bien immobilier      : 5 000 000 € (résidence principale)
  Revalorisation immo  : +2%/an → {vm_20/1e6:.2f}M€ à 20 ans
  Base IFI             : 3 500 000 € fixe (5M€ × 70%, abattement RP)
  Emprunt              : 5 000 000 € à 4% fixe sur 20 ans
  Mensualité           : {mens:,.0f} €/mois (payée depuis vos autres revenus)
  Placement            : 5 000 000 € en assurance-vie à 5% composé, 0% fiscalité
  Service de la dette  : vos autres revenus — le placement n'est jamais touché

──────────────────────────────────────────────────────────────────
LES 3 EFFETS DU FINANCEMENT BANCAIRE
──────────────────────────────────────────────────────────────────

1. PROTECTION IFI PENDANT 13 ANS
   La dette vient en déduction de votre base taxable IFI (règle Bofip).
   Tant que le Capital Restant Dû dépasse 2 200 000 €, votre base nette
   reste sous le seuil de 1 300 000 € → IFI = 0 €.
   → Économie : 20 690 €/an pendant 13 ans, puis décroissante.
   → Total économisé sur 20 ans : {tot_eco/1e3:.0f}k€.

2. CROISSANCE DU CAPITAL PRÉSERVÉ
   En n'immobilisant pas vos 5M€ dans l'achat, vous les placez à 5% composé.
   → 5M€ → {cp_20/1e6:.2f}M€ à 20 ans (sans fiscalité en cours de capitalisation).
   → Gain net du placement : +{(cp_20-CAPITAL_PLACE)/1e6:.2f}M€.

3. COÛT RÉEL DU CRÉDIT
   Les intérêts payés sur 20 ans (calculés mensuellement) s'élèvent à {tot_int/1e6:.2f}M€.
   Ce montant vient en déduction du bénéfice final.

──────────────────────────────────────────────────────────────────
RÉSULTAT À 20 ANS
──────────────────────────────────────────────────────────────────

  SCÉNARIO A — ACHAT CASH
    Maison revalorisée       : {vm_20/1e6:.2f}M€
    IFI payée (20 ans)       : −{tot_ifi_A/1e3:.0f}k€
    Patrimoine net           : {pat_A_net/1e6:.2f}M€

  SCÉNARIO B — EMPRUNT 4% / 20 ANS
    Maison revalorisée       : {vm_20/1e6:.2f}M€  (identique)
    Placement 5M€ → 20 ans   : {cp_20/1e6:.2f}M€
    Intérêts payés           : −{tot_int/1e6:.2f}M€
    IFI payée (20 ans)       : −{tot_ifi_B/1e3:.0f}k€
    Patrimoine net           : {pat_B_net/1e6:.2f}M€

  AVANTAGE NET DU FINANCEMENT : +{avantage/1e6:.2f}M€

  Décomposition :
    + Gain placement (5M→{cp_20/1e6:.2f}M€)   : +{(cp_20-CAPITAL_PLACE)/1e6:.2f}M€
    − Intérêts payés                : −{tot_int/1e6:.2f}M€
    + Économie IFI nette            : +{tot_eco/1e3:.0f}k€
    ───────────────────────────────────────
    = AVANTAGE NET                  : +{avantage/1e6:.2f}M€

──────────────────────────────────────────────────────────────────

Vous trouverez en pièce jointe le fichier Excel avec :
  • Onglet 1 : hypothèses (modifiables selon vos paramètres)
  • Onglet 2 : tableau comparatif année par année
  • Onglet 3 : détail de chaque formule et tableau de vérification

Je reste disponible pour échanger sur ces résultats.

Bien cordialement,
[Votre nom]
"""

with open("draft_email.txt", "w", encoding="utf-8") as f:
    f.write(email)
print("✓ Draft email : draft_email.txt")
print(email)
