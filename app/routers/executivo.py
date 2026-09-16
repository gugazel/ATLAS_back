"""Página 1 — Visão executiva."""
from fastapi import APIRouter, Depends

from app.data.loader import Base
from app.routers.dependencias import base_carregada
from app.schemas import Alerta, Executivo, Visao
from app.services.alertas import gerar_alertas
from app.services.executivo import executivo

router = APIRouter(prefix="/api", tags=["executivo"])


@router.get("/executivo", response_model=Executivo)
def get_executivo(visao: Visao = "cliente", base: Base = Depends(base_carregada)) -> Executivo:
    """Cartões, gráficos e os 5 alertas principais. `visao` = cliente (CNPJ) ou grupo econômico."""
    return executivo(base, visao)


@router.get("/alertas", response_model=list[Alerta])
def get_alertas(visao: Visao = "cliente", base: Base = Depends(base_carregada)) -> list[Alerta]:
    return gerar_alertas(base, visao)
