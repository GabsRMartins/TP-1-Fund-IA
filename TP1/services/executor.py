import statistics
from typing import Callable, List

from utils.metricas import ResultadoBusca, ResumoExecucoes
from utils.buscas import busca_a_estrela
from utils.heuristicas import h1_mais_lento, h2_soma_alternada
from entities.pessoa import Pessoa
from services.problema import ProblemaPonteTocha

Execucao = Callable[[], ResultadoBusca]

#: Numero padrao de repeticoes por algoritmo.
REPETICOES_PADRAO = 30


def executar(
    execucao: Execucao,
    repeticoes: int = REPETICOES_PADRAO,
) -> ResumoExecucoes:
    """Roda ``execucao`` varias vezes e agrega os resultados."""
    if repeticoes < 1:
        raise ValueError("repeticoes deve ser no minimo 1")

    resultados: List[ResultadoBusca] = [execucao() for _ in range(repeticoes)]
    referencia = resultados[0]
    tempos = [r.tempo for r in resultados]

    return ResumoExecucoes(
        algoritmo=referencia.algoritmo,
        repeticoes=repeticoes,
        custo=referencia.custo,
        travessias=referencia.travessias,
        nos_expandidos=statistics.fmean(r.nos_expandidos for r in resultados),
        nos_gerados=statistics.fmean(r.nos_gerados for r in resultados),
        tempo_medio=statistics.fmean(tempos),
        tempo_desvio=statistics.stdev(tempos) if repeticoes > 1 else 0.0,
        limite_atingido=referencia.limite_atingido,
        caminho=referencia.caminho_formatado(),
        tempos=tempos,
    )


def instancia_ampliada(n: int):


    base = [1, 2, 5]
    tempos = base + [10 + 5 * i for i in range(max(0, n - len(base)))]
    pessoas = [Pessoa(tempo=tempos[i], nome=chr(ord("A") + i)) for i in range(n)]
    return ProblemaPonteTocha(pessoas)


def experimento_escalabilidade(tamanhos=(4, 6, 8, 10, 12)):

    

    dados = []
    for n in tamanhos:
        problema = instancia_ampliada(n)
        com_h1 = busca_a_estrela(problema, h1_mais_lento, nome="Busca A* (h1)")
        com_h2 = busca_a_estrela(problema, h2_soma_alternada, nome="Busca A* (h2)")
        assert com_h1.custo == com_h2.custo, "heuristicas admissiveis divergiram"
        dados.append(
            {
                "pessoas": n,
                "custo": com_h1.custo,
                "expandidos_h1": com_h1.nos_expandidos,
                "expandidos_h2": com_h2.nos_expandidos,
                "tempo_h1": com_h1.tempo,
                "tempo_h2": com_h2.tempo,
            }
        )
    return dados
