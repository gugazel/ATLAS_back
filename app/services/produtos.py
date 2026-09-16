"""Página 4 — Produtos e famílias: treemap, tabela de famílias e tabela de produtos."""
from app.data.loader import NAO_CLASSIFICADO, Base
from app.services.filtros import FiltroProdutos, filtrar_produtos
from app.services.serializar import linhas

COLUNAS_PRODUTO = [
    "codigo", "descricao", "familia", "subfamilia", "aplicacao", "resina", "tipo",
    "especialidade", "estrategico", "site", "prioridade_mkt", "status",
    "volume_kg", "share", "n_clientes", "n_saidas", "kg_por_cliente", "dependencia",
    "classe_abc", "abc_planilha", "ipe_v5", "nivel", "faixa_risco", "motivo_risco", "indice_div", "tem_cadastro", "posicao",
    "compradores", "n_compradores",  # do relatório de vendas (+ clientes de referência)
]


def _familias(p, total_produtos: float, compras) -> list[dict]:
    # clientes distintos por família, segundo o relatório de vendas (antes só dava para somar)
    ligadas = compras[compras["id_cliente"].notna() & compras["codigo"].isin(set(p["codigo"]))]
    distintos = ligadas.groupby("familia")["id_cliente"].nunique().to_dict()
    familias = []
    for familia, g in p.groupby("familia"):
        v = float(g["volume_kg"].sum())
        familias.append({
            "familia": familia,
            "volume_kg": v,
            "share": v / total_produtos,
            "n_produtos": len(g),
            "clientes_distintos": int(distintos.get(familia, 0)),
            "clientes_somados": int(g["n_clientes"].sum()),
            "estrategicos": int(g["estrategico"].sum()),
            "site": int(g["site"].sum()),
            "especialidades": int(g["especialidade"].sum()),
            "risco_alto": int((g["faixa_risco"] == "Alto").sum()),
        })
    familias.sort(key=lambda f: (f["familia"] == NAO_CLASSIFICADO, -f["volume_kg"]))
    return familias


def _treemap(p) -> list[dict]:
    """Hierarquia Família → Subfamília → Produto (tamanho = volume)."""
    arvore = []
    for familia, gf in p.groupby("familia"):
        subfamilias = []
        for subfamilia, gs in gf.groupby("subfamilia"):
            filhos = [
                {"name": cod, "value": float(v), "risco": risco, "motivo": motivo, "nivel": nivel, "descricao": desc}
                for cod, v, risco, motivo, nivel, desc in zip(gs["codigo"], gs["volume_kg"], gs["faixa_risco"],
                                                               gs["motivo_risco"], gs["nivel"], gs["descricao"])
                if v > 0
            ]
            if filhos:
                subfamilias.append({"name": subfamilia, "value": float(gs["volume_kg"].sum()), "children": filhos})
        if subfamilias:
            arvore.append({"name": familia, "value": float(gf["volume_kg"].sum()), "children": subfamilias})
    return sorted(arvore, key=lambda n: -n["value"])


def pagina_produtos(base: Base, f: FiltroProdutos) -> dict:
    todos = base.produtos
    p = filtrar_produtos(todos, f)
    total_produtos = float(todos["volume_kg"].sum())
    total_oficial = float(base.registros["volume_kg"].sum())
    volume = float(p["volume_kg"].sum())
    return {
        "kpis": {
            "n": len(p),
            "volume_kg": volume,
            "share_produtos": volume / total_produtos,
            "cobertura_produtos": total_produtos / total_oficial,
            "estrategicos": int(p["estrategico"].sum()),
            "especialidades": int(p["especialidade"].sum()),
            "site": int(p["site"].sum()),
            "um_cliente": int((p["n_clientes"] == 1).sum()),
            "sem_cadastro": int((~p["tem_cadastro"]).sum()),
        },
        "produtos": linhas(p, COLUNAS_PRODUTO),
        "familias": _familias(p, total_produtos, base.compras),
        "treemap": _treemap(p),
    }
