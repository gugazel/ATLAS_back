"""Aba Prospecção — possíveis clientes levantados pela equipe.

Não são clientes: não têm volume e não entram em nenhum número da carteira.
"""
import pandas as pd

from app.data.loader import NAO_CLASSIFICADO, Base
from app.services.filtros import FiltroClientes, lista
from app.services.geografia import ORDEM_REGIOES, coordenadas_cidades
from app.services.serializar import linhas

COLUNAS = [
    "id", "nome", "razao_social", "cluster", "setor", "regiao", "regiao_planilha", "uf", "cidade", "status",
    "site", "telefone", "email", "cnpj", "cnpj_formatado", "confianca", "observacao", "observacoes_pesquisa",
    "aditivos_sugeridos", "ja_cliente", "mesmo_grupo", "cliente_nome",
]


def filtrar(prospeccao: pd.DataFrame, f: FiltroClientes, setor: list[str], status: list[str],
            menos: str | None = None) -> pd.DataFrame:
    """`menos` pula um filtro: cada gráfico ignora o próprio, senão sobraria só a barra escolhida."""
    p = prospeccao
    if f.regiao and menos != "regiao":
        p = p[p["regiao"].isin(f.regiao)]
    if f.uf and menos != "regiao":
        p = p[p["uf"].isin(f.uf)]
    if setor and menos != "setor":
        p = p[p["setor"].isin(setor)]
    if status and menos != "status":
        p = p[p["status"].isin(status)]
    return p


def com_coordenadas(prospeccao: pd.DataFrame) -> list[dict]:
    """Prospects prontos para o mapa: coordenada da cidade quando ela é conhecida."""
    cidades = coordenadas_cidades()
    pontos = linhas(prospeccao[prospeccao["uf"].notna()], COLUNAS)
    for ponto in pontos:
        ponto["coord"] = cidades.get(f"{ponto['uf']}|{ponto.get('cidade')}")
    return pontos


def _contagem(p: pd.DataFrame, coluna: str, ordem: list[str] | None = None, ultimos: tuple = ()) -> list[dict]:
    contagem = p.groupby(coluna).size()
    if ordem:
        chaves = [k for k in ordem if k in contagem.index]
    else:
        chaves = contagem.sort_values(ascending=False).index.tolist()
    for final in ultimos:  # "Não classificado"/"A confirmar" sempre no fim da lista
        if final in chaves:
            chaves = [k for k in chaves if k != final] + [final]
    return [{"nome": k, "n": int(contagem[k])} for k in chaves]


def pagina_prospeccao(base: Base, f: FiltroClientes, setor: str | None, status: str | None) -> dict:
    todos = base.prospeccao
    setores, status_ = lista(setor), lista(status)
    p = filtrar(todos, f, setores, status_)
    sem = {c: filtrar(todos, f, setores, status_, menos=c) for c in ("regiao", "setor", "status")}
    return {
        "kpis": {
            "n": len(p),
            "total": len(todos),
            "com_cnpj": int(p["cnpj"].notna().sum()),
            "com_cidade": int(p["cidade"].notna().sum()),
            "com_aditivos": int((p["aditivos_sugeridos"].map(len) > 0).sum()),
            "ja_clientes": int((p["ja_cliente"] | p["mesmo_grupo"]).sum()),
            "n_setores": int(p["setor"].nunique()),
            "contatados": int((p["status"] != "Sem Contato Feito").sum()),
        },
        "empresas": linhas(p.sort_values(["regiao", "setor", "nome"]), COLUNAS),
        "por_setor": _contagem(sem["setor"], "setor", ultimos=(NAO_CLASSIFICADO, "A confirmar")),
        "por_regiao": _contagem(sem["regiao"], "regiao", ORDEM_REGIOES, ultimos=(NAO_CLASSIFICADO,)),
        "por_uf": _contagem(p, "uf"),
        "por_status": _contagem(sem["status"], "status"),
    }
