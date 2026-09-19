from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet

from .pessoa import Pessoa


class Lado(Enum):
    """Margem da ponte em que a tocha (ou uma pessoa) se encontra."""

    ESQUERDA = "esq"
    DIREITA = "dir"

    @property
    def oposto(self) -> "Lado":
        return Lado.DIREITA if self is Lado.ESQUERDA else Lado.ESQUERDA

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Estado:
    """Estado ``s = (E, T)`` do quebra-cabeca.

    ``E``: conjunto de pessoas na margem inicial (esquerda).
    ``T``: lado da ponte em que a tocha se encontra.
    """

    esquerda: FrozenSet[Pessoa]
    tocha: Lado

    def direita(self, universo: FrozenSet[Pessoa]) -> FrozenSet[Pessoa]:
        """Pessoas que ja estao na margem final."""
        return universo - self.esquerda

    def pessoas_com_a_tocha(self, universo: FrozenSet[Pessoa]) -> FrozenSet[Pessoa]:
        """Pessoas que podem realizar a proxima travessia.

        Somente quem esta do mesmo lado da tocha pode atravessar, pois a
        travessia exige o uso dela.
        """
        if self.tocha is Lado.ESQUERDA:
            return self.esquerda
        return self.direita(universo)

    def mover(self, grupo: FrozenSet[Pessoa]) -> "Estado":
        """Estado resultante de mover ``grupo`` junto com a tocha."""
        if self.tocha is Lado.ESQUERDA:
            nova_esquerda = self.esquerda - grupo
        else:
            nova_esquerda = self.esquerda | grupo
        return Estado(esquerda=nova_esquerda, tocha=self.tocha.oposto)

    def __str__(self) -> str:
        nomes = "".join(sorted(p.nome for p in self.esquerda)) or "-"
        return f"({nomes} | {self.tocha})"
