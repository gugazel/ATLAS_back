# ATLAS — Dashboard de Inteligência Comercial Aditive

Diagnóstico da base `Base_Aditive.xlsx` e especificação do dashboard (backend FastAPI + frontend React).

> Todos os números deste documento foram recalculados a partir da planilha (versão de 10/09/2026). Nenhum dado foi estimado ou inventado. Onde algo é inferência, está marcado como **(inferência — validar)**.

---

## 0. Decisões v2 (10/09/2026) — esta seção prevalece sobre o restante do documento

### 0.1 Escopo e público
- **Usuária:** só a dona da Aditive, por enquanto. O dashboard roda localmente (no computador), sem login. A publicação pode ser decidida depois.
- **Objetivo:** ser uma forma visual e interativa de explorar a planilha. **Não há prioridade estratégica definida.** Por isso as páginas mostram os dados de forma neutra, sem ranquear "o que fazer".
- **Fontes usadas:** apenas `Base_Produtos`, `Base_Clientes` e `Panorama_Interno` (de `Base_Aditive.xlsx`), mais a **planilha de CNPJ** (`Planilha clientes aditivw 2.xlsx`: Cliente, CNPJ, Estado).
- **Fora do escopo:** Diretoria (incluindo a série mensal), Produtos_Estrategicos, Alvos_Comerciais, CRM_Pipeline, Benchmark_Estados, Clientes_por_Estado, Visao_Estadual e Metodologia.
- O `Panorama_Interno` é todo derivado das bases. O backend recalcula a tabela de famílias e o top 20, e **usa o Panorama como gabarito** nos testes automáticos (os números precisam bater).

### 0.2 Total oficial
- **Volume oficial = Σ Base_Clientes = 937.787,55 kg.** Motivos: (1) é a base do ranking e dos shares da própria planilha; (2) bate exatamente com a série mensal jan–jul/2026; (3) a base de produtos está 73,8 t menor.
- As visões de **produto e família** usam a Base_Produtos (863.993,41 kg). Os shares de família são calculados sobre ela, igual ao Panorama. A página de produtos mostra o aviso "volume detalhado por produto = 92,1% do total oficial".
- É uma decisão provisória, até a Aditive esclarecer a diferença.

### 0.3 Clientes: CNPJ, consolidação e grupo econômico
- **Chave do cliente = CNPJ.** Os nomes da Base_Clientes foram cruzados com a planilha de CNPJ. O resultado está em `data/de_para_clientes.csv` (fora do Git):

| Status | Registros | Volume | Tratamento no dashboard |
|--------|-----------|--------|-------------------------|
| `exato` | 244 | 633.025 kg | Consolidado automaticamente |
| `sugerido` | 69 | 129.306 kg | Consolidado (variação de nome ou erro de digitação). Trocar para `rejeitado` se estiver errado |
| `revisar` | 7 | 20.032 kg | **Não** consolidado até alguém mudar para `ok` |
| `sem_cnpj` | 1 | 155.425 kg | VALGROUP (unidade de Lorena/SP), que não está na planilha de CNPJ |

- Resultado: **321 registros → 249 clientes** (65 clientes tinham 2 ou mais grafias).
- Com o mesmo CNPJ sob nomes diferentes (MOURA, BUTTNER, E G IND e IPT/ITP PACK), o dashboard trata como um cliente só. **CD EMBALAGENS × CDI PLASTIC** têm o mesmo CNPJ na planilha nova e ficaram em `revisar`.
- **Grupo econômico:** os 6 registros VALGROUP formam o grupo **VALGROUP**, confirmado pela Aditive. Também entram no mesmo grupo os CNPJs com a mesma raiz (8 primeiros dígitos), como a matriz e a filial IBRACIL. O dashboard tem a opção **"Ver por: Cliente (CNPJ) | Grupo econômico"**.
- Nos clientes consolidados, "Produtos comprados" é a **soma** dos registros e pode contar o mesmo produto duas vezes. O tooltip avisa isso.

**Números atualizados (clientes consolidados):**

| Indicador | Por cliente (CNPJ) | Por grupo econômico |
|-----------|--------------------|---------------------|
| Nº de clientes / grupos | 249 | 243 |
| Maior | VALGROUP 16,6% | **VALGROUP 39,2%** |
| Top 5 | 42,3% | 53,2% |
| Top 10 | 56,5% | 65,5% |
| Clientes (ou grupos) para 80% do volume | 30 | 25 |

- **Correção (10/09/2026):** a versão anterior dizia 244 grupos. O certo é **243**: 249 clientes, menos 5 (os 6 VALGROUP viram 1) e menos 1 (matriz e filial IBRACIL viram 1).
- Registros em `revisar` não são juntados a outros clientes, mas usam a UF da planilha de CNPJ. A dúvida é se são a mesma empresa, não onde ficam: CDI PLASTIC e CD EMBALAGENS estão em SP nas duas linhas da planilha.

### 0.4 Geografia
> **Atualização 11/09/2026:** chegou a planilha `Planilha_clientes_aditive_estados_preenchida (1).xlsx`, com os mesmos 247 CNPJs e **todos os estados preenchidos**, mais a coluna "Fonte Estado" (link de onde a UF foi conferida; 14 dos 194 estados novos vieram sem link). Resultado: **248 de 249 clientes com UF (100% do volume)**. Só GLUD IND (25 kg, "revisar", sem CNPJ) fica sem UF. Região: Sudeste 71,6% · Sul 15,5% · Norte 7,8% · Nordeste 5,2% · Centro-Oeste 0,03%. SP = 51,3% do volume (165 clientes).
> **Conflito:** a Base_Clientes põe a VALGROUP BRASIL em SP (Lorena); a planilha nova, pelo CNPJ 04.285.109/0001-73, põe em RJ. Vale a planilha de CNPJ (regra abaixo), então 95 t (10,4%) vão para RJ e a cidade Lorena é descartada para esse cliente. Pode ser o endereço da matriz e não o da unidade que compra: **confirmar com a Aditive**. O conflito aparece nos avisos, na página Qualidade e no perfil do cliente.
> Os números abaixo são da versão anterior (10/09) e ficam como histórico.

- UF = planilha de CNPJ; se estiver vazia, a UF da Base_Clientes. Não houve conflito entre as duas fontes.
- **Cobertura: 59 de 249 clientes (23,7%), 575.075 kg (61,3% do volume).** Antes eram 46,3%.
- Região: Sudeste 52,1% · Sul 4,6% · Norte 2,8% · Nordeste 1,7% · Centro-Oeste ~0% · **Não classificado 38,7% (190 clientes)**.
- Maiores clientes ainda sem UF: MDG IND, TRAVI PLASTICOS, RESINPO, GDM IND, NOLD e PP FILME IND.
- **Próximo passo possível (depende de autorização):** consultar os CNPJs em uma base pública da Receita Federal. Isso preencheria UF, cidade, porte e atividade (CNAE) de praticamente todos os clientes, e hoje Porte e Segmento estão 100% vazios. A fonte e a data da consulta ficam registradas.
- Cidade: só existe para 10 registros, então o drill-down geográfico vai até **Região → UF → Cliente**.

### 0.5 Ajustes nas páginas
- Página 1: **sem** a tendência mensal (a aba Diretoria está fora do escopo).
- Página 6 vira **"Destaques"**, só com listas calculáveis pelas 3 bases: clientes com 1 produto, produtos com muitos clientes e baixo kg/cliente, produtos com alto volume e poucos clientes, produtos estratégicos (flag da Base_Produtos) com 1 cliente. **Sem** alvos, CRM ou a lista da aba de estratégicos.
- Alertas A05 (lista estratégica) e A11 (mês fraco): removidos.

### 0.6 Identidade visual
- **Fundo branco**. Todo o resto usa a paleta verde da Aditive. Os 5 verdes abaixo são os **códigos oficiais** enviados pela Aditive (10/09/2026).

