import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter

AZUL = "#2a78d6"
LARANJA = "#eb6834"
AQUA = "#1baf7a"
TEXTO = "#0b0b0b"
TEXTO_SECUNDARIO = "#52514e"
GRADE = "#e4e3df"
SUPERFICIE = "#fcfcfb"
FAIXA = "#f0efec"

N_GRAFICO2 = 5_000


def numero_br(valor, casas=0):
    """1234.5 -> '1.234,5'."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def formatador(casas=0):
    return FuncFormatter(lambda v, _: numero_br(v, casas))


def configurar_estilo():
    sns.set_theme(
        style="whitegrid",
        rc={
            "figure.facecolor": SUPERFICIE,
            "axes.facecolor": SUPERFICIE,
            "axes.edgecolor": GRADE,
            "axes.labelcolor": TEXTO_SECUNDARIO,
            "axes.titlecolor": TEXTO,
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.titlelocation": "left",
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.color": GRADE,
            "grid.linewidth": 0.8,
            "xtick.color": TEXTO_SECUNDARIO,
            "ytick.color": TEXTO_SECUNDARIO,
            "legend.frameon": False,
            "legend.labelcolor": TEXTO,
            "lines.linewidth": 2,
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
        },
    )


def quartis(df, por, coluna):
    """Mediana e intervalo interquartil de uma coluna, agrupando por 'por'."""
    g = df.groupby(por)[coluna]
    return pd.DataFrame(
        {"mediana": g.median(), "q1": g.quantile(0.25), "q3": g.quantile(0.75)}
    ).reset_index()


def grafico1(consultas, saida):
    """Tempo da busca na Trie em funcao do numero de candidatos devolvidos."""
    fig, ax = plt.subplots(figsize=(8, 5))
    cores = {1_000: AZUL, 5_000: LARANJA, 10_000: AQUA}

    for n, cor in cores.items():
        dados = consultas[consultas["n"] == n]
        ax.scatter(
            dados["candidatos"],
            dados["tempo_trie_ms"],
            s=28,
            color=cor,
            alpha=0.75,
            edgecolors=SUPERFICIE,
            linewidths=0.8,
            label=f"N = {numero_br(n)}",
        )

    x = consultas["candidatos"].to_numpy()
    y = consultas["tempo_trie_ms"].to_numpy()
    inclinacao, intercepto = np.polyfit(x, y, 1)
    xs = np.linspace(0, x.max(), 100)
    ax.plot(xs, inclinacao * xs + intercepto, color=TEXTO_SECUNDARIO, linewidth=1.5)

    ax.set_title("Tempo da busca na Trie")
    ax.set_xlabel("Candidatos devolvidos pela Trie (k)")
    ax.set_ylabel("Tempo da busca na Trie (ms, mediana)")
    ax.xaxis.set_major_formatter(formatador())
    ax.yaxis.set_major_formatter(formatador(1))
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.legend(title="Frota", loc="lower right", title_fontsize=10)

    fig.savefig(saida / "grafico1_tempo_vs_candidatos.png")
    plt.close(fig)


def marcar_precisoes(ax, rotulos=True):
    """Faixas do eixo x com a precisao do geohash usada em cada raio."""
    faixas = [
        (0.25, 0.75, "precisão 6"),
        (0.75, 4.75, "precisão 5"),
        (4.75, 5.25, "precisão 4"),
    ]
    for i, (ini, fim, texto) in enumerate(faixas):
        if i % 2 == 0:
            ax.axvspan(ini, fim, color=FAIXA, zorder=0, linewidth=0)
        if rotulos:
            ax.text(
                (ini + fim) / 2,
                1.02,
                texto,
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="bottom",
                fontsize=9,
                color=TEXTO_SECUNDARIO,
            )


def grafico2(consultas, saida):
    """Candidatos, entregadores no raio e tempo da consulta em funcao do raio."""
    dados = consultas[consultas["n"] == N_GRAFICO2]
    candidatos = quartis(dados, "raio_km", "candidatos")
    no_raio = quartis(dados, "raio_km", "no_raio")
    tempo = quartis(dados, "raio_km", "tempo_consulta_ms")

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(8, 7), sharex=True, gridspec_kw={"height_ratios": [3, 2]}
    )

    for serie, cor, nome in (
        (candidatos, AZUL, "Candidatos da Trie"),
        (no_raio, LARANJA, "Entregadores no raio"),
    ):
        ax1.fill_between(
            serie["raio_km"],
            serie["q1"],
            serie["q3"],
            color=cor,
            alpha=0.15,
            linewidth=0,
        )
        ax1.plot(
            serie["raio_km"],
            serie["mediana"],
            color=cor,
            marker="o",
            markersize=6,
            label=nome,
        )
        # Rotulo direto no fim da linha
        ultimo = serie.iloc[-1]
        ax1.annotate(
            nome,
            xy=(ultimo["raio_km"], ultimo["mediana"]),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=10,
            color=TEXTO,
        )
    ax1.axhline(N_GRAFICO2, color=TEXTO_SECUNDARIO, linewidth=1)
    ax1.annotate(
        f"frota inteira (N = {numero_br(N_GRAFICO2)})",
        xy=(0.5, N_GRAFICO2),
        xytext=(0, 4),
        textcoords="offset points",
        fontsize=9,
        color=TEXTO_SECUNDARIO,
    )
    marcar_precisoes(ax1)
    ax1.set_title("Efeito do raio na consulta", pad=22)
    ax1.set_ylabel("Entregadores (mediana)")
    ax1.yaxis.set_major_formatter(formatador())
    ax1.set_ylim(0, N_GRAFICO2 * 1.12)
    ax1.legend(loc="upper left", bbox_to_anchor=(0.12, 0.84))

    ax2.fill_between(
        tempo["raio_km"], tempo["q1"], tempo["q3"], color=AZUL, alpha=0.15, linewidth=0
    )
    ax2.plot(tempo["raio_km"], tempo["mediana"], color=AZUL, marker="o", markersize=6)
    marcar_precisoes(ax2, rotulos=False)
    ax2.set_ylabel("Tempo da consulta\n(ms, mediana)")
    ax2.set_xlabel("Raio de atendimento (km)")
    ax2.yaxis.set_major_formatter(formatador(1))
    ax2.xaxis.set_major_formatter(formatador(1))
    ax2.set_xticks(sorted(dados["raio_km"].unique()))
    ax2.set_xlim(0.25, 5.25)
    ax2.set_ylim(bottom=0)

    fig.tight_layout(rect=(0, 0.02, 0.86, 1))
    fig.savefig(saida / "grafico2_efeito_do_raio.png")
    plt.close(fig)


def grafico3(escala, saida):
    """Tempo da consulta pela Trie e por forca bruta em funcao de N."""
    trie = quartis(escala, "n", "tempo_trie_ms")
    bruta = quartis(escala, "n", "tempo_forca_bruta_ms")
    raio = escala["raio_km"].iloc[0]

    fig, ax = plt.subplots(figsize=(8, 5))
    for serie, cor, nome in (
        (bruta, LARANJA, "Força bruta (toda a frota)"),
        (trie, AZUL, "Trie + células vizinhas"),
    ):
        ax.fill_between(
            serie["n"], serie["q1"], serie["q3"], color=cor, alpha=0.15, linewidth=0
        )
        ax.plot(
            serie["n"],
            serie["mediana"],
            color=cor,
            marker="o",
            markersize=6,
            label=nome,
        )
        ultimo = serie.iloc[-1]
        ax.annotate(
            f"{nome}\n{numero_br(ultimo['mediana'], 1)} ms",
            xy=(ultimo["n"], ultimo["mediana"]),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=10,
            color=TEXTO,
        )

    ax.set_title(f"Consulta pela Trie x força bruta (raio = {numero_br(raio)} km)")
    ax.set_xlabel("Tamanho da frota (N)")
    ax.set_ylabel("Tempo da consulta (ms, mediana)")
    ax.xaxis.set_major_formatter(formatador())
    ax.yaxis.set_major_formatter(formatador(1))
    ax.set_xticks([1_000, 5_000, 10_000, 15_000, 20_000])
    ax.set_xlim(0, escala["n"].max() * 1.02)
    ax.set_ylim(bottom=0)
    ax.legend(loc="center left", bbox_to_anchor=(0.02, 0.7))
    fig.tight_layout(rect=(0, 0, 0.8, 1))
    fig.savefig(saida / "grafico3_trie_vs_forca_bruta.png")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Gera os graficos do relatorio a partir dos CSVs dos experimentos."
    )
    parser.add_argument("--entrada", default="resultados")
    parser.add_argument("--saida", default="resultados")
    args = parser.parse_args()

    entrada, saida = Path(args.entrada), Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    consultas = pd.read_csv(entrada / "consultas.csv")
    escala = pd.read_csv(entrada / "escala.csv")

    configurar_estilo()
    grafico1(consultas, saida)
    grafico2(consultas, saida)
    grafico3(escala, saida)
    print(f"Graficos salvos em {saida}/")


if __name__ == "__main__":
    main()
