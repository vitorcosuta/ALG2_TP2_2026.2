import argparse

import pandas as pd
from pyproj import Transformer

EPSG_UTM_23S = 31983
EPSG_WGS84 = 4326
TOLERANCIA_NUMERO = 100

ENDERECO = ["DESC_LOGRADOURO", "NOME_LOGRADOURO", "NUMERO_IMOVEL", "NOME_BAIRRO"]
NIVEIS = [
    (1, ["NOME", *ENDERECO]),
    (2, ENDERECO),
    (3, ["DESC_LOGRADOURO", "NOME_LOGRADOURO", "NUMERO_IMOVEL"]),
]
RUA_E_BAIRRO = ["DESC_LOGRADOURO", "NOME_LOGRADOURO", "NOME_BAIRRO"]


def normalizar(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """Remove espacos extras e padroniza maiusculas nas colunas de texto."""
    for c in colunas:
        df[c] = df[c].fillna("").str.strip().str.upper()
    return df


def carregar_pbh(caminho: str) -> pd.DataFrame:
    """Le a base da PBH e extrai as coordenadas UTM da coluna GEOMETRIA."""
    pbh = pd.read_csv(
        caminho, sep=";", dtype=str, usecols=["NOME", *ENDERECO, "GEOMETRIA"]
    )
    pbh = normalizar(pbh, ["NOME", *ENDERECO])

    xy = pbh["GEOMETRIA"].str.extract(r"POINT \(([-\d.]+) ([-\d.]+)\)")
    pbh["X"] = pd.to_numeric(xy[0], errors="coerce")
    pbh["Y"] = pd.to_numeric(xy[1], errors="coerce")
    return pbh.dropna(subset=["X", "Y"]).drop(columns="GEOMETRIA")


def cruzar_por_chave(
    bares: pd.DataFrame, pbh: pd.DataFrame, chave: list[str], nivel: int
) -> None:
    """Preenche X/Y dos bares ainda sem coordenada que casam pela chave.

    Varios estabelecimentos podem ocupar o mesmo endereco; usamos a mediana
    das coordenadas deles.
    """
    pontos = pbh.groupby(chave, as_index=False)[["X", "Y"]].median()
    pendentes = bares["NIVEL_CRUZAMENTO"] == 0

    achados = bares.loc[pendentes, chave].reset_index().merge(pontos, on=chave)
    achados = achados.set_index("index")

    bares.loc[achados.index, ["X", "Y"]] = achados[["X", "Y"]]
    bares.loc[achados.index, "NIVEL_CRUZAMENTO"] = nivel


def cruzar_numero_proximo(bares: pd.DataFrame, pbh: pd.DataFrame) -> None:
    """Nivel 4: mesmo logradouro e bairro, numero de imovel mais proximo."""
    pendentes = bares["NIVEL_CRUZAMENTO"] == 0

    alvo = bares.loc[pendentes, RUA_E_BAIRRO + ["NUMERO_IMOVEL"]].reset_index()
    alvo["NUM"] = pd.to_numeric(alvo["NUMERO_IMOVEL"], errors="coerce")
    alvo = alvo.dropna(subset=["NUM"]).sort_values("NUM")

    ref = pbh[RUA_E_BAIRRO + ["NUMERO_IMOVEL", "X", "Y"]].copy()
    ref["NUM"] = pd.to_numeric(ref["NUMERO_IMOVEL"], errors="coerce")
    ref = ref.dropna(subset=["NUM"])
    ref = ref.groupby(RUA_E_BAIRRO + ["NUM"], as_index=False)[["X", "Y"]].median()
    ref = ref.sort_values("NUM")

    achados = pd.merge_asof(
        alvo,
        ref,
        on="NUM",
        by=RUA_E_BAIRRO,
        direction="nearest",
        tolerance=TOLERANCIA_NUMERO,
    )
    achados = achados.dropna(subset=["X", "Y"]).set_index("index")

    bares.loc[achados.index, ["X", "Y"]] = achados[["X", "Y"]]
    bares.loc[achados.index, "NIVEL_CRUZAMENTO"] = 4


def utm_para_latlon(bares: pd.DataFrame) -> None:
    """Converte X/Y (UTM 23S) em LATITUDE/LONGITUDE (WGS84)."""
    transf = Transformer.from_crs(EPSG_UTM_23S, EPSG_WGS84, always_xy=True)
    lon, lat = transf.transform(bares["X"].to_numpy(), bares["Y"].to_numpy())
    bares["LATITUDE"] = lat.round(6)
    bares["LONGITUDE"] = lon.round(6)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bares", default="bares.csv")
    parser.add_argument("--pbh", default="20240801_atividade_economica.csv")
    parser.add_argument("--saida", default="bares_geo.csv")
    args = parser.parse_args()

    bares = pd.read_csv(args.bares, dtype=str)
    colunas_originais = list(bares.columns)
    chaves = normalizar(bares[["NOME", *ENDERECO]].copy(), ["NOME", *ENDERECO])

    trabalho = chaves.assign(X=float("nan"), Y=float("nan"), NIVEL_CRUZAMENTO=0)
    pbh = carregar_pbh(args.pbh)

    for nivel, chave in NIVEIS:
        cruzar_por_chave(trabalho, pbh, chave, nivel)
    cruzar_numero_proximo(trabalho, pbh)
    utm_para_latlon(trabalho)

    saida = bares[colunas_originais].copy()
    saida["LATITUDE"] = trabalho["LATITUDE"]
    saida["LONGITUDE"] = trabalho["LONGITUDE"]
    saida["NIVEL_CRUZAMENTO"] = trabalho["NIVEL_CRUZAMENTO"]
    saida.to_csv(args.saida, index=False)

    total = len(saida)
    print(f"{total} bares processados -> {args.saida}")
    contagem = saida["NIVEL_CRUZAMENTO"].value_counts().sort_index()
    for nivel_contado, qtd in contagem.items():
        print(f"  nivel {nivel_contado}: {qtd:6d} ({100 * qtd / total:5.1f}%)")


if __name__ == "__main__":
    main()
