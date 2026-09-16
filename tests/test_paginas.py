"""Páginas 2 a 7 e filtros."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.qualidade import codigos_parecidos


@pytest.fixture(scope="module")
def api():
    with TestClient(app) as cliente:
        yield cliente


def test_meta_filtros(api):
    r = api.get("/api/meta/filtros").json()
    assert r["regiao"][0] == "Sudeste" and r["regiao"][-1] == "Não classificado"
    assert {"valor": "SP", "regiao": "Sudeste", "n": 165} in r["uf"]
    assert len(r["uf"]) == 16
    assert r["familia"][-1] == "Não classificado"


def test_clientes_sem_filtro(api):
    r = api.get("/api/clientes").json()
    assert r["kpis"]["n"] == 249
    assert r["kpis"]["n_para_80"] == 30
    assert r["ranking"][0]["nome"] == "VALGROUP"
    assert sum(h["n"] for h in r["histograma"]) == 249


def test_clientes_por_grupo_no_sudeste(api):
    r = api.get("/api/clientes", params={"visao": "grupo", "regiao": "Sudeste"}).json()
    valgroup = r["ranking"][0]
    assert valgroup["nome"] == "VALGROUP"
    assert valgroup["n_membros"] == 4  # os VALGROUP de AM e BA ficam de fora
    assert valgroup["ufs"] == ["MG", "RJ", "SP"]  # VALGROUP BRASIL está em RJ pela planilha de CNPJ
    assert r["ranking"][-1]["share_acum"] == pytest.approx(1)


def test_share_minimo(api):
    r = api.get("/api/clientes", params={"share_min": 0.02}).json()
    assert all(c["share"] >= 0.02 for c in r["ranking"])
    assert r["kpis"]["n"] == 13  # de VALGROUP (16,6%) a VALGROUP AM (2,06%)


def test_geografia_sudeste(api):
    r = api.get("/api/geografia", params={"regiao": "Sudeste"}).json()
    assert {e["uf"] for e in r["estados"]} == {"SP", "MG", "RJ", "ES"}
    assert r["kpis"]["n_clientes"] == 178
    assert r["sem_uf"]["n"] == 0
    lorena = next(p for p in r["pontos"] if p["nome"] == "VALGROUP")
    assert lorena["coord"] == pytest.approx([-45.06, -22.794])


def test_geografia_sem_filtro(api):
    r = api.get("/api/geografia").json()
    assert len(r["pontos"]) == 248
    assert r["sem_uf"]["n"] == 1
    assert sum(e["n_clientes"] for e in r["estados"]) == 248


def test_produtos_filtrados(api):
    r = api.get("/api/produtos", params={"familia": "Antichama", "estrategico": "sim"}).json()
    assert r["kpis"]["n"] == 2
    assert all(p["familia"] == "Antichama" and p["estrategico"] for p in r["produtos"])
    todos = api.get("/api/produtos").json()
    assert sum(n["value"] for n in todos["treemap"]) == pytest.approx(863_993.41)


def test_riscos(api):
    r = api.get("/api/riscos").json()
    assert [f["n"] for f in r["faixas"]] == [87, 33, 17]
    assert len(r["curva"]) == 249
    assert r["curva"][-1] == pytest.approx(1)


def test_destaques(api):
    listas = {l["id"]: l for l in api.get("/api/destaques").json()["listas"]}
    assert [i["codigo"] for i in listas["estrategicos_1_cliente"]["itens"]] == ["M9590", "SL-L4224/01"]
    assert all(i["n_produtos"] == 1 for i in listas["clientes_1_produto"]["itens"])


def test_qualidade(api):
    r = api.get("/api/qualidade").json()
    assert r["reconciliacao"]["diferenca_kg"] == pytest.approx(73_794.14)
    assert (r["reconciliacao"]["pares_clientes"], r["reconciliacao"]["pares_produtos"]) == (606, 559)
    assert {s["status"]: s["n"] for s in r["de_para"]["status"]} == {"exato": 244, "sugerido": 69, "revisar": 7, "sem_cnpj": 1}
    assert len(r["abc_divergente"]) == 2


def test_justificativa_de_risco_de_cada_produto(api):
    produtos = {p["codigo"]: p for p in api.get("/api/produtos").json()["produtos"]}
    assert all(p["motivo_risco"] for p in produtos.values())
    assert produtos["SL-C2263/02"]["motivo_risco"].startswith("Tem um único cliente: todo o volume (31.000 kg)")
    m6009 = produtos["M6009/02"]["motivo_risco"]  # 2 clientes, 86% no maior, classe B
    assert "compra 86% do volume" in m6009 and "risco alto a partir de 70%" in m6009 and "classe B" in m6009
    assert "entre 40% e 70%" in produtos["SL-L4265/02"]["motivo_risco"]
    assert "risco baixo" in produtos["SL-L4269/02"]["motivo_risco"]


def test_alertas_explicam_o_risco(api):
    alertas = api.get("/api/alertas").json()
    assert all(a["porque"] for a in alertas)
    a01 = next(a for a in alertas if a["codigo"] == "A01")
    assert "VALGROUP sozinho representa 16,6%" in a01["porque"]
    definicoes = api.get("/api/meta/filtros").json()["definicoes_risco"]
    assert set(definicoes) == {"Alto", "Médio", "Baixo"}


def test_filtro_compra_a_familia(api):
    r = api.get("/api/geografia", params={"compra_familia": "Antichama"}).json()
    assert r["kpis"]["n_clientes"] == 41
    assert all("Antichama" in p["familias_compradas"] for p in r["pontos"])
    todos = api.get("/api/clientes").json()["kpis"]["n"]
    assert api.get("/api/clientes", params={"compra_produto": "M9089/01"}).json()["kpis"]["n"] < todos


def test_matriz_familia_regiao(api):
    m = api.get("/api/geografia").json()["matriz"]
    assert m["regioes"][0] == "Sudeste"
    assert len(m["valores"]) == len(m["familias"]) * len(m["regioes"])


def test_familias_com_clientes_distintos(api):
    familias = {f["familia"]: f for f in api.get("/api/produtos").json()["familias"]}
    # contagem distinta nunca passa da soma (que conta o mesmo cliente várias vezes)
    assert all(f["clientes_distintos"] <= f["clientes_somados"] or f["familia"] == "Não classificado" for f in familias.values())
    assert familias["Antichama"]["clientes_distintos"] > 0


def test_venda_cruzada(api):
    vc = api.get("/api/destaques").json()["venda_cruzada"]
    assert vc["regras"] and all(r["confianca"] >= 0.4 and r["lift"] >= 1.2 and r["n_se"] >= 5 for r in vc["regras"])
    for s in vc["sugestoes"]:
        assert s["familia_sugerida"] not in s["familias_atuais"] and s["compra"] in s["familias_atuais"]


def test_qualidade_relatorio(api):
    q = api.get("/api/qualidade").json()["relatorio_vendas"]
    assert q["pares"] == 360 and q["clientes_com"] == 187
    assert "1234" in q["codigos_fora_cadastro"]


def test_codigos_parecidos_do_diagnostico():
    """Os pares da seção 1.1 (achado 14) precisam ser encontrados; variações só de dígito, não."""
    pares = {(p["codigo_a"], p["codigo_b"]) for p in codigos_parecidos([
        "9041/CI", "M9041/CI", "S-L4058/01", "SL-L4058/01", "SD-900PP", "SD-900/PP", "SL-L4549/AO", "SL-S4549/AO",
        "M9436", "M9436/01", "M9034", "M9034N", "M9089/01", "M9088/01", "M9010/1", "M9010C",
    ])}
    assert pares == {
        ("9041/CI", "M9041/CI"), ("S-L4058/01", "SL-L4058/01"), ("SD-900/PP", "SD-900PP"),
        ("SL-L4549/AO", "SL-S4549/AO"), ("M9436", "M9436/01"), ("M9034", "M9034N"),
    }
