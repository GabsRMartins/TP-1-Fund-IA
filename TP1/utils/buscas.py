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
    """Busca em profundidade (DFS) com poda de ciclos."""
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
    """Busca em largura (BFS) com eliminacao de estados repetidos. """
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