| Token | Nome oficial | Hex | Uso |
|-------|--------------|-----|-----|
| `--verde-900` | Verde escuro | `#174C3C` | Títulos, menu ativo, números dos KPIs |
| `--verde-700` | Verde petróleo | `#28725A` | Série principal dos gráficos, botões |
| `--verde-500` | Verde médio | `#3F9874` | Série secundária, hover |
| `--verde-300` | Verde claro | `#7EB99D` | Série terciária, barras de fundo |
| `--verde-100` | Verde muito claro | `#C5DFD2` | Fundos de cartão/destaque, seleção |

Cores de apoio (não fazem parte da paleta da Aditive):

| Token | Hex | Uso |
|-------|-----|-----|
| `--fundo` | `#FFFFFF` | Fundo da página |
| `--texto` | `#1F2A26` | Texto principal |
| `--texto-suave` | `#5F6F68` | Legendas, eixos |
| `--borda` | `#E3EAE6` | Divisórias, grades |
| `--cinza-nc` | `#B8C2BD` | "Não classificado" / sem dado |
| `--alerta-alto` | `#C0392B` | **Somente** risco alto |
| `--alerta-medio` | `#D69E2E` | **Somente** risco médio |

- Risco baixo usa `--verde-500`. Vermelho e âmbar ficam fora da paleta de propósito: aparecem só para risco, e assim o alerta chama atenção.
- Categorias ordenadas (ABC, faixas) usam tons do verde escuro ao claro.
- Logo: `ATLAS_front/src/assets/logo-aditive.png`.

### 0.7 Classe ABC recalculada
- Na planilha, a coluna "Classe ABC" é **valor fixo**, sem fórmula, e não segue a regra 80%/95% em 2 produtos de fronteira: `SL-L4248/01` (acumulado 81,7%, está A na planilha) e `SL-F4095/02` (acumulado 95,4%, está B).
- O dashboard usa a regra documentada (seção 9): **A 15 · B 24 · C 98**, em vez de A 16 · B 24 · C 97. Com isso, o alerta A03 fica com 11 produtos, não 12.
- A diferença vai aparecer na página Qualidade da base.

### 0.8 Andamento
| Fase | Situação (10/09/2026) |
|------|------------------------|
| 0. Ambiente | ✅ Python 3.12, Node 24, `.venv` e `node_modules` |
| 1. Backend "olá mundo" | ✅ `GET /api/saude`, documentação em `/docs` |
| 2. Carga e limpeza | ✅ `app/data/loader.py`: bases, CNPJ, de-para, clientes e grupos |
| 3. Testes de validação | ✅ 20 testes; Panorama_Interno como gabarito |
| 4. API da página 1 | ✅ `GET /api/executivo?visao=cliente\|grupo`, `GET /api/alertas`, `POST /api/recarregar` |
| 5. Frontend "olá mundo" | ✅ Vite + React + React Router + ECharts |
| 6. Página 1 completa | ✅ 9 cartões, 5 gráficos (cada um com "Ver tabela"), 5 alertas, alternância cliente/grupo |
| 7. Filtros globais | ✅ barra de filtros por página, guardada na URL, com chips e "Limpar tudo" |
| 8. Páginas 2 a 7 | ✅ Clientes, Geografia (mapa), Produtos, Riscos, Destaques, Qualidade · 31 testes |
| 9. Interatividade | ✅ filtro cruzado (clique em barra/estado), migalhas Brasil › Região › UF, painéis de cliente e produto |
| 9a. Justificativa de risco (11/09) | ✅ todo selo, alerta, legenda e tooltip de risco explica o porquê ao passar o mouse ou clicar, com os números do item |
| 9c. Empresas e Prospecção (11/09) | ✅ aba Empresas (busca visual), aba Prospecção, prospects no mapa, clique no treemap abre o produto · 49 testes |
| 9b. Comparar 2–4 itens lado a lado | ⏳ |

Para abrir: `iniciar_atlas.bat` na pasta `dash_atlas`.

### 0.9 Mapa (página Geografia), pedido de 10/09/2026
- Mapa do Brasil por UF (contorno do IBGE) e **um ponto por cliente**, com tamanho proporcional ao volume. Passar o mouse mostra o nome; clicar abre o perfil. Clicar num estado filtra por ele.
- Filtrar uma região aproxima o mapa, pinta os estados da região (quem não tem cliente com UF fica verde-claro, o resto do país cinza) e mostra só os pontos da seleção.
- **Posição dos pontos:** 10 registros têm cidade. Esses ficam no centro do município (centroide do IBGE, em `app/data/cidades.json`, gerado por `scripts/baixar_geografia.py`). Os outros 49 clientes com UF ficam numa **posição ilustrativa dentro do estado**, desenhados vazados e explicados na legenda. Com a consulta dos CNPJs na Receita, quase todos passariam a ter cidade.
- Medida do mapa: **Toneladas, Share (%) ou Nº de clientes**. Os 190 clientes sem UF não aparecem no mapa: ficam num cartão e numa "fila de cadastro".
- **Não é possível com os dados atuais** (os botões aparecem bloqueados, com a explicação):
  - Filtrar o mapa por **aditivo ou família**, e mostrar os **aditivos comprados** por cliente: falta a base cliente × produto (seção 3.2).
  - **Receita (R$):** nenhuma planilha tem valores em reais. Precisa do campo Valor na exportação do SAP.

### 0.11 Relatório de vendas cliente × produto (11/09/2026) — substitui a restrição da 0.10
- Arquivo `01 - Relatorio de Vendas (Cliente x Produtos) .xlsx` (SAP): razão social × código do item × descrição. **Sem volume, data nem valor.** 360 pares únicos, 208 razões sociais, 106 códigos (13 fora da Base_Produtos, entre eles `1234` e `0013253`).
- Ligação razão social → cliente: começo do nome, com abreviações padronizadas (INDUSTRIA=IND, COMERCIO=COM…). Resultado: 175 exatas, 5 por nome muito parecido (≥ 90%), 4 para revisar (ex.: VALGROUP BRASIL II/III, que ficam só no grupo VALGROUP), 24 sem cliente na Base_Clientes. Correções em `data/de_para_vendas.csv` (gerado por `scripts/gerar_de_para_vendas.py`).
- Cobertura: **187 de 249 clientes (90% do volume)** com produtos conhecidos. Nos clientes de um registro só, o relatório tem o mesmo nº de produtos da Base_Clientes em 93 de 129. **Período do relatório não informado** — as diferenças podem vir daí. Faltam no relatório, por exemplo, VALGROUP (Lorena), COLERTEC e RESINPO.
- **O que passou a funcionar:** produtos e famílias no perfil de cada cliente; compradores no perfil de cada produto; filtros "Compra a família" e "Compra o produto" nas abas Clientes e Geografia (o mapa filtra por aditivo); matriz família × região; clientes **distintos** por família; produtos distintos por UF; venda cruzada por regra de associação (Destaques).
- **Cuidados:** com "Compra a família/produto", o volume mostrado é o total desses clientes (aviso na barra de filtros). A venda cruzada só usa os 105 clientes em que o relatório lista todos os produtos informados na Base_Clientes, e as sugestões são "a investigar".
- **Continua dependendo de dados:** volume por cliente × produto (quem é o maior comprador de cada produto, diversificação real, reconciliação dos totais), data (período, sazonalidade, churn) e valor (receita).

### 0.10 Aditivos por cliente: uso parcial (11/09/2026)
- A Base_Produtos traz família e subfamília **por produto**, mas não diz quem comprou. A única ligação cliente × produto da planilha é a coluna **"Cliente atual de referência" da aba Alvos_Comerciais**: até 3 clientes para cada um dos 20 maiores produtos, sem volume por cliente. Cruzada com a Base_Produtos, ela dá a família e a subfamília dos aditivos desses clientes.
- Cobertura: 49 ligações, todas identificadas na Base_Clientes. São **44 de 249 clientes** (67% do volume) e **49 de 606 pares** cliente-produto (8%).
- **Regra (pedido do usuário: não enviesar):** a lista aparece só no **perfil do cliente** ("Aditivos comprados") e no **perfil do produto** ("Compradores"), sempre marcada como parcial. Ela **não entra** em somas, shares, rankings, filtros, mapa nem venda cruzada. Quem não está na lista não é "não comprador": só não foi listado.
- A aba Alvos_Comerciais continua fora do escopo para todo o resto (alvos de prospecção).

