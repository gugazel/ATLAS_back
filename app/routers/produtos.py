"""Página 4 — Produtos e famílias."""
from fastapi import APIRouter, Depends

from app.data.loader import Base
from app.routers.dependencias import base_carregada, filtro_produtos
from app.services.filtros import FiltroProdutos
from app.services.produtos import pagina_produtos

router = APIRouter(prefix="/api", tags=["produtos"])


@router.get("/produtos")
def get_produtos(f: FiltroProdutos = Depends(filtro_produtos), base: Base = Depends(base_carregada)) -> dict:
    return pagina_produtos(base, f)
