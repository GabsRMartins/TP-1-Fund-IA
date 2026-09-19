import argparse
import heapq
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from entities.estado import Estado  # noqa: E402
from services.executor import (  # noqa: E402
    REPETICOES_PADRAO,
    executar,
    experimento_escalabilidade,
)
from services.problema import ProblemaPonteTocha  # noqa: E402
from utils.buscas import (  # noqa: E402
    LIMITE_NOS_PADRAO,
    busca_a_estrela,
    busca_largura,
    busca_profundidade,
)
from utils.heuristicas import h1_mais_lento, h2_soma_alternada  # noqa: E402
from utils.metricas import ResumoExecucoes  # noqa: E402


def custos_otimos(problema: ProblemaPonteTocha) -> Dict[Estado, int]:
    """Calcula o custo otimo de cada estado alcancavel usando Dijkstra reverso."""
    reverso: Dict[Estado, List[tuple]] = {}
    for estado in problema.estados_alcancaveis():
        for transicao in problema.sucessores(estado):
            reverso.setdefault(transicao.estado, []).append((estado, transicao.custo))

    distancia: Dict[Estado, int] = {}
    fila: List[tuple] = []
    for estado in problema.estados_alcancaveis():
        if problema.eh_objetivo(estado):
            distancia[estado] = 0
            heapq.heappush(fila, (0, str(estado), estado))

    while fila:
        custo, _, estado = heapq.heappop(fila)
        if custo > distancia.get(estado, float("inf")):
            continue
        for anterior, peso in reverso.get(estado, []):
            novo = custo + peso
            if novo < distancia.get(anterior, float("inf")):
                distancia[anterior] = novo
                heapq.heappush(fila, (novo, str(anterior), anterior))
    return distancia


def verificar(problema: ProblemaPonteTocha) -> None:
    """Confere as propriedades formais afirmadas no relatorio."""
    print("\nVERIFICACOES FORMAIS")
    print("-" * 78)

    estados = problema.estados_alcancaveis()
    print(f"Estados alcancaveis                : {len(estados)} de "
          f"{2 ** len(problema.pessoas) * 2} possiveis")

    otimos = custos_otimos(problema)
    custo_otimo = otimos[problema.estado_inicial]
    print(f"Custo otimo (Dijkstra de referencia): {custo_otimo} minutos")

    falhas_h1 = [s for s in estados if h1_mais_lento(s, problema) > otimos.get(s, 0)]
    falhas_h2 = [s for s in estados if h2_soma_alternada(s, problema) > otimos.get(s, 0)]
    print(f"h1 admissivel em todos os estados   : {not falhas_h1}")
    print(f"h2 admissivel em todos os estados   : {not falhas_h2}")

    domina = all(
        h2_soma_alternada(s, problema) >= h1_mais_lento(s, problema) for s in estados
    )
    print(f"h2 domina h1 em todos os estados    : {domina}")

    # Consistencia: h(s) <= custo(s, s') + h(s') para toda transicao.
    def consistente(h) -> bool:
        return all(
            h(s, problema) <= t.custo + h(t.estado, problema)
            for s in estados
            for t in problema.sucessores(s)
        )

    print(f"h1 consistente                      : {consistente(h1_mais_lento)}")
    print(f"h2 consistente                      : {consistente(h2_soma_alternada)}")
    print("-" * 78)


def coletar(
    problema: ProblemaPonteTocha,
    repeticoes: int,
    limite_nos: int,
) -> List[ResumoExecucoes]:
    """Executa os quatro cenarios comparados no relatorio."""
    return [
        executar(lambda: busca_profundidade(problema, limite_nos=limite_nos), repeticoes),
        executar(lambda: busca_largura(problema, limite_nos=limite_nos), repeticoes),
        executar(
            lambda: busca_a_estrela(
                problema, h1_mais_lento, limite_nos=limite_nos, nome="Busca A* (h1)"
            ),
            repeticoes,
        ),
        executar(
            lambda: busca_a_estrela(
                problema, h2_soma_alternada, limite_nos=limite_nos, nome="Busca A* (h2)"
            ),
            repeticoes,
        ),
    ]


