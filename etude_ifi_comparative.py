"""
ÉTUDE COMPARATIVE : ACHAT CASH vs EMPRUNT AMORTISSABLE
Résidence principale 5 000 000 € — Horizon 20 ans

Hypothèses validées :
  Maison        : 5 000 000 € (RP, abattement IFI 30% → base taxable 3 500 000 €)
  Emprunt       : 5 000 000 € à 4% fixe, amortissable sur 20 ans
  Placement     : 5 000 000 € à 5% composé, capitalisé en assurance-vie (0% fiscalité)
  Service dette : payé depuis autres revenus du client → capital placé INTOUCHÉ
  IFI           : barème légal 2024, seuil déclenchement 1 300 000 €
                  assiette rétroactive à 800 000 € (effet de seuil)
  Déduction IFI : capital restant dû uniquement (cf. Bofip BOI-PAT-IFI-20-30-30)
                  → les intérêts NE sont PAS déductibles du patrimoine IFI
                  → CRD = encours en capital au 1er janvier de l'année IFI

ARCHITECTURE DU BÉNÉFICE ANNUEL (Scénario B vs A) :

  ┌─────────────────────────────────────────────────────────────────┐
  │  COMPOSANTE 1 : EFFET DE LEVIER NET                             │
  │  = Rendement placement (5M capitalisé × 5%)                     │
  │  − Intérêts payés sur le prêt (décroissants au fil du temps)   │
  │  → Positif dès l'an 1, CROISSANT car :                          │
  │     • la base de placement grossit (intérêts composés)          │
  │     • les intérêts du prêt diminuent (amortissement)            │
  │                                                                  │
  │  COMPOSANTE 2 : ÉCONOMIE D'IFI                                  │
  │  = IFI que le client paierait en achat cash (20 690 €/an fixe)  │
  │  − IFI réellement due en scénario emprunt (0 € jusqu'à l'an 14) │
  │  → 20 690 €/an économisés de l'an 1 à l'an 13 inclus            │
  │  → Décroissante à partir de l'an 14 (IFI B se déclenche)       │
  │                                                                  │
  │  FLUX TOTAL RÉINVESTI = Composante 1 + Composante 2             │
  │  → Capitalisé à 5%/an dans la même enveloppe assurance-vie      │
  └─────────────────────────────────────────────────────────────────┘
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

# Barème IFI 2024
# Seuil de déclenchement : 1 300 000 €
# Assiette rétroactive   : à partir de 800 000 € (si seuil atteint)
IFI_SEUIL     = 1_300_000
IFI_FRANCHISE = 800_000
IFI_BAREME = [
    (800_000,    1_300_000,  0.005),
    (1_300_000,  2_570_000,  0.007),
    (2_570_000,  5_000_000,  0.010),
    (5_000_000,  10_000_000, 0.0125),
    (10_000_000, float('inf'), 0.015),
]

# ==============================================================================
# FONCTIONS
# ==============================================================================

def calcul_ifi(base_nette: float) -> float:
    """
    IFI annuel sur une base nette taxable.
    Règle : si base < 1 300 000 € → IFI = 0 (seuil non atteint).
             si base ≥ 1 300 000 € → impôt calculé À PARTIR de 800 000 €.
    """
    if base_nette < IFI_SEUIL:
        return 0.0
    ifi = 0.0
    for (bas, haut, taux) in IFI_BAREME:
        if base_nette <= bas:
            break
        ifi += (min(base_nette, haut) - bas) * taux
    return ifi


def tableau_amortissement_annuel():
    """
    Retourne (mensualité, liste_annuelle).
    Chaque élément : crd_debut, interets_annee, capital_annee, crd_fin.
    Le CRD est l'encours EN CAPITAL uniquement (les intérêts sont une charge,
    ils ne s'ajoutent pas au solde → conforme Bofip pour déduction IFI).
    """
    r = TAUX_EMPRUNT / 12
    mensualite = MONTANT_EMPRUNT * r / (1 - (1 + r) ** (-DUREE_MOIS))

    crd = MONTANT_EMPRUNT
    annees = []
    for annee in range(1, DUREE_ANS + 1):
        crd_debut = crd
        interets_an = 0.0
        capital_an  = 0.0
        for _ in range(12):
            interet_mois = crd * r
            capital_mois = mensualite - interet_mois
            interets_an += interet_mois
            capital_an  += capital_mois
            crd = max(0.0, crd - capital_mois)
        annees.append({
            'crd_debut': crd_debut,
            'interets':  interets_an,
            'capital':   capital_an,
            'crd_fin':   crd,
        })
    return mensualite, annees


# ==============================================================================
# MODÈLE PRINCIPAL
# ==============================================================================

def run():
    mensualite, amort = tableau_amortissement_annuel()
    annuite = mensualite * 12

    L = "═" * 155
    l = "─" * 155

    # ──────────────────────────────────────────────────────────────────────────
    # EN-TÊTE
    # ──────────────────────────────────────────────────────────────────────────
    print(L)
    print("  ÉTUDE COMPARATIVE : ACHAT CASH (A) vs EMPRUNT 4% / 20 ANS (B)")
    print("  Résidence principale 5 000 000 € — Horizon 20 ans")
    print(L)
    print(f"""
  HYPOTHÈSES VALIDÉES
  ┌{'─'*60}┐
  │  Valeur maison (résidence principale)   5 000 000 €     │
  │  Base IFI (abattement 30%)              3 500 000 €     │
  │  Montant emprunté                       5 000 000 €     │
  │  Taux d'emprunt                              4,00 %     │
  │  Durée                                       20 ans     │
  │  Mensualité                            {mensualite:>10,.0f} €     │
  │  Annuité totale (K + I)                {annuite:>10,.0f} €/an  │
  │  Capital placé (intouché)               5 000 000 €     │
  │  Rendement placement                         5,00 %     │
  │  Capitalisation (assurance-vie)       Sans fiscalité    │
  │  Service de la dette                  Autres revenus    │
  └{'─'*60}┘

  NOTE SUR LE CAPITAL RESTANT DÛ (CRD) ET L'IFI
  Le Bofip (BOI-PAT-IFI-20-30-30) précise que seul l'encours EN CAPITAL
  est déductible du patrimoine immobilier brut pour le calcul de l'IFI.
  Les intérêts sont une charge annuelle et n'entrent PAS dans le CRD.
  → Dans ce modèle, le CRD utilisé = capital amortissable restant au 31/12
    de l'année N, servant de base pour l'IFI au 1er janvier de l'année N+1.
