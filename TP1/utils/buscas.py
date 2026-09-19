"""Algoritmos de busca aplicados ao problema da Ponte e da Tocha.

Todas as funcoes compartilham a mesma assinatura

    busca_X(problema, limite_nos=...) -> ResultadoBusca

o que permite que o executor trate os metodos de forma uniforme na
comparacao experimental. Conforme recomendado no enunciado, toda busca
interrompe a execucao apos um numero fixo e elevado de nos expandidos,
evitando buscas excessivamente longas -- precaucao especialmente
importante para a busca em profundidade.
"""

import heapq
import itertools
import time
from typing import Callable, Dict, List, Optional

from entities.estado import Estado
from entities.no import No
from services.problema import ProblemaPonteTocha

from .heuristicas import h_nula
from .metricas import ResultadoBusca

#: Limite padrao de nos expandidos antes de abortar a busca.
LIMITE_NOS_PADRAO = 100_000

Heuristica = Callable[[Estado, ProblemaPonteTocha], int]


def busca_profundidade(
    problema: ProblemaPonteTocha,
    limite_nos: int = LIMITE_NOS_PADRAO,
    limite_profundidade: Optional[int] = None,
) -> ResultadoBusca:
    """Busca em profundidade (DFS) com poda de ciclos.

    A fronteira e uma pilha (LIFO): o ultimo no gerado e o primeiro a ser
    expandido, de modo que a busca desce o mais fundo possivel em um ramo
    antes de retroceder.

    Como toda acao do problema e reversivel (quem atravessa pode voltar), o
    grafo de estados possui ciclos e a DFS ingenua nao termina. Por isso
    aplica-se a *poda de ciclos*: um sucessor so entra na fronteira se o seu
    estado ainda nao aparece no caminho da raiz ate o no atual. Essa poda
    preserva a completude em espacos finitos, ao contrario da eliminacao
    global de estados repetidos, que descartaria caminhos alternativos que a
    DFS ainda precisa explorar.

    A DFS nao oferece garantia de otimalidade: ela devolve a primeira
    solucao encontrada, que depende apenas da ordem de expansao.
    """
    inicio = time.perf_counter()
    resultado = ResultadoBusca(algoritmo="Busca em Profundidade (DFS)")

    raiz = No(estado=problema.estado_inicial)
    fronteira: List[No] = [raiz]
    resultado.nos_gerados = 1

    while fronteira:
        resultado.tamanho_maximo_fronteira = max(
            resultado.tamanho_maximo_fronteira, len(fronteira)
        )
        no = fronteira.pop()

        if problema.eh_objetivo(no.estado):
            resultado.solucao = no
            break

        if resultado.nos_expandidos >= limite_nos:
            resultado.limite_atingido = True
            break
        resultado.nos_expandidos += 1

        if limite_profundidade is not None and no.profundidade >= limite_profundidade:
            continue

        # A ordem e invertida porque a pilha expande o ultimo empilhado
        # primeiro; assim a exploracao segue a ordem natural das acoes.
        for transicao in reversed(problema.sucessores(no.estado)):
            if no.contem_estado_no_caminho(transicao.estado):
                continue
            fronteira.append(
                No(
                    estado=transicao.estado,
                    pai=no,
                    acao=transicao.acao,
                    g=no.g + transicao.custo,
                    profundidade=no.profundidade + 1,
                )
            )
            resultado.nos_gerados += 1

    resultado.tempo = time.perf_counter() - inicio
    return resultado


