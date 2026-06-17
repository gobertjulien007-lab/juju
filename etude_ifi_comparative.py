"""
ÉTUDE COMPARATIVE : ACHAT CASH vs EMPRUNT AMORTISSABLE
Contexte : Résidence principale à 5 000 000 €, client à fort patrimoine.
Question : vaut-il mieux acheter cash ou s'endetter pour conserver son capital investi ?

Hypothèses de travail validées :
  - Maison        : 5 000 000 € (résidence principale, abattement IFI 30% → base 3 500 000 €)
  - Emprunt       : 5 000 000 € à 4% fixe, amortissable sur 20 ans
  - Placement     : 5 000 000 € à 5% composé, capitalisé (assurance-vie, sans fiscalité)
  - Service dette : payé depuis autres revenus du client → capital placé INTOUCHÉ
  - IFI           : barème légal 2024, seuil 1 300 000 €, assiette rétroactive à 800 000 €
  - Flux réinvesti: (levier net + économie IFI) capitalisé à 5% dès l'année 1
"""

# ==============================================================================
# HYPOTHÈSES
# ==============================================================================

VALEUR_MAISON       = 5_000_000
ABATTEMENT_RP       = 0.30
BASE_IFI_MAISON     = VALEUR_MAISON * (1 - ABATTEMENT_RP)   # 3 500 000 €

MONTANT_EMPRUNT     = 5_000_000
TAUX_EMPRUNT        = 0.04
DUREE_ANS           = 20
DUREE_MOIS          = DUREE_ANS * 12

TAUX_PLACEMENT      = 0.05
CAPITAL_PLACE_INIT  = 5_000_000

# Barème IFI 2024 (seuil déclenchement : 1 300 000 €, base taxable à partir de 800 000 €)
IFI_SEUIL   = 1_300_000
IFI_FRANCHISE = 800_000
IFI_BAREME  = [
    (800_000,   1_300_000,  0.005),
    (1_300_000, 2_570_000,  0.007),
    (2_570_000, 5_000_000,  0.010),
    (5_000_000, 10_000_000, 0.0125),
    (10_000_000, float('inf'), 0.015),
]

# ==============================================================================
# FONCTIONS
# ==============================================================================

def calcul_ifi(base_nette: float) -> float:
    """IFI annuel sur une base nette taxable.
    Si base < 1 300 000 € : IFI = 0 (seuil non atteint).
    Si base >= 1 300 000 € : impôt calculé à partir de 800 000 € (effet rétroactif).
    """
    if base_nette < IFI_SEUIL:
        return 0.0
    ifi = 0.0
    for (bas, haut, taux) in IFI_BAREME:
        if base_nette <= bas:
            break
        tranche = min(base_nette, haut) - bas
        ifi += tranche * taux
    return ifi


def tableau_amortissement():
    """Tableau mensuel : CRD, intérêts, capital remboursé."""
    r = TAUX_EMPRUNT / 12
    n = DUREE_MOIS
    mensualite = MONTANT_EMPRUNT * r / (1 - (1 + r) ** (-n))

    lignes = []
    crd = MONTANT_EMPRUNT
    for m in range(1, n + 1):
        interet  = crd * r
        capital  = mensualite - interet
        crd_fin  = max(0.0, crd - capital)
        lignes.append({
            'mois': m,
            'crd_debut': crd,
            'interet': interet,
            'capital': capital,
            'crd_fin': crd_fin,
        })
        crd = crd_fin
    return mensualite, lignes


# ==============================================================================
# MODÈLE ANNUEL
# ==============================================================================

def formater(v, decimales=0):
    if decimales == 0:
        return f"{v:>13,.0f} €"
    return f"{v:>13,.{decimales}f} €"


