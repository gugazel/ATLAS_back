"""Filtros globais (seção 11 do plano).

Com o relatório de vendas cliente × produto, as páginas de cliente podem ser filtradas por
"compra a família" / "compra o produto" (quem aparece comprando no relatório). O contrário
(filtrar produtos por região do cliente) continua fora: não há volume por cliente × produto,
então o volume de um produto não pode ser dividido por região.

Na URL, listas vêm separadas por vírgula: ?regiao=Sudeste,Sul&uf=SP&compra_familia=Antichama
"""
from dataclasses import dataclass, field

import pandas as pd

from app.data.loader import NAO_CLASSIFICADO, UF_REGIAO


def lista(valor: str | None) -> list[str]:
    return [v.strip() for v in (valor or "").split(",") if v.strip()]


def sim_nao(valor: str | None) -> bool | None:
    return {"sim": True, "nao": False, "não": False}.get((valor or "").strip().lower())


# ---------------------------------------------------------------- clientes

@dataclass
class FiltroClientes:
    regiao: list[str] = field(default_factory=list)
    uf: list[str] = field(default_factory=list)
    share_min: float = 0.0  # fração do total oficial (0.01 = 1%)
    compra_familia: list[str] = field(default_factory=list)  # clientes que compram alguma dessas famílias
    compra_produto: list[str] = field(default_factory=list)  # ... e/ou algum desses códigos

    @classmethod
    def da_url(cls, regiao: str | None, uf: str | None, share_min: float | None,
               compra_familia: str | None = None, compra_produto: str | None = None) -> "FiltroClientes":
        return cls(lista(regiao), [u.upper() for u in lista(uf)], share_min or 0.0,
                   lista(compra_familia), lista(compra_produto))

    @property
    def ativo(self) -> bool:
        return bool(self.regiao or self.uf or self.share_min or self.compra_familia or self.compra_produto)


def compradores(compras: pd.DataFrame, familias: list[str] | None = None, codigos: list[str] | None = None) -> set:
    """Clientes que aparecem comprando alguma das famílias (ou algum dos códigos)."""
    c = compras[compras["id_cliente"].notna()]
    if familias:
        c = c[c["familia"].isin(familias)]
    if codigos:
        c = c[c["codigo"].isin(codigos)]
    return set(c["id_cliente"])


def filtrar_clientes(clientes: pd.DataFrame, f: FiltroClientes, compras: pd.DataFrame | None = None) -> pd.DataFrame:
    """Filtra por local e pelo que o cliente compra. O share mínimo é aplicado depois (ver agrupar)."""
    c = clientes
    if f.regiao:
        c = c[c["regiao"].isin(f.regiao)]
    if f.uf:
        c = c[c["uf"].isin(f.uf)]
    if compras is not None and f.compra_familia:
        c = c[c["id_cliente"].isin(compradores(compras, familias=f.compra_familia))]
    if compras is not None and f.compra_produto:
        c = c[c["id_cliente"].isin(compradores(compras, codigos=f.compra_produto))]
    return c


def _juntar_compras(listas: pd.Series) -> list[dict]:
    """Produtos comprados por um grupo = união dos produtos dos clientes (sem repetir)."""
    unicos = {}
    for lista in listas:
        for a in lista if isinstance(lista, list) else []:
            unicos.setdefault(a["codigo"], a)
    return sorted(unicos.values(), key=lambda a: (a["familia"] == NAO_CLASSIFICADO, a["familia"], a["codigo"]))


def _juntar_familias(listas: pd.Series) -> list[str]:
    return sorted({f for lista in listas if isinstance(lista, list) for f in lista})


def agrupar(clientes_filtrados: pd.DataFrame, visao: str, total_oficial: float, f: FiltroClientes) -> pd.DataFrame:
    """Ranking da seleção, por cliente ou por grupo econômico.

    Na visão por grupo, o volume do grupo é só o dos clientes que passaram no
    filtro de local (ex.: "VALGROUP no Sudeste").
    - share: sobre o total oficial (a carteira inteira)
    - share_filtro: dentro da seleção
    """
    c = clientes_filtrados
    if visao == "grupo":
        ordenados = c.sort_values("volume_kg", ascending=False, kind="stable")
        df = ordenados.groupby("id_grupo", sort=False).agg(
            id=("id_grupo", "first"),
            nome=("nome_grupo", "first"),
            volume_kg=("volume_kg", "sum"),
            n_produtos=("n_produtos", "sum"),
            n_saidas=("n_saidas", "sum"),
            n_membros=("id_cliente", "size"),
            membros=("nome", list),
            uf=("uf", "first"),
            ufs=("uf", lambda s: sorted(s.dropna().unique().tolist())),
            produtos_comprados=("produtos_comprados", _juntar_compras),
            familias_compradas=("familias_compradas", _juntar_familias),
        ).reset_index(drop=True)
    else:
        df = c.rename(columns={"id_cliente": "id", "n_registros": "n_membros", "nomes_originais": "membros"}).copy()
        df["ufs"] = [[u] if isinstance(u, str) else [] for u in df["uf"]]

    df = df.sort_values("volume_kg", ascending=False, kind="stable").reset_index(drop=True)
    df["share"] = df["volume_kg"] / total_oficial
    if f.share_min:
        df = df[df["share"] >= f.share_min].reset_index(drop=True)
    total_filtro = df["volume_kg"].sum()
    df["posicao"] = df.index + 1
    df["share_filtro"] = df["volume_kg"] / total_filtro if total_filtro else 0.0
    df["share_acum"] = df["share_filtro"].cumsum()
    df["kg_por_saida"] = df["volume_kg"] / df["n_saidas"].where(df["n_saidas"] > 0)
    df["regiao"] = df["uf"].map(UF_REGIAO).fillna(NAO_CLASSIFICADO)
    return df


# ---------------------------------------------------------------- produtos

@dataclass
class FiltroProdutos:
    familia: list[str] = field(default_factory=list)
    abc: list[str] = field(default_factory=list)
    nivel: list[str] = field(default_factory=list)
    risco: list[str] = field(default_factory=list)
    tipo: list[str] = field(default_factory=list)
    estrategico: bool | None = None
    especialidade: bool | None = None
    site: bool | None = None

    @classmethod
    def da_url(cls, familia=None, abc=None, nivel=None, risco=None, tipo=None,
               estrategico=None, especialidade=None, site=None) -> "FiltroProdutos":
        return cls(lista(familia), lista(abc), lista(nivel), lista(risco), lista(tipo),
                   sim_nao(estrategico), sim_nao(especialidade), sim_nao(site))

    @property
    def ativo(self) -> bool:
        return any([self.familia, self.abc, self.nivel, self.risco, self.tipo,
                    self.estrategico is not None, self.especialidade is not None, self.site is not None])


def filtrar_produtos(produtos: pd.DataFrame, f: FiltroProdutos) -> pd.DataFrame:
    p = produtos
    for coluna, valores in (("familia", f.familia), ("classe_abc", f.abc), ("nivel", f.nivel),
                            ("faixa_risco", f.risco), ("tipo", f.tipo)):
        if valores:
            p = p[p[coluna].isin(valores)]
    for coluna, valor in (("estrategico", f.estrategico), ("especialidade", f.especialidade), ("site", f.site)):
        if valor is not None:
            p = p[p[coluna] == valor]
    return p
