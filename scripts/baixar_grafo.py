"""Baixa o grafo viario de Belo Horizonte do OpenStreetMap e salva em GraphML.

Uso:
    python scripts/baixar_grafo.py --saida data/bh_drive.graphml
"""

import argparse
import time
from pathlib import Path

import osmnx as ox

LUGAR = "Belo Horizonte, Minas Gerais, Brazil"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--saida", default="data/bh_drive.graphml")
    parser.add_argument(
        "--tipo",
        default="drive",
        help="network_type do osmnx (drive = vias transitaveis por veiculos)",
    )
    args = parser.parse_args()

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)

    inicio = time.perf_counter()
    print(f"Baixando grafo '{args.tipo}' de {LUGAR}...")
    grafo = ox.graph_from_place(LUGAR, network_type=args.tipo)
    ox.save_graphml(grafo, saida)
    duracao = time.perf_counter() - inicio

    tamanho_mb = saida.stat().st_size / 1e6
    print(
        f"{grafo.number_of_nodes()} nos, {grafo.number_of_edges()} arestas "
        f"-> {saida} ({tamanho_mb:.1f} MB) em {duracao:.0f}s"
    )


if __name__ == "__main__":
    main()