def run():
    mensualite, tab_mensuel = tableau_amortissement()
    annuite = mensualite * 12

    sep  = "─" * 200
    sep2 = "═" * 200

    print(sep2)
    print("  ÉTUDE COMPARATIVE : ACHAT CASH vs EMPRUNT AMORTISSABLE  │  Résidence principale 5 000 000 €")
    print(sep2)

    print(f"""
HYPOTHÈSES
  Valeur maison (RP)          : {VALEUR_MAISON:>13,.0f} €
  Base IFI (après abatt. 30%) : {BASE_IFI_MAISON:>13,.0f} €
  Montant emprunté            : {MONTANT_EMPRUNT:>13,.0f} €
  Taux emprunt                :          4,00 %  fixe
  Durée                       :          20 ans  amortissable
  Mensualité                  : {mensualite:>13,.0f} €/mois
  Annuité (capital + intérêts): {annuite:>13,.0f} €/an  ← payée depuis autres revenus
  Capital placé (intouché)    : {CAPITAL_PLACE_INIT:>13,.0f} €
  Rendement placement         :           5,00 %  composé, capitalisation assurance-vie
  Fiscalité sur placement     :          0 %  (pas de prélèvements pendant la capitalisation)
""")

    # En-têtes du tableau détaillé
    cols = (
        f"{'An':>3}",
        f"{'CRD début':>13}",
        f"{'Intérêts':>12}",
        f"{'Capital remb.':>13}",
        f"{'CRD fin':>13}",
        f"{'Rdt placement':>13}",
        f"{'Levier net':>12}",
        f"{'IFI Scenario A':>14}",
        f"{'Base IFI B':>13}",
        f"{'IFI Scénario B':>14}",
        f"{'Écon. IFI':>11}",
        f"{'Flux réinv.':>12}",
        f"{'Cumul réinv.':>13}",
        f"{'Placement val':>14}",
    )
    entete = " │ ".join(cols)
    print(sep)
    print(entete)
    print(sep)

    # Suivi
    capital_place   = CAPITAL_PLACE_INIT   # grossit à 5% composé chaque année
    cumul_reinvest  = 0.0                  # compte des flux réinvestis, grossit aussi à 5%

    total_ifi_A     = 0.0
    total_ifi_B     = 0.0
    total_interets  = 0.0
    total_levier    = 0.0

    resultats = []

    for annee in range(1, DUREE_ANS + 1):
        i0 = (annee - 1) * 12   # index premier mois de l'année
        i1 = annee * 12         # index exclusif

        crd_debut = tab_mensuel[i0]['crd_debut']
        crd_fin   = tab_mensuel[i1 - 1]['crd_fin']

        interets_an   = sum(tab_mensuel[m]['interet']  for m in range(i0, i1))
        capital_remb  = sum(tab_mensuel[m]['capital']  for m in range(i0, i1))

        # Rendement du placement (calculé sur la valeur EN DÉBUT D'ANNÉE)
        rdt_placement = capital_place * TAUX_PLACEMENT
        # Puis on capitalise : valeur en fin d'année
        capital_place_fin = capital_place * (1 + TAUX_PLACEMENT)

        # Effet de levier net (année par année)
        # = revenu financier généré - coût des intérêts payés
        levier_net = rdt_placement - interets_an

        # ── Scénario A (cash) : base IFI fixe = 3 500 000 €
        ifi_A = calcul_ifi(BASE_IFI_MAISON)

        # ── Scénario B (emprunt) : base IFI = 3 500 000 € - CRD fin d'année
        # (la dette vient en déduction du patrimoine immobilier brut)
        base_ifi_B = BASE_IFI_MAISON - crd_fin
        ifi_B      = calcul_ifi(base_ifi_B)

        # Économie d'IFI grâce à la dette (peut devenir négative si IFI_B > IFI_A)
        eco_ifi = ifi_A - ifi_B

        # Flux réinvesti cette année = levier net + économie IFI
        flux_reinvesti = levier_net + eco_ifi

        # Cumul réinvestissement : le stock précédent grossit à 5%, puis on ajoute le flux
        cumul_reinvest = cumul_reinvest * (1 + TAUX_PLACEMENT) + flux_reinvesti

        # Cumuls
        total_ifi_A    += ifi_A
        total_ifi_B    += ifi_B
        total_interets += interets_an
        total_levier   += levier_net

        resultats.append({
            'annee': annee,
            'crd_debut': crd_debut, 'crd_fin': crd_fin,
            'interets': interets_an, 'capital_remb': capital_remb,
            'capital_place_debut': capital_place,
            'rdt_placement': rdt_placement,
            'capital_place_fin': capital_place_fin,
            'levier_net': levier_net,
            'ifi_A': ifi_A,
            'base_ifi_B': base_ifi_B,
            'ifi_B': ifi_B,
            'eco_ifi': eco_ifi,
            'flux_reinvesti': flux_reinvesti,
            'cumul_reinvest': cumul_reinvest,
        })

        # Signalement du déclenchement IFI en scénario B
        flag = ""
        if ifi_B > 0 and (annee == 1 or resultats[-2]['ifi_B'] == 0):
            flag = "  ◄ IFI B se DÉCLENCHE"
        elif ifi_B == 0 and annee > 1 and resultats[-2]['ifi_B'] == 0:
            flag = ""

        ligne = " │ ".join([
            f"{annee:>3}",
            f"{crd_debut:>13,.0f}",
            f"{interets_an:>12,.0f}",
            f"{capital_remb:>13,.0f}",
            f"{crd_fin:>13,.0f}",
            f"{rdt_placement:>13,.0f}",
            f"{levier_net:>12,.0f}",
            f"{ifi_A:>14,.0f}",
            f"{base_ifi_B:>13,.0f}",
            f"{ifi_B:>14,.0f}",
            f"{eco_ifi:>11,.0f}",
            f"{flux_reinvesti:>12,.0f}",
            f"{cumul_reinvest:>13,.0f}",
            f"{capital_place_fin:>14,.0f}",
        ])
        print(ligne + flag)

        # On avance le capital place au début de l'année suivante
        capital_place = capital_place_fin

    print(sep)

    # ──────────────────────────────────────────────────────────────────────────
    # SYNTHÈSE FINALE
    # ──────────────────────────────────────────────────────────────────────────
    val_place_20   = resultats[-1]['capital_place_fin']
    cumul_renv_20  = resultats[-1]['cumul_reinvest']
    eco_ifi_totale = total_ifi_A - total_ifi_B

    # Avantage net B vs A à 20 ans :
    # B possède : placement 5M capitalisé + cumul flux réinvestis
    # B a payé  : intérêts (remboursements capital depuis autres revenus, hors scope)
    # A possède : rien de financier (5M utilisés pour la maison)
    # A a payé  : IFI pendant 20 ans
    # Delta : (val_place_20 - 5M) + cumul_renv_20 - total_interets + eco_ifi_totale
    # (val_place_20 - 5M) = la croissance nette du capital initialement préservé

    gain_place    = val_place_20 - CAPITAL_PLACE_INIT
    avantage_net  = gain_place + cumul_renv_20 - total_interets + eco_ifi_totale

    print(f"""
{'═'*80}
  SYNTHÈSE À 20 ANS
{'═'*80}

SCÉNARIO A — ACHAT CASH
  IFI payé chaque année       : {resultats[0]['ifi_A']:>13,.0f} €/an  (base 3 500 000 €, invariable)
  IFI payé sur 20 ans         : {total_ifi_A:>13,.0f} €
  Patrimoine financier        :               0 €  (5M engagés dans la maison dès J+1)

SCÉNARIO B — EMPRUNT AMORTISSABLE 4% / 20 ANS
  Mensualité                  : {mensualite:>13,.0f} €/mois  (payée hors placement)
  Total intérêts payés        : {total_interets:>13,.0f} €
  IFI payé sur 20 ans         : {total_ifi_B:>13,.0f} €
  Valeur placement (5M→20 ans): {val_place_20:>13,.0f} €  (5M × 1.05^20)
  Cumul flux réinvestis à 5%  : {cumul_renv_20:>13,.0f} €
  Patrimoine financier total  : {val_place_20 + cumul_renv_20:>13,.0f} €

{'─'*80}
  DÉTAIL DE L'AVANTAGE NET (B vs A)
{'─'*80}
  + Croissance placement 5M   : {gain_place:>13,.0f} €  (5M → {val_place_20:,.0f} €)
  + Flux réinvestis capitalisés: {cumul_renv_20:>13,.0f} €
  − Intérêts payés            : {-total_interets:>13,.0f} €
  + Économie IFI nette (20 ans): {eco_ifi_totale:>13,.0f} €
{'─'*80}
  = AVANTAGE NET SCÉNARIO B   : {avantage_net:>13,.0f} €
{'═'*80}
""")

    # Tableau récapitulatif IFI
    print(f"{'─'*80}")
    print(f"  ZOOM — IFI SCÉNARIO B : déclenchement progressif")
    print(f"{'─'*80}")
    print(f"  {'An':>3}  {'CRD fin':>13}  {'Base IFI B':>13}  {'IFI B':>10}  {'Statut'}")
    print(f"  {'─'*3}  {'─'*13}  {'─'*13}  {'─'*10}  {'─'*30}")
    for r in resultats:
        statut = "✓ Pas d'IFI (dette couvre)" if r['ifi_B'] == 0 else f"⚠ IFI due : {r['ifi_B']:,.0f} €"
        print(f"  {r['annee']:>3}  {r['crd_fin']:>13,.0f}  {r['base_ifi_B']:>13,.0f}  {r['ifi_B']:>10,.0f}  {statut}")
    print()

    print(f"  Rappel barème IFI 2024 :")
    print(f"    0 %    de         0 à   800 000 €")
    print(f"    0,5 %  de   800 000 à 1 300 000 €  ← seuil de déclenchement (effet rétroactif)")
    print(f"    0,7 %  de 1 300 000 à 2 570 000 €")
    print(f"    1,0 %  de 2 570 000 à 5 000 000 €")
    print(f"    1,25%  de 5 000 000 à 10 000 000 €")
    print(f"    1,5 %  au-delà de 10 000 000 €")
    print()


if __name__ == "__main__":
    run()
