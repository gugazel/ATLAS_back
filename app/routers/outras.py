"""Páginas 5 a 7 (Riscos, Destaques, Qualidade) e os valores dos filtros."""
from fastapi import APIRouter, Depends

from app.data.loader import Base
from app.routers.dependencias import base_carregada, filtro_clientes, filtro_produtos
from app.schemas import Visao
from app.services.destaques import pagina_destaques
from app.services.filtros import FiltroClientes, FiltroProdutos
from app.services.meta import opcoes_filtros
from app.services.prospeccao import pagina_prospeccao
from app.services.qualidade import pagina_qualidade
from app.services.riscos import pagina_riscos

router = APIRouter(prefix="/api")


@router.get("/riscos", tags=["riscos"])
def get_riscos(visao: Visao = "cliente", f: FiltroProdutos = Depends(filtro_produtos),
               base: Base = Depends(base_carregada)) -> dict:
    return pagina_riscos(base, visao, f)


@router.get("/prospeccao", tags=["prospeccao"])
def get_prospeccao(setor: str | None = None, status: str | None = None,
                   f: FiltroClientes = Depends(filtro_clientes), base: Base = Depends(base_carregada)) -> dict:
    """Empresas prospectadas pela equipe (possíveis clientes)."""
    return pagina_prospeccao(base, f, setor, status)


@router.get("/destaques", tags=["destaques"])
def get_destaques(base: Base = Depends(base_carregada)) -> dict:
    return pagina_destaques(base)


@router.get("/qualidade", tags=["qualidade"])
def get_qualidade(base: Base = Depends(base_carregada)) -> dict:
    return pagina_qualidade(base)


@router.get("/meta/filtros", tags=["sistema"])
def get_filtros(base: Base = Depends(base_carregada)) -> dict:
    return opcoes_filtros(base)
