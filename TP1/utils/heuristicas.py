"""Heuristicas admissiveis para o problema da Ponte e da Tocha.

Uma heuristica ``h(n)`` estima o custo restante do estado ``n`` ate o
objetivo. Ela e admissivel quando nunca superestima esse custo, isto e,
``h(n) <= h*(n)`` para todo estado, onde ``h*`` e o custo otimo real. Essa
propriedade e o que garante que o A* devolva um caminho de custo minimo.

As duas heuristicas aqui implementadas dependem apenas do conjunto de
pessoas que ainda estao na margem inicial.
"""

from typing import TYPE_CHECKING

from entities.estado import Estado

if TYPE_CHECKING:  # pragma: no cover - apenas para anotacao de tipos
    from services.problema import ProblemaPonteTocha


def h_nula(estado: Estado, problema: "ProblemaPonteTocha") -> int:
    """Heuristica identicamente nula.

    Trivialmente admissivel. Com ela, o A* degenera na Busca de Custo
    Minimo, servindo como referencia para medir o ganho das heuristicas
    informativas.
    """
    return 0


def h1_mais_lento(estado: Estado, problema: "ProblemaPonteTocha") -> int:
    """``h1(n) = max{t(i) : i na margem inicial}``.   """
    if not estado.esquerda:
        return 0
    return max(pessoa.tempo for pessoa in estado.esquerda)


def h2_soma_alternada(estado: Estado, problema: "ProblemaPonteTocha") -> int:
    """Soma dos tempos de indice impar na ordem decrescente.

    Ordenando os tempos das pessoas na margem inicial como
    ``t1 >= t2 >= ... >= tk``, tem-se ``h2(n) = t1 + t3 + t5 + ...``."""
    tempos = sorted((pessoa.tempo for pessoa in estado.esquerda), reverse=True)
    return sum(tempos[::2])
