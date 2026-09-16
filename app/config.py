"""Limites de negócio e caminhos dos arquivos.

Os limites ficam aqui (e não espalhados pelo código) para poderem ser
ajustados sem mexer nas regras de cálculo. Ver seção 9 do plano.
"""
import os
from pathlib import Path

PASTA_DADOS = Path(os.environ.get("ATLAS_PASTA_DADOS", Path(__file__).resolve().parents[1] / "data"))
ARQ_BASE = PASTA_DADOS / "Base_Aditive.xlsx"
# Planilha de CNPJ e estado. Usa a versão mais nova que existir (11/09/2026: todos os estados preenchidos)
ARQ_CNPJ = next(
    (a for a in (
        PASTA_DADOS / "Planilha_clientes_aditive_estados_preenchida (1).xlsx",
        PASTA_DADOS / "Planilha clientes aditivw 2.xlsx",
    ) if a.exists()),
    PASTA_DADOS / "Planilha clientes aditivw 2.xlsx",
)
ARQ_DE_PARA = PASTA_DADOS / "de_para_clientes.csv"
# Relatório de vendas cliente × produto (SAP, 11/09/2026): quem comprou o quê. Sem volume, data ou valor.
ARQ_VENDAS = next(iter(sorted(PASTA_DADOS.glob("*Cliente x Produto*.xlsx"))), PASTA_DADOS / "relatorio_vendas.xlsx")
# Ligação razão social do relatório -> cliente do dashboard (gerada automaticamente; editável)
ARQ_DE_PARA_VENDAS = PASTA_DADOS / "de_para_vendas.csv"

# Empresas prospectadas pela equipe (possíveis clientes, nunca entram nos números da carteira)
ARQ_PROSPECCAO = next(iter(sorted(PASTA_DADOS.glob("*Prospec*.xlsx"))), PASTA_DADOS / "prospeccao.xlsx")

# Centroide dos municípios (IBGE), gerado por scripts/baixar_geografia.py. Não tem dado de cliente.
ARQ_CIDADES = Path(__file__).resolve().parent / "data" / "cidades.json"

# Status do de-para que juntam o registro ao CNPJ. "revisar" e "rejeitado" não juntam.
STATUS_CONSOLIDA = {"exato", "sugerido", "ok"}

# Faixa de risco de concentração do produto (dependência do maior cliente)
RISCO_ALTO = 0.70
RISCO_MEDIO = 0.40

# Curva ABC (participação acumulada do volume)
ABC_LIMITE_A = 0.80
ABC_LIMITE_B = 0.95

# IPE V5: cortes do nível
NIVEL_OURO = 80
NIVEL_PRATA = 65
NIVEL_BRONZE = 50

# Alertas
ALERTA_SHARE_CLIENTE = 0.10     # A01: cliente com share >= 10%
ALERTA_TOP5 = 0.40              # A02: top 5 >= 40%
ALERTA_TOP_SEM_UF = 50          # A06: clientes do top N sem UF
ALERTA_DIVERGENCIA = 0.01       # A07: divergência de totais > 1%
ALERTA_COMPLETUDE = 0.50        # A09: campo com completude < 50%

# Destaques (página 6): listas "a investigar"
DESTAQUE_CLIENTE_1_PRODUTO_KG = 5_000   # clientes com 1 produto e pelo menos este volume
DESTAQUE_MUITOS_CLIENTES = 10           # produtos com pelo menos N clientes...
DESTAQUE_KG_POR_CLIENTE_BAIXO = 500     # ...e no máximo este kg por cliente
DESTAQUE_ALTO_VOLUME_KG = 10_000        # produtos com pelo menos este volume...
DESTAQUE_POUCOS_CLIENTES = 3            # ...e no máximo N clientes

# Frontend que pode chamar a API (Vite roda na 5173)
ORIGENS_PERMITIDAS = ["http://localhost:5173", "http://127.0.0.1:5173"]
