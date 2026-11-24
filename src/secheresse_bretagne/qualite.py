"""Contrôles bloquants : aucune table n'est publiée si l'un d'eux échoue."""

from __future__ import annotations

import pandas as pd

CLES = {
    "dim_commune": ["code_commune"],
    "dim_departement": ["code_departement"],
    "dim_mois": ["mois"],
    "fact_restrictions_mois": ["code_commune", "mois"],
    "fact_nappes_mois": ["code_departement", "mois"],
}


def controler(tables: dict[str, pd.DataFrame], jours_par_mois: pd.Series) -> None:
    """`jours_par_mois` : jours comptés (vigilance comprise) par commune et par mois."""
    erreurs: list[str] = []
    for nom, cles in CLES.items():
        if tables[nom].duplicated(cles).any():
            erreurs.append(f"{nom} : clé dupliquée {cles}")

    connues = set(tables["dim_commune"].code_commune)
    orphelins = set(tables["fact_restrictions_mois"].code_commune) - connues
    if orphelins:
        erreurs.append(f"fact_restrictions_mois : {len(orphelins)} communes hors référentiel")

    calendrier = set(tables["dim_mois"].mois)
    for nom in ("fact_restrictions_mois", "fact_nappes_mois"):
        if not set(tables[nom].mois) <= calendrier:
            erreurs.append(f"{nom} : mois absent du calendrier")

    mois = tables["fact_restrictions_mois"].mois
    if (jours_par_mois.to_numpy() > mois.dt.days_in_month.to_numpy()).any():
        erreurs.append("fact_restrictions_mois : plus de jours que le mois n'en compte")

    centiles = tables["fact_nappes_mois"].percentile_median
    if centiles.isna().any() or not centiles.between(0, 100).all():
        erreurs.append("fact_nappes_mois : centile manquant ou hors de [0, 100]")

    coordonnees = tables["dim_commune"][["longitude", "latitude"]]
    if coordonnees.isna().any().any():
        erreurs.append("dim_commune : commune sans coordonnées")

    if erreurs:
        raise ValueError("Contrôles qualité en échec :\n- " + "\n- ".join(erreurs))
    print(f"contrôles qualité : {len(CLES) + 5} familles de contrôles validées")
