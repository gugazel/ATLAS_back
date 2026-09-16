"""Página 7 — Qualidade da base: o que precisa ser corrigido no cadastro."""
import re
from itertools import combinations

from app.data.loader import Base
from app.services.alertas import gerar_alertas
from app.services.clientes import COLUNAS_RANKING
from app.services.filtros import FiltroClientes, agrupar
from app.services.serializar import linhas

ORDEM_STATUS = ["exato", "sugerido", "ok", "revisar", "rejeitado", "sem_cnpj", "sem_de_para"]


def _normalizar_codigo(codigo: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", codigo.upper())


def _uma_edicao_com_letra(a: str, b: str) -> bool:
    """True se a e b diferem por 1 letra: inserida, removida ou trocada por outra letra.

    Trocas que envolvem dígitos (M9089 × M9088, M9010/1 × M9010C) são códigos diferentes de verdade.
    """
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        diferentes = [(x, y) for x, y in zip(a, b) if x != y]
        return len(diferentes) == 1 and diferentes[0][0].isalpha() and diferentes[0][1].isalpha()
    curto, longo = sorted((a, b), key=len)
    for i in range(len(longo)):
        if longo[:i] + longo[i + 1:] == curto:
            return not longo[i].isdigit()
    return False


def codigos_parecidos(codigos: list[str]) -> list[dict]:
    """Pares de códigos que podem ser o mesmo produto digitado de outro jeito (a validar)."""
    pares = []
    for a, b in combinations(sorted(codigos), 2):
        na, nb = _normalizar_codigo(a), _normalizar_codigo(b)
        curto, longo = sorted((na, nb), key=len)
        if na == nb:
            motivo = "iguais sem pontuação"
        elif longo.startswith(curto) and longo[len(curto):] == "01":
            motivo = "um tem o sufixo /01"
        elif _uma_edicao_com_letra(na, nb):
            motivo = "diferem em uma letra"
        else:
            continue
        pares.append({"codigo_a": a, "codigo_b": b, "motivo": motivo})
    return pares


def relatorio_vendas(base: Base, total: float) -> dict:
    """O quanto o relatório de vendas cliente × produto cobre a base, e o que ficou sem ligação."""
    c, p, v, m = base.clientes, base.produtos, base.vendas, base.casamento
    com = c[c["produtos_comprados"].map(len) > 0]
    do_relatorio = base.compras[base.compras["origem"] == "relatório de vendas"]
    por_produto = do_relatorio.groupby("codigo")["razao"].nunique()
    comparacao = [
        {"codigo": cod, "no_relatorio": int(por_produto.get(cod, 0)), "na_base": int(n)}
        for cod, n in zip(p["codigo"], p["n_clientes"]) if int(por_produto.get(cod, 0)) != int(n)
    ]
    comparacao.sort(key=lambda x: -(x["na_base"] - x["no_relatorio"]))
    fora_cadastro = sorted(set(v["codigo"]) - set(p["codigo"]))
    return {
        "existe": len(v) > 0,
        "pares": len(v),
        "razoes": int(v["razao"].nunique()),
        "codigos": int(v["codigo"].nunique()),
        "status": {k: int(n) for k, n in m["status"].value_counts().items()},
        "clientes_com": len(com),
        "clientes": len(c),
        "volume_clientes_com": float(com["volume_kg"].sum()) / total if total else 0.0,
        "produtos_sem_linha": int((~p["codigo"].isin(set(v["codigo"]))).sum()),
        "codigos_fora_cadastro": fora_cadastro,
        "comparacao_produtos": comparacao,
        "iguais_base": int(len(p) - len(comparacao)),
        "para_revisar": linhas(m[m["status"] != "exato"].sort_values("status"),
                               ["razao", "status", "nome_no_dashboard", "observacao"]),
        "de_referencia": int((base.compras["origem"] != "relatório de vendas").sum()),
    }


def pagina_qualidade(base: Base) -> dict:
    r, c, p = base.registros, base.clientes, base.produtos
    vol_cli, vol_prod = float(r["volume_kg"].sum()), float(p["volume_kg"].sum())

    completude_clientes = {
        "UF": c["tem_uf"].mean(),
        "CNPJ": c["cnpj"].notna().mean(),
        "Cidade": c["cidade"].notna().mean(),
        "Segmento": c["segmento"].notna().mean(),
        "Porte": c["porte"].notna().mean(),
        "Responsável": c["responsavel"].notna().mean(),
    }
    completude_produtos = {
        "Família": p["tem_cadastro"].mean(),
        "Descrição": p["descricao"].notna().mean(),
        "Aplicação": p["aplicacao"].notna().mean(),
        "Resina": p["resina"].notna().mean(),
        "Tipo": p["tipo"].notna().mean(),
        "Responsável": p["responsavel"].notna().mean(),
        "Observação": p["observacao"].notna().mean(),
    }

    status = []
    for s in ORDEM_STATUS:
        g = r[r["status_de_para"] == s]
        if len(g):
            status.append({"status": s, "n": len(g), "volume_kg": float(g["volume_kg"].sum())})
    para_validar = r[r["status_de_para"].isin(["revisar", "sugerido", "sem_cnpj", "sem_de_para"])].sort_values(
        ["status_de_para", "volume_kg"], ascending=[True, False])

    total = float(c["volume_kg"].sum())
    ranking = agrupar(c, "cliente", total, FiltroClientes())
    incoerentes = p[(p["especialidade"] & (p["tipo"] == "Intermediário")) | (~p["especialidade"] & (p["tipo"] == "Especialidade"))]

    return {
        "reconciliacao": {
            "volume_clientes_kg": vol_cli,
            "volume_produtos_kg": vol_prod,
            "diferenca_kg": vol_cli - vol_prod,
            "diferenca_pct": (vol_cli - vol_prod) / vol_cli,
            "saidas_clientes": int(r["n_saidas"].sum()),
            "saidas_produtos": int(p["n_saidas"].sum()),
            "pares_clientes": int(r["n_produtos"].sum()),   # Σ "Produtos comprados"
            "pares_produtos": int(p["n_clientes"].sum()),   # Σ "Nº clientes"
        },
        "cobertura": {
            "clientes": len(c),
            "com_uf": int(c["tem_uf"].sum()),
            "volume_com_uf": float(c.loc[c["tem_uf"], "volume_kg"].sum()) / total,
            "fonte_uf": {k: int(v) for k, v in c["fonte_uf"].value_counts().items()},
            "com_link_fonte": int(c["fonte_uf_link"].notna().sum()),
            "uf_divergente": linhas(r[r["uf_conflito"].notna()],
                                    ["nome", "volume_kg", "uf_conflito", "uf", "local_base", "fonte_uf_link"]),
        },
        "completude": {
            "clientes": [{"campo": k, "pct": float(v)} for k, v in completude_clientes.items()],
            "produtos": [{"campo": k, "pct": float(v)} for k, v in completude_produtos.items()],
        },
        "de_para": {
            "status": status,
            "para_validar": linhas(para_validar, ["nome", "volume_kg", "status_de_para", "nome_sugerido", "cnpj_sugerido", "obs_de_para"]),
        },
        "sem_uf": linhas(ranking[ranking["uf"].isna()].head(30), COLUNAS_RANKING),
        "abc_divergente": linhas(p[p["classe_abc"] != p["abc_planilha"]],
                                 ["codigo", "volume_kg", "share_acum", "classe_abc", "abc_planilha"]),
        "flags_incoerentes": linhas(incoerentes, ["codigo", "descricao", "especialidade", "tipo", "volume_kg"]),
        "codigos_parecidos": codigos_parecidos(p["codigo"].tolist()),
        "relatorio_vendas": relatorio_vendas(base, total),
        "alertas": [a.model_dump() for a in gerar_alertas(base, "cliente")],
    }
