import pandas as pd
import pytest

from secheresse_bretagne import transform as t


def test_niveau_du_jour_est_le_plus_severe():
    df = pd.DataFrame(
        {
            "code_commune": ["1", "1"],
            "date": ["2022-08-01", "2022-08-02"],
            "AEP": [None, None],
            "SOU": ["alerte", None],
            "SUP": ["crise", "vigilance"],
        }
    )
    assert t.jours_par_niveau(df).niveau.tolist() == [4, 1]


def test_jours_comptes_par_niveau_et_par_mois():
    jours = pd.DataFrame(
        {
            "code_commune": ["1"] * 4,
            "date": pd.to_datetime(["2022-08-01", "2022-08-02", "2022-08-03", "2022-09-01"]),
            "niveau": [1, 2, 4, 4],
        }
    )
    mensuel = t.agreger_restrictions(jours).set_index("mois")
    aout = mensuel.loc["2022-08-01"]
    assert (aout.jours_vigilance, aout.jours_alerte, aout.jours_crise) == (1, 1, 1)
    assert mensuel.loc["2022-09-01"].jours_crise == 1


def test_percentile_nappe_compare_au_meme_mois():
    dates = pd.date_range("2010-08-15", periods=10, freq=pd.DateOffset(years=1))
    df = pd.DataFrame(
        {"code_bss": "B", "date": dates, "niveau_nappe_ngf": [float(i) for i in range(10)]}
    )
    resultat = t.percentile_nappe(df)
    assert resultat.percentile.iloc[0] == pytest.approx(10)
    assert resultat.percentile.iloc[-1] == pytest.approx(100)


def test_percentile_exige_huit_annees():
    dates = pd.date_range("2010-08-15", periods=7, freq=pd.DateOffset(years=1))
    df = pd.DataFrame({"code_bss": "B", "date": dates, "niveau_nappe_ngf": range(7)})
    assert t.percentile_nappe(df).empty
