# Backtest de fatores na B3: diário e documentação do projeto

Matheus Alves Cavalcante · Início: 12/11/2026 · Documento vivo, atualizado a cada mudança relevante no código ou nas decisões

## 1. Objetivo

Construir um backtest de estratégias de fatores (momento 12-1 e baixa volatilidade) em ações da B3, com validação walk-forward, custos de transação, comparação com o Ibovespa e limitações documentadas. Este documento registra **o que foi feito, como e por quê**, incluindo as checagens e as decisões que não estavam no plano original.

## 2. Estrutura do projeto

- `src/dados.py`: download de preços e CDI, diagnóstico de qualidade, cálculo de retornos.
- `src/metricas.py`: retorno anualizado, volatilidade, Sharpe, drawdown.
- `rodar_parte_ab.py`: executa as Partes A e B e imprime os resultados.
- `data/`: cópias locais dos dados baixados (fora do Git, reproduzíveis pelo script).

## 3. Parte A: dados e retornos

**Fontes e decisões**

- **Preços:** Yahoo Finance via biblioteca `yfinance` (não oficial, gratuita, não auditada). Usamos a coluna `Adj Close`, que ajusta desdobramentos, grupamentos e dividendos. Escolha explícita com `auto_adjust=False` para não depender do comportamento padrão da biblioteca.
- **Ibovespa:** ticker `^BVSP`. É índice de **preço**, não de retorno total (não reinveste dividendos), então subestima o retorno de quem investe no índice. Tratado como limitação.
- **CDI:** série 12 do SGS do Banco Central (CDI diário, em % ao dia). Convertido para fração dividindo por 100. Baixado em blocos de 5 anos por limite da API.
- **Retornos:** simples (compõem no tempo), logarítmicos (somam) e mensais (último preço ajustado de cada mês).

**Pipeline em cinco etapas:** obter, guardar localmente, validar, transformar, consumir. Erros nas primeiras etapas contaminam as seguintes, por isso a validação vem antes de qualquer métrica.

## 4. Validação dos dados

O plano original previa apenas contar retornos extremos. Durante a execução surgiu a ideia de **listar cada ocorrência** para poder investigar, e isso virou a função `listar_extremos` (limite de ±20% em um dia, sem excluir nada automaticamente).

**Procedimento adotado:** para cada retorno diário acima de 20% encontrado, conferir a data em fonte independente (eventos corporativos da empresa, histórico de cotações) e verificar se o preço permaneceu no novo patamar (possível split não ajustado) ou voltou no dia seguinte (possível erro pontual).

**Resultado:** todos os casos encontrados nas ações de teste foram conferidos e confirmados como dados válidos. Nenhuma correção foi necessária.

