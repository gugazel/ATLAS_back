# ATLAS_back

API do dashboard ATLAS (Aditive), em FastAPI + pandas. Lê as planilhas, junta os clientes pelo CNPJ e recalcula todos os indicadores. A especificação completa está em [docs/plano_dashboard_aditive.md](docs/plano_dashboard_aditive.md).

## Arquivos de dados (não vão para o Git)

Coloque em `data/`:

- `Base_Aditive.xlsx`: abas Base_Produtos, Base_Clientes e Panorama_Interno
- `Planilha_clientes_aditive_estados_preenchida (1).xlsx`: Cliente, CNPJ, Estado e Fonte Estado (se não existir, usa a versão antiga `Planilha clientes aditivw 2.xlsx`)
- `de_para_clientes.csv`: liga cada nome da Base_Clientes a um CNPJ. A coluna `status` pode ser editada no Excel: `ok` junta, `rejeitado` separa
- `01 - Relatorio de Vendas (Cliente x Produtos) .xlsx`: quem comprou o quê (qualquer arquivo com "Cliente x Produto" no nome)
- `de_para_vendas.csv`: liga cada razão social do relatório a um cliente. Gerado por `scripts/gerar_de_para_vendas.py`; edite `status` (`ok` + `nome_no_dashboard`, ou `rejeitado`)
- `Grupo_8_Prospeccao_Aditive_CNPJ_contatos.xlsx`: empresas prospectadas pela equipe (qualquer arquivo com "Prospec" no nome). Aba `Página1` = uma linha por empresa; as abas por região trazem os aditivos sugeridos. **Não são clientes**: não entram em volume, share nem ranking

Depois de trocar um arquivo, clique em **Recarregar dados** no dashboard (ou chame `POST /api/recarregar`).

## Rodar

```powershell
python -m venv .venv                         # só na primeira vez
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload
```

A documentação interativa da API fica em http://127.0.0.1:8000/docs.

## Testes

```powershell
.venv\Scripts\python -m pytest
```

Os testes conferem os números recalculados com o Panorama_Interno (gabarito) e com o diagnóstico do plano.

## Mapa

O contorno dos estados (`ATLAS_front/src/assets/brasil-uf.json`) e o centro das cidades dos clientes e das empresas prospectadas (`app/data/cidades.json`) vêm da API pública do IBGE. Para atualizar, por exemplo quando aparecerem cidades novas:

```powershell
.venv\Scripts\python scripts\baixar_geografia.py
```

Nenhum dado de cliente é enviado: o script baixa a lista inteira de municípios de cada estado e procura as cidades localmente.

## Estrutura

```
app/
├── main.py          cria o FastAPI e registra as rotas
├── config.py        caminhos e limites de negócio (risco, ABC, alertas, destaques)
├── schemas.py       formato das respostas da página 1
├── data/loader.py   leitura, limpeza, consolidação por CNPJ e cálculos
├── data/estado.py   base carregada em memória
├── services/        regras de cada página + filtros e alertas
└── routers/         endpoints (/api/executivo, /clientes, /geografia, /produtos, /riscos, /destaques, /prospeccao, /qualidade)
scripts/             baixar_geografia.py, gerar_de_para_vendas.py
```
