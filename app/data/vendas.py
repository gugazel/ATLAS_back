"""Relatório de vendas cliente × produto (exportação do SAP enviada em 11/09/2026).

Uma linha por par "razão social × código do item". Diz QUEM comprou O QUÊ, mas não traz
volume, data nem valor. Por isso:
  - serve para listar produtos/famílias de cada cliente, compradores de cada produto,
    contar clientes distintos, filtrar "clientes que compram X" e sugerir venda cruzada;
  - não serve para dividir volume por produto dentro do cliente, nem para período ou receita.

A razão social ("3B IND E COM DE ARTEFATOS PLAST LTDA") é ligada ao cliente do dashboard
("3B IND") pelo começo do nome. O resultado pode ser corrigido em data/de_para_vendas.csv.
"""
from __future__ import annotations

import csv
import difflib
import io
import re
import unicodedata
from pathlib import Path

import pandas as pd

from app.data.loader import NAO_CLASSIFICADO, texto

ABREVIACOES = {
    "INDUSTRIA": "IND", "INDUSTRIAS": "IND", "INDUSTRIAL": "IND", "COMERCIO": "COM", "COMERCIAL": "COM",
    "EMBALAGENS": "EMB", "EMBALAGEM": "EMB", "PLASTICOS": "PLAST", "PLASTICO": "PLAST",
}
FORMAS_JURIDICAS = {"LTDA", "LTD", "ME", "EPP", "EIRELI", "SA", "S/A"}
ROMANOS = {"I", "II", "III", "IV", "V", "VI"}
PALAVRAS_VAZIAS = {"E", "DE", "DO", "DA", "DOS", "DAS", "IND", "COM", "EMB", "PLAST"}
STATUS_LIGA = {"exato", "sugerido", "ok"}


def palavras(nome: str) -> list[str]:
    """Nome em palavras normalizadas: sem acento, pontuação, forma jurídica; abreviações padronizadas."""
    ascii_ = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode().upper()
    ascii_ = ascii_.replace("S/A", " SA ")
    tokens = [ABREVIACOES.get(t, t) for t in re.split(r"[^A-Z0-9]+", ascii_) if t]
    while tokens and tokens[-1] in FORMAS_JURIDICAS:
        tokens.pop()
    return tokens


def carregar_vendas(caminho: Path) -> pd.DataFrame:
    """Pares únicos razão social × código, com a descrição do item."""
    colunas = ["razao", "codigo", "descricao"]
    if not caminho.exists():
        return pd.DataFrame(columns=colunas)
    df = pd.read_excel(caminho)
    df.columns = [texto(c) or "" for c in df.columns]
    df = df.rename(columns={"Nome Cliente": "razao", "Cód. Item": "codigo", "Descrição do Item": "descricao"})
    faltando = [c for c in colunas if c not in df.columns]
    if faltando:
        raise ValueError(f"{caminho.name}: colunas não encontradas: {faltando}")
    df = df[colunas].copy()
    for c in colunas:
        df[c] = [texto(v) for v in df[c]]
    df = df[df["razao"].notna() & df["codigo"].notna()]
    return df.drop_duplicates(["razao", "codigo"]).reset_index(drop=True)


def _candidatos(registros: pd.DataFrame, clientes: pd.DataFrame, cnpjs: dict) -> dict[tuple, set]:
    """Nome curto (em palavras) -> clientes do dashboard que usam esse nome."""
    cand: dict[tuple, set] = {}
    for nome, sugerido, id_cliente in zip(registros["nome"], registros["nome_sugerido"], registros["id_cliente"]):
        for n in (nome, texto(sugerido)):
            if n:
                cand.setdefault(tuple(palavras(n)), set()).add(id_cliente)
    por_cnpj = dict(zip(clientes["cnpj"], clientes["id_cliente"]))
    for digitos, info in cnpjs.items():
        if info.get("nome") and digitos in por_cnpj:
            cand.setdefault(tuple(palavras(info["nome"])), set()).add(por_cnpj[digitos])
    cand.pop((), None)
    return cand


def _essencia(tokens) -> str:
    return " ".join(t for t in tokens if t not in PALAVRAS_VAZIAS)


