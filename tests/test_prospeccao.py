"""Prospecção: possíveis clientes levantados pela equipe.

A regra que mais importa aqui é de isolamento: prospect não é cliente e nunca
pode entrar em volume, share ou ranking da carteira.
"""
import pytest
from fastapi.testclient import TestClient

from app.data.prospeccao import _setor
from app.main import app


@pytest.fixture(scope="module")
def api():
    with TestClient(app) as cliente:
        yield cliente


def test_setor_junta_as_grafias_do_cluster():
    assert _setor("Embalagem Flexível & Filmes (agro)") == "Embalagem Flexível & Filmes"
    assert _setor("Embalagem Flexível & Filmes — conservação FLV") == "Embalagem Flexível & Filmes"
    assert _setor("Embalagem Flexível + Médico-Hospitalar") == "Embalagem Flexível & Filmes"
    assert _setor("Construção: tubos, conexões & perfis") == "Construção"
    assert _setor("Injeção técnica / Eletroeletrônico") == "Injeção técnica"
    assert _setor("Injeção / Embalagem") == "Injeção técnica"
    assert _setor("Compostos / Reciclagem") == "Compostos & Masterbatch"
    assert _setor("confirmar cluster") == "A confirmar"
    # o que já é tronco não muda, e o "/" sem espaços é parte do nome
    assert _setor("Reciclagem/PCR") == "Reciclagem/PCR"


def test_prospeccao_carregada(base):
    p = base.prospeccao
    assert len(p) == 102
    assert p["nome"].is_unique and p["id"].is_unique
    assert p["setor"].nunique() == 12  # 30 clusters em texto livre viram 12 setores
    assert p["uf"].notna().sum() == 92  # 10 empresas ficaram sem UF na planilha


def test_prospect_nao_entra_na_carteira(base):
    """Nenhum id de prospecção pode aparecer entre os clientes (nem o contrário)."""
    assert set(base.prospeccao["id"]) & set(base.clientes["id_cliente"]) == set()
    assert all(i.startswith("p-") for i in base.prospeccao["id"])


def test_prospect_que_ja_e_cliente_fica_marcado(base):
    p = base.prospeccao
    marcados = p[p["ja_cliente"] | p["mesmo_grupo"]]
    assert len(marcados) == 4
    assert marcados["cliente_nome"].notna().all()
    # quem foi marcado por CNPJ igual tem mesmo CNPJ de um cliente da base
    cnpjs = set(base.clientes["cnpj"].dropna())
    assert all(c in cnpjs for c in p[p["ja_cliente"]]["cnpj"])


def test_api_prospeccao(api):
    r = api.get("/api/prospeccao").json()
    k = r["kpis"]
    assert (k["n"], k["total"], k["n_setores"]) == (102, 102, 12)
    assert k["com_cnpj"] == 89 and k["com_aditivos"] == 47 and k["ja_clientes"] == 4
    assert len(r["empresas"]) == 102
    assert sum(s["n"] for s in r["por_setor"]) == 102
    assert r["por_setor"][0]["nome"] == "Reciclagem/PCR"
    assert r["por_setor"][-1]["nome"] == "A confirmar"  # sem setor definido vai para o fim
    assert r["por_regiao"][0]["nome"] == "Sudeste"  # ordem geográfica, não por tamanho


def test_api_prospeccao_filtros(api):
    todos = api.get("/api/prospeccao").json()["kpis"]["n"]
    sul = api.get("/api/prospeccao", params={"regiao": "Sul"}).json()
    assert 0 < sul["kpis"]["n"] < todos
    assert all(e["regiao"] == "Sul" for e in sul["empresas"])

    setor = api.get("/api/prospeccao", params={"setor": "Reciclagem/PCR"}).json()
    assert all(e["setor"] == "Reciclagem/PCR" for e in setor["empresas"])
    assert setor["kpis"]["total"] == todos  # "total" continua sendo a lista inteira
    # o gráfico de setor ignora o filtro de setor: continua dando para clicar noutro
    assert len(setor["por_setor"]) == 12 and sum(s["n"] for s in setor["por_setor"]) == todos
    # já os outros gráficos respeitam a seleção
    assert sum(s["n"] for s in setor["por_status"]) == setor["kpis"]["n"] < todos


def test_geografia_traz_prospectos(api):
    g = api.get("/api/geografia").json()
    assert len(g["prospectos"]) == 92  # só os que têm UF
    assert all(p["uf"] for p in g["prospectos"])
    com_coord = [p for p in g["prospectos"] if p["coord"]]
    assert len(com_coord) == 91  # uma cidade não foi encontrada no IBGE
    # o mapa não pode misturar prospect com cliente
    assert set(p["id"] for p in g["prospectos"]).isdisjoint(p["id"] for p in g["pontos"])
