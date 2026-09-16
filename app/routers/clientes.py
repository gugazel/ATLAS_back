"""Página 2 — Clientes."""
from fastapi import APIRouter, Depends

from app.data.loader import Base
from app.routers.dependencias import base_carregada, filtro_clientes
from app.schemas import Visao
from app.services.clientes import pagina_clientes
from app.services.filtros import FiltroClientes

router = APIRouter(prefix="/api", tags=["clientes"])


@router.get("/clientes")
def get_clientes(visao: Visao = "cliente", f: FiltroClientes = Depends(filtro_clientes),
                 base: Base = Depends(base_carregada)) -> dict:
    """Ranking com share, share acumulado e dados de perfil de cada cliente (ou grupo)."""
    return pagina_clientes(base, visao, f)
