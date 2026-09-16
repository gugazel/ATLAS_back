"""Formatos das respostas da API. Aparecem documentados em /docs."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Visao = Literal["cliente", "grupo"]


class Saude(BaseModel):
    status: Literal["ok", "erro"]
    carregado_em: datetime | None = None
    registros_clientes: int = 0
    clientes: int = 0
    grupos: int = 0
    produtos: int = 0
    avisos: list[str] = []
    erro: str | None = None


class Alerta(BaseModel):
    codigo: str
    severidade: Literal["alta", "media", "baixa"]
    titulo: str
    valor: str
    itens: list[str]
    acao: str
    porque: str                      # por que isto é um risco, com os números


class Kpis(BaseModel):
    volume_oficial_kg: float
    volume_produtos_kg: float
    cobertura_produtos: float        # volume de produtos ÷ volume oficial
    divergencia_kg: float
    n_clientes: int                  # clientes (CNPJ) ou grupos, conforme a visão
    n_produtos: int
    n_saidas: int
    volume_medio_cliente_kg: float
    maior_nome: str
    maior_share: float
    top5_share: float
    produtos_risco_alto: int
    risco_alto_share_volume: float
    clientes_com_uf: int
    cobertura_uf_qtd: float
    cobertura_uf_volume: float


class ItemRanking(BaseModel):
    id: str
    nome: str
    volume_kg: float
    share: float
    uf: str | None
    n_membros: int                   # registros juntados (cliente) ou clientes do grupo


class Fatia(BaseModel):
    nome: str
    volume_kg: float
    share: float
    n: int                           # nº de produtos ou de clientes, conforme o gráfico


class Executivo(BaseModel):
    visao: Visao
    kpis: Kpis
    top10: list[ItemRanking]
    familias: list[Fatia]
    regioes: list[Fatia]
    abc: list[Fatia]
    risco: list[Fatia]
    alertas: list[Alerta]
    titulos: dict[str, str]