""")

    # ──────────────────────────────────────────────────────────────────────────
    # TABLEAU DÉTAILLÉ
    # ──────────────────────────────────────────────────────────────────────────
    print(l)
    print("  TABLEAU DÉTAILLÉ ANNÉE PAR ANNÉE")
    print(l)

    # En-têtes sur 2 lignes pour lisibilité
    h1 = (
        f"{'':>4}"
        f"{'── PRÊT AMORTISSABLE ──────────────────':>42}"
        f"{'── PLACEMENT 5M ──────────────────':>36}"
        f"{'── COMPOSANTE 1 ──':>20}"
        f"{'── COMPOSANTE 2 ──────────':>28}"
        f"{'── FLUX TOTAL ──────────────────────────':>40}"
    )
    h2 = (
        f"  {'An':>2}  "
        f"{'CRD début':>12}  {'Intérêts':>10}  {'Capital':>10}  {'CRD fin':>12}  "
        f"{'Base (début)':>12}  {'Rdt 5%':>10}  {'Val (fin)':>12}  "
        f"{'Lvr net':>10}  {'Expl.':>8}  "
        f"{'IFI (A)':>9}  {'Base IFI(B)':>11}  {'IFI (B)':>9}  {'Éco IFI':>9}  "
        f"{'Flux/an':>10}  {'Cumul 5%':>12}  {'Statut'}"
    )
    print(h1)
    print(h2)
    print(l)

    capital_place  = CAPITAL_PLACE_INIT
    cumul_reinvest = 0.0

    total_ifi_A    = 0.0
    total_ifi_B    = 0.0
    total_interets = 0.0

    resultats = []

    for annee in range(1, DUREE_ANS + 1):
        a = amort[annee - 1]

        # Placement : rendement sur la valeur en début d'année
        rdt_placement     = capital_place * TAUX_PLACEMENT
        capital_place_fin = capital_place * (1 + TAUX_PLACEMENT)

        # ── COMPOSANTE 1 : Effet de levier net ──────────────────────────────
        # Rendement financier généré par le placement
        # moins le coût des intérêts payés sur le prêt
        levier_net = rdt_placement - a['interets']
        explication_levier = f"{rdt_placement:,.0f}-{a['interets']:,.0f}"

        # ── COMPOSANTE 2 : Économie d'IFI ───────────────────────────────────
        # Scénario A : IFI sur base fixe 3 500 000 €
        ifi_A = calcul_ifi(BASE_IFI_MAISON)

        # Scénario B : IFI sur base nette = 3 500 000 € - CRD fin d'année
        # (le CRD est l'encours capital uniquement, conforme Bofip)
        base_ifi_B = BASE_IFI_MAISON - a['crd_fin']
        ifi_B      = calcul_ifi(base_ifi_B)

        eco_ifi = ifi_A - ifi_B   # économie positive tant que IFI_B < IFI_A

        # ── FLUX TOTAL RÉINVESTI ─────────────────────────────────────────────
        flux_reinvesti = levier_net + eco_ifi

        # Capitalisation à 5% : le cumul de l'an précédent grossit, puis on ajoute le flux
        cumul_reinvest = cumul_reinvest * (1 + TAUX_PLACEMENT) + flux_reinvesti

        # Cumuls globaux
        total_ifi_A    += ifi_A
        total_ifi_B    += ifi_B
        total_interets += a['interets']

        resultats.append({
            'annee': annee,
            'a': a,
            'capital_place': capital_place,
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

        # Statut IFI
        prev_ifi_B = resultats[-2]['ifi_B'] if annee > 1 else 0
        if ifi_B == 0:
            statut = "✓ Pas d'IFI — dette couvre"
        elif prev_ifi_B == 0:
            statut = "◄ IFI B se DÉCLENCHE ici"
        else:
            statut = f"⚠  IFI progressive"

        print(
            f"  {annee:>2}  "
            f"{a['crd_debut']:>12,.0f}  {a['interets']:>10,.0f}  {a['capital']:>10,.0f}  {a['crd_fin']:>12,.0f}  "
            f"{capital_place:>12,.0f}  {rdt_placement:>10,.0f}  {capital_place_fin:>12,.0f}  "
            f"{levier_net:>10,.0f}  {explication_levier:>8}  "
            f"{ifi_A:>9,.0f}  {base_ifi_B:>11,.0f}  {ifi_B:>9,.0f}  {eco_ifi:>9,.0f}  "
            f"{flux_reinvesti:>10,.0f}  {cumul_reinvest:>12,.0f}  {statut}"
        )

        capital_place = capital_place_fin

    print(l)

    # ──────────────────────────────────────────────────────────────────────────
    # LÉGENDE DU TABLEAU
    # ──────────────────────────────────────────────────────────────────────────
    print(f"""
  LÉGENDE DES COLONNES
  ┌{'─'*110}┐
  │  PRÊT AMORTISSABLE                                                                                            │
  │    CRD début / fin  : Capital Restant Dû (encours en capital UNIQUEMENT, hors intérêts → déductible IFI)    │
  │    Intérêts         : charge annuelle payée, NON déductible IFI (Bofip BOI-PAT-IFI-20-30-30)                │
  │    Capital remb.    : fraction du capital amortie dans l'année                                               │
  │                                                                                                               │
  │  COMPOSANTE 1 — EFFET DE LEVIER NET                                                                          │
  │    Rdt 5%           : rendement du placement 5M sur la valeur en début d'année (grossit par capitalisation) │
  │    Lvr net          : Rdt 5% − Intérêts payés = gain annuel généré par la stratégie d'endettement           │
  │    Expl.            : décomposition rapide (rendement − intérêts)                                            │
  │    → Croissant car : (1) la base de placement grossit à 5% composé                                          │
  │                      (2) les intérêts du prêt diminuent au fil de l'amortissement                           │
  │                                                                                                               │
  │  COMPOSANTE 2 — ÉCONOMIE D'IFI                                                                               │
  │    IFI (A)          : IFI payée en scénario cash (base 3 500 000 € fixe = 20 690 €/an)                      │
  │    Base IFI (B)     : base nette scénario emprunt = 3 500 000 € − CRD fin                                   │
  │                       (négative = dette > base → 0 IFI, pas de patrimoine net taxable)                      │
  │    IFI (B)          : IFI due en scénario emprunt (0 jusqu'à l'an 13 inclus)                                │
  │    Éco IFI          : IFI(A) − IFI(B) = économie annuelle grâce à la dette                                  │
  │                                                                                                               │
  │  FLUX TOTAL RÉINVESTI                                                                                         │
  │    Flux/an          : Levier net + Économie IFI = flux annuel généré par la stratégie                        │
  │    Cumul 5%         : capitalisation de ces flux à 5% (compte séparé, même enveloppe assurance-vie)         │
  └{'─'*110}┘
