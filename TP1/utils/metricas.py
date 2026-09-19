"""Estruturas para registrar o desempenho de uma execucao de busca."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from entities.no import No


@dataclass
class ResultadoBusca:

    algoritmo: str
    solucao: Optional[No] = None
    nos_expandidos: int = 0
    nos_gerados: int = 0
    tempo: float = 0.0
    limite_atingido: bool = False
    tamanho_maximo_fronteira: int = 0

    @property
    def sucesso(self) -> bool:
        return self.solucao is not None

    @property
    def custo(self) -> Optional[int]:
        """Tempo total de travessia da solucao encontrada."""
        return self.solucao.g if self.solucao else None

    @property
    def travessias(self) -> Optional[int]:
        """Numero de travessias (profundidade da solucao)."""
        return self.solucao.profundidade if self.solucao else None

    def caminho_formatado(self) -> str:
        """Descreve a solucao como ``AB -> (2) | A <- (3) | ...``."""
        if not self.solucao:
            return "sem solucao"
        partes = [f"{acao} [{acumulado} min]" for acao, acumulado in self.solucao.acoes()]
        return "  ".join(partes)


@dataclass
class ResumoExecucoes:
    """Agregacao de varias repeticoes de um mesmo algoritmo.   """

    algoritmo: str
    repeticoes: int
    custo: Optional[int]
    travessias: Optional[int]
    nos_expandidos: float
    nos_gerados: float
    tempo_medio: float
    tempo_desvio: float
    limite_atingido: bool
    caminho: str
    tempos: List[float] = field(default_factory=list)

    def linha_tabela(self) -> Tuple[str, str, str, str, str]:
        """Campos formatados para a tabela comparativa do relatorio."""
        custo = str(self.custo) if self.custo is not None else "--"
        travessias = str(self.travessias) if self.travessias is not None else "--"
        return (
            self.algoritmo,
            custo,
            travessias,
            f"{self.nos_expandidos:.0f}",
            f"{self.tempo_medio * 1000:.4f}",
        )
