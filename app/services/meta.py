"""Valores possíveis de cada filtro, para montar os menus do frontend."""
from app.data.loader import NAO_CLASSIFICADO, Base, definicoes_risco
from app.services.geografia import ORDEM_REGIOES


def opcoes_filtros(base: Base) -> dict:
    c, p = base.clientes, base.produtos
    regioes_presentes = set(c["regiao"])
    ufs = (c[c["tem_uf"]].groupby("uf").agg(regiao=("regiao", "first"), n=("id_cliente", "size"))
           .reset_index().sort_values("uf"))
    familias = p.groupby("familia")["volume_kg"].sum().sort_values(ascending=False).index.tolist()
    if NAO_CLASSIFICADO in familias:
        familias = [f for f in familias if f != NAO_CLASSIFICADO] + [NAO_CLASSIFICADO]
    return {
        "regiao": [r for r in ORDEM_REGIOES if r in regioes_presentes],
        "uf": [{"valor": u, "regiao": r, "n": int(n)} for u, r, n in zip(ufs["uf"], ufs["regiao"], ufs["n"])],
        "familia": familias,
        "abc": ["A", "B", "C"],
        "nivel": ["OURO", "PRATA", "BRONZE", "MONITORAR"],
        "risco": ["Alto", "Médio", "Baixo"],
        "tipo": sorted(p["tipo"].dropna().unique().tolist()),
        "definicoes_risco": definicoes_risco(),
        # aba Prospecção
        "setor": sorted(base.prospeccao["setor"].dropna().unique().tolist()),
        "status_prospeccao": sorted(base.prospeccao["status"].dropna().unique().tolist()),
        # filtros "compra a família" / "compra o produto" (clientes que aparecem comprando no relatório)
        "compra_familia": [f for f in familias if f != NAO_CLASSIFICADO and f in set(base.compras["familia"])],
        "compra_produto": [
            {"valor": cod, "rotulo": cod, "extra": texto_curto(desc)}
            for cod, desc in base.compras.sort_values("codigo").drop_duplicates("codigo")[["codigo", "descricao"]].itertuples(index=False)
        ],
    }


def texto_curto(texto, limite: int = 34) -> str:
    texto = str(texto or "")
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"
