"""Ligne de commande : python -m secheresse_bretagne [collecte|transformation|tout]."""

import sys

from . import ingest, pipeline


def collecte() -> None:
    ingest.collecter_communes()
    ingest.collecter_piezometrie()
    ingest.collecter_restrictions_communes()


if __name__ == "__main__":
    etape = sys.argv[1] if len(sys.argv) > 1 else "tout"
    if etape not in ("collecte", "transformation", "tout"):
        raise SystemExit("usage : python -m secheresse_bretagne [collecte|transformation|tout]")
    if etape in ("collecte", "tout"):
        collecte()
    if etape in ("transformation", "tout"):
        for nom, table in pipeline.construire().items():
            print(f"{nom}: {len(table)} lignes")
