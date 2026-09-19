"""No da arvore de busca."""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .estado import Estado


@dataclass
class No:
    """Representa um caminho da raiz ate ``estado``. """

    estado: Estado
    pai: Optional["No"] = None
    acao: Optional[str] = None
    g: int = 0
    h: int = 0
    profundidade: int = 0

    @property
    def f(self) -> int:
        """Estimativa do custo total do caminho que passa por este no."""
        return self.g + self.h

    def caminho(self) -> List["No"]:
        """Sequencia de nos da raiz ate este no."""
        no: Optional[No] = self
        caminho: List[No] = []
        while no is not None:
            caminho.append(no)
            no = no.pai
        caminho.reverse()
        return caminho

    def acoes(self) -> List[Tuple[str, int]]:
        """Lista de ``(acao, custo acumulado)`` da raiz ate este no."""
        return [(no.acao, no.g) for no in self.caminho() if no.acao is not None]

    def contem_estado_no_caminho(self, estado: Estado) -> bool:
        no: Optional[No] = self
        while no is not None:
            if no.estado == estado:
                return True
            no = no.pai
        return False
