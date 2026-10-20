import geohash
import math

def verifica_raio(entregadores,raio_busca_m,lat_restaurante,lon_restaurante):
    """Cada entregador e um dicionario {"id": ..., "lat": ..., "lon": ...}.
    Retorna lista de (distancia_m, entregador) ordenada pela distancia"""
    RAIO_TERRA = 6371000 #padronizamos em metros
    entregadores_raio = []

    #transformada para radianos
    lat_restaurante = math.radians(lat_restaurante)
    lon_restaurante = math.radians(lon_restaurante)

    for entregador in entregadores:
        #usamos a posicao real do entregador, e nao o centro da celula do geohash
        lat_entregador = math.radians(entregador["lat"])
        lon_entregador = math.radians(entregador["lon"])
        
        #diferenca
        dlat = lat_entregador-lat_restaurante
        dlon = lon_entregador-lon_restaurante
        
        # Formula de Haversine para calculo de distancia
        a = math.sin(dlat / 2)**2 + math.cos(lat_entregador) * math.cos(lat_restaurante) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distancia = RAIO_TERRA * c
        
        if distancia<=raio_busca_m:
            entregadores_raio.append((distancia,entregador))

    #ordenacao pela distancia (dicionarios nao sao comparaveis em caso de empate)
    entregadores_raio.sort(key=lambda item: item[0])
    
    return entregadores_raio
            
            
            
def filtragem_entregadores(trie_entregadores, restaurante, raio_busca_km):
    """Busca os entregadores dentro dos quadrantes e verifica quais deles estao dentro do raio de busca"""
    lat,lon = restaurante
    entregadores = []
    raio_busca_m = raio_busca_km*1000.0
    precisao = geohash.precisao_raio(raio_busca_m, lat)
    
    #pega o prefixo do restaurante e entorno com precisao dinamica
    gstr = geohash.encode_geohash(lat,lon,precisao)
    geo_quadrantes = geohash.vizinhos(gstr)
    geo_quadrantes.append(gstr)
    
    for geo_q in geo_quadrantes:
        entregadores.extend(trie_entregadores.Buscar_prefixo(geo_q))
        
    entregadores_raio = verifica_raio(entregadores,raio_busca_m,lat,lon)
    
    return entregadores_raio
        
        
        
    
        
    