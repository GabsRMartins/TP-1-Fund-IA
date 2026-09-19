from dataclasses import dataclass
from itertools import combinations
from typing import FrozenSet, Iterable, Iterator, List, Sequence, Tuple

from entities.estado import Estado, Lado
from entities.pessoa import PESSOAS_PADRAO, Pessoa


@dataclass(frozen=True)
class Transicao:

    acao: str
    estado: Estado
    custo: int
    grupo: FrozenSet[Pessoa]


class ProblemaPonteTocha:
    def __init__(
        self,
        pessoas: Sequence[Pessoa] = PESSOAS_PADRAO,
        capacidade: int = 2,
    ) -> None:
        self.pessoas: Tuple[Pessoa, ...] = tuple(pessoas)
        self.universo: FrozenSet[Pessoa] = frozenset(self.pessoas)
        self.capacidade = capacidade

    # ------------------------------------------------------------------
    # Estados inicial e objetivo
    # ------------------------------------------------------------------
    @property
    def estado_inicial(self) -> Estado:
        """``s0 = (P, esquerda)``: todos na margem inicial, com a tocha."""
        return Estado(esquerda=self.universo, tocha=Lado.ESQUERDA)

    @property
    def estado_objetivo(self) -> Estado:
        """``sg = (vazio, direita)``: todos na margem final."""
        return Estado(esquerda=frozenset(), tocha=Lado.DIREITA)

    def eh_objetivo(self, estado: Estado) -> bool:

        return len(estado.esquerda) == 0

    # ------------------------------------------------------------------
    # Funcao sucessora
    # ------------------------------------------------------------------
    def grupos_validos(self, estado: Estado) -> Iterator[FrozenSet[Pessoa]]:
        candidatos = sorted(estado.pessoas_com_a_tocha(self.universo))
        for tamanho in range(1, self.capacidade + 1):
            for grupo in combinations(candidatos, tamanho):
                yield frozenset(grupo)

    def custo(self, grupo: Iterable[Pessoa]) -> int:
        """Custo da travessia: o tempo da pessoa mais lenta do grupo."""
        return max(pessoa.tempo for pessoa in grupo)

    def sucessores(self, estado: Estado) -> List[Transicao]:
        transicoes: List[Transicao] = []
        for grupo in self.grupos_validos(estado):
            novo_estado = estado.mover(grupo)
            transicoes.append(
                Transicao(
                    acao=self.rotular(grupo, estado.tocha),
                    estado=novo_estado,
                    custo=self.custo(grupo),
                    grupo=grupo,
                )
            )
        return transicoes

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    @staticmethod
    def rotular(grupo: Iterable[Pessoa], origem: Lado) -> str:
        """Rotulo legivel de uma acao, por exemplo ``AB ->`` ou ``A <-``."""
        nomes = "".join(sorted(pessoa.nome for pessoa in grupo))
        seta = "->" if origem is Lado.ESQUERDA else "<-"
        return f"{nomes} {seta}"

    def estados_alcancaveis(self) -> List[Estado]:
        vistos = {self.estado_inicial}
        fila = [self.estado_inicial]
        while fila:
            atual = fila.pop(0)
            for transicao in self.sucessores(atual):
                if transicao.estado not in vistos:
                    vistos.add(transicao.estado)
                    fila.append(transicao.estado)
        return sorted(vistos, key=lambda e: (len(e.esquerda), str(e)))
