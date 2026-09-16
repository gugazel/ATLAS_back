"""Página 5 — Concentração e riscos."""
from app import config
from app.data.loader import Base
from app.services.alertas import gerar_alertas, ranking
from app.services.filtros import FiltroProdutos, filtrar_produtos
from app.services.produtos import COLUNAS_PRODUTO
from app.services.serializar import linhas

FAIXAS = ["Alto", "Médio", "Baixo"]


def pagina_riscos(base: Base, visao: str, f: FiltroProdutos) -> dict:
    p = filtrar_produtos(base.produtos, f)
    total_produtos = float(base.produtos["volume_kg"].sum())
    rk = ranking(base, visao)

    faixas = []
    for faixa in FAIXAS:
        g = p[p["faixa_risco"] == faixa]
        faixas.append({"faixa": faixa, "n": len(g), "volume_kg": float(g["volume_kg"].sum()),
                       "share": float(g["volume_kg"].sum()) / total_produtos})

    return {
        "visao": visao,
        "faixas": faixas,
        "kpis": {
            "n": len(p),
            "um_cliente": int((p["n_clientes"] == 1).sum()),
            "ab_dependentes": int((p["classe_abc"].isin(["A", "B"]) & (p["dependencia"] >= config.RISCO_ALTO)).sum()),
            "hhi": float(((rk["share"] * 100) ** 2).sum()),
            "top5": float(rk["share"].head(5).sum()),
            "top10": float(rk["share"].head(10).sum()),
            "n_para_80": int((rk["share_acum"] < 0.80).sum() + 1),
            "n_carteira": len(rk),
        },
        "limites": {"alto": config.RISCO_ALTO, "medio": config.RISCO_MEDIO},
        "produtos": linhas(p, COLUNAS_PRODUTO),
        # curva acumulada da carteira: posição × share acumulado
        "curva": [float(v) for v in rk["share_acum"]],
        "alertas": [a.model_dump() for a in gerar_alertas(base, visao)],
    }