### 0.12 Empresas, Prospecção e produto clicável (11/09/2026)
Três pedidos do mesmo dia, já no ar:

**Aba Empresas** (`/empresas`) — jeito visual de achar uma empresa sem passar por tabela: uma busca grande (nome, CNPJ, cidade, estado ou família de aditivo), ordenação por volume / nome / nº de famílias, e um cartão por empresa com posição, volume, share, nº de produtos, saídas e as famílias que ela compra. Clicar abre o perfil completo. Os cartões usam os mesmos números da aba Clientes — quem não aparece no relatório de vendas mostra "Produtos não identificados no relatório de vendas" em vez de família nenhuma.

**Clique no treemap de Produtos** — clicar num retângulo abre o perfil do produto (volume, share, nº de clientes, faixa de risco com o porquê, ABC, IPE e a lista de **compradores** vinda do relatório de vendas). Antes só a tabela abria o painel.

**Aba Prospecção** (`/prospeccao`) — planilha `Grupo_8_Prospeccao_Aditive_CNPJ_contatos.xlsx`, 102 empresas levantadas pela equipe:
- **Isolamento:** prospect **não é cliente**. O id começa com `p-`, não entra em volume, share, ranking, ABC, risco nem venda cruzada, e há teste garantindo que os conjuntos não se cruzam. Um aviso no topo da aba diz isso.
- **Setor:** a planilha escreve o cluster em texto livre e a mesma atividade aparece em várias grafias ("Embalagem Flexível & Filmes", "(agro)", "(+ interesse PCR)", "— conservação FLV"…): são **30 textos para 102 empresas**, o que deixa gráfico e filtro inúteis. O `setor` corta complementos (parênteses, `+`, `/`, `:`) e junta as grafias equivalentes → **12 setores**. O cluster original continua no painel e na planilha baixada. Os 13 marcados "confirmar cluster" viram **"A confirmar"**, sempre no fim da lista.
- **Já são clientes:** 4 empresas da lista batem com a carteira — 2 pelo mesmo CNPJ e 2 pela raiz (mesmo grupo). Ficam marcadas no cartão, no painel e num KPI, para não abordar como nova.
- **Cobertura:** 89 com CNPJ, 92 com UF (**10 sem UF não entram no mapa**), 91 com cidade conhecida no IBGE, 47 com aditivos sugeridos pela equipe (sugestão, **não** é compra confirmada), 7 já contatadas.
- **Filtros:** região, estado, setor e status do contato. Cada gráfico ignora o próprio filtro (senão sobraria uma barra só) e realça a seleção.
- **No mapa (Geografia):** um botão escolhe **Clientes / Prospecção / Ambos**. Cliente é **círculo cheio** com tamanho por volume; prospect é **losango vazado** (contorno verde-escuro, miolo branco), do mesmo tamanho — não tem volume para dimensionar. Tudo na paleta da Aditive: a diferença é forma + preenchimento, não cor, e o losango vazado continua visível mesmo sobre SP (o estado mais escuro). A legenda explica os dois.
- **Ajuste de 12/09/2026:** o usuário pediu para tirar os indicadores "Já contatadas" e "Já são clientes" e o gráfico "Status do contato" (a lista é quase toda "Sem Contato Feito", então o gráfico não dizia nada). O aviso das empresas que já são clientes passou para a caixa de texto do topo, e o filtro por status continua na barra de filtros. Restaram 4 indicadores e 2 gráficos (região e setor).

---

## 1. Diagnóstico da estrutura e da qualidade da base

### 1.1 Resumo executivo do diagnóstico

| # | Achado | Gravidade | Impacto no dashboard |
|---|--------|-----------|----------------------|
| 1 | **Não existe tabela cliente × produto.** | Crítica | Impossível dizer quais produtos cada cliente compra, calcular venda cruzada ou filtrar clientes por produto. |
| 2 | **Totais divergentes:** clientes somam **937.787,55 kg** e produtos somam **863.993,41 kg** (diferença de **73.794,14 kg**, ou 7,9%). | Alta | Os cartões de "Volume total" mostram valores diferentes dependendo da visão. |
| 3 | A série mensal (aba Diretoria) soma exatamente **937.787,55 kg**, que é o total de clientes. A base de produtos é que está incompleta ou tem outro recorte. | Alta | O total "oficial" provavelmente é o de clientes, mas a Aditive precisa confirmar. |
| 4 | Os pares cliente-produto também não batem: 606 (Σ "Produtos comprados") contra 559 (Σ "Nº clientes"). As saídas idem: 1.319 contra 1.255. | Alta | Confirma que as duas bases vêm de extrações diferentes. |
| 5 | **Cliente não tem código**: a chave é o nome, com variações e erros de digitação (ex.: `GDM IND` / `GDM INDUSTRIA` / `GDM`; `BRINQUEDOS BANDEIRANTES` / `BRINQUEDOS BAANDEIRASNTES`; `WILPACK` / `WILPCK` / `WILLPACK`). Uma normalização simples já agrupa **90 registros em 44 grupos**. | Alta | O "nº de clientes" (321) está inflado e o share por cliente está fragmentado. |
| 6 | **Cobertura geográfica de 3,1%**: só 10 dos 321 registros têm UF/cidade (46,3% do volume). Os outros 311 estão "Não classificado" (53,7% do volume). Dos top 20 clientes, **12 não têm UF** (23,2% do volume total). | Alta | Mapa e análise regional cobrem menos da metade do volume. |
| 7 | Os campos **Segmento, Porte e Responsável estão 100% vazios** em clientes, e **Responsável e Observação estão 100% vazios** em produtos. | Alta | Não dá para segmentar oportunidades nem comparar responsáveis comerciais. |
| 8 | 79 dos 137 produtos (58%) **não têm descrição, família, aplicação, resina nem tipo**. Juntos, representam só 13.386 kg (1,5% do volume). | Média | Viram "Não classificado" nas análises de família. |
| 9 | **Duas listas de "estratégicos" conflitantes:** a Base_Produtos marca 22 produtos, e a aba Produtos_Estrategicos lista 9. Desses 9, três (`SL-P4600`, `SL-S4549/AO` e `SD-615`) estão como **não estratégicos, sem família e fora do site** na base. | Média | Os alertas de "estratégico sem site" dependem de qual lista vale. |
| 10 | Flags incoerentes: 6 produtos têm `Especialidade?=Sim` mas `Tipo=Intermediário`, e `T7200` tem `Tipo=Especialidade` com `Especialidade?=Não`. `M9584` se chama "Masterfil Acoplante" na base e "Masterfil Adibond PP" na aba de estratégicos. | Média | Confusão no KPI "Participação de especialidades". |
| 11 | **Valores de fórmula desatualizados** no Excel: a aba Visao_Estadual mostra participação 0% e cobertura 0% para SP, quando o correto seria 29,8% e 100%. | Média | O backend **não pode ler células calculadas**. Precisa recalcular tudo a partir das bases. |
| 12 | Denominadores diferentes para o share por estado: Clientes_por_Estado usa o total geral (SP = 29,8%), e Benchmark_Estados usa só o volume classificado (SP = 64,3%). | Média | É preciso padronizar uma regra só (proposta: total geral). |
| 13 | "Status comercial" é "Ativo" em 100% dos produtos. | Baixa | O filtro e o gráfico de status não trazem informação hoje. |
| 14 | Códigos de produto parecidos, a validar (podem ser variantes legítimas ou erro de digitação): `9041/CI`×`M9041/CI`, `S-L4058/01`×`SL-L4058/01`, `SD-900PP`×`SD-900/PP`, `SL-L4549/AO`×`SL-S4549/AO`, `M9436`×`M9436/01`, `M9581`×`M9581/01`, `M9034`×`M9034N`. Subfamília `"Antichama "` tem espaço sobrando. | Baixa | Pode fragmentar o volume de um mesmo produto. |
| 15 | Benchmark_Estados: os campos externos (transformadores estimados, % de mercado, fonte) estão vazios. ICC e IOR não são calculáveis. | Baixa | A análise de "potencial regional" não tem base externa hoje. |
| 16 | CRM_Pipeline: 100 linhas, todas com status "Não iniciado" e responsável "A definir", sem UF, datas ou valor potencial. | Baixa | O pipeline pode ser exibido, mas ainda não mede avanço. |

