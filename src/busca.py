import geohash
import math

def verifica_raio(entregadores,raio_busca_m,lat_restaurante,lon_restaurante):
    RAIO_TERRA = 6371000 #padronizamos em metros
    entregadores_raio = []
    
    #transformada para radianos
    lat_restaurante = math.radians(lat_restaurante)
    lon_restaurante = math.radians(lon_restaurante)
    
    for geo_e in entregadores:
        lat_min,lat_max,lon_min,lon_max = geohash.decode_geohash(geo_e)
        lat_entregador = (lat_min+lat_max)/2
        lon_entregador = (lon_max+lon_min)/2
        
        #transformação para radianos
        lat_entregador,lon_entregador = map(math.radians,[lat_entregador,lon_entregador])
        
        #diferenca
        dlat = lat_entregador-lat_restaurante
        dlon = lon_entregador-lon_restaurante
        
        # Formula de Haversine para calculo de distancia
        a = math.sin(dlat / 2)**2 + math.cos(lat_entregador) * math.cos(lat_restaurante) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distancia = RAIO_TERRA * c
        
        if distancia<=raio_busca_m:
            entregadores_raio.append((distancia,geo_e))
        
        entregadores_raio.sort() #ordenacao dos entregadores
    
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
        
        
        
    
        
    