| Ticker | Data | Retorno | Fonte conferida | Conclusão |
| --- | --- | --- | --- | --- |
| BBDC4 | 2026-10-26 | -0.2170 | B3 e Google Finance | Queda de 21,7% confirmada nas fontes consultadas. Causa não confirmada por fonte independente. |
| PETR4 | 2020-03-09 | -0.2970 | B3 e Google Finance | No dia **9 de março de 2020** (conhecido mundialmente como a *"Segunda-Feira Negra"*), as ações preferenciais da Petrobras (BVMF: PETR4) desabaram exatamente **-29,70%** (fechando a R$ 16,05). Essa foi a **maior queda percentual diária da história da companhia** até então. O colapso histórico foi provocado por uma combinação de dois fatores globais de pânico: **Guerra de Preços do Petróleo e Pandemia de COVID-19** |
| PETR4 | 2020-03-12 | -0.2050 | B3 e Google Finance | O mercado global entrou em colapso total após a Organização Mundial da Saúde (OMS) decretar oficialmente a pandemia no dia anterior e o governo dos EUA suspender voos vindos da Europa. A Bolsa brasileira (B3) sofreu tamanha pressão de venda que o mecanismo de *Circuit Breaker* (interrupção de negociações) foi acionado **duas vezes no mesmo dia**. As ações da Petrobras fecharam com queda massiva de 20,50%. |
| PETR4 | 2020-03-13 | 0.2222 | B3 e Google Finance | No dia seguinte, após o tombo histórico e o derretimento generalizado dos preços, ocorreu o que o mercado chama de *short squeeze* ou repique técnico exagerado. Os investidores aproveitaram os preços severamente depreciados para comprar e os mercados globais reagiram a pacotes de estímulos financeiros bilionários injetados por Bancos Centrais (como o Federal Reserve dos EUA). Com isso, a PETR4 registrou uma alta histórica de recuperação de 22,22% em uma única sessão. |
| PETR4 | 2021-02-22 | -0.2071 | B3 e Google Finance | O colapso original começou após o fechamento do mercado na sexta-feira (19/02), quando foi anunciada a intervenção do governo na troca de comando da estatal, fazendo com que o mercado abrisse em forte gap de baixa e desabasse na segunda-feira, dia 22. |
| VALE3 | 2019-01-28 | -0.2456 | B3 e Google Finance | No dia **28 de janeiro de 2019** (uma segunda-feira), as ações ordinárias da Vale SA (BVMF: VALE3) despencaram exatamente **-24,56%** (fechando o pregão a R$ 42,38). Esta foi a maior queda percentual diária da história da empresa em termos de perda de valor de mercado até então.<br>A desvalorização histórica ocorreu no **primeiro dia de negociações da Bolsa de Valores após o rompimento da barragem de rejeitos da Mina do Córrego do Feijão, em Brumadinho (MG)**, ocorrido na tarde da sexta-feira anterior, 25 de janeiro de 2019.<br>O mercado financeiro reagiu em pânico generalizado com a tragédia humana e ambiental, precificando os pesados riscos operacionais e financeiros imediatos enfrentados pela mineradora:<br>• **Perda de Valor:** A Vale perdeu **R$ 71,3 bilhões** em valor de mercado em uma única sessão.<br>• **Bloqueios e Multas:** O pregão abriu sob o peso de decisões judiciais que já haviam bloqueado mais de R$ 11 bilhões das contas da empresa para garantir indenizações e reparações, além da aplicação de multas milionárias pelo Ibama e pelo governo de Minas Gerais.<br>• **Suspensão de Proventos:** Logo no domingo (27/01), o Conselho de Administração da Vale suspendeu o pagamento de dividendos, juros sobre o capital próprio (JCP) e bônus de executivos, o que acelerou a forte pressão vendedora por parte de fundos de investimento institucionais e estrangeiros. |
| VALE3 | 2020-03-13 | 0.2136 | B3 e Google Finance | No dia **13 de março de 2020** (uma sexta-feira), as ações ordinárias da Vale SA (BVMF:VALE3) dispararam exatamente **+21,36%**, fechando o pregão cotadas a R$ 43,45.<br>Esse movimento foi uma forte **recuperação técnica (repique de mercado)** após o pânico extremo vivenciado no dia anterior. Em 12 de março de 2020, o Ibovespa havia desabado quase 15% e acionado dois *Circuit Breakers* devido à decretação oficial da pandemia de COVID-19 pela OMS. |
| WEGE3 | 2020-03-16 | -0.2062 | B3 e Google Finance | No dia **16 de março de 2020** (uma segunda-feira), as ações ordinárias da WEG SA (BVMF:WEGE3) desabaram exatamente **-20,62%**, fechando o pregão cotadas a R$ 13,83 (valor ajustado por desdobramentos posteriores).<br>Essa queda histórica fez parte do pânico global generalizado nos mercados financeiros provocado pelo avanço acelerado da pandemia de COVID-19. Naquele dia específico, o desespero tomou conta dos investidores mesmo após o Federal Reserve (o Banco Central dos EUA) ter cortado os juros americanos para zero e anunciado um programa massivo de estímulo de US$ 700 bilhões no domingo à noite.<br>O mercado interpretou a ação emergencial do Fed como um sinal de que a crise econômica global seria muito mais profunda do que o antecipado. Como resultado, o Ibovespa desabou 13,92% no dia e acionou o mecanismo de *Circuit Breaker* (interrupção temporária das negociações) logo nos primeiros trinta minutos de pregão. As ações da WEG, consideradas de alta qualidade e que vinham apresentando forte valorização, sofreram com uma onda severa de realização de lucros e liquidação forçada por parte de fundos de investimento que precisavam gerar caixa imediato. |

