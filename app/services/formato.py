"""Números no padrão brasileiro, para os títulos-conclusão dos gráficos."""


def numero(valor: float, casas: int = 0) -> str:
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def pct(fracao: float, casas: int = 1) -> str:
    return numero(fracao * 100, casas) + "%"


def toneladas(kg: float, casas: int = 1) -> str:
    return numero(kg / 1000, casas) + " t"
