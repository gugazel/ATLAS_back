"""Empresas prospectadas pela equipe (planilha Grupo_8_Prospeccao_Aditive_CNPJ_contatos.xlsx).

São possíveis clientes, não clientes: nunca entram em volume, share, ranking ou qualquer
número da carteira. Ficam na aba Prospecção e, no mapa, como pontos de outra cor.

A aba "Página1" tem uma linha por empresa (cluster, região, status do contato, CNPJ, UF,
cidade, contato). As abas por região trazem os "Aditivos Aditive de encaixe" sugeridos para
parte delas — a sugestão é da equipe, não é compra confirmada.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

from app.data.loader import UF_REGIAO, so_digitos_cnpj, texto

COLUNAS = {
    "Nome empresa": "nome", "Cluster": "cluster", "Contato": "site", "Região": "regiao_planilha",
    "Status": "status", "Obs": "observacao", "Contato.1": "telefone", "Email": "email",
    "CNPJ": "cnpj_formatado", "UF": "uf", "Cidade": "cidade",
    "Razão social (Receita Federal)": "razao_social", "Confiança da identificação": "confianca",
    "Observações da pesquisa": "observacoes_pesquisa",
}
ABAS_IGNORADAS = {"Página1", "Legenda e método"}
NAO_CLASSIFICADO = "Não classificado"

# A planilha escreve o cluster livre: "Embalagem Flexível & Filmes" aparece em 5 grafias
# ("(agro)", "(+ interesse PCR)", "— conservação FLV"...). São 30 textos para 102 empresas,
# o que deixa gráfico e filtro inúteis. O setor junta as variações; o cluster original
# continua visível no cartão e no painel da empresa.
A_CONFIRMAR = "A confirmar"
APELIDOS_SETOR = {
    "confirmar cluster": A_CONFIRMAR,
    "Embalagem Flexível": "Embalagem Flexível & Filmes",
    "Injeção": "Injeção técnica",
    "Compostos": "Compostos & Masterbatch",
}


def _setor(cluster: str) -> str:
    """Tronco do cluster: corta complementos e mapeia as grafias equivalentes."""
    if not isinstance(cluster, str) or not cluster.strip():
        return NAO_CLASSIFICADO
    tronco = re.split(r"\s+[(+—–-]\s*|\s+/\s+|:", cluster)[0].strip(" -–—")
    return APELIDOS_SETOR.get(tronco, tronco)


def _chave(nome: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", "", ascii_)


def _aditivos_sugeridos(caminho: Path) -> dict[str, list[str]]:
    """Lê as abas por região: empresa -> aditivos que a equipe considerou de encaixe."""
    livro = pd.read_excel(caminho, sheet_name=None, header=None)
    sugestoes: dict[str, list[str]] = {}
    for aba, df in livro.items():
        if aba in ABAS_IGNORADAS or df.empty:
            continue
        cabecalho = next((i for i, linha in df.iterrows() if any(texto(v) == "Empresa" for v in linha)), None)
        if cabecalho is None:
            continue
        titulos = [texto(v) or "" for v in df.iloc[cabecalho]]
        col_empresa = titulos.index("Empresa")
        col_aditivos = next((i for i, t in enumerate(titulos) if t.lower().startswith("aditivos")), None)
        for _, linha in df.iloc[cabecalho + 1:].iterrows():
            empresa = texto(linha.iloc[col_empresa])
            if not empresa:
                continue
            bruto = texto(linha.iloc[col_aditivos]) if col_aditivos is not None else None
            itens = [texto(a) for a in re.split(r"[,;/]| e ", bruto)] if bruto else []
            if "etileno" in aba.lower():
                itens.append("Sequestrador de etileno")
            lista = sugestoes.setdefault(_chave(empresa), [])
            for item in itens:
                if item and item not in lista:
                    lista.append(item)
    return sugestoes


def carregar_prospeccao(caminho: Path, clientes: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por empresa prospectada, já marcando quem já é cliente (mesmo CNPJ ou mesma raiz)."""
    colunas_saida = list(COLUNAS.values()) + ["id", "cnpj", "regiao", "setor", "aditivos_sugeridos",
                                              "ja_cliente", "cliente_nome", "mesmo_grupo"]
    if not caminho.exists():
        return pd.DataFrame(columns=colunas_saida)
    df = pd.read_excel(caminho, sheet_name="Página1")
    df.columns = [texto(c) or "" for c in df.columns]
    faltando = [c for c in COLUNAS if c not in df.columns]
    if faltando:
        raise ValueError(f"{caminho.name}, aba 'Página1': colunas não encontradas: {faltando}")
    df = df[list(COLUNAS)].rename(columns=COLUNAS)
    for c in df.columns:
        df[c] = [texto(v) for v in df[c]]
    df = df[df["nome"].notna()].reset_index(drop=True)

    df["uf"] = df["uf"].str.upper()
    df["regiao"] = df["uf"].map(UF_REGIAO).fillna(NAO_CLASSIFICADO)
    df["cluster"] = df["cluster"].fillna(NAO_CLASSIFICADO)
    df["setor"] = [_setor(c) for c in df["cluster"]]
    df["status"] = df["status"].fillna("Sem Contato Feito")
    df["cnpj"] = [so_digitos_cnpj(c) for c in df["cnpj_formatado"]]
    df["id"] = ["p-" + _chave(n)[:30] for n in df["nome"]]

    sugestoes = _aditivos_sugeridos(caminho)
    df["aditivos_sugeridos"] = [sugestoes.get(_chave(n), []) for n in df["nome"]]

    por_cnpj = {c: n for c, n in zip(clientes["cnpj"], clientes["nome"]) if isinstance(c, str)}
    raizes = {c[:8]: n for c, n in por_cnpj.items()}
    cnpjs = [c if isinstance(c, str) else None for c in df["cnpj"]]  # pandas 3: vazio vem como NaN
    df["ja_cliente"] = [bool(c and c in por_cnpj) for c in cnpjs]
    df["mesmo_grupo"] = [bool(c and c not in por_cnpj and c[:8] in raizes) for c in cnpjs]
    df["cliente_nome"] = [
        por_cnpj.get(c) or (raizes.get(c[:8]) if c else None) if c else None for c in cnpjs
    ]
    return df[colunas_saida]