### 1.2 O que está correto (validado)

- A participação de cada cliente é igual a volume ÷ Σ volume de clientes em **todos os 321 registros**. A soma dá 100%.
- A posição no ranking é sequencial e ordenada por volume decrescente.
- Não há código de produto duplicado nem nome de cliente duplicado exato.
- A tabela de famílias (Panorama_Interno) bate 100% com a Base_Produtos em volume, nº de produtos e clientes somados. As participações somam 100%.
- **IPE V5** recalculado bate em todos os 137 produtos. **Nível** é coerente com o IPE (≥80 OURO, ≥65 PRATA, ≥50 BRONZE, senão MONITORAR).
- `Risco concentração = Dependência maior cliente × 100` e `Índice diversificação = MIN(100; Nº clientes × 5)` valem em todas as linhas.
- A Classe ABC é coerente com a curva acumulada de volume (A até ~80%, B até ~95%, C no restante).

### 1.3 Período de referência

- A aba Diretoria declara a base como **jan–jul/2026** e traz a série mensal. Essa série soma exatamente o total de clientes, então a Base_Clientes cobre jan–jul/2026.
- A Base_Produtos chama a coluna de "Volume 2026 (kg)" sem dizer os meses. Como o total é menor, **não é possível confirmar que o período é o mesmo**. Isso é pergunta para a Aditive.
- Não há data em nenhuma tabela detalhada. Só existe histórico mensal no nível da empresa inteira.

---

## 2. Tabelas e granularidades

| Aba | Granularidade (1 linha =) | Linhas | Tipo | Usar no dashboard? |
|-----|---------------------------|--------|------|--------------------|
| `Base_Produtos` | 1 código Aditive (acumulado do período) | 137 | Base (dimensão + agregados) | **Sim — fonte principal de produtos** |
| `Base_Clientes` | 1 nome de cliente (acumulado jan–jul/2026) | 321 | Base (dimensão + agregados) | **Sim — fonte principal de clientes** |
| `Diretoria` (bloco R18–R25) | 1 mês (empresa inteira) | 7 | Série temporal agregada | Sim — tendência mensal |
| `Produtos_Estrategicos` | 1 produto priorizado (com ICE) | 9 | Cadastro de estratégia | Sim — após decidir a lista oficial |
| `Alvos_Comerciais` | 1 produto × empresa-alvo | 100 (20 produtos × 5 alvos) | Hipóteses de prospecção | Sim — página de oportunidades |
| `CRM_Pipeline` | 1 empresa-alvo × produto | 100 | Pipeline | Sim — página de oportunidades |
| `Clientes_por_Estado` | 1 UF (+ lista de clientes) | 28 + 321 | **Derivada** (fórmulas sobre Base_Clientes) | Não ler: recalcular no backend |
| `Panorama_Interno` | 1 família / top 20 clientes | 20 + 20 | **Derivada** | Não ler: recalcular |
| `Benchmark_Estados` | 1 UF | 27 | Derivada + campos externos vazios | Futuro (quando houver dados externos) |
| `Visao_Estadual` | Painel interativo do Excel | — | Visualização | Não (valores desatualizados) |
| `Metodologia` | 1 indicador | 7 | Dicionário | Sim — tela "Sobre os indicadores" |

O "Ranking comercial de clientes" (item 5 do briefing) **não é uma tabela independente**. É o bloco direito da aba Panorama_Interno, ou seja, os top 20 da Base_Clientes.

### 2.1 Campos originais × calculados

**Base_Produtos**
- *Cadastro (original):* Código, Descrição, Família, Subfamília, Aplicação, Resina, Tipo, Especialidade?, Estratégico?, Site?, Prioridade mkt, Status, Responsável, Observação.
- *Agregados de vendas (vêm prontos, sem fórmula; não dá para recalcular sem a base transacional):* Volume 2026, Nº clientes, Nº saídas, Dependência maior cliente.
- *Calculados (fórmula no Excel ou recalculáveis):* Classe ABC, IPE V5, Nível, Índice diversificação, Risco concentração.

**Base_Clientes**
- *Original:* Cliente (nome).
- *Agregados de vendas (prontos):* Volume, Produtos comprados, Nº saídas.
- *Calculados:* Posição, Participação.
- *Enriquecimento (não vem do ERP):* UF, Cidade, Região, Confiança, Observação CRM ("identificada automaticamente" / "inferência pelo nome").
- *Vazios:* Segmento principal, Porte, Responsável.

---

## 3. Relacionamentos

### 3.1 Situação atual

```
 Base_Clientes (nome)          Base_Produtos (código)
        │                             │
        │   ✗ sem ligação direta ✗    │
        │                             │
   Região/UF (texto)           Família/Subfamília (texto)
```

- `Base_Produtos.Código Aditive` → `Produtos_Estrategicos.Produto`, `Alvos_Comerciais.Produto`, `CRM_Pipeline.Produto/Família`: **existe chave** (código).
- `Base_Clientes.Cliente` → `Alvos_Comerciais."Cliente atual de referência"`: só ligação textual, para 20 produtos e até 3 clientes cada, sem volume por cliente. **Não substitui a tabela cliente × produto.**
- `Base_Clientes` ↔ `Base_Produtos`: **nenhuma chave**.

### 3.2 Tabela necessária: `fato_vendas` (cliente × produto × saída)

Pedir à Aditive uma exportação do SAP com **1 linha por item de nota fiscal/saída**:

| Campo | Obrigatório | Por quê |
|-------|-------------|---------|
| Código do cliente (SAP) **e/ou CNPJ** | Sim | Chave única. Resolve os nomes duplicados. Com o CNPJ dá para buscar UF/cidade/CNAE em fonte pública e resolver a cobertura cadastral. |
| Nome do cliente | Sim | Exibição |
| Código Aditive | Sim | Chave com Base_Produtos |
| Descrição do produto | Sim | Conferência |
| Volume (kg) | Sim | Métrica principal |
| Nº da NF / saída | Sim | Conta saídas sem duplicar |
| Data de emissão | Sim | Período, tendência, recorrência |
| UF / cidade de entrega | Recomendado | Geografia por entrega |
| Vendedor / responsável | Recomendado | Performance por responsável |
| Valor (R$) | Opcional | Receita e preço médio (se puderem compartilhar) |

---

## 4. O que dá para calcular hoje

Legenda: ✅ viável · ⚠️ viável com ressalva · ❌ depende de dado novo

