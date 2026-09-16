"""Página 3 — Geografia: mapa por UF, pontos dos clientes e a fila de clientes sem UF."""
import json
from functools import lru_cache

from app import config
from app.data.loader import NAO_CLASSIFICADO, Base
from app.services.clientes import COLUNAS_RANKING
from app.services.filtros import FiltroClientes, agrupar, filtrar_clientes
from app.services.serializar import linhas

ORDEM_REGIOES = ["Sudeste", "Sul", "Centro-Oeste", "Nordeste", "Norte", NAO_CLASSIFICADO]


@lru_cache
def coordenadas_cidades() -> dict[str, list[float]]:
    if not config.ARQ_CIDADES.exists():
        return {}
    return json.loads(config.ARQ_CIDADES.read_text(encoding="utf-8"))


def matriz_familia_regiao(compras, clientes_sel) -> dict:
    """Quantos clientes (distintos) de cada região compram cada família, segundo o relatório de vendas."""
    regiao_de = dict(zip(clientes_sel["id"], clientes_sel["regiao"]))
    c = compras[compras["id_cliente"].isin(regiao_de) & (compras["familia"] != NAO_CLASSIFICADO)].copy()
    c["regiao"] = c["id_cliente"].map(regiao_de)
    tabela = c.drop_duplicates(["id_cliente", "familia"]).groupby(["familia", "regiao"]).size()
    familias = c.drop_duplicates(["id_cliente", "familia"]).groupby("familia").size().sort_values(ascending=False).index.tolist()
    regioes = [r for r in ORDEM_REGIOES if r in set(c["regiao"])]
    clientes_por_regiao = {r: int((clientes_sel["regiao"] == r).sum()) for r in regioes}
    com_compras = {r: int(c.loc[c["regiao"] == r, "id_cliente"].nunique()) for r in regioes}
    return {
        "familias": familias,
        "regioes": regioes,
        "valores": [[fi, ri, int(tabela.get((f, r), 0))] for fi, f in enumerate(familias) for ri, r in enumerate(regioes)],
        "clientes_por_regiao": clientes_por_regiao,
        "com_compras_por_regiao": com_compras,
    }


def pontos_prospeccao(base: Base, f: FiltroClientes) -> list[dict]:
    from app.services.prospeccao import com_coordenadas, filtrar  # evita import circular
    return com_coordenadas(filtrar(base.prospeccao, f, [], []))


def pagina_geografia(base: Base, f: FiltroClientes) -> dict:
    total = float(base.clientes["volume_kg"].sum())
    rk = agrupar(filtrar_clientes(base.clientes, f, base.compras), "cliente", total, f)
    volume = float(rk["volume_kg"].sum())
    com_uf = rk[rk["uf"].notna()]
    sem_uf = rk[rk["uf"].isna()]
    compras_sel = base.compras[base.compras["id_cliente"].isin(set(rk["id"]))]

    estados = []
    for uf, grupo in com_uf.groupby("uf"):
        v = float(grupo["volume_kg"].sum())
        comprado = compras_sel[compras_sel["id_cliente"].isin(set(grupo["id"]))]
        estados.append({
            "uf": uf,
            "regiao": grupo["regiao"].iloc[0],
            "volume_kg": v,
            "share": v / total,
            "share_filtro": v / volume if volume else 0.0,
            "n_clientes": len(grupo),
            "maior_cliente": grupo["nome"].iloc[0],
            # contagens distintas (relatório de vendas): antes só dava para somar contagens
            "n_produtos_distintos": int(comprado["codigo"].nunique()),
            "n_familias": int(comprado.loc[comprado["familia"] != NAO_CLASSIFICADO, "familia"].nunique()),
        })
    estados.sort(key=lambda e: -e["volume_kg"])

    regioes = []
    for regiao in ORDEM_REGIOES:
        grupo = rk[rk["regiao"] == regiao]
        if len(grupo):
            v = float(grupo["volume_kg"].sum())
            regioes.append({"regiao": regiao, "volume_kg": v, "share": v / total,
                            "share_filtro": v / volume if volume else 0.0, "n_clientes": len(grupo)})

    cidades = coordenadas_cidades()
    pontos = linhas(com_uf, COLUNAS_RANKING)
    for ponto in pontos:
        # [longitude, latitude] do centro do município; sem cidade, o mapa posiciona dentro do estado
        ponto["coord"] = cidades.get(f"{ponto['uf']}|{ponto.get('cidade')}")

    return {
        "kpis": {
            "n_clientes": len(rk),
            "volume_kg": volume,
            "share_do_total": volume / total if total else 0.0,
            "n_com_uf": len(com_uf),
            "n_estados": len(estados),
            "n_com_cidade": sum(1 for p in pontos if p["coord"]),
            "volume_com_uf_kg": float(com_uf["volume_kg"].sum()),
        },
        "estados": estados,
        "regioes": regioes,
        "matriz": matriz_familia_regiao(base.compras, rk),
        "pontos": pontos,
        # possíveis clientes: aparecem no mapa com outra cor, sem entrar em nenhum número da carteira
        "prospectos": pontos_prospeccao(base, f),
        "sem_uf": {
            "n": len(sem_uf),
            "volume_kg": float(sem_uf["volume_kg"].sum()),
            "share": float(sem_uf["volume_kg"].sum()) / total if total else 0.0,
            "clientes": linhas(sem_uf, COLUNAS_RANKING),
        },
    }
