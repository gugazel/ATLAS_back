"""Guarda a base carregada em memória (os dados são pequenos: ~460 linhas)."""
from app.data.loader import Base, carregar

_base: Base | None = None
_erro: str | None = None


def recarregar() -> None:
    """Relê as planilhas. Se falhar, guarda a mensagem para o /api/saude mostrar."""
    global _base, _erro
    try:
        _base, _erro = carregar(), None
    except Exception as e:  # noqa: BLE001 - a mensagem vai para a tela
        _base, _erro = None, f"{type(e).__name__}: {e}"


def base_atual() -> Base | None:
    return _base


def erro_atual() -> str | None:
    return _erro
