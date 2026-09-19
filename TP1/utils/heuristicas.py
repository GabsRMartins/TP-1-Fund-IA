from typing import TYPE_CHECKING

from entities.estado import Estado

if TYPE_CHECKING:  
    from services.problema import ProblemaPonteTocha


def h_nula(estado: Estado, problema: "ProblemaPonteTocha") -> int:

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
