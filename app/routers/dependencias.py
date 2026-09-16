"""Peças reaproveitadas pelas rotas: a base carregada e os filtros lidos da URL."""
from fastapi import HTTPException, Query

from app.data import estado
from app.data.loader import Base
from app.services.filtros import FiltroClientes, FiltroProdutos


def base_carregada() -> Base:
    base = estado.base_atual()
    if base is None:
        raise HTTPException(status_code=503, detail=estado.erro_atual() or "Base não carregada")
    return base


def filtro_clientes(
    regiao: str | None = Query(None, description="Regiões separadas por vírgula"),
    uf: str | None = Query(None, description="UFs separadas por vírgula"),
    share_min: float | None = Query(None, ge=0, le=1, description="Share mínimo do cliente (0.01 = 1%)"),
    compra_familia: str | None = Query(None, description="Clientes que compram estas famílias (vírgula)"),
    compra_produto: str | None = Query(None, description="Clientes que compram estes códigos (vírgula)"),
) -> FiltroClientes:
    return FiltroClientes.da_url(regiao, uf, share_min, compra_familia, compra_produto)


def filtro_produtos(
    familia: str | None = None,
    abc: str | None = None,
    nivel: str | None = None,
    risco: str | None = None,
    tipo: str | None = None,
    estrategico: str | None = Query(None, description="sim ou nao"),
    especialidade: str | None = Query(None, description="sim ou nao"),
    site: str | None = Query(None, description="sim ou nao"),
) -> FiltroProdutos:
    return FiltroProdutos.da_url(familia, abc, nivel, risco, tipo, estrategico, especialidade, site)
