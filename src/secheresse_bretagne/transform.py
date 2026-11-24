"""Calcul des indicateurs. Fonctions pures, testées unitairement."""

from __future__ import annotations

import pandas as pd

from .config import GRAVITE

NIVEAUX = ["jours_vigilance", "jours_alerte", "jours_alerte_renforcee", "jours_crise"]


def jours_par_niveau(restrictions: pd.DataFrame) -> pd.DataFrame:
    """Niveau quotidien d'une commune : le plus sévère parmi les ressources AEP, SOU et SUP."""
    df = restrictions.copy()
    niveaux = df[["AEP", "SOU", "SUP"]].apply(lambda c: c.map(GRAVITE)).fillna(0)
    df["niveau"] = niveaux.max(axis=1).astype(int)
    df["date"] = pd.to_datetime(df.date)
    return df[df.niveau > 0][["code_commune", "date", "niveau"]]


def agreger_restrictions(jours: pd.DataFrame) -> pd.DataFrame:
    """Nombre de jours par niveau, par commune et par mois."""
    mois = jours.date.dt.to_period("M").dt.start_time
    tableau = (
        jours.assign(mois=mois)
        .pivot_table(
            index=["code_commune", "mois"],
            columns="niveau",
            values="date",
            aggfunc="count",
            fill_value=0,
        )
        .reindex(columns=[1, 2, 3, 4], fill_value=0)
    )
    tableau.columns = NIVEAUX
    return tableau.reset_index()


def percentile_nappe(chroniques: pd.DataFrame, min_annees: int = 8) -> pd.DataFrame:
    """Situe chaque mois d'une station par rapport aux mêmes mois de son propre historique."""
    df = chroniques.dropna(subset=["niveau_nappe_ngf"]).copy()
    df["mois"] = pd.to_datetime(df.date).dt.to_period("M").dt.start_time
    mensuel = df.groupby(["code_bss", "mois"], as_index=False).niveau_nappe_ngf.mean()
    mensuel["mois_calendaire"] = mensuel.mois.dt.month
    groupes = mensuel.groupby(["code_bss", "mois_calendaire"]).niveau_nappe_ngf
    mensuel["percentile"] = groupes.rank(pct=True) * 100
    mensuel = mensuel[groupes.transform("count") >= min_annees]
    return mensuel.drop(columns="mois_calendaire")