def imprimir_solucoes(resumos: List[ResumoExecucoes]) -> None:
    print("\nSOLUCOES ENCONTRADAS")
    print("-" * 78)
    for resumo in resumos:
        print(f"{resumo.algoritmo}")
        print(f"  custo total : {resumo.custo} minutos em {resumo.travessias} travessias")
        print(f"  caminho     : {resumo.caminho}")
        if resumo.limite_atingido:
            print("  ATENCAO     : limite de nos expandidos atingido")
        print()


def imprimir_tabela(resumos: List[ResumoExecucoes], repeticoes: int) -> None:
    print("TABELA COMPARATIVA "
          f"(medias de {repeticoes} execucoes)")
    print("-" * 78)
    cabecalho = f"{'Algoritmo':<28}{'Custo':>8}{'Travessias':>12}" \
                f"{'Nos exp.':>12}{'Tempo (ms)':>16}"
    print(cabecalho)
    print("-" * 78)
    for resumo in resumos:
        custo = resumo.custo if resumo.custo is not None else "--"
        print(
            f"{resumo.algoritmo:<28}{custo:>8}{resumo.travessias:>12}"
            f"{resumo.nos_expandidos:>12.1f}"
            f"{resumo.tempo_medio * 1000:>11.4f} +/- {resumo.tempo_desvio * 1000:.4f}"
        )
    print("-" * 78)


def imprimir_escalabilidade() -> None:
    """Mostra o efeito da dominancia de h2 em instancias maiores."""
    print("\nESCALABILIDADE: NOS EXPANDIDOS PELO A*")
    print("-" * 78)
    print(f"{'Pessoas':>8}{'Custo otimo':>14}{'A* com h1':>12}{'A* com h2':>12}"
          f"{'Reducao':>10}")
    print("-" * 78)
    for linha in experimento_escalabilidade():
        reducao = 1 - linha["expandidos_h2"] / linha["expandidos_h1"]
        print(
            f"{linha['pessoas']:>8}{linha['custo']:>14}"
            f"{linha['expandidos_h1']:>12}{linha['expandidos_h2']:>12}"
            f"{reducao * 100:>9.1f}%"
        )
    print("-" * 78)


def main() -> None:
    parser = argparse.ArgumentParser(description="TP1 - Ponte e Tocha")
    parser.add_argument(
        "--repeticoes", type=int, default=REPETICOES_PADRAO,
        help="numero de execucoes por algoritmo (padrao: %(default)s)",
    )
    parser.add_argument(
        "--limite-nos", type=int, default=LIMITE_NOS_PADRAO,
        help="limite de nos expandidos por busca (padrao: %(default)s)",
    )
    parser.add_argument(
        "--escala", action="store_true",
        help="executa o experimento de escalabilidade das heuristicas",
    )
    parser.add_argument(
        "--verificar", action="store_true",
        help="executa as verificacoes formais da modelagem e das heuristicas",
    )
    args = parser.parse_args()

    problema = ProblemaPonteTocha()

    print("=" * 78)
    print("TP1 - PROBLEMA DA PONTE E DA TOCHA")
    print("=" * 78)
    print("Pessoas          : " + ", ".join(
        f"{p.nome}={p.tempo} min" for p in problema.pessoas))
    print(f"Estado inicial   : {problema.estado_inicial}")
    print(f"Estado objetivo  : {problema.estado_objetivo}")
    print(f"Limite de nos    : {args.limite_nos}")

    if args.verificar:
        verificar(problema)

    resumos = coletar(problema, args.repeticoes, args.limite_nos)
    imprimir_solucoes(resumos)
    imprimir_tabela(resumos, args.repeticoes)

    if args.escala:
        imprimir_escalabilidade()


if __name__ == "__main__":
    main()
