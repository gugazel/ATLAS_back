"""Leitura, limpeza e cálculo das bases da Aditive.

Tudo que o dashboard mostra sai daqui. São lidas só as abas-base
(Base_Produtos e Base_Clientes), a planilha de CNPJ e o de-para de clientes.
Nenhuma célula calculada do Excel é usada: ABC, IPE, nível, risco e shares são
recalculados (achado 11 do plano). Os valores que vêm prontos da planilha ficam
em colunas *_planilha, só para os testes compararem.
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

from app import config
from app.services.formato import numero, pct

NAO_CLASSIFICADO = "Não classificado"

UF_REGIAO = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste",
    "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

COLUNAS_PRODUTOS = {
    "Código Aditive": "codigo",
    "Descrição comercial": "descricao",
    "Família": "familia",
    "Subfamília": "subfamilia",
    "Aplicação principal": "aplicacao",
    "Resina / Substrato": "resina",
    "Tipo de produto": "tipo",
    "Especialidade?": "especialidade",
    "Produto estratégico?": "estrategico",
    "Divulgar no site?": "site",
    "Prioridade marketing (1-5)": "prioridade_mkt",
    "Status comercial": "status",
    "Responsável": "responsavel",
    "Volume 2026 (kg)": "volume_kg",
    "Nº clientes": "n_clientes",
    "Nº saídas": "n_saidas",
    "Classe ABC": "abc_planilha",
    "Dependência maior cliente": "dependencia",
    "Observação": "observacao",
    "IPE V5": "ipe_planilha",
    "Nível": "nivel_planilha",
}

COLUNAS_CLIENTES = {
    "Posição": "posicao_planilha",
    "Cliente": "nome",
    "Volume (kg)": "volume_kg",
    "Participação": "share_planilha",
    "Produtos comprados": "n_produtos",
    "Nº saídas": "n_saidas",
    "UF": "uf_base",
    "Cidade": "cidade",
    "Segmento principal": "segmento",
    "Porte": "porte",
    "Responsável": "responsavel",
    "Observação CRM": "obs_crm",
    "Confiança da localização": "confianca",
}

COLUNAS_CNPJ = {"Cliente": "nome", "Cnpj": "cnpj", "Estado": "uf"}


@dataclass
class Base:
    produtos: pd.DataFrame   # 1 linha por código Aditive
    registros: pd.DataFrame  # 1 linha por nome da Base_Clientes
    clientes: pd.DataFrame   # 1 linha por cliente consolidado (CNPJ)
    grupos: pd.DataFrame     # 1 linha por grupo econômico
    referencias: pd.DataFrame  # clientes de referência da Alvos_Comerciais (ver carregar_referencias)
    vendas: pd.DataFrame       # relatório de vendas: razão social × código (sem volume)
    casamento: pd.DataFrame    # razão social -> cliente do dashboard
    compras: pd.DataFrame      # quem comprou o quê (relatório + referência), ver app/data/vendas.py
    prospeccao: pd.DataFrame   # possíveis clientes levantados pela equipe (ver app/data/prospeccao.py)
    carregado_em: datetime
    avisos: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- limpeza

def texto(valor) -> str | None:
    """Apara espaços, junta espaços duplos e troca vazio por None."""
    if valor is None or pd.isna(valor):
        return None
    limpo = re.sub(r"\s+", " ", str(valor)).strip()
    return limpo or None


def sim_nao(valor) -> bool:
    return (texto(valor) or "").lower() == "sim"


def so_digitos_cnpj(valor) -> str | None:
    digitos = re.sub(r"\D", "", texto(valor) or "")
    if not digitos:
        return None
    return digitos.zfill(14)  # CNPJ salvo como número perde os zeros à esquerda


def slug(valor: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", valor).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


def _ler_aba(caminho: Path, aba: str, colunas: dict[str, str]) -> pd.DataFrame:
    df = pd.read_excel(caminho, sheet_name=aba)
    df.columns = [texto(c) or "" for c in df.columns]
    faltando = [c for c in colunas if c not in df.columns]
    if faltando:
        raise ValueError(f"{caminho.name}, aba '{aba}': colunas não encontradas: {faltando}")
    return df[list(colunas)].rename(columns=colunas)


def _numeros(df: pd.DataFrame, colunas: list[str]) -> None:
    for c in colunas:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)


def ler_de_para(caminho: Path) -> dict[str, dict[str, str]]:
    """Lê o de-para (CSV com ';'), aceitando o arquivo salvo pelo Excel em UTF-8 ou ANSI."""
    if not caminho.exists():
        return {}
    bruto = caminho.read_bytes()
    try:
        conteudo = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        conteudo = bruto.decode("cp1252")
    linhas = list(csv.reader(io.StringIO(conteudo), delimiter=";"))
    cabecalho = [c.strip() for c in linhas[0]]
    n = len(cabecalho)
    de_para = {}
    for linha in linhas[1:]:
        if not any(c.strip() for c in linha):
            continue
        if len(linha) > n:  # ';' sem aspas dentro da observação (última coluna)
            linha = linha[: n - 1] + [";".join(linha[n - 1 :])]
        registro = dict(zip(cabecalho, linha))
        nome = texto(registro.get("nome_base_clientes"))
        if nome:
            de_para[nome] = {k: texto(v) for k, v in registro.items()}
    return de_para


# ---------------------------------------------------------------- produtos

def classe_abc(share_acum: pd.Series, share: pd.Series) -> pd.Series:
    """A até 80% do acumulado, B até 95%, C no resto. O item que cruza o limite fica na classe de cima."""
    anterior = share_acum - share
    return pd.Series(
        ["A" if a < config.ABC_LIMITE_A else "B" if a < config.ABC_LIMITE_B else "C" for a in anterior],
        index=share.index,
    )


def nivel_ipe(ipe: float) -> str:
    if ipe >= config.NIVEL_OURO:
        return "OURO"
    if ipe >= config.NIVEL_PRATA:
        return "PRATA"
    if ipe >= config.NIVEL_BRONZE:
        return "BRONZE"
    return "MONITORAR"


def faixa_risco(dependencia: float, n_clientes: int) -> str:
    if dependencia >= config.RISCO_ALTO or n_clientes == 1:
        return "Alto"
    if dependencia >= config.RISCO_MEDIO:
        return "Médio"
    return "Baixo"


def definicoes_risco() -> dict[str, str]:
    """Regra de cada faixa, em texto, para as legendas e dicas do dashboard."""
    alto, medio = pct(config.RISCO_ALTO, 0), pct(config.RISCO_MEDIO, 0)
    return {
        "Alto": f"O maior cliente compra {alto} ou mais do volume do produto, ou o produto tem um único cliente. "
                "Se esse cliente parar de comprar, o produto perde quase todo o volume.",
        "Médio": f"O maior cliente compra entre {medio} e {alto} do volume do produto. "
                 "A perda desse cliente derrubaria boa parte do volume.",
        "Baixo": f"O maior cliente compra menos de {medio} do volume do produto: o volume está distribuído entre vários clientes.",
    }


def motivo_risco(faixa: str, dependencia: float, n_clientes: int, volume: float, classe: str) -> str:
    """Por que este produto está nesta faixa de risco, com os números dele."""
    alto, medio = pct(config.RISCO_ALTO, 0), pct(config.RISCO_MEDIO, 0)
    if n_clientes == 1:
        texto_ = f"Tem um único cliente: todo o volume ({numero(volume)} kg) depende dele."
    elif faixa == "Alto":
        texto_ = f"O maior cliente compra {pct(dependencia, 0)} do volume do produto (risco alto a partir de {alto})."
    elif faixa == "Médio":
        texto_ = f"O maior cliente compra {pct(dependencia, 0)} do volume do produto (risco médio: entre {medio} e {alto})."
    else:
        return (f"O maior cliente compra só {pct(dependencia, 0)} do volume, que está distribuído entre "
                f"{n_clientes} clientes (risco baixo: abaixo de {medio}).")
    if n_clientes > 1:
        texto_ += f" Se esse cliente parar de comprar, o produto perde cerca de {numero(dependencia * volume)} kg."
    if classe in ("A", "B"):
        texto_ += f" É um produto de classe {classe}, com peso relevante no volume total."
    return texto_


def carregar_produtos(caminho: Path) -> pd.DataFrame:
    df = _ler_aba(caminho, "Base_Produtos", COLUNAS_PRODUTOS)
    for c in ("codigo", "descricao", "familia", "subfamilia", "aplicacao", "resina", "tipo",
              "status", "responsavel", "observacao", "abc_planilha", "nivel_planilha"):
        df[c] = df[c].map(texto)
    df = df[df["codigo"].notna()].copy()
    for c in ("especialidade", "estrategico", "site"):
        df[c] = df[c].map(sim_nao)
    _numeros(df, ["volume_kg", "n_clientes", "n_saidas", "dependencia", "prioridade_mkt"])
    df["ipe_planilha"] = pd.to_numeric(df["ipe_planilha"], errors="coerce")
    df["n_clientes"] = df["n_clientes"].astype(int)
    df["n_saidas"] = df["n_saidas"].astype(int)

    df["tem_cadastro"] = df["familia"].notna()
    df["familia"] = df["familia"].fillna(NAO_CLASSIFICADO)
    df["subfamilia"] = df["subfamilia"].fillna(NAO_CLASSIFICADO)

    df = df.sort_values("volume_kg", ascending=False, kind="stable").reset_index(drop=True)
    df["posicao"] = df.index + 1
    df["share"] = df["volume_kg"] / df["volume_kg"].sum()
    df["share_acum"] = df["share"].cumsum()
    df["classe_abc"] = classe_abc(df["share_acum"], df["share"])

    ipe = (
        df["volume_kg"] / df["volume_kg"].max() * 25
        + (df["n_clientes"] / 20).clip(upper=1) * 20
        + df["especialidade"] * 15
        + df["estrategico"] * 15
        + df["site"] * 8
        + df["prioridade_mkt"] / 5 * 12
        + (1 - df["dependencia"]) * 5
    )
    df["ipe_v5"] = ipe.clip(upper=100)
    df["nivel"] = df["ipe_v5"].map(nivel_ipe)
    df["indice_div"] = (df["n_clientes"] * 5).clip(upper=100)
    df["faixa_risco"] = [faixa_risco(d, n) for d, n in zip(df["dependencia"], df["n_clientes"])]
    df["motivo_risco"] = [
        motivo_risco(f, d, n, v, c)
        for f, d, n, v, c in zip(df["faixa_risco"], df["dependencia"], df["n_clientes"], df["volume_kg"], df["classe_abc"])
    ]
    df["kg_por_cliente"] = df["volume_kg"] / df["n_clientes"].where(df["n_clientes"] > 0)
    return df


# ---------------------------------------------------------------- clientes

def carregar_cnpjs(caminho: Path) -> dict[str, dict[str, str | None]]:
    """CNPJ -> nome, UF e link de onde a UF foi conferida (coluna "Fonte Estado", opcional)."""
    completo = pd.read_excel(caminho, sheet_name="Sheet1")
    completo.columns = [texto(c) or "" for c in completo.columns]
    fontes = completo["Fonte Estado"] if "Fonte Estado" in completo.columns else [None] * len(completo)
    df = _ler_aba(caminho, "Sheet1", COLUNAS_CNPJ)
    cnpjs = {}
    for nome, cnpj, uf, fonte in zip(df["nome"], df["cnpj"], df["uf"], fontes):
        digitos = so_digitos_cnpj(cnpj)
        if digitos and digitos not in cnpjs:
            cnpjs[digitos] = {"nome": texto(nome), "uf": (texto(uf) or "").upper() or None, "fonte": texto(fonte)}
    return cnpjs


def carregar_registros(caminho_base: Path, caminho_cnpj: Path, caminho_de_para: Path) -> pd.DataFrame:
    """1 linha por nome da Base_Clientes, já com o CNPJ e o cliente consolidado de cada uma."""
    df = _ler_aba(caminho_base, "Base_Clientes", COLUNAS_CLIENTES)
    for c in ("nome", "uf_base", "cidade", "segmento", "porte", "responsavel", "obs_crm", "confianca"):
        df[c] = df[c].map(texto)
    df = df[df["nome"].notna()].copy()
    _numeros(df, ["volume_kg", "n_produtos", "n_saidas"])
    df["n_produtos"] = df["n_produtos"].astype(int)
    df["n_saidas"] = df["n_saidas"].astype(int)
    df["share_planilha"] = pd.to_numeric(df["share_planilha"], errors="coerce")
    df["uf_base"] = df["uf_base"].str.upper()

    cnpjs = carregar_cnpjs(caminho_cnpj)
    de_para = ler_de_para(caminho_de_para)

    colunas = {k: [] for k in ("status_de_para", "cnpj", "id_cliente", "nome_cliente", "uf", "fonte_uf", "fonte_uf_link",
                               "uf_conflito", "grupo_informado", "cnpj_sugerido", "nome_sugerido", "obs_de_para")}
    for nome, uf_base in zip(df["nome"], df["uf_base"]):
        uf_base = texto(uf_base)  # NaN -> None
        linha = de_para.get(nome, {})
        status = linha.get("status") or "sem_de_para"
        cnpj_sugerido = so_digitos_cnpj(linha.get("cnpj")) if status != "rejeitado" else None
        # "revisar" não junta clientes (a dúvida é se são a mesma empresa), mas a UF da planilha de CNPJ vale
        uf_cnpj = cnpjs.get(cnpj_sugerido, {}).get("uf") if cnpj_sugerido else None
        consolida = status in config.STATUS_CONSOLIDA and cnpj_sugerido is not None
        cnpj = cnpj_sugerido if consolida else None

        colunas["status_de_para"].append(status)
        colunas["cnpj"].append(cnpj)
        colunas["id_cliente"].append(cnpj if cnpj else "n-" + slug(nome))
        colunas["nome_cliente"].append((linha.get("nome_planilha_cnpj") or nome) if cnpj else nome)
        colunas["uf"].append(uf_cnpj or uf_base)
        colunas["fonte_uf"].append("Planilha de CNPJ" if uf_cnpj else ("Base_Clientes" if uf_base else None))
        colunas["fonte_uf_link"].append(cnpjs.get(cnpj_sugerido, {}).get("fonte") if uf_cnpj else None)
        # as duas fontes discordam? (a planilha de CNPJ prevalece, mas fica registrado)
        colunas["uf_conflito"].append(uf_base if uf_cnpj and uf_base and uf_base != uf_cnpj else None)
        colunas["grupo_informado"].append(linha.get("grupo_economico"))
        colunas["cnpj_sugerido"].append(linha.get("cnpj"))  # formatado, como está no de-para
        colunas["nome_sugerido"].append(linha.get("nome_planilha_cnpj"))
        colunas["obs_de_para"].append(linha.get("observacao"))
    for c, valores in colunas.items():
        df[c] = valores
    # Quando a UF da planilha de CNPJ diverge, a cidade da Base_Clientes (que é da outra UF) deixa de valer
    conflito = df["uf_conflito"].notna()
    df["local_base"] = [
        f"{cid}/{uf}" if cid else uf for cid, uf in zip(df["cidade"].map(texto), df["uf_conflito"])
    ]
    df.loc[~conflito, "local_base"] = None
    df.loc[conflito, "cidade"] = None
    return df.reset_index(drop=True)


def _ranking(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("volume_kg", ascending=False, kind="stable").reset_index(drop=True)
    df["posicao"] = df.index + 1
    df["share"] = df["volume_kg"] / df["volume_kg"].sum()
    df["share_acum"] = df["share"].cumsum()
    df["kg_por_saida"] = df["volume_kg"] / df["n_saidas"].where(df["n_saidas"] > 0)
    return df


def consolidar_clientes(registros: pd.DataFrame) -> pd.DataFrame:
    """Junta os registros com o mesmo CNPJ. UF e cidade vêm do maior registro que tiver o dado."""
    ordenados = registros.sort_values("volume_kg", ascending=False, kind="stable")
    clientes = ordenados.groupby("id_cliente", sort=False).agg(
        nome=("nome_cliente", "first"),
        cnpj=("cnpj", "first"),
        volume_kg=("volume_kg", "sum"),
        n_produtos=("n_produtos", "sum"),
        n_saidas=("n_saidas", "sum"),
        n_registros=("nome", "size"),
        nomes_originais=("nome", list),
        uf=("uf", "first"),
        n_ufs=("uf", "nunique"),
        fonte_uf=("fonte_uf", "first"),
        fonte_uf_link=("fonte_uf_link", "first"),
        local_base=("local_base", "first"),
        cidade=("cidade", "first"),
        confianca=("confianca", "first"),
        segmento=("segmento", "first"),
        porte=("porte", "first"),
        responsavel=("responsavel", "first"),
        status_de_para=("status_de_para", "first"),
        grupo_informado=("grupo_informado", "first"),
    ).reset_index()
    clientes["regiao"] = clientes["uf"].map(UF_REGIAO).fillna(NAO_CLASSIFICADO)
    clientes["tem_uf"] = clientes["uf"].notna()
    return _ranking(clientes)


def montar_grupos(clientes: pd.DataFrame) -> pd.DataFrame:
    """Grupo econômico = grupo informado no de-para, ou mesma raiz de CNPJ (8 primeiros dígitos)."""
    raiz = clientes["cnpj"].str[:8]
    # No pandas 3, None vira NaN em coluna de texto (e NaN é "verdadeiro"), por isso o texto() em cada valor
    informados = [texto(g) for g in clientes["grupo_informado"]]
    grupo_por_raiz = {r: g for r, g in zip(raiz, informados) if isinstance(r, str) and g}
    clientes_por_raiz = raiz.value_counts()

    ids, nomes = [], []
    for id_cliente, nome, r, informado in zip(clientes["id_cliente"], clientes["nome"], raiz, informados):
        grupo = informado or (grupo_por_raiz.get(r) if isinstance(r, str) else None)
        if grupo:
            ids.append("g-" + slug(grupo))
            nomes.append(grupo)
        elif isinstance(r, str) and clientes_por_raiz[r] > 1:
            ids.append("r-" + r)
            nomes.append(None)  # nome do maior cliente da raiz, preenchido abaixo
        else:
            ids.append(id_cliente)
            nomes.append(nome)
    clientes["id_grupo"] = ids
    clientes["nome_grupo"] = nomes
    maior_da_raiz = clientes.sort_values("volume_kg", ascending=False).groupby("id_grupo")["nome"].first()
    clientes["nome_grupo"] = clientes["nome_grupo"].fillna(clientes["id_grupo"].map(maior_da_raiz))

    ordenados = clientes.sort_values("volume_kg", ascending=False, kind="stable")
    grupos = ordenados.groupby("id_grupo", sort=False).agg(
        nome=("nome_grupo", "first"),
        volume_kg=("volume_kg", "sum"),
        n_produtos=("n_produtos", "sum"),
        n_saidas=("n_saidas", "sum"),
        n_clientes=("id_cliente", "size"),
        clientes=("nome", list),
        uf=("uf", "first"),
        n_ufs=("uf", "nunique"),
    ).reset_index()
    return _ranking(grupos)


# ---------------------------------------------------------------- aditivos por cliente (parcial)

def carregar_referencias(caminho: Path, registros: pd.DataFrame) -> pd.DataFrame:
    """Ligação PARCIAL cliente × produto: coluna "Cliente atual de referência" da aba Alvos_Comerciais.

    A planilha lista até 3 clientes para cada um dos 20 maiores produtos, sem volume por cliente.
    É a única ligação cliente-produto que existe hoje. Serve só para DESCREVER o que se sabe de
    cada cliente e de cada produto — nunca para somar, calcular share ou filtrar, porque os
    clientes que não aparecem aqui não são "não compradores": só não foram listados.

    Colunas: codigo, nome_referencia, id_cliente (None quando o nome não bate com a Base_Clientes)
    """
    colunas = ["codigo", "nome_referencia", "id_cliente"]
    try:
        df = pd.read_excel(caminho, sheet_name="Alvos_Comerciais", header=4)
    except ValueError:  # aba não existe
        return pd.DataFrame(columns=colunas)
    df.columns = [texto(c) or "" for c in df.columns]
    if "Produto" not in df.columns or "Cliente atual de referência" not in df.columns:
        return pd.DataFrame(columns=colunas)

    # o nome pode estar na Base_Clientes ou (como variação) na planilha de CNPJ
    por_nome = {}
    for nome, sugerido, id_cliente in zip(registros["nome"], registros["nome_sugerido"], registros["id_cliente"]):
        por_nome.setdefault(slug(nome), id_cliente)
        if texto(sugerido):
            por_nome.setdefault(slug(texto(sugerido)), id_cliente)

    vistos, linhas = set(), []
    for codigo, lista_nomes in zip(df["Produto"], df["Cliente atual de referência"]):
        codigo, lista_nomes = texto(codigo), texto(lista_nomes)
        if not codigo or not lista_nomes:
            continue
        for nome in (texto(n) for n in lista_nomes.split(",")):
            if not nome:
                continue
            id_cliente = por_nome.get(slug(nome))
            chave = (codigo, id_cliente or nome)
            if chave not in vistos:  # "TRAVI" e "TRAVI PLASTICOS" são o mesmo cliente
                vistos.add(chave)
                linhas.append({"codigo": codigo, "nome_referencia": nome, "id_cliente": id_cliente})
    return pd.DataFrame(linhas, columns=colunas)


# ---------------------------------------------------------------- tudo junto

def carregar() -> Base:
    for arquivo in (config.ARQ_BASE, config.ARQ_CNPJ):
        if not arquivo.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    produtos = carregar_produtos(config.ARQ_BASE)
    registros = carregar_registros(config.ARQ_BASE, config.ARQ_CNPJ, config.ARQ_DE_PARA)
    clientes = consolidar_clientes(registros)
    grupos = montar_grupos(clientes)
    referencias = carregar_referencias(config.ARQ_BASE, registros)

    # quem comprou o quê: relatório de vendas (SAP) + clientes de referência da Alvos_Comerciais
    from app.data.vendas import carregar_vendas, casar_razoes, ligar_compras, montar_compras  # evita import circular
    vendas = carregar_vendas(config.ARQ_VENDAS)
    casamento = casar_razoes(vendas, registros, clientes, carregar_cnpjs(config.ARQ_CNPJ), config.ARQ_DE_PARA_VENDAS)
    compras = montar_compras(vendas, casamento, referencias, produtos, clientes)
    ligar_compras(produtos, clientes, compras)

    from app.data.prospeccao import carregar_prospeccao  # possíveis clientes (não entram na carteira)
    prospeccao = carregar_prospeccao(config.ARQ_PROSPECCAO, clientes)

    avisos = []
    if not config.ARQ_VENDAS.exists():
        avisos.append("Relatório de vendas cliente × produto não encontrado: só a lista de referência da Alvos_Comerciais é usada.")
    if not config.ARQ_DE_PARA.exists():
        avisos.append("de_para_clientes.csv não encontrado: nenhum cliente foi consolidado por CNPJ.")
    sem_de_para = registros.loc[registros["status_de_para"] == "sem_de_para", "nome"].tolist()
    if sem_de_para and config.ARQ_DE_PARA.exists():
        avisos.append(f"{len(sem_de_para)} nome(s) da Base_Clientes não estão no de-para: {', '.join(sem_de_para[:10])}")
    conflito = clientes.loc[clientes["n_ufs"] > 1, "nome"].tolist()
    if conflito:
        avisos.append(f"Clientes com registros em UFs diferentes: {', '.join(conflito)}")
    divergentes = registros[registros["uf_conflito"].notna()]
    if len(divergentes):
        avisos.append("UF da planilha de CNPJ diferente da Base_Clientes (vale a de CNPJ): " + ", ".join(
            f"{n} ({b} → {u})" for n, b, u in zip(divergentes["nome"], divergentes["uf_conflito"], divergentes["uf"])))

    return Base(
        produtos=produtos,
        registros=registros,
        clientes=clientes,
        grupos=grupos,
        referencias=referencias,
        vendas=vendas,
        casamento=casamento,
        compras=compras,
        prospeccao=prospeccao,
        carregado_em=datetime.now(),
        avisos=avisos,
    )