def busca_largura(
    problema: ProblemaPonteTocha,
    limite_nos: int = LIMITE_NOS_PADRAO,
) -> ResultadoBusca:
    """Busca em largura (BFS) com eliminacao de estados repetidos.

    A fronteira e uma fila (FIFO): os nos sao expandidos na ordem em que
    foram gerados, o que faz a busca varrer o grafo nivel a nivel.

    A BFS e completa e devolve a solucao com o menor *numero de travessias*.
    Como o custo das arestas nao e uniforme -- cada travessia custa o tempo
    da pessoa mais lenta do grupo --, minimizar o numero de arestas nao e o
    mesmo que minimizar o tempo total, e portanto a BFS nao garante a
    solucao otima para este problema.

    O teste de objetivo e feito na geracao do sucessor, variante usual da
    BFS que evita expandir um nivel inteiro desnecessariamente.
    """
    inicio = time.perf_counter()
    resultado = ResultadoBusca(algoritmo="Busca em Largura (BFS)")

    raiz = No(estado=problema.estado_inicial)
    resultado.nos_gerados = 1
    if problema.eh_objetivo(raiz.estado):
        resultado.solucao = raiz
        resultado.tempo = time.perf_counter() - inicio
        return resultado

    fronteira: List[No] = [raiz]
    indice = 0
    alcancados = {raiz.estado}

    while indice < len(fronteira):
        resultado.tamanho_maximo_fronteira = max(
            resultado.tamanho_maximo_fronteira, len(fronteira) - indice
        )
        no = fronteira[indice]
        indice += 1

        if resultado.nos_expandidos >= limite_nos:
            resultado.limite_atingido = True
            break
        resultado.nos_expandidos += 1

        for transicao in problema.sucessores(no.estado):
            if transicao.estado in alcancados:
                continue
            filho = No(
                estado=transicao.estado,
                pai=no,
                acao=transicao.acao,
                g=no.g + transicao.custo,
                profundidade=no.profundidade + 1,
            )
            resultado.nos_gerados += 1
            if problema.eh_objetivo(filho.estado):
                resultado.solucao = filho
                resultado.tempo = time.perf_counter() - inicio
                return resultado
            alcancados.add(filho.estado)
            fronteira.append(filho)

    resultado.tempo = time.perf_counter() - inicio
    return resultado


def busca_a_estrela(
    problema: ProblemaPonteTocha,
    heuristica: Heuristica = h_nula,
    limite_nos: int = LIMITE_NOS_PADRAO,
    nome: str = "Busca A*",
) -> ResultadoBusca:
    """Busca A*.

    O A* combina a busca de custo minimo (*lowest-cost-first search*) com a
    informacao fornecida por uma funcao heuristica. Para um caminho
    ``p = <v0, v1, ..., vn>`` presente na fronteira, com ``vn`` como ultimo
    no, define-se

        ``f(p) = custo(p) + h(vn) = g(vn) + h(vn)``

    isto e, uma estimativa do custo total do caminho que passa por ``p`` e
    segue ate o no objetivo. A fronteira e uma fila de prioridade ordenada
    por ``f``, e o caminho de menor ``f`` e sempre o proximo a ser expandido.

    Se ``h`` for admissivel, o primeiro caminho objetivo removido da
    fronteira e garantidamente de custo minimo. Para nao depender da
    hipotese mais forte de consistencia, a implementacao mantem o melhor
    ``g`` conhecido por estado e reabre um estado sempre que um caminho mais
    barato ate ele e descoberto (*multiple-path pruning* seguro).

    O desempate por um contador crescente torna a ordem de expansao
    deterministica entre nos de mesmo ``f``.
    """
    inicio = time.perf_counter()
    resultado = ResultadoBusca(algoritmo=nome)

    raiz = No(
        estado=problema.estado_inicial,
        h=heuristica(problema.estado_inicial, problema),
    )
    resultado.nos_gerados = 1

    contador = itertools.count()
    fronteira = [(raiz.f, next(contador), raiz)]
    melhor_g: Dict[Estado, int] = {raiz.estado: 0}

    while fronteira:
        resultado.tamanho_maximo_fronteira = max(
            resultado.tamanho_maximo_fronteira, len(fronteira)
        )
        _, _, no = heapq.heappop(fronteira)

        # Entrada obsoleta: um caminho mais barato ate este estado ja foi
        # processado depois que esta entrada entrou na fila.
        if no.g > melhor_g.get(no.estado, no.g):
            continue

        if problema.eh_objetivo(no.estado):
            resultado.solucao = no
            break

        if resultado.nos_expandidos >= limite_nos:
            resultado.limite_atingido = True
            break
        resultado.nos_expandidos += 1

        for transicao in problema.sucessores(no.estado):
            novo_g = no.g + transicao.custo
            if novo_g >= melhor_g.get(transicao.estado, float("inf")):
                continue
            melhor_g[transicao.estado] = novo_g
            filho = No(
                estado=transicao.estado,
                pai=no,
                acao=transicao.acao,
                g=novo_g,
                h=heuristica(transicao.estado, problema),
                profundidade=no.profundidade + 1,
            )
            resultado.nos_gerados += 1
            heapq.heappush(fronteira, (filho.f, next(contador), filho))

    resultado.tempo = time.perf_counter() - inicio
    return resultado
