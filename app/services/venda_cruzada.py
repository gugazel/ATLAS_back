"""Venda cruzada a partir do relatório de vendas (quem comprou o quê).

Regra de associação entre famílias: "dos N clientes que compram A, X% também compram B".
Um cliente que compra A e não compra B vira sugestão "a investigar" de B.

Cuidados para não enviesar (a ausência de compra sozinha não é oportunidade — seção 8 do plano):
  - só entram clientes cujo relatório parece completo: nº de produtos no relatório pelo menos
    igual ao nº de produtos da Base_Clientes (senão a família "faltando" pode ser só falta de dado);
  - a regra precisa de base mínima (N clientes), confiança mínima e lift > 1 (B é mais comum
    entre quem compra A do que na carteira em geral).
"""
from collections import Counter

import pandas as pd

from app.data.loader import NAO_CLASSIFICADO, Base
from app.services.formato import pct

MIN_BASE = 5          # clientes que compram A
MIN_CONFIANCA = 0.40  # dos que compram A, quantos compram B
MIN_LIFT = 1.2        # B é 20% mais comum entre quem compra A do que em geral


def clientes_completos(base: Base) -> set:
    """Clientes em que o relatório lista pelo menos tantos produtos quanto a Base_Clientes informa."""
    maior_registro = base.registros.groupby("id_cliente")["n_produtos"].max()
    do_relatorio = (base.compras[base.compras["origem"] == "relatório de vendas"]
                    .groupby("id_cliente")["codigo"].nunique())
    return {i for i, n in do_relatorio.items() if n >= maior_registro.get(i, 10**9)}


def regras_familias(conjuntos: pd.Series) -> list[dict]:
    n_total = len(conjuntos)
    por_familia = Counter(f for s in conjuntos for f in s)
    pares = Counter((a, b) for s in conjuntos for a in s for b in s if a != b)
    regras = []
    for (a, b), juntos in pares.items():
        n_a = por_familia[a]
        if n_a < MIN_BASE:
            continue
        confianca = juntos / n_a
        lift = confianca / (por_familia[b] / n_total)
        if confianca >= MIN_CONFIANCA and lift >= MIN_LIFT:
            regras.append({"se": a, "entao": b, "n_se": n_a, "n_ambos": juntos,
                           "confianca": confianca, "lift": lift})
    return sorted(regras, key=lambda r: (-r["confianca"], -r["n_se"]))


def venda_cruzada(base: Base) -> dict:
    compras = base.compras[base.compras["id_cliente"].notna() & (base.compras["familia"] != NAO_CLASSIFICADO)]
    conjuntos = compras.drop_duplicates(["id_cliente", "familia"]).groupby("id_cliente")["familia"].apply(set)
    regras = regras_familias(conjuntos)

    completos = clientes_completos(base)
    info = base.clientes.set_index("id_cliente")
    melhores: dict[tuple, dict] = {}
    for id_cliente, familias in conjuntos.items():
        if id_cliente not in completos:
            continue
        for r in regras:
            if r["se"] in familias and r["entao"] not in familias:
                chave = (id_cliente, r["entao"])
                if chave not in melhores or r["confianca"] > melhores[chave]["confianca"]:
                    melhores[chave] = r

    sugestoes = []
    for (id_cliente, familia), r in melhores.items():
        c = info.loc[id_cliente]
        sugestoes.append({
            "id": id_cliente, "nome": c["nome"], "volume_kg": float(c["volume_kg"]), "uf": c["uf"] if isinstance(c["uf"], str) else None,
            "familia_sugerida": familia, "compra": r["se"],
            "familias_atuais": sorted(conjuntos[id_cliente]),
            "confianca": r["confianca"], "n_se": r["n_se"], "lift": r["lift"],
            "porque": f"{pct(r['confianca'], 0)} dos {r['n_se']} clientes que compram {r['se']} também compram {familia}",
        })
    sugestoes.sort(key=lambda s: (-s["volume_kg"], -s["confianca"]))

    return {
        "regras": regras[:20],
        "sugestoes": sugestoes,
        "n_clientes_com_familias": len(conjuntos),
        "n_clientes_completos": len(completos & set(conjuntos.index)),
        "limites": {"min_base": MIN_BASE, "min_confianca": MIN_CONFIANCA, "min_lift": MIN_LIFT},
    }