def casar_automatico(razao: str, cand: dict[tuple, set], nome_cliente: dict) -> dict:
    """Liga uma razão social a um cliente. Devolve id_cliente, status e uma observação."""
    toks = palavras(razao)
    acertos = [(k, ids) for k, ids in cand.items() if tuple(toks[: len(k)]) == k]
    if acertos:
        maior = max(len(k) for k, _ in acertos)
        ids_maior = set().union(*(ids for k, ids in acertos if len(k) == maior))
        todos = set().union(*(ids for _, ids in acertos))
        if len(ids_maior) == 1:
            id_cliente = next(iter(ids_maior))
            resto = toks[maior:]
            if resto and resto[0] in ROMANOS:
                return {"id_cliente": None, "status": "revisar", "sugestao": id_cliente,
                        "observacao": f"Começa como {nome_cliente[id_cliente]}, mas tem a numeração {resto[0]}: pode ser outra empresa do mesmo grupo"}
            if len(todos) == 1:
                return {"id_cliente": id_cliente, "status": "exato", "sugestao": None, "observacao": None}
            return {"id_cliente": id_cliente, "status": "sugerido", "sugestao": None,
                    "observacao": f"Mais de um nome combina; escolhido o mais completo ({nome_cliente[id_cliente]})"}
        return {"id_cliente": None, "status": "revisar", "sugestao": None,
                "observacao": "Combina com mais de um cliente: " + ", ".join(sorted(nome_cliente[i] for i in ids_maior))}

    # sem começo em comum: procura um nome muito parecido (erro de digitação, singular/plural)
    alvo = _essencia(toks)
    melhor, nota = None, 0.0
    for k, ids in cand.items():
        if len(ids) != 1:
            continue
        r = difflib.SequenceMatcher(None, alvo, _essencia(k)).ratio()
        if r > nota:
            melhor, nota = next(iter(ids)), r
    if melhor and nota >= 0.9:  # abaixo disso aparecem falsos pares (ex.: DPLASTIC × DS PLASTIC)
        return {"id_cliente": melhor, "status": "sugerido", "sugestao": None,
                "observacao": f"Nome parecido com {nome_cliente[melhor]} ({nota:.0%} de semelhança)"}
    return {"id_cliente": None, "status": "sem_cliente", "sugestao": None,
            "observacao": "Não encontrado na Base_Clientes (pode ter comprado fora de jan–jul/2026)"}


def ler_de_para_vendas(caminho: Path) -> dict[str, dict]:
    """Correções manuais: status "ok" (liga ao nome_no_dashboard) ou "rejeitado" (não liga)."""
    if not caminho.exists():
        return {}
    bruto = caminho.read_bytes()
    try:
        conteudo = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        conteudo = bruto.decode("cp1252")
    linhas = list(csv.DictReader(io.StringIO(conteudo), delimiter=";"))
    return {texto(l.get("razao_social")): {k: texto(v) for k, v in l.items()} for l in linhas if texto(l.get("razao_social"))}


def casar_razoes(vendas: pd.DataFrame, registros: pd.DataFrame, clientes: pd.DataFrame,
                 cnpjs: dict, caminho_de_para: Path) -> pd.DataFrame:
    """Uma linha por razão social: a qual cliente (e grupo) ela foi ligada, e com que certeza."""
    cand = _candidatos(registros, clientes, cnpjs)
    nome_cliente = dict(zip(clientes["id_cliente"], clientes["nome"]))
    grupo_de = dict(zip(clientes["id_cliente"], clientes["id_grupo"]))
    membros_grupo = clientes.groupby("id_grupo").size().to_dict()
    por_nome = {texto(n): i for n, i in zip(clientes["nome"], clientes["id_cliente"])}
    por_nome.update({texto(n): i for n, i in zip(registros["nome"], registros["id_cliente"])})
    correcoes = ler_de_para_vendas(caminho_de_para)

    linhas = []
    for razao in sorted(vendas["razao"].unique()):
        r = casar_automatico(razao, cand, nome_cliente)
        manual = correcoes.get(razao, {})
        if manual.get("status") == "ok" and por_nome.get(manual.get("nome_no_dashboard")):
            r = {"id_cliente": por_nome[manual["nome_no_dashboard"]], "status": "ok", "sugestao": None,
                 "observacao": manual.get("observacao")}
        elif manual.get("status") == "rejeitado":
            r = {"id_cliente": None, "status": "rejeitado", "sugestao": None, "observacao": manual.get("observacao")}
        # sem cliente certo, mas de um grupo com vários clientes: conta só para o grupo
        base_grupo = r["id_cliente"] or r["sugestao"]
        id_grupo = grupo_de.get(base_grupo) if base_grupo else None
        if not r["id_cliente"] and (not id_grupo or membros_grupo.get(id_grupo, 0) < 2):
            id_grupo = None
        linhas.append({"razao": razao, "id_cliente": r["id_cliente"], "id_grupo": id_grupo, "status": r["status"],
                       "nome_no_dashboard": nome_cliente.get(r["id_cliente"] or r["sugestao"]),
                       "observacao": r["observacao"]})
    return pd.DataFrame(linhas, columns=["razao", "id_cliente", "id_grupo", "status", "nome_no_dashboard", "observacao"])


