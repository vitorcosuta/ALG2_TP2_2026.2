import argparse
import platform
import statistics
import sys
import time
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import busca
import geohash
import simulador

SEMENTE_RESTAURANTES = 7
NUM_RESTAURANTES_CENTRO = 15
NUM_RESTAURANTES_FORA = 15

FROTAS_CONSULTAS = [1_000, 5_000, 10_000]
RAIOS_KM = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]

FROTAS_ESCALA = [1_000, 2_000, 5_000, 10_000, 20_000]
RAIO_ESCALA_KM = 2.0

AQUECIMENTO = 3
REPETICOES = 30


def mediana_ms(funcao):
    """Executa a funcao varias vezes e devolve (resultado, mediana em ms)."""
    for _ in range(AQUECIMENTO):
        funcao()
    tempos = []
    for _ in range(REPETICOES):
        inicio = time.perf_counter_ns()
        resultado = funcao()
        tempos.append((time.perf_counter_ns() - inicio) / 1e6)
    return resultado, statistics.median(tempos)


def escolher_restaurantes(bares, centros):
    """Metade dos restaurantes entre os bares de origem (regiao densa) e
    metade entre os demais bares (regiao em geral mais esparsa)."""
    rng = np.random.default_rng(SEMENTE_RESTAURANTES)
    chaves_centros = set(zip(centros["LATITUDE"], centros["LONGITUDE"], strict=True))
    eh_centro = [
        (lat, lon) in chaves_centros
        for lat, lon in zip(bares["LATITUDE"], bares["LONGITUDE"], strict=True)
    ]
    eh_centro = np.array(eh_centro)

    idx_centro = rng.choice(
        np.flatnonzero(eh_centro), NUM_RESTAURANTES_CENTRO, replace=False
    )
    idx_fora = rng.choice(
        np.flatnonzero(~eh_centro), NUM_RESTAURANTES_FORA, replace=False
    )

    escolhidos = []
    for regiao, indices in (("bar de origem", idx_centro), ("outro bar", idx_fora)):
        for i in indices:
            bar = bares.loc[i]
            escolhidos.append(
                {
                    "restaurante": int(i),
                    "regiao": regiao,
                    "lat": float(bar["LATITUDE"]),
                    "lon": float(bar["LONGITUDE"]),
                }
            )
    return escolhidos


def candidatos_trie(trie, lat, lon, raio_m):
    """Etapa 1 da consulta: busca na Trie na celula do restaurante e nas 8
    vizinhas (o mesmo que busca.filtragem_entregadores faz antes do filtro)."""
    precisao = geohash.precisao_raio(raio_m, lat)
    celula = geohash.encode_geohash(lat, lon, precisao)
    candidatos = []
    for prefixo in geohash.vizinhos(celula) + [celula]:
        candidatos.extend(trie.Buscar_prefixo(prefixo))
    return candidatos


def experimento_consultas(grafo, centros, restaurantes):
    linhas = []
    for n in FROTAS_CONSULTAS:
        entregadores = simulador.gerar_entregadores(n, grafo, centros)
        trie = simulador.construir_trie(entregadores)
        print(f"[consultas] N={n}")
        for raio_km in RAIOS_KM:
            raio_m = raio_km * 1000
            for r in restaurantes:
                lat, lon = r["lat"], r["lon"]
                candidatos, t_trie = mediana_ms(
                    partial(candidatos_trie, trie, lat, lon, raio_m)
                )
                no_raio, t_filtro = mediana_ms(
                    partial(busca.verifica_raio, candidatos, raio_m, lat, lon)
                )
                _, t_total = mediana_ms(
                    partial(busca.filtragem_entregadores, trie, (lat, lon), raio_km)
                )
                linhas.append(
                    {
                        "n": n,
                        "raio_km": raio_km,
                        "precisao": geohash.precisao_raio(raio_m, lat),
                        "restaurante": r["restaurante"],
                        "regiao": r["regiao"],
                        "candidatos": len(candidatos),
                        "no_raio": len(no_raio),
                        "tempo_trie_ms": t_trie,
                        "tempo_filtro_ms": t_filtro,
                        "tempo_consulta_ms": t_total,
                    }
                )
    return pd.DataFrame(linhas)


def experimento_escala(grafo, centros, restaurantes):
    linhas = []
    raio_m = RAIO_ESCALA_KM * 1000
    for n in FROTAS_ESCALA:
        entregadores = simulador.gerar_entregadores(n, grafo, centros)
        trie = simulador.construir_trie(entregadores)
        print(f"[escala] N={n}")
        for r in restaurantes:
            lat, lon = r["lat"], r["lon"]
            pela_trie, t_trie = mediana_ms(
                partial(busca.filtragem_entregadores, trie, (lat, lon), RAIO_ESCALA_KM)
            )
            # Forca bruta: mesmo filtro Haversine aplicado a toda a frota
            bruta, t_bruta = mediana_ms(
                partial(busca.verifica_raio, entregadores, raio_m, lat, lon)
            )
            ids_trie = {e["id"] for _, e in pela_trie}
            ids_bruta = {e["id"] for _, e in bruta}
            linhas.append(
                {
                    "n": n,
                    "raio_km": RAIO_ESCALA_KM,
                    "restaurante": r["restaurante"],
                    "regiao": r["regiao"],
                    "no_raio": len(ids_trie),
                    "resultados_iguais": ids_trie == ids_bruta,
                    "tempo_trie_ms": t_trie,
                    "tempo_forca_bruta_ms": t_bruta,
                }
            )
    return pd.DataFrame(linhas)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--saida", default="resultados")
    args = parser.parse_args()

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)

    print("Carregando grafo e bares...")
    grafo = simulador.carregar_grafo()
    bares = simulador.carregar_bares()
    centros = simulador.sortear_centros(bares)
    restaurantes = escolher_restaurantes(bares, centros)

    consultas = experimento_consultas(grafo, centros, restaurantes)
    consultas.to_csv(saida / "consultas.csv", index=False)

    escala = experimento_escala(grafo, centros, restaurantes)
    escala.to_csv(saida / "escala.csv", index=False)

    ambiente = (
        f"Python {platform.python_version()} | {platform.system()} "
        f"{platform.release()} | {platform.processor() or platform.machine()} | "
        f"repeticoes={REPETICOES}, aquecimento={AQUECIMENTO}\n"
    )
    (saida / "ambiente.txt").write_text(ambiente)

    divergencias = (~escala["resultados_iguais"]).sum()
    print(f"Consultas: {len(consultas)} linhas | Escala: {len(escala)} linhas")
    print(f"Divergencias Trie x forca bruta: {divergencias}")
    print(f"CSVs salvos em {saida}/")


if __name__ == "__main__":
    main()
