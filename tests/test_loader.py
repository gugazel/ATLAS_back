"""As validações do diagnóstico (seções 0 e 1 do plano) como testes automáticos.

O Panorama_Interno é todo derivado das bases, então serve de gabarito:
os números recalculados precisam bater com ele.
"""
import openpyxl
import pandas as pd
import pytest

from app import config
from app.data.loader import NAO_CLASSIFICADO, ler_de_para


@pytest.fixture(scope="module")
def panorama():
    wb = openpyxl.load_workbook(config.ARQ_BASE, data_only=True, read_only=True)
    linhas = list(wb["Panorama_Interno"].iter_rows(min_row=6, max_row=25, values_only=True))
    familias = {l[0]: l[1:8] for l in linhas if l[0]}
    top20 = [l[9:15] for l in linhas if l[9]]
    return familias, top20


# ---------------------------------------------------------------- totais

def test_totais_das_bases(base):
    assert len(base.registros) == 321
    assert len(base.produtos) == 137
    assert base.registros["volume_kg"].sum() == pytest.approx(937_787.55)
    assert base.produtos["volume_kg"].sum() == pytest.approx(863_993.41)
    assert base.registros["n_saidas"].sum() == 1319
    assert base.produtos["n_saidas"].sum() == 1255


def test_share_de_cada_registro_bate_com_a_planilha(base):
    r = base.registros
    recalculado = r["volume_kg"] / r["volume_kg"].sum()
    assert (recalculado - r["share_planilha"]).abs().max() < 1e-12


# ---------------------------------------------------------------- gabarito: Panorama_Interno

def test_tabela_de_familias_bate_com_o_panorama(base, panorama):
    familias, _ = panorama
    p = base.produtos
    total = p["volume_kg"].sum()
    assert set(familias) == set(p["familia"])
    for familia, (volume, share, n_prod, clientes, estrategicos, site, especialidades) in familias.items():
        f = p[p["familia"] == familia]
        assert f["volume_kg"].sum() == pytest.approx(volume), familia
        assert f["volume_kg"].sum() / total == pytest.approx(share), familia
        assert len(f) == n_prod, familia
        assert f["n_clientes"].sum() == clientes, familia
        assert f["estrategico"].sum() == estrategicos, familia
        assert f["site"].sum() == site, familia
        assert f["especialidade"].sum() == especialidades, familia


def test_top20_bate_com_o_panorama(base, panorama):
    _, top20 = panorama
    r = base.registros.sort_values("volume_kg", ascending=False, kind="stable").head(20)
    total = base.registros["volume_kg"].sum()
    for (pos, nome, volume, share, produtos, saidas), (_, linha) in zip(top20, r.iterrows()):
        assert linha["nome"] == nome, pos
        assert linha["volume_kg"] == pytest.approx(volume), nome
        assert linha["volume_kg"] / total == pytest.approx(share), nome
        assert linha["n_produtos"] == produtos, nome
        assert linha["n_saidas"] == saidas, nome


# ---------------------------------------------------------------- produtos

def test_ipe_e_nivel_recalculados_batem_com_a_planilha(base):
    p = base.produtos
    assert (p["ipe_v5"] - p["ipe_planilha"]).abs().max() < 1e-9
    assert (p["nivel"] == p["nivel_planilha"]).all()
    assert p["nivel"].value_counts().to_dict() == {"MONITORAR": 120, "BRONZE": 11, "PRATA": 5, "OURO": 1}


def test_abc_so_difere_da_planilha_nos_dois_produtos_de_fronteira(base):
    """A coluna ABC da planilha é valor fixo e não segue a regra 80/95% em 2 produtos."""
    p = base.produtos
    diferentes = p.loc[p["classe_abc"] != p["abc_planilha"], "codigo"].tolist()
    assert sorted(diferentes) == ["SL-F4095/02", "SL-L4248/01"]
    assert p["classe_abc"].value_counts().to_dict() == {"A": 15, "B": 24, "C": 98}


def test_faixas_de_risco(base):
    assert base.produtos["faixa_risco"].value_counts().to_dict() == {"Alto": 87, "Médio": 33, "Baixo": 17}


def test_texto_normalizado(base):
    assert "Antichama " not in set(base.produtos["subfamilia"])
    assert (base.produtos["familia"] == NAO_CLASSIFICADO).sum() == 79


# ---------------------------------------------------------------- clientes (seção 0.3 e 0.4)

def test_de_para_aceita_ponto_e_virgula_na_observacao():
    de_para = ler_de_para(config.ARQ_DE_PARA)
    assert de_para["VALGROUP"]["status"] == "sem_cnpj"
    assert "não está na planilha" in de_para["VALGROUP"]["observacao"]


def test_consolidacao_por_cnpj(base):
    c = base.clientes
    assert len(c) == 249
    assert (c["n_registros"] > 1).sum() == 65
    assert c["volume_kg"].sum() == pytest.approx(937_787.55)
    gdm = c[c["nome"] == "GDM IND"].iloc[0]
    assert sorted(gdm["nomes_originais"]) == ["GDM", "GDM IND", "GDM INDUSTRIA"]


