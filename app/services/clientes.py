"""Página 2 — Clientes: ranking, concentração, dispersão, famílias compradas e perfil."""
from app.data.loader import NAO_CLASSIFICADO, Base
from app.services.filtros import FiltroClientes, agrupar, filtrar_clientes
from app.services.serializar import linhas

COLUNAS_RANKING = [
    "id", "posicao", "nome", "volume_kg", "share", "share_filtro", "share_acum",
    "n_produtos", "n_saidas", "kg_por_saida", "uf", "ufs", "regiao", "cidade", "fonte_uf", "fonte_uf_link", "local_base",
    "cnpj", "nome_grupo", "id_grupo", "n_membros", "membros", "status_de_para",
    "produtos_comprados", "familias_compradas",  # do relatório de vendas (sem volume por produto)
]

FAIXAS_PRODUTOS = [("1", 1, 1), ("2", 2, 2), ("3", 3, 3), ("4–5", 4, 5), ("6+", 6, 10**9)]


def familias_por_clientes(compras, ids: set) -> list[dict]:
    """Quantos clientes (distintos) do conjunto compram cada família, segundo o relatório de vendas."""
    c = compras[compras["id_cliente"].isin(ids) & (compras["familia"] != NAO_CLASSIFICADO)]
    contagem = c.drop_duplicates(["id_cliente", "familia"]).groupby("familia").size().sort_values(ascending=False)
    return [{"familia": f, "n_clientes": int(n)} for f, n in contagem.items()]


def pagina_clientes(base: Base, visao: str, f: FiltroClientes) -> dict:
    total = float(base.clientes["volume_kg"].sum())
    selecao = filtrar_clientes(base.clientes, f, base.compras)
    rk = agrupar(selecao, visao, total, f)
    volume = float(rk["volume_kg"].sum())
    ids = set(selecao["id_cliente"]) if visao == "cliente" else set(selecao.loc[selecao["id_grupo"].isin(rk["id"]), "id_cliente"])
    com_compras = selecao[selecao["id_cliente"].isin(ids) & (selecao["produtos_comprados"].map(len) > 0)]

    histograma = []
    for rotulo, minimo, maximo in FAIXAS_PRODUTOS:
        faixa = rk[(rk["n_produtos"] >= minimo) & (rk["n_produtos"] <= maximo)]
        histograma.append({"faixa": rotulo, "n": len(faixa), "volume_kg": float(faixa["volume_kg"].sum())})

    return {
        "visao": visao,
        "kpis": {
            "n": len(rk),
            "volume_kg": volume,
            "share_do_total": volume / total if total else 0.0,
            "n_para_80": int((rk["share_acum"] < 0.80).sum() + 1) if len(rk) else 0,
            "maior_nome": rk["nome"].iloc[0] if len(rk) else None,
            "maior_share_filtro": float(rk["share_filtro"].iloc[0]) if len(rk) else 0.0,
            "com_1_produto": int((rk["n_produtos"] == 1).sum()),
            "mediana_kg_por_saida": float(rk["kg_por_saida"].median()) if len(rk) else 0.0,
            "clientes_no_relatorio": len(com_compras),
            "clientes_selecao": len(ids),
        },
        "ranking": linhas(rk, COLUNAS_RANKING),
        "histograma": histograma,
        "familias": familias_por_clientes(base.compras, ids),
    }
