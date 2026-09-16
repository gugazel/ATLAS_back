"""Rotas de sistema: saúde da API e recarga das planilhas."""
from fastapi import APIRouter

from app.data import estado
from app.schemas import Saude

router = APIRouter(prefix="/api", tags=["sistema"])


@router.get("/saude", response_model=Saude)
def saude() -> Saude:
    base = estado.base_atual()
    if base is None:
        return Saude(status="erro", erro=estado.erro_atual())
    return Saude(
        status="ok",
        carregado_em=base.carregado_em,
        registros_clientes=len(base.registros),
        clientes=len(base.clientes),
        grupos=len(base.grupos),
        produtos=len(base.produtos),
        avisos=base.avisos,
    )


@router.post("/recarregar", response_model=Saude)
def recarregar() -> Saude:
    """Relê as planilhas da pasta data/ (use depois de trocar o Excel ou editar o de-para)."""
    estado.recarregar()
    return saude()