| Indicador | Status | Fórmula / regra | Campos | Valor atual |
|-----------|--------|-----------------|--------|-------------|
| Volume total (visão clientes) | ⚠️ | Σ Volume | Base_Clientes.Volume | 937.787,55 kg |
| Volume total (visão produtos) | ⚠️ | Σ Volume 2026 | Base_Produtos.Volume 2026 | 863.993,41 kg |
| Divergência de totais | ✅ | Vol_cli − Vol_prod | ambos | 73.794,14 kg (7,9%) |
| Nº clientes | ⚠️ | CONTAR(registros). Depois da padronização: CONTAR.DISTINTO(nome_padronizado) | Cliente | 321 registros |
| Nº produtos | ✅ | CONTAR.DISTINTO(Código) com volume > 0 | Código Aditive | 137 |
| Nº saídas | ⚠️ | Σ Nº saídas (definir qual base vale) | Nº saídas | 1.319 (cli) / 1.255 (prod) |
| Volume médio por cliente | ⚠️ | Vol_cli ÷ Nº clientes | — | 2.921 kg/registro |
| Volume médio por produto | ✅ | Vol_prod ÷ Nº produtos | — | 6.307 kg |
| Share do cliente *i* | ✅ | Vol_i ÷ Vol_cli | Volume | validado |
| Share do maior cliente | ⚠️ | MÁX(share_i) | — | 16,57% (VALGROUP) |
| Share top 5 / top 10 | ⚠️ | Σ share dos N maiores | — | 41,14% / 53,05% |
| Nº de clientes para 80% do volume | ✅ | menor N com acumulado ≥ 80% | — | 38 |
| HHI de clientes | ✅ | Σ (share_i × 100)² | — | 529 (baixa concentração pelo critério usual, mas distorcido pelos nomes duplicados) |
| Registros com nome "VALGROUP" | ⚠️ | Σ volume de nomes com "VALGROUP" **(inferência — validar se é o mesmo grupo econômico)** | Cliente | 6 registros, 367.575 kg (39,2%) |
| Média de produtos por cliente | ✅ | MÉDIA(Produtos comprados) | Produtos comprados | 1,89 |
| Clientes com 1 produto | ✅ | CONTAR(Produtos comprados = 1) | — | 205 (63,9%) |
| Nº de clientes por produto | ✅ | campo direto | Nº clientes | média 4,1 |
| Volume e share por família | ✅ | Σ Vol por família ÷ Vol_prod | Família, Volume | PPA 46,3% |
| Volume e share por subfamília | ✅ | idem, por subfamília (aparar espaços) | Subfamília | — |
| Volume e share por UF / região | ⚠️ | Σ Vol_cli por UF ÷ **Vol_cli total** ("Não classificado" explícito) | UF, Região | SP 29,8%; NC 53,7% |
| Clientes por UF / região | ⚠️ | CONTAR por UF | UF | — |
| Volume médio por cliente na UF | ⚠️ | Vol_UF ÷ Clientes_UF | — | SP 93.042 kg |
| Cobertura cadastral (quantidade) | ✅ | registros com UF e confiança ∈ {Alta, Média} ÷ total | UF, Confiança | **3,1%** |
| Cobertura cadastral (volume) | ✅ | Σ Vol desses registros ÷ Vol_cli | — | **46,3%** |
| Completude por campo | ✅ | preenchidos ÷ total, por campo | todos | Segmento/Porte/Resp. = 0% |
| Clientes por confiança | ✅ | CONTAR por Confiança | Confiança | Alta 9 · Média 1 · Baixa 311 |
| Sem localização classificada | ✅ | CONTAR(UF vazia) | UF | 311 |
| Share dos estratégicos | ⚠️ | Σ Vol(Estratégico=Sim) ÷ Vol_prod | Estratégico? | 22 produtos, 71,0% |
| Share das especialidades | ⚠️ | Σ Vol(Especialidade?=Sim) ÷ Vol_prod | Especialidade? | 20 produtos, 69,3% |
| Distribuição ABC | ✅ | recalcular: ordenar por volume; A até 80% acumulado, B até 95%, C no restante | Volume | A 16 (81,7%) · B 24 (13,7%) · C 97 (4,6%) |
| Produtos no site | ✅ | CONTAR(Site=Sim) | Divulgar no site? | 26 |
| Estratégicos fora do site | ⚠️ | CONTAR(Estratégico=Sim E Site≠Sim) | ambos | 0 pela base; 3 pela aba Produtos_Estrategicos |
| Dependência do maior cliente | ✅ | campo direto (vem pronto) | Dependência | 60 produtos com 1 cliente |
| Faixa de risco de concentração | ✅ | Alto ≥ 70% · Médio 40–70% · Baixo < 40% *(limites propostos, configuráveis)* | Dependência | Alto 87 · Médio 33 · Baixo 17 |
| Índice de diversificação | ⚠️ | MÍN(100; Nº clientes × 5). Satura em 20 clientes e ignora a distribuição de volume | Nº clientes | — |
| IPE V5 / Nível | ✅ | fórmula da aba Metodologia (validada) | vários | OURO 1 · PRATA 5 · BRONZE 11 · MONITORAR 120 |
| Volume médio por saída (cliente) | ✅ | Vol ÷ Nº saídas | Volume, Nº saídas | mediana 138 kg |
| Tendência mensal (empresa) | ✅ | série da aba Diretoria | Mês, Volume, Produtos, Clientes, Saídas | jan–jul/2026 |
| Status comercial | ⚠️ | CONTAR por Status | Status | 100% "Ativo" (sem variação) |
| Distribuição por responsável | ❌ | — | Responsável | 0% preenchido |

## 5. O que depende de dados adicionais

### 5.1 Depende da tabela cliente × produto (`fato_vendas`)
- Produtos e famílias comprados por cada cliente (perfil completo).
- Compradores de cada produto e **quem** é o maior cliente de cada produto.
- Venda cruzada: famílias/produtos não comprados por clientes com perfil parecido.
- Clientes semelhantes com portfólios diferentes.
- Contagem **distinta** de produtos por UF (hoje "Produtos somados" soma contagens e conta o mesmo produto várias vezes).
- Contagem **distinta** de clientes por família (hoje "Clientes somados" tem o mesmo problema).
- Diversificação real por produto: `1 − Σ(s_i²)` (HHI do produto), no lugar de `Nº clientes × 5`.
- Filtros cruzados cliente ↔ produto (ex.: "clientes do Sudeste que compram Antichama").
- Reconciliação exata dos totais (clientes × produtos).

### 5.2 Depende de histórico com data
- Filtro de período e comparações mês a mês e ano a ano por cliente, produto e região.
- Crescimento/queda por cliente, clientes novos, perdidos e inativos (churn).
- Recorrência, frequência de compra e intervalo entre pedidos.
- Sazonalidade por produto e família.
- Hoje só existe a série mensal agregada da empresa (jan–jul/2026).

### 5.3 Depende de cadastro complementar
- **Segmento, porte e responsável** do cliente, necessários para oportunidades qualificadas e comparação de responsáveis.
- UF/cidade dos 311 clientes sem localização (o CNPJ resolve).
- Família/descrição dos 79 produtos sem cadastro.
- Dados externos por UF (transformadores, % de mercado) para ICC/IOR.

---

## 6. Modelagem de dados

### 6.1 Modelo atual (MVP, com os dados que existem)

O backend lê as abas-base, limpa, padroniza e **recalcula** tudo. Nenhuma célula calculada do Excel é usada.

```
dim_produto        (codigo PK, descricao, familia, subfamilia, aplicacao, resina, tipo,
                    especialidade, estrategico, site, prioridade_mkt, status, responsavel,
                    volume_kg, n_clientes, n_saidas, dependencia_maior_cliente)
                    + calculados: classe_abc, ipe_v5, nivel, faixa_risco, indice_div

dim_cliente        (id_cliente PK gerado, nome_original, nome_padronizado*, uf, cidade,
                    regiao, confianca, obs_crm, segmento, porte, responsavel,
                    volume_kg, n_produtos, n_saidas)
                    + calculados: posicao, share, share_acumulado, kg_por_saida

dim_uf             (uf PK, nome_estado, regiao)       ← tabela fixa das 27 UFs
agg_mensal         (mes PK, volume_kg, n_produtos, n_clientes, n_saidas)
estrategia_produto (codigo FK, prioridade, ice, motivo, estrategia, mercado_alvo, meta_2027)
alvo_comercial     (codigo FK, empresa_alvo, ramo, justificativa, fonte_url, aderencia, status)
pipeline_crm       (empresa, codigo_ou_familia, origem, responsavel, status, prioridade, ...)
de_para_clientes*  (nome_original → nome_padronizado, grupo_economico)  ← validado pela Aditive
```

