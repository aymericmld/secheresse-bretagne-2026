"""Assemble les sources en un modèle en étoile pour le rapport Power BI."""

from __future__ import annotations

import json

import pandas as pd

from . import qualite
from . import transform as t
from .config import DEBUT, DEPARTEMENTS_NOMS, POWERBI, PROCESSED, RAW

COLONNES_RESTRICTIONS = [
    "code_commune",
    "mois",
    "jours_alerte",
    "jours_alerte_renforcee",
    "jours_crise",
]


def charger_json(chemin) -> pd.DataFrame:
    return pd.DataFrame(json.loads(chemin.read_text()))


def construire_communes() -> pd.DataFrame:
    communes = charger_json(RAW / "geo" / "communes.json")
    epci = charger_json(RAW / "geo" / "epci.json").rename(
        columns={"code": "codeEpci", "nom": "nom_epci"}
    )
    communes = communes.merge(epci, on="codeEpci", how="left")
    communes["longitude"] = communes.centre.map(lambda c: c["coordinates"][0])
    communes["latitude"] = communes.centre.map(lambda c: c["coordinates"][1])
    communes = communes.rename(
        columns={
            "code": "code_commune",
            "nom": "nom_commune",
            "codeDepartement": "code_departement",
        }
    )
    # Les îles sans intercommunalité forment leur propre territoire.
    communes["nom_epci"] = communes.nom_epci.fillna(communes.nom_commune)
    colonnes = [
        "code_commune",
        "nom_commune",
        "code_departement",
        "nom_epci",
        "longitude",
        "latitude",
    ]
    return communes[colonnes]


def construire() -> dict[str, pd.DataFrame]:
    communes = construire_communes()

    brut = pd.read_csv(
        RAW / "vigieau" / "restrictions_communes_bretagne.csv",
        dtype={"code_commune": str},
        usecols=["code_commune", "date", "AEP", "SOU", "SUP"],
    )
    jours = t.jours_par_niveau(brut)
    # Quelques communes VigiEau n'existent plus : leur commune de rattachement a son propre historique.
    jours = jours[jours.code_commune.isin(communes.code_commune)]
    mensuel = t.agreger_restrictions(jours)
    jours_comptes = mensuel[t.NIVEAUX].sum(axis=1)

    stations = charger_json(RAW / "hubeau" / "piezo_stations.json")
    piezo = pd.read_csv(RAW / "hubeau" / "piezo_chroniques.csv")
    nappes = t.percentile_nappe(piezo).merge(
        stations[["code_bss", "code_departement"]], on="code_bss"
    )
    fact_nappes = nappes.groupby(["code_departement", "mois"], as_index=False).agg(
        percentile_median=("percentile", "median")
    )

    dim_departement = pd.DataFrame(
        DEPARTEMENTS_NOMS.items(), columns=["code_departement", "departement"]
    )
    mois = pd.date_range(DEBUT, "2026-12-01", freq="MS")
    dim_mois = pd.DataFrame({"mois": mois, "annee": mois.year, "numero_mois": mois.month})

    tables = {
        "dim_commune": communes,
        "dim_departement": dim_departement,
        "dim_mois": dim_mois,
        "fact_restrictions_mois": mensuel[COLONNES_RESTRICTIONS],
        "fact_nappes_mois": fact_nappes,
    }
    qualite.controler(tables, jours_comptes)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    POWERBI.mkdir(parents=True, exist_ok=True)
    for nom, table in tables.items():
        table.to_parquet(PROCESSED / f"{nom}.parquet", index=False)
    with pd.ExcelWriter(POWERBI / "secheresse_bretagne.xlsx") as classeur:
        for nom, table in tables.items():
            table.to_excel(classeur, sheet_name=nom, index=False)
    return tables