*Observação: a conferência vale para a lista de teste atual. Quando o universo completo for definido (Parte C), o procedimento deve ser repetido.*

## 5. Parte B: métricas e como ler a saída do script

**Métricas implementadas:** retorno anualizado (média geométrica), volatilidade anualizada (desvio padrão × √252), Sharpe sobre o excesso em relação ao CDI e drawdown máximo.

**Como ler a saída**

- **"Datas do Ibovespa sem CDI correspondente":** o script pega cada dia em que o Ibovespa teve retorno e procura o CDI do mesmo dia. Esse número é quantos dias do Ibovespa ficaram sem CDI. O esperado é zero ou muito perto disso. Importa porque o Sharpe subtrai o CDI do retorno **do mesmo dia**; se as datas não casam, a conta fica errada ou dias são descartados sem aviso.
- **"Período analisado":** o intervalo em que Ibovespa e CDI existem ao mesmo tempo, do primeiro ao último pregão com os dois dados. O download começa em 01/01/2010, então o primeiro pregão é o primeiro de janeiro de 2010 com dado.
- **"Métricas, período completo":** todas as métricas calculadas sobre esse intervalo inteiro, sem dividir em partes. "Completo" contrasta com as análises por sub-período que virão na Parte G (por exemplo, antes e depois de 2020).
- **"CDI acumulado no período" e "Ibovespa acumulado":** quanto cada um rendeu do início ao fim do período analisado (por exemplo, 2,0 significa +200%). Ambos são calculados sobre as mesmas datas, para a comparação ser justa.
- **Sharpe do CDI:** não se aplica (o CDI não tem risco a ser remunerado acima dele mesmo), por isso aparece vazio na tabela.

**Conferências a fazer:** comparar o CDI acumulado com a Calculadora do Cidadão do Banco Central e o Ibovespa acumulado com o gráfico do índice em outra fonte. Se bater, a conversão de unidades e o alinhamento de datas estão corretos. Resultados reais: \[preencher após rodar\].

## 6. Limitações conhecidas até aqui

- Fonte gratuita e não auditada (Yahoo Finance); ajustes de proventos brasileiros, como JCP, podem não ser perfeitos.
- Ibovespa de preço, não de retorno total.
- Lista de ações da Parte A é só um teste; o universo e o viés de sobrevivência serão tratados na Parte C.

## 7. Registro de alterações

| Data | Alteração | Motivo |
| --- | --- | --- |
| 12/11/2026 | Criação das Partes A e B (`dados.py`, `metricas.py`, script) | Início do projeto |
| 12/11/2026 | Adicionada `listar_extremos` e chamada no script | Ideia de investigar cada retorno acima de 20% em vez de só contá-los |
| 12/11/2026 | Dados extremos conferidos manualmente: todos válidos | Validação antes de usar os dados |
| 12/11/2026 | Script passou a imprimir o período analisado, calcular os acumulados sobre as mesmas datas e omitir o Sharpe do CDI | Deixar claro o período usado e evitar comparação com datas diferentes e um número sem sentido |

## 8. Próximos passos

- Rodar o script completo e preencher os resultados reais acima.
- Estudar e iniciar a **Parte C**: universo de ações, liquidez e viés de sobrevivência.

## 9. Resultados da primeira execução (12/11/2026)

