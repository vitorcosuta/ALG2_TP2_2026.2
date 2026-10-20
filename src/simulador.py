from pathlib import Path

import numpy as np
import osmnx as ox
import pandas as pd
from shapely.geometry import LineString, Point

import geohash
from trie import ArvoreTrie

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_BARES = RAIZ / "bares_cruzada.csv"
CAMINHO_GRAFO = RAIZ / "data" / "bh_drive.graphml"

DESVIO_PADRAO_M = 300
NUM_CENTROS = 100
SEMENTE = 2026
PRECISAO_GEOHASH = 8
METROS_POR_GRAU_LAT = 111_320


def carregar_bares(caminho=CAMINHO_BARES):
    """Le os bares com coordenadas (descarta os nao encontrados no cruzamento)."""
    bares = pd.read_csv(caminho, dtype={"_id": str})
    return bares[bares["NIVEL_CRUZAMENTO"] > 0].reset_index(drop=True)


def carregar_grafo(caminho=CAMINHO_GRAFO):
    """Carrega o grafo viario salvo por scripts/baixar_grafo.py."""
    return ox.load_graphml(caminho)


def sortear_centros(bares, quantidade=NUM_CENTROS, semente=SEMENTE):
    """Escolhe os bares que servirao de centro da distribuicao normal.

    A semente fixa garante que os centros sejam sempre os mesmos, para que os
    experimentos do relatorio possam ser repetidos.
    """
    return bares.sample(n=quantidade, random_state=semente).reset_index(drop=True)


def repartir(n, num_centros, rng):
    """Divide N entregadores igualmente entre os centros.

    Cada centro recebe N // C; o resto (N % C) vai para centros sorteados.
    """
    contagem = np.full(num_centros, n // num_centros)
    sorteados = rng.choice(num_centros, size=n % num_centros, replace=False)
    contagem[sorteados] += 1
    return contagem


def sortear_posicoes(centros, contagem, desvio_m, rng):
    """Sorteia as posicoes com distribuicao normal 2D ao redor de cada centro.

    O deslocamento e sorteado em metros e convertido para graus. Um grau de
    longitude encolhe com cos(latitude), por isso a correcao em dlon.
    """
    lat_centro = np.repeat(centros["LATITUDE"].to_numpy(), contagem)
    lon_centro = np.repeat(centros["LONGITUDE"].to_numpy(), contagem)

    dy = rng.normal(0.0, desvio_m, size=lat_centro.size)
    dx = rng.normal(0.0, desvio_m, size=lat_centro.size)

    lat = lat_centro + dy / METROS_POR_GRAU_LAT
    lon = lon_centro + dx / (METROS_POR_GRAU_LAT * np.cos(np.radians(lat_centro)))
    return lat, lon


def geometria_aresta(grafo, u, v, chave):
    """Devolve a geometria da aresta como LineString (lon, lat).

    Arestas retas nao tem o atributo 'geometry' no osmnx; nesse caso a
    geometria e o segmento entre os dois nos.
    """
    dados = grafo.edges[u, v, chave]
    if "geometry" in dados:
        return dados["geometry"]
    no_u, no_v = grafo.nodes[u], grafo.nodes[v]
    return LineString([(no_u["x"], no_u["y"]), (no_v["x"], no_v["y"])])


def projetar_nas_ruas(grafo, lat, lon):
    """Leva cada ponto ao ponto mais proximo da rua mais proxima.

    nearest_edges encontra a aresta (rua) mais proxima de cada ponto; depois,
    project() mede a que distancia do inicio da rua fica o pe da perpendicular
    e interpolate() devolve esse ponto sobre a rua.
    """
    arestas = ox.distance.nearest_edges(grafo, X=lon, Y=lat)

    lat_rua = np.empty_like(lat)
    lon_rua = np.empty_like(lon)
    for i, (u, v, chave) in enumerate(arestas):
        rua = geometria_aresta(grafo, u, v, chave)
        ponto = rua.interpolate(rua.project(Point(lon[i], lat[i])))
        lon_rua[i], lat_rua[i] = ponto.x, ponto.y
    return lat_rua, lon_rua


def gerar_entregadores(n, grafo, centros, desvio_m=DESVIO_PADRAO_M, semente=SEMENTE):
    """Gera N entregadores no formato {"id", "lat", "lon"} ja sobre as ruas."""
    if n <= 0:
        return []
    rng = np.random.default_rng(semente)

    contagem = repartir(n, len(centros), rng)
    lat, lon = sortear_posicoes(centros, contagem, desvio_m, rng)
    lat, lon = projetar_nas_ruas(grafo, lat, lon)

    digitos = len(str(n))
    return [
        {"id": f"E{i + 1:0{digitos}d}", "lat": float(lat[i]), "lon": float(lon[i])}
        for i in range(n)
    ]


def construir_trie(entregadores):
    """Cria uma Trie nova e insere cada entregador pelo seu geohash."""
    trie = ArvoreTrie()
    for entregador in entregadores:
        chave = geohash.encode_geohash(
            entregador["lat"], entregador["lon"], PRECISAO_GEOHASH
        )
        trie.inserir_objeto(chave, entregador)
    return trie
