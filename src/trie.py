class No:
    def __init__(self, prefixo=""):
        self.prefixo = prefixo
        self.filhos = {}
        self.fim_de_palavra = False
        self.entregadores = [] # Se for o fim, guardamos os dados do entregador


class ArvoreTrie:
    def __init__(self):
        self.raiz = No()
        
    def inserir_objeto(self, geohash_str,dados_entregador):
        no_atual = self.raiz
        palavra_restante = geohash_str
        
        while len(palavra_restante)>0:
            primeira_letra = palavra_restante[0]
            
            #caso 1: nao existe nenhuma ramificacao com a primeira letra
            if primeira_letra not in no_atual.filhos:
                novo_no = No(palavra_restante)
                novo_no.fim_de_palavra = True
                novo_no.entregadores.append(dados_entregador)
                no_atual.filhos[primeira_letra] = novo_no
                return
            
            
            #descemos o nivel se existe a primeira letra nos filhos
            filho = no_atual.filhos[primeira_letra]
            i=0
            
            #verifica quantos caracteres iguais o prefixo do no e o restante da palavra tem em comum
            while i<len(filho.prefixo) and i<len(palavra_restante) and palavra_restante[i] == filho.prefixo[i]:
                i+=1
            
            #Caso 2: palavra restante engloba todo o prefixo
            if i == len(filho.prefixo):
                palavra_restante = palavra_restante[i:]
                no_atual = filho
                
                # se a palavra acabou, os geoshash eram identicos
                if len(palavra_restante) == 0:
                    no_atual.fim_de_palavra = True
                    no_atual.entregadores.append(dados_entregador)
                    return
            
            #caso 3: diveregencia entre o sufixo do filho e a palavra restante no meio da palavra
            else:
                # criamos um novo no para a sobra do no filho antigo
                prefixo_antigo_filho_sobra = filho.prefixo[i:]
                no_sobra = No(prefixo_antigo_filho_sobra)
                no_sobra.fim_de_palavra = filho.fim_de_palavra
                no_sobra.filhos = filho.filhos
                no_sobra.entregadores = filho.entregadores
                
                # atualizamos o nó filho antigo
                filho.prefixo = filho.prefixo[:i]
                filho.filhos = {prefixo_antigo_filho_sobra[0]:no_sobra}
                filho.fim_de_palavra = False
                filho.entregadores = []
                
                # criamos um novo no para o restante da palavra
                palavra_nova_sobra  = palavra_restante[i:]
            
                novo_no_folha = No(palavra_nova_sobra)
                novo_no_folha.fim_de_palavra =True
                novo_no_folha.entregadores.append(dados_entregador)
                filho.filhos[palavra_nova_sobra[0]] = novo_no_folha
                
                return
                
    def Buscar_prefixo(self, geohash_str):
        """"Recebe geohash do quadrante e retorna todos os entregadores dentro do quadrante"""
        
        no_atual = self.raiz

        while len(geohash_str)>0:
            
            primeira_letra = geohash_str[0]    
            #previne erro se a letra nao existir
            if primeira_letra not in no_atual.filhos:
                return []
            
            no_filho = no_atual.filhos[geohash_str[0]] 
 
            # caso 1: string buscada cobre todo prefixo do no
            if len(geohash_str)>= len(no_filho.prefixo) and geohash_str[:len(no_filho.prefixo)] == no_filho.prefixo:
                geohash_str = geohash_str[len(no_filho.prefixo):]
                no_atual= no_filho
            
            # caso 2: prefixo do filho é maior que a string buscada    
            elif len(geohash_str)<len(no_filho.prefixo) and geohash_str == no_filho.prefixo[:len(geohash_str)]:
                entregadores = []
                self.dfs(no_filho,entregadores) 
                return entregadores
            
            # caso 3: strings divergiram
            else:
                return []

        # termino do while, no atual é o no do quadrante
        entregadores = []
        self.dfs(no_atual,entregadores) 
        return entregadores
    
    def dfs(self, no, entregadores):
        
        #insere todos os entregadores daquele quadrante na lista
        if no.fim_de_palavra:
            entregadores.extend(no.entregadores)
        
        #percorre os filhos do no atual
        for letra_proximo_no in no.filhos:
            proximo_no = no.filhos[letra_proximo_no]
            self.dfs(proximo_no,entregadores)
        
        