""")

    # ──────────────────────────────────────────────────────────────────────────
    # ZOOM IFI
    # ──────────────────────────────────────────────────────────────────────────
    print("═" * 90)
    print("  ZOOM — DÉCLENCHEMENT PROGRESSIF DE L'IFI EN SCÉNARIO B")
    print("═" * 90)
    print(f"""
  Règle IFI rappel :
    • Si patrimoine net taxable < 1 300 000 €  →  IFI = 0 (seuil non atteint)
    • Si patrimoine net taxable ≥ 1 300 000 €  →  IFI calculée À PARTIR de 800 000 €
      (effet de seuil : on "remonte" à 800 000 €, d'où les 20 690 €/an pour 3 500 000 €)

  Condition de déclenchement IFI en scénario B :
    3 500 000 € − CRD fin > 1 300 000 €
    ↔  CRD fin < 2 200 000 €  ←  seuil à surveiller
""")
    print(f"  {'An':>3}  {'CRD fin':>13}  {'Base IFI B':>13}  {'IFI B':>10}  {'IFI A':>10}  {'Éco IFI':>10}  Statut")
    print(f"  {'─'*3}  {'─'*13}  {'─'*13}  {'─'*10}  {'─'*10}  {'─'*10}  {'─'*35}")
    for r in resultats:
        crd_fin = r['a']['crd_fin']
        marker  = " ← CRD passe sous 2 200 000 €" if (crd_fin < 2_200_000 and
                  (r['annee'] == 1 or resultats[r['annee']-2]['a']['crd_fin'] >= 2_200_000)) else ""
        statut  = "✓ Protégé — aucune IFI" if r['ifi_B'] == 0 else f"⚠  IFI due ({r['ifi_B']:,.0f} €)"
        print(f"  {r['annee']:>3}  {crd_fin:>13,.0f}  {r['base_ifi_B']:>13,.0f}  "
              f"{r['ifi_B']:>10,.0f}  {r['ifi_A']:>10,.0f}  {r['eco_ifi']:>10,.0f}  {statut}{marker}")

    # ──────────────────────────────────────────────────────────────────────────
    # SYNTHÈSE FINALE
    # ──────────────────────────────────────────────────────────────────────────
    val_place_20  = resultats[-1]['capital_place_fin']
    cumul_renv_20 = resultats[-1]['cumul_reinvest']
    eco_ifi_tot   = total_ifi_A - total_ifi_B
    gain_place    = val_place_20 - CAPITAL_PLACE_INIT
    avantage_net  = gain_place + cumul_renv_20 - total_interets + eco_ifi_tot

    print(f"""
{'═'*90}
  SYNTHÈSE FINANCIÈRE À 20 ANS
{'═'*90}

  ┌{'─'*86}┐
  │  SCÉNARIO A — ACHAT CASH                                                             │
  │    IFI payée chaque année      :   20 690 €/an  (base 3 500 000 € fixe, invariable) │
  │    IFI payée sur 20 ans        :  {total_ifi_A:>10,.0f} €                                    │
  │    Patrimoine financier final  :           0 €  (5M engagés dans la maison dès J+1) │
  ├{'─'*86}┤
  │  SCÉNARIO B — EMPRUNT AMORTISSABLE 4% / 20 ANS                                      │
  │    IFI protégée (ans 1 à 13)   :          13 ans  → IFI = 0 € pendant 13 ans        │
  │    IFI déclenchée (ans 14–20)  :       7 ans  (montants progressifs)                │
  │    IFI payée sur 20 ans        :  {total_ifi_B:>10,.0f} €                                    │
  │    Total intérêts payés        :  {total_interets:>10,.0f} €                                    │
  │                                                                                      │
  │    Placement 5M après 20 ans   :  {val_place_20:>10,.0f} €  (5 000 000 × 1,05^20)            │
  │    Cumul flux réinvestis à 5%  :  {cumul_renv_20:>10,.0f} €                                    │
  │    Patrimoine financier total  :  {val_place_20 + cumul_renv_20:>10,.0f} €                                    │
  ├{'─'*86}┤
  │  AVANTAGE NET SCÉNARIO B vs A — DÉCOMPOSÉ                                           │
  │                                                                                      │
  │    [1] Croissance placement 5M (hors capital de départ)                             │
  │        5 000 000 → {val_place_20:,.0f} €                                   │
  │        Gain net           :  {gain_place:>10,.0f} €                                    │
  │                                                                                      │
  │    [2] Flux (levier + IFI éco) capitalisés à 5% sur 20 ans                         │
  │        Gain net           :  {cumul_renv_20:>10,.0f} €                                    │
  │                                                                                      │
  │    [3] Coût des intérêts payés sur le prêt                                          │
  │        Charge nette       :  {-total_interets:>10,.0f} €                                    │
  │                                                                                      │
  │    [4] Économie d'IFI nette sur 20 ans                                              │
  │        (413 800 € − {total_ifi_B:,.0f} €)                                           │
  │        Gain net           :  {eco_ifi_tot:>10,.0f} €                                    │
  │                                                                                      │
  │    ═══════════════════════════════════════════════════                               │
  │    AVANTAGE NET TOTAL     :  {avantage_net:>10,.0f} €                                    │
  └{'─'*86}┘

  BARÈME IFI 2024 (pour référence)
    0 %    de          0 à    800 000 €
    0,5 %  de    800 000 à  1 300 000 €  ← seuil déclenchement (effet rétroactif à 800 000 €)
    0,7 %  de  1 300 000 à  2 570 000 €
    1,0 %  de  2 570 000 à  5 000 000 €
    1,25 % de  5 000 000 à 10 000 000 €
    1,5 %  au-delà de 10 000 000 €
""")


if __name__ == "__main__":
    run()
