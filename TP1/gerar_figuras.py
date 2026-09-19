"""Geracao das figuras utilizadas no relatorio do TP1.

Produz quatro imagens em ``Figuras/``:

* ``grafo_estados.png``              -- grafo do espaco de estados com o caminho otimo;
* ``solucao_otima.png``              -- diagrama em escada da solucao de 17 minutos;
* ``comparativo_algoritmos.png``     -- custo e nos expandidos por algoritmo;
* ``escalabilidade_heuristicas.png`` -- efeito da dominancia de h2.

Uso::

    python gerar_figuras.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["text.usetex"] = False

import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402

from entities.estado import Lado  # noqa: E402
from main import coletar  # noqa: E402
from services.executor import experimento_escalabilidade  # noqa: E402
from services.problema import ProblemaPonteTocha  # noqa: E402
from utils.buscas import busca_a_estrela  # noqa: E402
from utils.heuristicas import h2_soma_alternada  # noqa: E402

DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Figuras")

AZUL = "#2f5d8c"
LARANJA = "#d1701c"
CINZA = "#9aa5b1"
VERDE = "#2e7d4f"
VERMELHO = "#a83232"


def _salvar(fig, nome: str) -> str:
    os.makedirs(DESTINO, exist_ok=True)
    caminho = os.path.join(DESTINO, nome)
    fig.savefig(caminho, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"gerado: {caminho}")
    return caminho


def _rotulo(estado) -> str:
    nomes = "".join(sorted(p.nome for p in estado.esquerda)) or "-"
    lado = "esq" if estado.tocha is Lado.ESQUERDA else "dir"
    return f"{nomes}\n{lado}"


def figura_grafo_estados(problema: ProblemaPonteTocha) -> None:
    """Grafo completo do espaco de estados, com o caminho otimo destacado."""
    grafo = nx.DiGraph()
    for estado in problema.estados_alcancaveis():
        grafo.add_node(estado)
        for transicao in problema.sucessores(estado):
            grafo.add_edge(estado, transicao.estado, custo=transicao.custo)

    # Layout em camadas: a coluna indica quantas pessoas ja estao na margem
    # final, de modo que o progresso rumo ao objetivo cresce da esquerda
    # para a direita.
    posicoes = {}
    colunas = {}
    for estado in sorted(grafo.nodes, key=lambda e: (len(e.esquerda), str(e))):
        coluna = len(problema.pessoas) - len(estado.esquerda)
        indice = colunas.get(coluna, 0)
        colunas[coluna] = indice + 1
        posicoes[estado] = (coluna * 2.6, -indice * 1.25)

    solucao = busca_a_estrela(problema, h2_soma_alternada).solucao
    caminho = [no.estado for no in solucao.caminho()]
    arestas_otimas = set(zip(caminho, caminho[1:]))

    fig, eixo = plt.subplots(figsize=(11, 6.5))
    cores = [AZUL if e.tocha is Lado.ESQUERDA else LARANJA for e in grafo.nodes]
    bordas = [VERDE if e in caminho else "white" for e in grafo.nodes]

    nx.draw_networkx_edges(
        grafo, posicoes, ax=eixo,
        edgelist=[a for a in grafo.edges if a not in arestas_otimas],
        edge_color=CINZA, width=0.5, alpha=0.35,
        arrows=True, arrowsize=6, connectionstyle="arc3,rad=0.12",
    )
    nx.draw_networkx_edges(
        grafo, posicoes, ax=eixo, edgelist=list(arestas_otimas),
        edge_color=VERDE, width=2.6, arrows=True, arrowsize=16,
        connectionstyle="arc3,rad=0.12",
    )
    nx.draw_networkx_nodes(
        grafo, posicoes, ax=eixo, node_color=cores, node_size=760,
        edgecolors=bordas, linewidths=2.2,
    )
    nx.draw_networkx_labels(
        grafo, posicoes, ax=eixo,
        labels={e: _rotulo(e) for e in grafo.nodes},
        font_size=6.5, font_color="white", font_weight="bold",
    )

    for coluna in sorted(colunas):
        eixo.text(
            coluna * 2.6, 1.0, f"{coluna} do outro lado",
            ha="center", va="bottom", fontsize=8.5, color="#39424e",
        )

    marcadores = [
        plt.Line2D([], [], marker="o", linestyle="", markersize=10,
                   markerfacecolor=AZUL, markeredgecolor="white",
                   label="tocha na margem inicial"),
        plt.Line2D([], [], marker="o", linestyle="", markersize=10,
                   markerfacecolor=LARANJA, markeredgecolor="white",
                   label="tocha na margem final"),
        plt.Line2D([], [], color=VERDE, linewidth=2.6,
                   label="caminho otimo (17 min)"),
    ]
    eixo.legend(handles=marcadores, loc="lower center", ncol=3,
                frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.09))
    eixo.set_title(
        "Espaco de estados do problema da Ponte e da Tocha\n"
        "rotulo: pessoas na margem inicial e margem onde esta a tocha",
        fontsize=11,
    )
    eixo.axis("off")
    _salvar(fig, "grafo_estados.png")


def figura_solucao_otima(problema: ProblemaPonteTocha) -> None:
    """Diagrama em escada das travessias da solucao otima."""
    solucao = busca_a_estrela(problema, h2_soma_alternada).solucao
    passos = solucao.caminho()[1:]

    fig, eixo = plt.subplots(figsize=(8.2, 4.6))
    total = len(passos)

    for indice, no in enumerate(passos):
        y = total - indice
        vai_para_direita = "->" in no.acao
        x0, x1 = (0.12, 0.88) if vai_para_direita else (0.88, 0.12)
        cor = VERDE if vai_para_direita else VERMELHO
        eixo.annotate(
            "", xy=(x1, y), xytext=(x0, y),
            arrowprops=dict(arrowstyle="-|>", color=cor, linewidth=2.4),
        )
        custo = no.g - no.pai.g
        eixo.text(
            0.5, y + 0.17, f"{no.acao.split()[0]}  ({custo} min)",
            ha="center", va="bottom", fontsize=10.5, color=cor, fontweight="bold",
        )
        eixo.text(
            0.965, y, f"{no.g} min", ha="left", va="center",
            fontsize=9.5, color="#39424e",
        )
        nomes = "".join(sorted(p.nome for p in no.estado.esquerda)) or "vazio"
        eixo.text(0.035, y, nomes, ha="right", va="center",
                  fontsize=9, color="#6b7480")

    eixo.axvline(0.10, color="#39424e", linewidth=2)
    eixo.axvline(0.90, color="#39424e", linewidth=2)
    eixo.text(0.30, total + 0.62, "margem inicial", ha="center", fontsize=9.5)
    eixo.text(0.70, total + 0.62, "margem final", ha="center", fontsize=9.5)
    eixo.text(0.035, total + 0.62, "restam", ha="right", fontsize=8.5, color="#6b7480")
    eixo.text(0.965, total + 0.62, "acumulado", ha="left", fontsize=8.5,
              color="#6b7480")

    eixo.set_xlim(-0.06, 1.12)
    eixo.set_ylim(0.3, total + 1.35)
    eixo.set_title(
        f"Solucao otima: {solucao.g} minutos em {total} travessias", fontsize=12
    )
    eixo.axis("off")
    _salvar(fig, "solucao_otima.png")


def figura_comparativo(problema: ProblemaPonteTocha) -> None:
    """Custo da solucao e nos expandidos por algoritmo."""
    resumos = coletar(problema, repeticoes=30, limite_nos=100_000)
    nomes = [
        r.algoritmo.replace("Busca ", "")
        .replace(" (DFS)", "\n(DFS)")
        .replace(" (BFS)", "\n(BFS)")
        .replace("A* (h", "A*\n(h")
        for r in resumos
    ]
    custos = [r.custo for r in resumos]
    expandidos = [r.nos_expandidos for r in resumos]

    fig, (esq, dir_) = plt.subplots(1, 2, figsize=(10, 4.1))
    cores = [VERMELHO, LARANJA, AZUL, AZUL]

    barras = esq.bar(nomes, custos, color=cores, width=0.6)
    esq.axhline(17, color=VERDE, linestyle="--", linewidth=1.6,
                label="custo otimo = 17 min")
    esq.legend(frameon=False, fontsize=9, loc="upper right")
    esq.bar_label(barras, fmt="%d min", padding=3, fontsize=9)
    esq.set_ylabel("Custo da solucao (minutos)")
    esq.set_title("Qualidade da solucao encontrada", fontsize=11)
    esq.set_ylim(0, max(custos) * 1.22)

    barras = dir_.bar(nomes, expandidos, color=cores, width=0.6)
    dir_.bar_label(barras, fmt="%.0f", padding=3, fontsize=9)
    dir_.set_ylabel("Nos expandidos")
    dir_.set_title("Esforco de busca", fontsize=11)
    dir_.set_ylim(0, max(expandidos) * 1.22)

    for eixo in (esq, dir_):
        eixo.tick_params(axis="x", labelsize=8.5)
        eixo.spines["top"].set_visible(False)
        eixo.spines["right"].set_visible(False)

    fig.suptitle("Comparacao dos metodos na instancia de quatro pessoas", fontsize=12)
    fig.tight_layout()
    _salvar(fig, "comparativo_algoritmos.png")


def figura_escalabilidade() -> None:
    """Nos expandidos pelo A* com h1 e com h2 conforme o problema cresce."""
    dados = experimento_escalabilidade()
    pessoas = [d["pessoas"] for d in dados]
    com_h1 = [d["expandidos_h1"] for d in dados]
    com_h2 = [d["expandidos_h2"] for d in dados]

    fig, eixo = plt.subplots(figsize=(7.2, 4.3))
    eixo.plot(pessoas, com_h1, marker="o", color=LARANJA, linewidth=2,
              label="A* com $h_1$")
    eixo.plot(pessoas, com_h2, marker="s", color=AZUL, linewidth=2,
              label="A* com $h_2$")
    eixo.set_yscale("log")
    eixo.set_xticks(pessoas)
    eixo.set_xlabel("Numero de pessoas na instancia")
    eixo.set_ylabel("Nos expandidos (escala log)")
    eixo.set_title(
        "Efeito da dominancia: $h_2 \\geq h_1$ reduz o esforco de busca",
        fontsize=11,
    )
    eixo.grid(True, which="both", linestyle=":", linewidth=0.6, alpha=0.6)
    eixo.legend(frameon=False)
    eixo.spines["top"].set_visible(False)
    eixo.spines["right"].set_visible(False)

    for x, a, b in zip(pessoas, com_h1, com_h2):
        if a > b:
            eixo.annotate(
                f"-{(1 - b / a) * 100:.0f}%", xy=(x, b), xytext=(0, -16),
                textcoords="offset points", ha="center", fontsize=8.5, color=AZUL,
            )

    fig.tight_layout()
    _salvar(fig, "escalabilidade_heuristicas.png")


def main() -> None:
    problema = ProblemaPonteTocha()
    figura_grafo_estados(problema)
    figura_solucao_otima(problema)
    figura_comparativo(problema)
    figura_escalabilidade()


if __name__ == "__main__":
    main()
