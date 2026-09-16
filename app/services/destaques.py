"""Página 6 — Destaques: listas calculáveis pelas 3 bases, sempre "a investigar" (seção 0.5).

Nenhuma lista é uma recomendação: não há prioridade estratégica definida (seção 0.1).
"""
from app import config
from app.data.loader import Base
from app.services.clientes import COLUNAS_RANKING
from app.services.filtros import FiltroClientes, agrupar
from app.services.produtos import COLUNAS_PRODUTO
from app.services.serializar import linhas
from app.services.venda_cruzada import venda_cruzada


def pagina_destaques(base: Base) -> dict:
    total = float(base.clientes["volume_kg"].sum())
    c = agrupar(base.clientes, "cliente", total, FiltroClientes())
    p = base.produtos

    um_produto = c[c["n_produtos"] == 1]
    relevantes = um_produto[um_produto["volume_kg"] >= config.DESTAQUE_CLIENTE_1_PRODUTO_KG]
    muitos_clientes = p[(p["n_clientes"] >= config.DESTAQUE_MUITOS_CLIENTES)
                        & (p["kg_por_cliente"] <= config.DESTAQUE_KG_POR_CLIENTE_BAIXO)].sort_values("n_clientes", ascending=False)
    alto_volume = p[(p["volume_kg"] >= config.DESTAQUE_ALTO_VOLUME_KG)
                    & (p["n_clientes"] <= config.DESTAQUE_POUCOS_CLIENTES)]
    estrategicos_1 = p[p["estrategico"] & (p["n_clientes"] == 1)]

    def lista(id_, titulo, regra, df, colunas, total_regra=None):
        return {"id": id_, "titulo": titulo, "regra": regra, "n": len(df),
                "total_regra": total_regra, "itens": linhas(df, colunas)}

    return {
        "n_clientes": len(c),
        "venda_cruzada": venda_cruzada(base),
        "listas": [
            lista("clientes_1_produto",
                  "Clientes que compraram um único produto",
                  f"Clientes com 1 produto e pelo menos {config.DESTAQUE_CLIENTE_1_PRODUTO_KG:,} kg no período".replace(",", "."),
                  relevantes, COLUNAS_RANKING, total_regra=len(um_produto)),
            lista("muitos_clientes_baixo_kg",
                  "Produtos com muitos clientes e pouco volume por cliente",
                  f"Pelo menos {config.DESTAQUE_MUITOS_CLIENTES} clientes e até {config.DESTAQUE_KG_POR_CLIENTE_BAIXO} kg por cliente",
                  muitos_clientes, COLUNAS_PRODUTO),
            lista("alto_volume_poucos_clientes",
                  "Produtos com volume alto e poucos clientes",
                  f"Pelo menos {config.DESTAQUE_ALTO_VOLUME_KG:,} kg e até {config.DESTAQUE_POUCOS_CLIENTES} clientes".replace(",", "."),
                  alto_volume, COLUNAS_PRODUTO),
            lista("estrategicos_1_cliente",
                  "Produtos estratégicos com um único cliente",
                  "Marcados como estratégicos na Base_Produtos e com 1 cliente",
                  estrategicos_1, COLUNAS_PRODUTO),
        ],
    }
