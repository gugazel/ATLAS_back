"""Gera (ou atualiza) data/de_para_vendas.csv: cada razão social do relatório de vendas e o
cliente do dashboard a que ela foi ligada.

Para corrigir, edite no Excel:
  status = ok        -> liga ao cliente escrito em nome_no_dashboard (use o nome como aparece no dashboard)
  status = rejeitado -> não liga a nenhum cliente
As linhas com ok/rejeitado são mantidas quando o script roda de novo.

Rodar de ATLAS_back:  .venv\\Scripts\\python scripts\\gerar_de_para_vendas.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402
from app.data.loader import carregar  # noqa: E402

base = carregar()
m = base.casamento
with open(config.ARQ_DE_PARA_VENDAS, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["razao_social", "nome_no_dashboard", "status", "observacao"])
    for linha in m.sort_values(["status", "razao"]).itertuples(index=False):
        w.writerow([linha.razao, linha.nome_no_dashboard or "", linha.status, linha.observacao or ""])
print(f"{len(m)} razões sociais -> {config.ARQ_DE_PARA_VENDAS}")
print(m["status"].value_counts().to_string())
