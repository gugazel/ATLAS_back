import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def api():
    with TestClient(app) as cliente:  # o "with" dispara o carregamento das planilhas
        yield cliente


def test_saude(api):
    r = api.get("/api/saude").json()
    assert r["status"] == "ok"
    assert (r["registros_clientes"], r["clientes"], r["grupos"], r["produtos"]) == (321, 249, 243, 137)


def test_executivo_por_cliente(api):
    r = api.get("/api/executivo").json()
    k = r["kpis"]
    assert k["n_clientes"] == 249
    assert k["volume_oficial_kg"] == pytest.approx(937_787.55)
    assert k["cobertura_produtos"] == pytest.approx(0.921, abs=1e-3)
    assert k["maior_nome"] == "VALGROUP"
    assert k["produtos_risco_alto"] == 87
    assert k["clientes_com_uf"] == 248  # planilha de estados de 11/09/2026
    assert len(r["top10"]) == 10
    assert r["regioes"][-1]["nome"] == "Não classificado"
    assert sum(f["share"] for f in r["familias"]) == pytest.approx(1)
    assert [a["n"] for a in r["abc"]] == [15, 24, 98]
    assert len(r["alertas"]) == 5


def test_executivo_por_grupo(api):
    r = api.get("/api/executivo", params={"visao": "grupo"}).json()
    assert r["kpis"]["n_clientes"] == 243
    assert r["top10"][0]["nome"] == "VALGROUP"
    assert r["top10"][0]["n_membros"] == 6
    assert "39,2%" in r["titulos"]["top10"]


def test_alertas(api):
    codigos = [a["codigo"] for a in api.get("/api/alertas").json()]
    assert {"A01", "A02", "A03", "A07", "A08", "A09", "A10"} <= set(codigos)
    assert "A05" not in codigos and "A11" not in codigos  # fora do escopo (seção 0.5)


def test_visao_invalida(api):
    assert api.get("/api/executivo", params={"visao": "xyz"}).status_code == 422
