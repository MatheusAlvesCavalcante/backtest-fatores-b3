# Backtest de fatores na B3

Projeto em andamento: backtest de estratégias de fatores (momento 12-1 e baixa volatilidade) em ações da B3, com validação walk-forward, custos de transação e comparação com o Ibovespa e o CDI.

O objetivo é o método, não um número bonito: cada etapa documenta o que foi feito, como foi validado e quais são as limitações.

## Status

| Parte | Conteúdo | Situação |
|---|---|---|
| A | Dados e retornos | Concluída |
| B | Benchmark, CDI e métricas | Concluída |
| C | Universo de ações e liquidez | A fazer |
| D | Fatores (momento e baixa volatilidade) | A fazer |
| E | Carteira e backtest sem custos | A fazer |
| F | Custos de transação e giro | A fazer |
| G | Walk-forward e robustez | A fazer |
| H | Inferência estatística | A fazer |
| I | Gráficos, resultados finais e limitações | A fazer |

O diário completo, com decisões e validações de cada etapa, está em [`docs/diario.md`](docs/diario.md).

## Resultados até aqui: benchmark

Período de 05/01/2010 a 11/11/2026 (4.179 pregões). Ainda não há resultado de estratégia; estes números são a régua para comparar depois.

| Métrica | Ibovespa (preço) | CDI |
|---|---|---|
| Retorno anualizado | 5,57% | 9,97% |
| Volatilidade anual | 23,22% | 0,21% |
| Sharpe | -0,06 | não se aplica |
| Drawdown máximo | -48,63% | 0% |
| Retorno acumulado | 145,64% | 383,49% |

O Ibovespa usado é o índice de **preço** (não reinveste dividendos), então subestima o retorno de quem investe no índice.

## Como reproduzir

```bash
python -m venv .venv
.venv\Scripts\activate        # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python rodar_parte_ab.py
```

O script baixa os dados, salva cópias em `data/` (fora do Git), roda as validações e imprime as métricas. O fim do período está fixado em 11/11/2026 para os resultados serem reproduzíveis.

## Estrutura

```
backtest-fatores-b3/
├── src/
│   ├── dados.py       # download de preços e CDI, diagnóstico, retornos, calendário
│   └── metricas.py    # retorno, volatilidade, Sharpe, drawdown
├── docs/diario.md     # decisões, validações e registro de alterações
├── rodar_parte_ab.py  # executa as Partes A e B
├── checagens.py       # confere o alinhamento de calendários e o nível do Ibovespa
└── requirements.txt
```

## Decisões e validações até aqui

- **Preços ajustados** por proventos, desdobramentos e grupamentos (`Adj Close` do Yahoo Finance), escolhidos de forma explícita.
- **CDI** da série 12 do SGS do Banco Central, convertido de % ao dia para fração.
- **Retornos extremos:** todo retorno diário acima de ±20% é listado, nunca excluído automaticamente. Os 8 casos encontrados foram conferidos em fonte externa e são válidos (crise de março de 2020, Brumadinho, entre outros).
- **Calendário:** o Yahoo traz nas ações algumas linhas em feriados com a bolsa fechada. O calendário de pregão adotado é o do Ibovespa, e as datas fora dele são removidas e listadas a cada execução.

## Limitações conhecidas

- Fonte gratuita e não auditada (Yahoo Finance); ajustes de alguns proventos brasileiros, como JCP, podem não ser perfeitos.
- Ibovespa de preço, não de retorno total.
- A lista de ações atual (6 papéis) é apenas um teste do pipeline. O universo definitivo e o viés de sobrevivência serão tratados na Parte C.
