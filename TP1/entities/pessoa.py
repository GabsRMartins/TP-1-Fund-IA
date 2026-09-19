from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Pessoa:

    tempo: int
    nome: str

    def __str__(self) -> str:
        return self.nome



PESSOAS_PADRAO = (
    Pessoa(tempo=1, nome="A"),
    Pessoa(tempo=2, nome="B"),
    Pessoa(tempo=5, nome="C"),
    Pessoa(tempo=10, nome="D"),
)
