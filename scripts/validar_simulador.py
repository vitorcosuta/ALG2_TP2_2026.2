import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import graficos as g

import simulador


def deslocamentos(n, centros):
    """Deslocamentos (m) sorteados pelo simulador, com a mesma semente e os
    mesmos passos de simulador.gerar_entregadores (antes da projecao)."""
    rng = np.random.default_rng(simulador.SEMENTE)
    contagem = simulador.repartir(n, len(centros), rng)
    lat, lon = simulador.sortear_posicoes(
        centros, contagem, simulador.DESVIO_PADRAO_M, rng
    )
    lat_centro = np.repeat(centros["LATITUDE"].to_numpy(), contagem)
    lon_centro = np.repeat(centros["LONGITUDE"].to_numpy(), contagem)

    # Inverso da conversao metros -> graus feita em simulador.sortear_posicoes
    metros_lat = simulador.METROS_POR_GRAU_LAT
    dy = (lat - lat_centro) * metros_lat
    dx = (lon - lon_centro) * metros_lat * np.cos(np.radians(lat_centro))
    return pd.DataFrame({"dx_m": dx, "dy_m": dy})


def grafico4(dados, n, saida):
    sigma = simulador.DESVIO_PADRAO_M
    limite = 4 * sigma
    # Os dois eixos seguem a mesma normal, entao entram juntos no histograma
    valores = np.concatenate([dados["dx_m"], dados["dy_m"]])
    sigma_est = valores.std()

    x = np.linspace(-limite, limite, 400)
    normal = np.exp(-(x**2) / (2 * sigma**2)) / (sigma * np.sqrt(2 * np.pi))

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(
        valores,
        bins=np.arange(-limite, limite + 50, 50),
        density=True,
        color=g.AZUL,
        alpha=0.85,
        edgecolor=g.SUPERFICIE,
        linewidth=1,
        label=f"Entregadores simulados (σ medido = {g.numero_br(sigma_est)} m)",
    )
    ax.plot(
        x,
        normal,
        color=g.TEXTO,
        linewidth=2,
        label=f"Normal teórica (média 0, σ = {g.numero_br(sigma)} m)",
    )

    ax.set_title(
        f"Deslocamento dos entregadores em relação ao bar (N = {g.numero_br(n)})"
    )
    ax.set_xlabel("Deslocamento em relação ao bar de origem (m)")
    ax.set_ylabel("Densidade")
    ax.set_xlim(-limite, limite)
    # Espaco acima do pico para a legenda nao cobrir a curva
    ax.set_ylim(0, normal.max() * 1.3)
    ax.xaxis.set_major_formatter(g.formatador())
    ax.yaxis.set_major_formatter(g.FuncFormatter(lambda v, _: ""))
    ax.legend(loc="upper left")

    fig.savefig(saida / "grafico4_validacao_simulador.png")
    plt.close(fig)
    return sigma_est


def main():
    parser = argparse.ArgumentParser(
        description="Valida o simulador de entregadores com um histograma."
    )
    parser.add_argument("--n", type=int, default=10_000)
    parser.add_argument("--saida", default="resultados")
    args = parser.parse_args()

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)

    centros = simulador.sortear_centros(simulador.carregar_bares())
    dados = deslocamentos(args.n, centros)
    dados.to_csv(saida / "simulador.csv", index=False)

    g.configurar_estilo()
    sigma_est = grafico4(dados, args.n, saida)
    print(f"σ medido: {sigma_est:.1f} m (configurado: {simulador.DESVIO_PADRAO_M} m)")
    print(f"Grafico salvo em {saida}/grafico4_validacao_simulador.png")


if __name__ == "__main__":
    main()