\* O `de_para_clientes` é uma planilha pequena que **a Aditive valida**. O sistema sugere os agrupamentos, mas não decide sozinho.

### 6.2 Modelo-alvo (estrela), quando chegar a `fato_vendas`

```
                 dim_tempo (data, mes, trimestre, ano)
                        │
dim_cliente ──── fato_vendas (nf, item, data, id_cliente, codigo, volume_kg, valor_rs) ──── dim_produto
    │                                                                                          │
  dim_uf                                                                                familia/subfamilia
```

Com a fato, `volume`, `n_clientes`, `n_produtos`, `n_saidas`, `dependencia` e `classe_abc` passam a ser **calculados a partir dela**, em vez de vir prontos.

---

## 7. Estrutura das páginas

| # | Página | Pergunta que responde | Viabilidade hoje |
|---|--------|-----------------------|------------------|
| 1 | Visão executiva | Como está a carteira e onde estão os riscos? | ✅ |
| 2 | Clientes | Quem compra, quanto e com que concentração? | ✅ (perfil de produtos do cliente ❌) |
| 3 | Geografia | Onde está o volume e o que falta cadastrar? | ⚠️ (46% do volume localizado) |
| 4 | Produtos e famílias | O que vende e como está o portfólio? | ✅ (compradores do produto ❌) |
| 5 | Concentração e riscos | Onde a Aditive está vulnerável? | ✅ |
| 6 | Oportunidades | Onde agir comercialmente e em marketing? | ⚠️ (venda cruzada ❌) |
| 7 | **Qualidade da base** *(recomendação extra)* | O que precisa ser corrigido no cadastro? | ✅ |

A página 7 é uma sugestão fora do briefing original. Os problemas de cadastro são grandes o bastante para merecer uma página própria com a lista de ações, em vez de ficar só na página geográfica.

---

## 8 e 10. Indicadores e gráficos por página

### Página 1 — Visão executiva
- **Cartões (9):** Volume total · Nº clientes · Nº produtos · Nº saídas · Volume médio/cliente · Share do maior cliente · Share top 5 · Produtos com risco alto · Cobertura cadastral (quantidade e volume).
  - O cartão de volume mostra os dois totais e um aviso de divergência enquanto ela existir.
- **Gráficos:**
  - Top 10 clientes, barras horizontais. Título-conclusão: *"3 registros VALGROUP somam 34,6% do volume"* (gerado automaticamente).
  - Volume por família, barras horizontais ordenadas (treemap como alternativa).
  - Volume por região, barras com "Não classificado" em cinza.
  - Distribuição ABC, barra 100% empilhada (nº de produtos × % do volume).
  - Produtos por faixa de risco, 3 barras nas cores de alerta.
  - Tendência mensal jan–jul, linha (único histórico disponível).
  - Lista dos 5 alertas principais.

### Página 2 — Clientes
- Tabela-ranking: posição, cliente, volume, share, share acumulado, nº produtos, nº saídas, kg/saída, UF, cidade, segmento, porte, responsável e confiança, com ícone de alerta para confiança baixa.
- **Pareto:** barras (volume por cliente) + linha (share acumulado), com marca nos 80%.
- **Dispersão** Nº saídas × kg/saída, com tamanho do ponto = volume. Separa "muitas saídas pequenas" de "poucos pedidos grandes".
- Histograma de "produtos comprados" (1, 2, 3, 4–5, 6+).
- **Painel de perfil** (ao clicar em um cliente): KPIs do cliente, posição, localização e confiança. A seção "Produtos e famílias comprados" mostra *"Disponível quando houver a base cliente × produto"*.

### Página 3 — Geografia
- **Mapa do Brasil por UF** (coropleto por volume), com "Não classificado" em um cartão lateral grande. Esconder essa fatia distorceria a leitura.
- Barras por região e por UF: volume, share, nº clientes, volume médio/cliente, saídas.
- Barra empilhada de confiança (Alta/Média/Baixa) por UF.
- Tabela de clientes sem localização, ordenada por volume. Na prática é a fila de trabalho do cadastro.
- Drill: Região → UF → Cidade → Cliente.

### Página 4 — Produtos e famílias
- **Treemap Família → Subfamília → Produto** (tamanho = volume, cor = faixa de risco ou nível IPE, alternável).
- Tabela de produtos: código, descrição, família, volume, share, nº clientes, saídas, ABC, IPE, nível, dependência, faixa de risco, flags (estratégico, especialidade, site).
- Barras por família: volume + nº produtos + nº estratégicos/site/especialidades.
- **Painel do produto** (ao clicar): KPIs e flags. A seção "Compradores" mostra *"Disponível quando houver a base cliente × produto"*.

### Página 5 — Concentração e riscos
- Curva acumulada de clientes (Lorenz/Pareto).
- **Matriz Volume × Dependência** (dispersão, eixo X em log, cor = faixa de risco, quadrantes fixos: alto volume/alta dependência = crítico).
- **Matriz Dependência × Nº clientes** (a diversificação atual é só `Nº clientes × 5`, então usar o nº de clientes direto é mais honesto).
- Tabela de alertas críticos (regras da seção 13).
- Cores: vermelho = alto, âmbar = médio, verde = baixo. **Somente nesta semântica.**

### Página 6 — Oportunidades
Todas as listas saem com o rótulo **"a investigar"**, nunca como "oportunidade confirmada".
- **Clientes relevantes com 1 produto** (volume ≥ limite configurável). Hoje: COLERTEC 31.000 kg, CARTONALE 28.525 kg, MDG 16.500 kg, VALGROUP BA 13.750 kg etc.
- **Estratégicos com baixo volume ou 1 cliente** (ex.: M9034N 945 kg; M9590 e SL-L4224/01 com 1 cliente).
- **Estratégicos fora do site ou sem cadastro** (lista da aba Produtos_Estrategicos).
- **Produtos com muitos clientes e baixo kg/cliente** (ex.: M9027C: 23 clientes, 203 kg/cliente). Indicam uso pontual e possível potencial de volume.
- **Produtos com alto volume e poucos clientes** (ex.: SL-C2263/02, 31.000 kg, 1 cliente).
- **Alvos comerciais** (100 hipóteses, 40 com aderência ≥ 90) e **pipeline CRM** (funil por status).
- Regiões/UFs com poucos clientes: exibir, com o aviso de que 53,7% do volume não tem UF.
- **Venda cruzada e "famílias não compradas":** bloco desativado, com a explicação do dado que falta. Quando ativado, só sugerir famílias compradas por clientes do **mesmo segmento/aplicação/resina**. A ausência de compra sozinha não conta como oportunidade.
- Oportunidades por responsável: desativado (campo vazio).

### Página 7 — Qualidade da base
- Completude por campo (barras de %), clientes e produtos.
- Divergência de totais (cartão de reconciliação).
- Lista de **possíveis duplicidades de cliente** (grupos sugeridos) para validação.
- Códigos de produto parecidos, a validar.
- Conflitos de flags (estratégico, especialidade).
- Top clientes sem UF (fila de enriquecimento).

---

## 9. Regras de cálculo (resumo técnico para o backend)

```
VOL_CLI            = Σ clientes.volume_kg                      (filtros de cliente aplicados)
VOL_PROD           = Σ produtos.volume_kg                      (filtros de produto aplicados)
share_cliente_i    = volume_i / VOL_CLI(sem filtro)            → share na carteira total
share_no_filtro_i  = volume_i / VOL_CLI(filtrado)              → share dentro da seleção
share_acum         = cumsum(share) ordenado por volume desc
topN_share         = Σ share dos N maiores
n_para_80          = min N tal que share_acum ≥ 0,80
hhi                = Σ (100·share_i)²
kg_por_saida       = volume / n_saidas
share_familia      = Σ volume(família) / VOL_PROD
share_uf           = Σ volume(UF) / VOL_CLI       ("Não classificado" = UF vazia)
cobertura_qtd      = #(UF preenchida E confiança ∈ {Alta, Média}) / #clientes
cobertura_vol      = Σ volume desses / VOL_CLI
classe_abc         = ordena por volume desc; acum ≤ 0,80 → A (inclui o item que cruza 80%);
                     ≤ 0,95 → B; resto → C
ipe_v5             = MIN(100, vol/vol_max·25 + MIN(n_cli/20,1)·20 + 15·esp + 15·estr
                             + 8·site + prioridade/5·12 + (1−dependência)·5)
nivel              = ≥80 OURO | ≥65 PRATA | ≥50 BRONZE | senão MONITORAR
faixa_risco        = dependência ≥ 0,70 ou n_cli = 1 → Alto | ≥ 0,40 → Médio | senão Baixo
```