def montar_compras(vendas: pd.DataFrame, casamento: pd.DataFrame, referencias: pd.DataFrame,
                   produtos: pd.DataFrame, clientes: pd.DataFrame) -> pd.DataFrame:
    """Tabela "quem comprou o quê", juntando o relatório de vendas e os clientes de referência
    da Alvos_Comerciais. Uma linha por cliente (ou razão sem cliente) × código."""
    info = produtos.set_index("codigo")
    grupo_de = dict(zip(clientes["id_cliente"], clientes["id_grupo"]))
    ligado = casamento.set_index("razao")
    linhas = {}
    for razao, codigo, descricao in zip(vendas["razao"], vendas["codigo"], vendas["descricao"]):
        c = ligado.loc[razao]
        id_cliente = c["id_cliente"] if isinstance(c["id_cliente"], str) else None
        chave = (id_cliente or f"razao:{razao}", codigo)
        linhas.setdefault(chave, {
            "id_cliente": id_cliente, "id_grupo": c["id_grupo"] if isinstance(c["id_grupo"], str) else None,
            "razao": razao, "codigo": codigo, "descricao_relatorio": descricao, "origem": "relatório de vendas",
        })
    for codigo, id_cliente in zip(referencias["codigo"], referencias["id_cliente"]):
        if not id_cliente:
            continue
        chave = (id_cliente, codigo)
        if chave in linhas:
            continue
        linhas[chave] = {"id_cliente": id_cliente, "id_grupo": grupo_de.get(id_cliente), "razao": None,
                         "codigo": codigo, "descricao_relatorio": None, "origem": "cliente de referência (Alvos_Comerciais)"}
    df = pd.DataFrame(list(linhas.values()),
                      columns=["id_cliente", "id_grupo", "razao", "codigo", "descricao_relatorio", "origem"])
    df["no_cadastro"] = df["codigo"].isin(info.index)
    df["familia"] = [info.loc[c, "familia"] if c in info.index else NAO_CLASSIFICADO for c in df["codigo"]]
    df["subfamilia"] = [info.loc[c, "subfamilia"] if c in info.index else NAO_CLASSIFICADO for c in df["codigo"]]
    df["descricao"] = [
        (texto(info.loc[c, "descricao"]) if c in info.index else None) or d for c, d in zip(df["codigo"], df["descricao_relatorio"])
    ]
    return df


def ligar_compras(produtos: pd.DataFrame, clientes: pd.DataFrame, compras: pd.DataFrame) -> None:
    """Põe em cada cliente os produtos comprados e em cada produto os compradores."""
    nome_cliente = dict(zip(clientes["id_cliente"], clientes["nome"]))
    por_cliente: dict[str, list] = {}
    por_produto: dict[str, list] = {}
    for linha in compras.itertuples(index=False):
        id_cliente = linha.id_cliente if isinstance(linha.id_cliente, str) else None  # pandas 3: vazio vem como NaN
        item = {"codigo": linha.codigo, "descricao": linha.descricao, "familia": linha.familia,
                "subfamilia": linha.subfamilia, "origem": linha.origem, "no_cadastro": bool(linha.no_cadastro)}
        if id_cliente:
            por_cliente.setdefault(id_cliente, []).append(item)
        por_produto.setdefault(linha.codigo, []).append({
            "id": id_cliente,
            "nome": nome_cliente.get(id_cliente) or linha.razao,
            "no_dashboard": id_cliente is not None,
            "origem": linha.origem,
        })
    ordem = lambda i: (i["familia"] == NAO_CLASSIFICADO, i["familia"], i["codigo"])  # noqa: E731
    clientes["produtos_comprados"] = [sorted(por_cliente.get(i, []), key=ordem) for i in clientes["id_cliente"]]
    clientes["familias_compradas"] = [
        sorted({i["familia"] for i in lista if i["familia"] != NAO_CLASSIFICADO}) for lista in clientes["produtos_comprados"]
    ]
    produtos["compradores"] = [sorted(por_produto.get(c, []), key=lambda x: (not x["no_dashboard"], x["nome"]))
                               for c in produtos["codigo"]]
    produtos["n_compradores"] = [len(x) for x in produtos["compradores"]]
