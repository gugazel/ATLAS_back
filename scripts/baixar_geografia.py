"""Baixa do IBGE (API pública) os dados de referência do mapa.

1. Contorno dos 27 estados  -> ATLAS_front/src/assets/brasil-uf.json
2. Centroide das cidades que aparecem na Base_Clientes -> app/data/cidades.json

Nenhum dado de cliente é enviado: a lista de municípios de cada UF é baixada
inteira e a busca pelo nome da cidade é feita aqui.

Rodar de ATLAS_back:  .venv\\Scripts\\python scripts\\baixar_geografia.py
(de novo sempre que aparecerem clientes com cidades novas)
"""
import gzip
import json
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from app.data.loader import UF_REGIAO, carregar, slug  # noqa: E402

IBGE = "https://servicodados.ibge.gov.br/api"
CODIGO_UF = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS",
    "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}
NOME_UF = {
    "RO": "Rondônia", "AC": "Acre", "AM": "Amazonas", "RR": "Roraima", "PA": "Pará", "AP": "Amapá",
    "TO": "Tocantins", "MA": "Maranhão", "PI": "Piauí", "CE": "Ceará", "RN": "Rio Grande do Norte",
    "PB": "Paraíba", "PE": "Pernambuco", "AL": "Alagoas", "SE": "Sergipe", "BA": "Bahia",
    "MG": "Minas Gerais", "ES": "Espírito Santo", "RJ": "Rio de Janeiro", "SP": "São Paulo",
    "PR": "Paraná", "SC": "Santa Catarina", "RS": "Rio Grande do Sul", "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso", "GO": "Goiás", "DF": "Distrito Federal",
}


def baixar(url: str):
    with urllib.request.urlopen(url, timeout=60) as resposta:
        conteudo = resposta.read()
    if conteudo[:2] == b"\x1f\x8b":  # o IBGE às vezes responde compactado
        conteudo = gzip.decompress(conteudo)
    return json.loads(conteudo.decode("utf-8"))


def estados() -> None:
    malha = baixar(f"{IBGE}/v3/malhas/paises/BR?formato=application/vnd.geo+json&intrarregiao=UF&qualidade=minima")
    for feature in malha["features"]:
        uf = CODIGO_UF[feature["properties"]["codarea"]]
        feature["properties"] = {"name": uf, "nome": NOME_UF[uf], "regiao": UF_REGIAO[uf]}
    destino = RAIZ.parent / "ATLAS_front" / "src" / "assets" / "brasil-uf.json"
    destino.write_text(json.dumps(malha, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(malha['features'])} estados -> {destino}")


def cidades() -> None:
    base = carregar()
    pares = sorted({
        (uf, cidade)
        for tabela in (base.registros, base.prospeccao)  # clientes e empresas prospectadas
        for uf, cidade in zip(tabela["uf"], tabela["cidade"])
        if isinstance(uf, str) and isinstance(cidade, str)
    })
    resultado, municipios_por_uf = {}, {}
    for uf, cidade in pares:
        if uf not in municipios_por_uf:
            municipios_por_uf[uf] = {slug(m["nome"]): m["id"] for m in baixar(f"{IBGE}/v1/localidades/estados/{uf}/municipios")}
        codigo = municipios_por_uf[uf].get(slug(cidade))
        if codigo is None:
            print(f"  ! cidade não encontrada no IBGE: {cidade}/{uf}")
            continue
        centro = baixar(f"{IBGE}/v3/malhas/municipios/{codigo}/metadados")[0]["centroide"]
        resultado[f"{uf}|{cidade}"] = [centro["longitude"], centro["latitude"]]
        print(f"  {cidade}/{uf}: {centro['latitude']}, {centro['longitude']}")
    destino = RAIZ / "app" / "data" / "cidades.json"
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(resultado)} cidades -> {destino}")


if __name__ == "__main__":
    estados()
    cidades()
