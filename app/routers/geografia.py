"""Página 3 — Geografia."""
from fastapi import APIRouter, Depends

from app.data.loader import Base
from app.routers.dependencias import base_carregada, filtro_clientes
from app.services.filtros import FiltroClientes
from app.services.geografia import pagina_geografia

router = APIRouter(prefix="/api", tags=["geografia"])


@router.get("/geografia")
def get_geografia(f: FiltroClientes = Depends(filtro_clientes), base: Base = Depends(base_carregada)) -> dict:
    """Volume por UF e região, pontos dos clientes (com coordenada da cidade, quando houver) e clientes sem UF."""
    return pagina_geografia(base, f)
