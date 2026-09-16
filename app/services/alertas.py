"""Motor de alertas (seção 13.2 do plano). A05 e A11 saíram do escopo (seção 0.5)."""
import pandas as pd

from app import config
from app.data.loader import Base
from app.schemas import Alerta, Visao
from app.services.formato import numero, pct, toneladas

ORDEM_SEVERIDADE = {"alta": 0, "media": 1, "baixa": 2}
MAX_ITENS = 10


def ranking(base: Base, visao: Visao) -> pd.DataFrame:
    return base.grupos if visao == "grupo" else base.clientes


def plural(n: int, singular: str, plural_: str) -> str:
    return f"{n} {singular if n == 1 else plural_}"


def gerar_alertas(base: Base, visao: Visao = "cliente") -> list[Alerta]:
    rk = ranking(base, visao)
    p, c = base.produtos, base.clientes
    nome_um, nome_varios = ("grupo", "grupos") if visao == "grupo" else ("cliente", "clientes")
    alertas: list[Alerta] = []

    # A01 — cliente (ou grupo) com share alto
    grandes = rk[rk["share"] >= config.ALERTA_SHARE_CLIENTE]
    if len(grandes):
        alertas.append(Alerta(
            codigo="A01", severidade="alta",
            titulo=f"{plural(len(grandes), nome_um, nome_varios)} com {pct(config.ALERTA_SHARE_CLIENTE, 0)} ou mais do volume",
            valor=f"{pct(grandes['share'].iloc[0])} ({grandes['nome'].iloc[0]})",
            itens=[f"{n}: {pct(s)}" for n, s in zip(grandes["nome"], grandes["share"])],
            acao="Acompanhar de perto: a saída de um deles muda muito o volume total.",
            porque=f"Quanto maior o share de um só {nome_um}, maior o impacto se ele comprar menos. "
                   f"{grandes['nome'].iloc[0]} sozinho representa {pct(grandes['share'].iloc[0])}: "
                   f"perdê-lo tiraria {toneladas(grandes['volume_kg'].iloc[0])} do volume.",
        ))

    # A02 — top 5 concentrado
    top5 = float(rk["share"].head(5).sum())
    if top5 >= config.ALERTA_TOP5:
        alertas.append(Alerta(
            codigo="A02", severidade="alta",
            titulo=f"Os 5 maiores {nome_varios} somam {pct(top5)} do volume",
            valor=pct(top5),
            itens=[f"{n}: {pct(s)}" for n, s in zip(rk["nome"].head(5), rk["share"].head(5))],
            acao="Carteira concentrada: acompanhar o volume dos maiores mês a mês.",
            porque=f"Com {pct(top5)} do volume em 5 {nome_varios}, uma mudança em qualquer um deles afeta muito o total. "
                   f"A partir de {pct(config.ALERTA_TOP5, 0)} a carteira é considerada concentrada.",
        ))

    # A03 — produto relevante (A/B) muito dependente de um cliente
    dependentes = p[p["classe_abc"].isin(["A", "B"]) & (p["dependencia"] >= config.RISCO_ALTO)]
    if len(dependentes):
        alertas.append(Alerta(
            codigo="A03", severidade="alta",
            titulo=f"{plural(len(dependentes), 'produto', 'produtos')} de classe A ou B "
                   f"{'depende' if len(dependentes) == 1 else 'dependem'} {pct(config.RISCO_ALTO, 0)} ou mais de um só cliente",
            valor=str(len(dependentes)),
            itens=[f"{cod} ({abc}): {pct(d, 0)} no maior cliente · {numero(v)} kg"
                   for cod, abc, d, v in zip(dependentes["codigo"], dependentes["classe_abc"],
                                             dependentes["dependencia"], dependentes["volume_kg"])][:MAX_ITENS],
            acao="Ampliar a base de clientes desses produtos.",
            porque="São produtos que pesam no volume total (classe A ou B) e dependem de um único cliente. "
                   f"Se esses clientes pararem de comprar, a Aditive perde cerca de "
                   f"{numero((dependentes['dependencia'] * dependentes['volume_kg']).sum())} kg desses produtos.",
        ))

    # A04 — produto estratégico com um único cliente
    estrategicos_1 = p[p["estrategico"] & (p["n_clientes"] == 1)]
    if len(estrategicos_1):
        alertas.append(Alerta(
            codigo="A04", severidade="alta",
            titulo=f"{plural(len(estrategicos_1), 'produto estratégico tem', 'produtos estratégicos têm')} um único cliente",
            valor=str(len(estrategicos_1)),
            itens=[f"{cod}: {numero(v)} kg" for cod, v in zip(estrategicos_1["codigo"], estrategicos_1["volume_kg"])],
            acao="Verificar se há outros clientes com perfil para esses produtos.",
            porque="Estão marcados como estratégicos, mas têm um só comprador: todo o volume deles depende desse cliente.",
        ))

    # A06 — clientes grandes sem UF (sempre por cliente: a geografia é do CNPJ)
    vol_total = float(c["volume_kg"].sum())
    topo = c.head(config.ALERTA_TOP_SEM_UF)
    sem_uf = topo[~topo["tem_uf"]]
    if len(sem_uf):
        alertas.append(Alerta(
            codigo="A06", severidade="media",
            titulo=f"{len(sem_uf)} dos {config.ALERTA_TOP_SEM_UF} maiores clientes estão sem UF",
            valor=str(len(sem_uf)),
            itens=[f"{n}: {numero(v)} kg" for n, v in zip(sem_uf["nome"], sem_uf["volume_kg"])][:MAX_ITENS],
            acao="Completar a UF no cadastro para melhorar a leitura geográfica.",
            porque=f"Sem UF, esses clientes ficam fora do mapa e das análises por região. "
                   f"Juntos somam {toneladas(sem_uf['volume_kg'].sum())} ({pct(sem_uf['volume_kg'].sum() / vol_total)} do volume).",
        ))

    # A07 — totais das duas bases não batem
    vol_cli = float(base.registros["volume_kg"].sum())
    vol_prod = float(p["volume_kg"].sum())
    divergencia = (vol_cli - vol_prod) / vol_cli if vol_cli else 0.0
    if abs(divergencia) > config.ALERTA_DIVERGENCIA:
        alertas.append(Alerta(
            codigo="A07", severidade="alta",
            titulo=f"A base de produtos soma {numero(vol_cli - vol_prod)} kg a menos que a de clientes",
            valor=pct(divergencia),
            itens=[f"Clientes: {numero(vol_cli, 2)} kg", f"Produtos: {numero(vol_prod, 2)} kg"],
            acao="Confirmar com a Aditive a origem da diferença. Até lá, o total oficial é o de clientes.",
            porque=f"Com as bases diferentes, os números por produto e por cliente não fecham: "
                   f"{pct(divergencia)} do volume não aparece na base de produtos.",
        ))

    # A08 — nomes que o de-para ainda não resolveu
    pendentes = base.registros[base.registros["status_de_para"].isin(["revisar", "sem_de_para"])]
    if len(pendentes):
        alertas.append(Alerta(
            codigo="A08", severidade="media",
            titulo=f"{plural(len(pendentes), 'nome de cliente aguarda', 'nomes de clientes aguardam')} revisão no de-para",
            valor=str(len(pendentes)),
            itens=[f"{n}: {numero(v)} kg" for n, v in zip(pendentes["nome"], pendentes["volume_kg"])][:MAX_ITENS],
            acao="Marcar como ok ou rejeitado em data/de_para_clientes.csv.",
            porque="Enquanto não forem revisados, esses nomes contam como clientes separados, "
                   "o que pode dividir o volume de uma mesma empresa.",
        ))

    # A09 — campos obrigatórios pouco preenchidos
    completude = {
        "UF do cliente": c["tem_uf"].mean(),
        "Segmento do cliente": c["segmento"].notna().mean(),
        "Porte do cliente": c["porte"].notna().mean(),
        "Responsável do cliente": c["responsavel"].notna().mean(),
        "Família do produto": p["tem_cadastro"].mean(),
        "Responsável do produto": p["responsavel"].notna().mean(),
    }
    baixos = {campo: v for campo, v in completude.items() if v < config.ALERTA_COMPLETUDE}
    if baixos:
        alertas.append(Alerta(
            codigo="A09", severidade="media",
            titulo=f"{plural(len(baixos), 'campo do cadastro tem', 'campos do cadastro têm')} "
                   f"menos de {pct(config.ALERTA_COMPLETUDE, 0)} de preenchimento",
            valor=str(len(baixos)),
            itens=[f"{campo}: {pct(v)}" for campo, v in sorted(baixos.items(), key=lambda kv: kv[1])],
            acao="Completar o cadastro. Sem esses campos, alguns filtros ficam desativados.",
            porque="Sem esses campos não dá para filtrar nem comparar por eles (segmento, porte, responsável), "
                   "e parte das análises fica limitada.",
        ))

    # A10 — flags incoerentes entre "Especialidade?" e "Tipo de produto"
    incoerentes = p[(p["especialidade"] & (p["tipo"] == "Intermediário")) | (~p["especialidade"] & (p["tipo"] == "Especialidade"))]
    if len(incoerentes):
        alertas.append(Alerta(
            codigo="A10", severidade="baixa",
            titulo=f"{plural(len(incoerentes), 'produto tem', 'produtos têm')} \"Especialidade?\" incoerente com o tipo",
            valor=str(len(incoerentes)),
            itens=[f"{cod}: Especialidade? {'Sim' if e else 'Não'} · Tipo {t}"
                   for cod, e, t in zip(incoerentes["codigo"], incoerentes["especialidade"], incoerentes["tipo"])],
            acao="Corrigir o cadastro do produto.",
            porque="O cadastro diz uma coisa em \"Especialidade?\" e outra em \"Tipo\": "
                   "a contagem de especialidades pode sair errada.",
        ))

    return sorted(alertas, key=lambda a: ORDEM_SEVERIDADE[a.severidade])