def test_revisar_nao_junta_clientes(base):
    r = base.registros.set_index("nome")
    assert r.loc["CD EMBALAGENS", "id_cliente"] != r.loc["CDI PLASTIC", "id_cliente"]
    assert r.loc["CDI PLASTIC", "uf"] == "SP"  # mas a UF da planilha de CNPJ vale


def test_grupos_economicos(base):
    g = base.grupos
    assert len(g) == 243  # 249 clientes - 5 (VALGROUP) - 1 (IBRACIL matriz/filial)
    valgroup = g[g["nome"] == "VALGROUP"].iloc[0]
    assert valgroup["n_clientes"] == 6
    assert valgroup["volume_kg"] == pytest.approx(367_575)
    assert (g["n_clientes"] > 1).sum() == 2


@pytest.mark.parametrize("tabela, maior, top5, top10, n80", [
    ("clientes", 0.1657, 0.4226, 0.5648, 30),
    ("grupos", 0.3920, 0.5316, 0.6547, 25),
])
def test_concentracao(base, tabela, maior, top5, top10, n80):
    df = getattr(base, tabela)
    assert df["share"].iloc[0] == pytest.approx(maior, abs=1e-4)
    assert df["share"].head(5).sum() == pytest.approx(top5, abs=1e-4)
    assert df["share"].head(10).sum() == pytest.approx(top10, abs=1e-4)
    assert (df["share_acum"] < 0.80).sum() + 1 == n80


def test_referencias_alvos_comerciais(base):
    """Alvos_Comerciais lista até 3 clientes para os 20 maiores produtos: 49 ligações, todas identificadas."""
    r = base.referencias
    assert len(r) == 49 and r["codigo"].nunique() == 20
    assert r["id_cliente"].notna().all()


def test_relatorio_de_vendas(base):
    """Relatório cliente × produto (11/09/2026): 360 pares únicos, 208 razões sociais, 106 códigos."""
    v, m = base.vendas, base.casamento.set_index("razao")
    assert (len(v), v["razao"].nunique(), v["codigo"].nunique()) == (360, 208, 106)
    assert m.loc["3B IND E COM DE ARTEFATOS PLAST LTDA", "status"] == "exato"
    assert m.loc["BRINQUEDOS BANDEIRANTE S/A", "nome_no_dashboard"] == "BRINQUEDOS BANDEIRANTES"  # nome parecido
    assert m.loc["DPLASTIC IND E COM DE PLAST LTDA", "status"] == "sem_cliente"  # 89% parecido não basta
    # "VALGROUP BRASIL II" pode ser outra empresa do grupo: não liga a um cliente, só ao grupo
    assert m.loc["VALGROUP BRASIL II IND DE EMB PLASTICAS LTDA", "status"] == "revisar"
    assert m.loc["VALGROUP BRASIL II IND DE EMB PLASTICAS LTDA", "id_grupo"] == "g-valgroup"


def test_produtos_comprados_por_cliente(base):
    c = base.clientes.set_index("nome")
    assert [(a["codigo"], a["familia"]) for a in c.loc["CARTONALE", "produtos_comprados"]] == [("M9089/01", "Antichama")]
    # VALGROUP (Lorena) não está no relatório: fica com os 2 produtos de referência da Alvos_Comerciais
    assert {a["codigo"] for a in c.loc["VALGROUP", "produtos_comprados"]} == {"SL-L4265/02", "M9028B"}
    assert (base.clientes["produtos_comprados"].map(len) > 0).sum() == 187
    p = base.produtos.set_index("codigo")
    # o único comprador do SL-C2263/02 no relatório não está na Base_Clientes
    assert [(x["nome"], x["no_dashboard"]) for x in p.loc["SL-C2263/02", "compradores"]] == [("MOTRIX COM DE PECAS LTDA - ME", False)]


def test_cobertura_geografica(base):
    """Planilha de estados de 11/09/2026: só GLUD IND (revisar, sem CNPJ, 25 kg) fica sem UF."""
    c = base.clientes
    com_uf = c[c["tem_uf"]]
    assert len(com_uf) == 248
    assert c.loc[~c["tem_uf"], "nome"].tolist() == ["GLUD IND"]
    share = c.groupby("regiao")["volume_kg"].sum() / c["volume_kg"].sum()
    assert share["Sudeste"] == pytest.approx(0.7156, abs=1e-4)
    assert share["Sul"] == pytest.approx(0.1546, abs=1e-4)
    assert (c["n_ufs"] <= 1).all()  # nenhum cliente com registros em UFs diferentes


def test_uf_divergente_entre_as_fontes(base):
    """VALGROUP BRASIL: Base_Clientes diz SP (Lorena), planilha de CNPJ diz RJ. Vale a de CNPJ, sem a cidade."""
    r = base.registros.set_index("nome")
    assert r.loc["VALGROUP BRASIL", "uf"] == "RJ"
    assert r.loc["VALGROUP BRASIL", "uf_conflito"] == "SP"
    assert r.loc["VALGROUP BRASIL", "local_base"] == "Lorena/SP"
    assert pd.isna(r.loc["VALGROUP BRASIL", "cidade"])  # Lorena é de SP: não vale para RJ
    assert r["uf_conflito"].notna().sum() == 1
    assert any("VALGROUP BRASIL (SP → RJ)" in a for a in base.avisos)
