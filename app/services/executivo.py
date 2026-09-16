"""Página 1 — Visão executiva: cartões, gráficos e alertas principais."""
import pandas as pd

from app.data.loader import NAO_CLASSIFICADO, Base
from app.schemas import Executivo, Fatia, ItemRanking, Kpis, Visao
from app.services.alertas import gerar_alertas, ranking
from app.services.formato import pct

ORDEM_RISCO = ["Alto", "Médio", "Baixo"]


def _fatias(df: pd.DataFrame, chave: str, total: float, contar: str, ordem: list[str] | None = None) -> list[Fatia]:
    """Soma o volume por `chave`. Sem `ordem`, ordena por volume e deixa "Não classificado" por último."""
    agrupado = df.groupby(chave).agg(volume_kg=("volume_kg", "sum"), n=(contar, "size"))
    if ordem:
        agrupado = agrupado.reindex(ordem, fill_value=0)
    else:
        agrupado = agrupado.sort_values("volume_kg", ascending=False)
        if NAO_CLASSIFICADO in agrupado.index:
            agrupado = pd.concat([agrupado.drop(NAO_CLASSIFICADO), agrupado.loc[[NAO_CLASSIFICADO]]])
    return [
        Fatia(nome=str(nome), volume_kg=float(linha.volume_kg), share=float(linha.volume_kg / total), n=int(linha.n))
        for nome, linha in agrupado.iterrows()
    ]


def executivo(base: Base, visao: Visao = "cliente") -> Executivo:
    rk = ranking(base, visao)
    p, c = base.produtos, base.clientes
    vol = float(base.registros["volume_kg"].sum())
    vol_prod = float(p["volume_kg"].sum())
    risco_alto = p[p["faixa_risco"] == "Alto"]
    com_uf = c[c["tem_uf"]]

    kpis = Kpis(
        volume_oficial_kg=vol,
        volume_produtos_kg=vol_prod,
        cobertura_produtos=vol_prod / vol,
        divergencia_kg=vol - vol_prod,
        n_clientes=len(rk),
        n_produtos=len(p),
        n_saidas=int(base.registros["n_saidas"].sum()),
        volume_medio_cliente_kg=vol / len(rk),
        maior_nome=str(rk["nome"].iloc[0]),
        maior_share=float(rk["share"].iloc[0]),
        top5_share=float(rk["share"].head(5).sum()),
        produtos_risco_alto=len(risco_alto),
        risco_alto_share_volume=float(risco_alto["volume_kg"].sum() / vol_prod),
        clientes_com_uf=len(com_uf),
        cobertura_uf_qtd=len(com_uf) / len(c),
        cobertura_uf_volume=float(com_uf["volume_kg"].sum() / vol),
    )

    membros = "n_clientes" if visao == "grupo" else "n_registros"
    top10 = [
        ItemRanking(
            id=str(linha[("id_grupo" if visao == "grupo" else "id_cliente")]),
            nome=str(linha["nome"]),
            volume_kg=float(linha["volume_kg"]),
            share=float(linha["share"]),
            uf=None if pd.isna(linha["uf"]) else str(linha["uf"]),
            n_membros=int(linha[membros]),
        )
        for _, linha in rk.head(10).iterrows()
    ]

    familias = _fatias(p, "familia", vol_prod, "codigo")
    regioes = _fatias(c, "regiao", vol, "id_cliente")
    abc = _fatias(p, "classe_abc", vol_prod, "codigo", ordem=["A", "B", "C"])
    risco = _fatias(p, "faixa_risco", vol_prod, "codigo", ordem=ORDEM_RISCO)

    maior = top10[0]
    if visao == "grupo" and maior.n_membros > 1:
        titulo_top = f"O grupo {maior.nome} ({maior.n_membros} clientes) soma {pct(maior.share)} do volume"
    else:
        titulo_top = f"{maior.nome} é o maior cliente, com {pct(maior.share)} do volume"
    classificadas = [r for r in regioes if r.nome != NAO_CLASSIFICADO]
    sem_regiao = next((r for r in regioes if r.nome == NAO_CLASSIFICADO), None)
    titulo_regiao = f"{classificadas[0].nome} concentra {pct(classificadas[0].share)} do volume" if classificadas else "Volume por região"
    if sem_regiao and sem_regiao.share >= 0.005:  # só menciona quando pesa (≥ 0,5% do volume)
        titulo_regiao += f"; {pct(sem_regiao.share)} ainda está sem UF"
    titulos = {
        "top10": titulo_top,
        "familias": f"{familias[0].nome} responde por {pct(familias[0].share)} do volume de produtos",
        "regioes": titulo_regiao,
        "abc": f"{abc[0].n} produtos de classe A fazem {pct(abc[0].share)} do volume",
        "risco": f"{risco[0].n} produtos com risco alto de concentração, somando {pct(risco[0].share)} do volume",
    }

    return Executivo(
        visao=visao,
        kpis=kpis,
        top10=top10,
        familias=familias,
        regioes=regioes,
        abc=abc,
        risco=risco,
        alertas=gerar_alertas(base, visao)[:5],
        titulos=titulos,
    )