Regras de negócio:
- **Os filtros de cliente não afetam as visões de produto e vice-versa**, até existir a `fato_vendas`. A interface mostra um aviso quando um filtro não se aplica ao gráfico.
- Os limites (70%/40% de risco, 10% de share alto, volume mínimo para oportunidade) ficam em um arquivo de configuração, não no código.
- Texto é normalizado sempre: `strip()`, remoção de espaços duplos, "Sim/Não" viram booleano.

---

## 11. Filtros e interações

| Filtro | Aplica-se a | Disponível hoje? |
|--------|-------------|------------------|
| Cliente, UF, Cidade, Região, Confiança | páginas 2, 3 (e cartões de cliente da 1) | ✅ |
| Segmento, Porte, Responsável (cliente) | idem | ❌ vazio. Aparece desabilitado com a explicação |
| Produto, Família, Subfamília, Aplicação, Resina, Tipo, ABC, Estratégico, Especialidade, Site, Prioridade mkt, Nível, Faixa de risco | páginas 4, 5 (e cartões de produto da 1) | ✅ |
| Status comercial | produtos | ⚠️ só tem "Ativo" |
| Período | tudo | ❌ (só a série mensal agregada) |

Interações:
- **Barra de filtros global** fixa no topo, com "chips" dos filtros ativos e o botão **Limpar tudo**.
- **Filtro cruzado:** clicar numa barra, fatia ou UF aplica o filtro, e clicar de novo remove.
- **Drill-down:** Região → UF → Cidade → Cliente (barras + migalhas "Brasil › Sudeste › SP"); Família → Subfamília → Produto (treemap com zoom).
- **Painel lateral de perfil** para cliente e produto.
- **Tooltips** com volume, share, nº clientes/produtos, saídas e confiança.
- **Comparar:** marcar 2 a 4 clientes, produtos, famílias ou regiões e abrir um quadro lado a lado.
- O estado dos filtros vai para a URL (`?regiao=Sudeste&familia=Anti-UV`), então dá para compartilhar um link com a visão pronta.

---

## 12. Wireframes textuais

### Página 1 — Visão executiva
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ATLAS · Aditive     [Executivo][Clientes][Geografia][Produtos][Riscos][Oport.]│
│ Filtros: [Região ▾][UF ▾][Família ▾][ABC ▾][Estratégico ▾]   chips… [Limpar] │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────────┤
│ Volume   │ Clientes │ Produtos │ Saídas   │ Vol/cli  │ Maior    │ Top 5      │
│ 937,8 t ⚠│ 321      │ 137      │ 1.319    │ 2,9 t    │ 16,6%    │ 41,1%      │
├──────────┴──────────┴──────────┴──────────┴──────────┼──────────┴────────────┤
│ Risco alto: 87 produtos   Cobertura: 3,1% (46% vol)  │ ⚠ ALERTAS             │
├──────────────────────────────────┬───────────────────┤ • Divergência 73,8 t  │
│ Top 10 clientes (barras)         │ Volume por família│ • 12 do top 20 sem UF │
│ "VALGROUP (3 registros) = 34,6%" │ "PPA = 46% do vol"│ • 60 produtos c/ 1 cli│
├──────────────────────────────────┼───────────────────┤ • 3 estratégicos     │
│ Volume por região (barras)       │ ABC (100% empilh.)│   sem cadastro/site   │
│ Não classificado em cinza        │ Risco (3 barras)  │ • 205 clientes c/ 1   │
├──────────────────────────────────┴───────────────────┤   produto             │
│ Tendência mensal jan–jul/2026 (linha)                │                       │
└──────────────────────────────────────────────────────┴───────────────────────┘
```

### Página 2 — Clientes
```
┌─ Filtros ────────────────────────────────────────────────────────────────────┐
├─────────────────────────────────────────────┬────────────────────────────────┤
│ Pareto (barras + linha acumulada, marca 80%)│ Dispersão saídas × kg/saída    │
│ "38 registros fazem 80% do volume"          │ (bolha = volume)               │
├─────────────────────────────────────────────┴────────────────────────────────┤
│ Tabela-ranking (ordenável, busca, exportar CSV)                              │
│ # | Cliente | Volume | Share | Acum. | Prod | Saídas | kg/saída | UF | Conf. │
├──────────────────────────────────────────────────────────────────────────────┤
│ Histograma: clientes por nº de produtos comprados                            │
└──────────────────────────────────────────────────────────────────────────────┘
   → clique numa linha abre o painel lateral ▸ Perfil do cliente
```

### Página 3 — Geografia
```
┌─ Migalhas: Brasil › Sudeste › SP ─────────────────────────── [Limpar] ──────┐
├───────────────────────────────┬──────────────────────────────────────────────┤
│                               │ ┌──────────────────────────────────────────┐ │
│      MAPA DO BRASIL (UF)      │ │ NÃO CLASSIFICADO: 311 clientes · 53,7%   │ │
│      cor = volume             │ └──────────────────────────────────────────┘ │
│                               │ Barras por região / UF (volume, clientes)    │
├───────────────────────────────┼──────────────────────────────────────────────┤
│ Confiança por UF (empilhada)  │ Tabela: clientes sem UF, por volume          │
└───────────────────────────────┴──────────────────────────────────────────────┘
```

### Página 4 — Produtos e famílias
```
┌─ Filtros de produto ─────────────────────────────────────────────────────────┐
├──────────────────────────────────────────────┬───────────────────────────────┤
│ TREEMAP Família › Subfamília › Produto       │ Barras por família            │
│ [cor: Risco | Nível IPE]                     │ volume · nº prod · estr · site│
├──────────────────────────────────────────────┴───────────────────────────────┤
│ Tabela de produtos (ABC, IPE, nível, dependência, flags)                     │
└──────────────────────────────────────────────────────────────────────────────┘
   → clique abre ▸ Painel do produto
```

### Página 5 — Concentração e riscos
```
┌──────────────┬──────────────┬──────────────┬─────────────────────────────────┐
│ Risco alto 87│ Médio 33     │ Baixo 17     │ Produtos com 1 cliente: 60      │
├──────────────┴──────────────┴──────────────┼─────────────────────────────────┤
│ Matriz Volume (log) × Dependência          │ Curva acumulada de clientes     │
│ quadrante crítico destacado                │                                 │
├────────────────────────────────────────────┼─────────────────────────────────┤
│ Matriz Dependência × Nº clientes           │ Tabela de alertas críticos      │
└────────────────────────────────────────────┴─────────────────────────────────┘
```

### Página 6 — Oportunidades
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ⓘ Listas "a investigar". Venda cruzada requer a base cliente × produto.      │
├──────────────────────────────────────┬───────────────────────────────────────┤
│ Clientes relevantes com 1 produto    │ Estratégicos: volume × nº clientes    │
│ (tabela)                             │ (dispersão, rótulos)                  │
├──────────────────────────────────────┼───────────────────────────────────────┤
│ Muitos clientes / baixo kg por cli.  │ Estratégicos sem cadastro/site        │
├──────────────────────────────────────┴───────────────────────────────────────┤
│ Alvos comerciais (100) — filtro por produto/aderência │ Funil CRM por status │
├──────────────────────────────────────────────────────────────────────────────┤
│ [🔒 Venda cruzada]  [🔒 Por responsável]  → "dado necessário: …"             │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Página 7 — Qualidade da base
```
┌─────────────────────┬────────────────────┬───────────────────────────────────┐
│ Reconciliação       │ Cobertura cadastral│ Completude por campo (barras %)   │
│ Cli 937,8 t         │ 3,1% qtd / 46% vol │ UF 3% · Segmento 0% · Porte 0% …  │
│ Prod 864,0 t  Δ7,9% │                    │                                   │
├─────────────────────┴────────────────────┴───────────────────────────────────┤
│ Possíveis duplicidades de clientes (44 grupos) → [validar]                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ Códigos parecidos · Conflitos de flags · Top clientes sem UF                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Insights atuais e alertas automáticos