**Dados baixados:** 6 ações de teste (ABEV3, BBDC4, ITUB4, PETR4, VALE3, WEGE3), Ibovespa e CDI, de 04/01/2010 a 12/11/2026. Cada ação tem 4.190 observações e 0% de dados faltantes.

**Validação de extremos:** 8 retornos diários acima de 20% (BBDC4: 1, PETR4: 4, VALE3: 2, WEGE3: 1), todos conferidos em fonte externa. Os preços impressos pelo script são **ajustados** por proventos e desdobramentos, então os níveis diferem dos preços históricos publicados (exemplo: PETR4 em 09/03/2020 aparece de 6,16 para 4,33 no script). A comparação com a fonte externa deve ser feita pelo **retorno percentual**, que independe do ajuste, e não pelo nível do preço.

**Métricas de 05/01/2010 a 11/11/2026 (4.179 pregões):**

| Métrica | Ibovespa (preço) | CDI |
| --- | --- | --- |
| Retorno anualizado | 5,57% | 9,97% |
| Volatilidade anual | 23,22% | 0,21% |
| Sharpe | -0,06 | não se aplica |
| Drawdown máximo | -48,63% | 0% |
| Retorno acumulado | 145,64% | 383,49% |

**Leitura:** no período, o Ibovespa de preço rendeu menos que o CDI e teve Sharpe ligeiramente negativo. Como o índice de preço não inclui dividendos, o retorno total do Ibovespa seria maior, e esse efeito não foi medido aqui (limitação registrada). A barra para qualquer estratégia de ações é alta: precisa superar um CDI médio de cerca de 10% ao ano.

**Pendências de conferência:**

- Uma data do Ibovespa ficou sem CDI. Hipótese: é 12/11/2026, dia da execução, em que o Banco Central ainda não havia publicado o CDI. A confirmar. O último dia baixado pode ainda ser parcial (preço do pregão em andamento), então não deve entrar nas análises seguintes.
- As ações têm 4.190 datas e o Ibovespa cerca de 4.181. Comparar os calendários para entender a diferença antes da Parte C.
- Conferir o CDI acumulado na Calculadora do Cidadão do Banco Central e o nível do Ibovespa no início e no fim do período em fonte externa.

**Registro:** 12/11/2026, primeira execução completa das Partes A e B; resultados registrados nesta seção.

## 10. Resolução das pendências de conferência (12/11/2026)

**Calendários desalinhados.** O script `checagens.py` mostrou que as ações tinham 9 datas que o Ibovespa não tem: 02/01/2012, 15/06/2017, 07/09/2017, 12/10/2017, 02/11/2017, 15/11/2017, 20/11/2017, 25/12/2017 e 25/01/2018. Nenhuma data do Ibovespa estava ausente nas ações, ou seja, o calendário do Ibovespa está contido no das ações. Quase todas as datas são feriados brasileiros, o que indica linhas extras do Yahoo em dias sem pregão. As datas de 02/01/2012 e 20/11/2017 devem ser confirmadas no calendário de feriados da B3.

**Decisão:** usar as datas do Ibovespa como calendário oficial de pregão e remover das ações as datas que não estão nele (função `alinhar_calendario`). Nenhum preço é alterado, e a lista de datas removidas é impressa a cada execução.

**Data sem CDI:** confirmada como 12/11/2026, dia da execução, em que o CDI ainda não estava publicado. Decisão: congelar o fim do período em 11/11/2026 (`FIM` no script), o que também evita usar o preço parcial do dia em andamento e deixa os resultados reproduzíveis.

**Nível do Ibovespa:** primeiro fechamento 70.045 e fechamento de 11/11/2026 em 172.060; a razão é 2,4564, igual ao acumulado do script. Conferência do CDI na Calculadora do Cidadão: pendente.

**Registro:** 12/11/2026, adicionada `alinhar_calendario`, fim do período fixado em 11/11/2026; as métricas do Ibovespa e do CDI não mudam, pois ambas já usavam o período até 11/11.
