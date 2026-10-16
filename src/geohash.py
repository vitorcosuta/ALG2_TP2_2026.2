#definindo base 32
BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
#dicionario: tabela pronta de consulta do BASE32, sabemos imediatamente qual valor é o certo
dict_base32 = {}
for pos, c in enumerate(BASE32):
    dict_base32[c] = pos #dicionario para decode

def encode_geohash(lat, lon, precision):
    #precision limitada a 8 no enunciado
    if precision > 8 or precision < 1:
        raise ValueError("Precisao Invalida")
    #definindo intervaos iniciais, que serao atualizados recursivamente
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    
    geohash = [] #vazio no inicio
    #bits = [16, 8, 4, 2, 1] #servem para multiplicar o inteiro na base dois
    bit = 0 #define se o bit atual é 0 ou 1
    intercalacao = 1
    i = 0 #inteiro acumulador de bits
    pt = [lat, lon]
    if pt[0] > 90 or pt[0] < -90:
        raise ValueError("Latitude Invalida")
    if pt[1] > 180 or pt[1]< -180:
        raise ValueError("Longitude Invalida")
    while intercalacao <=  (precision * 5): 
        if (intercalacao % 2 == 0):
            #nesse caso estamos em uma intercalacao par, logo estamos no nivel de lat
            mid = (lat_interval[0] + lat_interval[1]) / 2
            if lat >= mid:
                bit = 1 #marcamos 1
                lat_interval = [mid, lat_interval[1]] #olhamos quadrante superior
            else:
                bit = 0
                lat_interval = [lat_interval[0], mid] #olhamos quadrante inferior
        else:
            #nesse caso a intercalacao e impar, ou seja, estamos em nivel long
            mid = (lon_interval[0]+ lon_interval[1]) / 2
            if lon >= mid:
                bit = 1
                lon_interval = [mid, lon_interval[1]]
            else:
                bit = 0
                lon_interval = [lon_interval[0], mid]
        i = (i << 1) | bit #move tudo um espaço para esq e o OU insere o bit do nivel atual
        if (intercalacao % 5 ==0):
            #definimos BASE32 como str, que pode ser acessada por indice
            ch = BASE32[i]
            i = 0
            geohash.append(ch) #adiciona novo char ao final
        intercalacao = intercalacao + 1
    return "".join(geohash) 

def decode_geohash(geohash_str):
    #agora o caminho oposto: temos char e queremos o numero entre 0-31 correspondente
    #intervalos iniciais
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    intercalacao = 1
    #dicionario: tabela pronta de consulta
    for c in geohash_str: #dada uma str em geohash, pegamos um char por vez
        if c not in dict_base32:
            raise ValueError(f"Caractere Invalido no Geohash: {c}")
        valor = dict_base32[c] #converte char em decimal
        for j in range(4, -1, -1): #percorre os bits do decimal do maior para menor
            bit = ((1<< j) & valor == (1 <<j)) #para j =0, temos (1<<0) =1 e para um c, suponha 
            if (intercalacao % 2 ==0):
                #estamos no caso lat de novo
                mid = (lat_interval[0] + lat_interval[1]) /2
                if bit == True:
                    #nesse caso olhamos o quadrante superior
                    lat_interval = [mid, lat_interval[1]]
                else:
                    lat_interval = [lat_interval[0], mid]
            else:
                #estamos no caso long
                mid = (lon_interval[0] + lon_interval[1]) /2
                if bit == True:
                    lon_interval = [mid, lon_interval[1]]
                else:
                    lon_interval = [lon_interval[0], mid]
            intercalacao = intercalacao +1

    return (lat_interval[0], lat_interval[1], lon_interval[0], lon_interval[1])

def vizinhos(gstr):
    (lat_min, lat_max, lon_min, lon_max) = decode_geohash(str) #daqui recebemos quatro limites de intervalos
    #calculamos centro
    #centro = [lat_centro, lon_centro] #[y,x]
    lat_centro = (lat_min + lat_max) /2
    lon_centro = (lon_min + lon_max) /2
    #calculando largura(variacao em x)
    larg = lon_max - lon_min 
    #calculando altura (varicao em y)
    alt = lat_max - lat_min
    #calculando vizinhos
    #vizinho norte:
    viz_norte_centro = [lat_centro + alt, lon_centro]
    if viz_norte_centro[0] > 90:
        viz_norte_centro[0] = 90
    viz_sul_centro = [lat_centro - alt, lon_centro]
    if viz_sul_centro[0] < -90:
        viz_sul_centro[0] = -90
    viz_leste_centro = [lat_centro, lon_centro + larg]
    if viz_leste_centro[1] > 180:
        viz_leste_centro[1] = 180
    viz_oeste_centro = [lat_centro, lon_centro - larg]
    if viz_oeste_centro[1] < - 180:
            viz_oeste_centro[1] =  -180