### 13.1 Insights que a base já mostra
1. **Concentração alta em um nome:** os 6 registros com "VALGROUP" somam 39,2% do volume *(inferência — validar se é um único grupo econômico)*. Top 5 = 41,1%; top 10 = 53,1%.
2. **Portfólio concentrado:** `SL-L4265/02` sozinho responde por 31,8% do volume de produtos. Os 3 maiores somam 49,7%. Process Aid/PPA = 46,3%.
3. **Carteira "rasa":** 205 clientes (64%) compram 1 único produto, e 102 clientes compraram menos de 100 kg no período.
4. **Cauda de produtos frágil:** 60 produtos (44%) têm um único cliente. 87 estão na faixa de risco alto, mas somam só 12,2% do volume.
5. **O risco mais relevante está no meio:** a faixa média (40–70% de dependência) concentra 52,0% do volume, incluindo `SL-L4265/02` (48,6%) e `M9089/01` (49,9%).
6. **Estratégicos com base de clientes estreita:** `M9590`, `SL-L4224/01` e `M9593` dependem 100% (ou quase) de um cliente. `M9584`, `M9025` e `M9034N` passam de 80%.
7. **Geografia pouco confiável:** o que está localizado aponta Sudeste (38,7% do volume), mas 53,7% está sem UF, então **nenhuma conclusão regional é segura hoje**.
8. **Padrões de pedido:** alguns clientes compram com frequência e pouco (ex.: GRUD IND, 41 saídas a 66 kg/saída), enquanto outros fazem poucos pedidos grandes (ex.: VALGROUP MG, 14.850 kg/saída). Mediana: 138 kg/saída.
9. **Março foi o pico** (214,9 t) e **junho o vale** (81,8 t) em jan–jul/2026.

### 13.2 Regras de alerta (motor de alertas no backend)

| Código | Regra | Severidade | Hoje dispara? |
|--------|-------|------------|---------------|
| A01 | Cliente com share ≥ 10% | Alta | Sim (VALGROUP, VALGROUP BRASIL) |
| A02 | Top 5 ≥ 40% | Alta | Sim (41,1%) |
| A03 | Produto classe A/B com dependência ≥ 70% | Alta | Sim (12 produtos) |
| A04 | Produto estratégico com 1 cliente | Alta | Sim |
| A05 | Produto da lista estratégica sem flag/site/família | Média | Sim (3) |
| A06 | Cliente do top 50 sem UF | Média | Sim (41) |
| A07 | Divergência de totais > 1% | Alta | Sim (7,9%) |
| A08 | Grupo de nomes de cliente possivelmente duplicados | Média | Sim (44 grupos) |
| A09 | Campo obrigatório com completude < 50% | Média | Sim (Segmento, Porte, Responsável, UF) |
| A10 | Flags incoerentes (Especialidade × Tipo) | Baixa | Sim (7) |
| A11 | Mês com volume < média − 1 desvio-padrão | Informativo | Sim (junho) |

Cada alerta traz: **título-conclusão**, número, lista de itens e ação sugerida.

---

## 14. Plano de desenvolvimento — FastAPI + React

### Arquitetura
```
Excel (SAP) ──► FastAPI (pandas: carga, limpeza, cálculo, alertas) ──JSON──► React (Vite + ECharts)
                 ATLAS_back                                                  ATLAS_front
```
- **Backend:** Python 3.12, FastAPI, Uvicorn, pandas, openpyxl, pytest. Os dados são pequenos (321 + 137 linhas), então ficam em memória, com um endpoint para recarregar quando chegar uma planilha nova.
- **Frontend:** React + Vite (JavaScript), React Router (páginas), **Apache ECharts** via `echarts-for-react` (uma biblioteca só cobre barras, Pareto, treemap, dispersão e mapa do Brasil), CSS com variáveis de tema.

### Estrutura de pastas
```
ATLAS_back/
├── app/
│   ├── main.py              # cria o FastAPI, CORS, registra rotas
│   ├── config.py            # limites de negócio (risco, share, etc.)
│   ├── data/loader.py       # lê o Excel, limpa, padroniza, calcula colunas
│   ├── services/            # regras: kpis, clientes, produtos, geo, riscos, oportunidades, qualidade, alertas
│   ├── routers/             # 1 arquivo por página
│   └── schemas.py           # formatos de resposta (Pydantic)
├── data/Base_Aditive.xlsx   # NÃO versionar (.gitignore)
├── tests/                   # as validações da seção 1 viram testes automáticos
└── requirements.txt

ATLAS_front/
├── src/
│   ├── api/                 # funções que chamam o backend
│   ├── context/Filtros.jsx  # estado global dos filtros
│   ├── components/          # KpiCard, BarChart, Pareto, Treemap, Mapa, Tabela, PainelLateral, BarraFiltros
│   ├── pages/               # Executivo, Clientes, Geografia, Produtos, Riscos, Oportunidades, Qualidade
│   └── theme.css
└── package.json
```

### Endpoints (rascunho)
```
GET  /api/meta/filtros                 valores possíveis de cada filtro
GET  /api/executivo                    cartões + blocos da página 1
GET  /api/alertas
GET  /api/clientes                     ranking com share/acumulado (aceita filtros via query)
GET  /api/clientes/{id}                perfil
GET  /api/geografia?nivel=regiao|uf|cidade&regiao=&uf=
GET  /api/produtos                     tabela de produtos (filtros de produto)
GET  /api/produtos/{codigo}
GET  /api/familias                     hierarquia família › subfamília › produto
GET  /api/riscos
GET  /api/oportunidades
GET  /api/qualidade
GET  /api/mensal
POST /api/recarregar                   relê o Excel
```

### Passo a passo

| Fase | Entrega | Você aprende |
|------|---------|--------------|
| **0. Ambiente** | Python 3.12 + Node LTS instalados, `.gitignore` protegendo o Excel | terminal, venv, npm |
| **1. Backend "olá mundo"** | FastAPI rodando com `/api/saude` e a documentação automática em `/docs` | rotas, Uvicorn |
| **2. Carga e limpeza** | `loader.py` lê as abas-base e padroniza texto e booleanos | pandas |
| **3. Testes de validação** | As checagens deste diagnóstico viram testes `pytest` | testes automáticos |
| **4. API da página 1** | `/api/executivo` e `/api/alertas` | services × routers, Pydantic |
| **5. Frontend "olá mundo"** | Vite + React rodando e consumindo `/api/saude` | componentes, `fetch`, CORS |
| **6. Página 1 completa** | Cartões + 5 gráficos + alertas | ECharts, layout |
| **7. Filtros globais** | Barra de filtros + contexto + URL | estado global |
| **8. Páginas 2 a 7** | Uma por vez, com o mesmo padrão | reutilização de componentes |
| **9. Interatividade** | Filtro cruzado, drill-down, painéis, comparação | eventos de gráfico |
| **10. Identidade visual** | Cores e logo da Aditive, títulos-conclusão | design |
| **11. Publicação** | Depende do público (local, rede interna ou nuvem com login) | deploy |
| **12. Fase 2 de dados** | Entrada da `fato_vendas` e ativação de venda cruzada, período e responsável | modelagem |
