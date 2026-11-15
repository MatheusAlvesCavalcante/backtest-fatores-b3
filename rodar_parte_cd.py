"""Roda as Partes C e D: universo de ações elegíveis e sinais dos fatores.

Pré-requisito: config/tickers_candidatos.csv, com a composição de um índice
amplo (Ibovespa ou IBrX 100) baixada do site da B3.
Execute da raiz do projeto:  python rodar_parte_cd.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src import config, dados, fatores, universo

RAIZ = Path(__file__).resolve().parent
CSV_CANDIDATOS = RAIZ / "config" / "tickers_candidatos.csv"
CSV_EMPRESAS = RAIZ / "config" / "empresas.csv"
DOCS = RAIZ / "docs"
DOCS.mkdir(exist_ok=True)

# =============================== PARTE C ===============================
if not CSV_CANDIDATOS.exists():
    raise SystemExit(
        "Falta config/tickers_candidatos.csv. Baixe a composição do Ibovespa ou do "
        "IBrX 100 no site da B3 e salve nesse caminho."
    )
candidatos = universo.ler_candidatos(CSV_CANDIDATOS)
print(f"{len(candidatos)} tickers candidatos")

print("Baixando preços e volumes (pode levar alguns minutos)...")
bruto = dados.baixar_ohlcv(
    [t + ".SA" for t in candidatos], inicio=config.INICIO, fim=config.FIM_YF
)
ibov = dados.baixar_precos(["^BVSP"], inicio=config.INICIO, fim=config.FIM_YF)["^BVSP"].dropna()

# Calendário de pregão = datas do Ibovespa (mesma regra das Partes A e B)
adj = dados.alinhar_calendario(bruto["adj_close"], ibov.index)
close = bruto["close"].loc[adj.index]
volume = bruto["volume"].loc[adj.index]
for tabela in (adj, close, volume):
    tabela.columns = [c.replace(".SA", "") for c in tabela.columns]

sem_dado = list(adj.columns[adj.notna().sum() == 0])
if sem_dado:
    print("Sem nenhum dado no Yahoo (removidos):", sem_dado)
    adj, close, volume = (t.drop(columns=sem_dado) for t in (adj, close, volume))

adj.to_parquet(dados.DATA_DIR / "adj_close.parquet")
close.to_parquet(dados.DATA_DIR / "close.parquet")
volume.to_parquet(dados.DATA_DIR / "volume.parquet")

# ---- mapa ticker -> empresa (revisar a mão) ----
if not CSV_EMPRESAS.exists():
    universo.rascunho_mapa(list(adj.columns)).to_csv(CSV_EMPRESAS, index=False)
    print(f"\nCriado rascunho de {CSV_EMPRESAS.relative_to(RAIZ)}. REVISE: agrupa pelas 4 "
          "primeiras letras e pode errar em casos especiais.")
mapa = universo.carregar_mapa(CSV_EMPRESAS)
mapa = mapa[mapa.index.isin(adj.columns)]
multi = mapa.groupby(mapa).filter(lambda s: len(s) > 1)
print(f"\nEmpresas com mais de uma classe nas candidatas: {multi.nunique()}")
print(multi.reset_index().groupby("empresa")["ticker"].apply(" ".join).to_string())

# ---- universo ----
vol_fin = universo.volume_financeiro(close, volume)
liq = universo.liquidez(vol_fin, config.JANELA_LIQUIDEZ, config.ESTATISTICA_LIQUIDEZ)
regras = universo.regras_elegibilidade(
    adj, liq, config.CORTE_LIQUIDEZ,
    config.HISTORICO_MIN, config.JANELA_COBERTURA, config.COBERTURA_MIN,
)
datas = universo.datas_rebalanceamento(adj.index)
elig_acao = regras["elegivel"].loc[datas]
elig_rep = universo.escolher_representantes(elig_acao, liq.loc[datas], mapa)

n_acoes = elig_acao.sum(axis=1)
n_empresas = elig_rep.sum(axis=1)
print("\n=== Universo no último rebalanceamento de cada ano ===")
print(pd.DataFrame({"acoes_elegiveis": n_acoes, "empresas_elegiveis": n_empresas})
      .groupby(lambda d: d.year).last().to_string())

ultima = datas[-1]
print(f"\n=== Regras em {ultima:%d/%m/%Y}: quantas ações passam em cada uma ===")
for nome in ("historico", "cobertura", "liquidez", "elegivel"):
    print(f"{nome:10s}: {int(regras[nome].loc[ultima].sum())} de {adj.shape[1]}")

resumo = universo.resumo_empresas(mapa, elig_acao, elig_rep)
resumo.to_csv(dados.DATA_DIR / "resumo_empresas.csv", index=False)
print("\n=== Empresas com mais de uma classe ===")
print(resumo[resumo["n_classes"] > 1].to_string(index=False))

fig, ax = plt.subplots(figsize=(9, 4))
n_empresas.plot(ax=ax, label="empresas elegíveis (1 classe cada)")
n_acoes.plot(ax=ax, label="ações elegíveis (todas as classes)", alpha=0.6)
ax.axhline(config.MIN_ACOES, color="gray", linestyle="--", linewidth=1,
           label=f"mínimo para quintis ({config.MIN_ACOES})")
ax.set_title("Tamanho do universo por mês")
ax.legend()
fig.tight_layout()
fig.savefig(DOCS / "universo_por_mes.png", dpi=130)
print("\nGráfico salvo em docs/universo_por_mes.png")

# =============================== PARTE D ===============================
sinais = fatores.calcular_sinais(
    adj, datas, config.SALTO_MOMENTO, config.JANELA_MOMENTO, config.JANELA_VOL
)
q_mom = fatores.quintis(sinais["momento"], elig_rep, True, config.N_QUANTIS, config.MIN_ACOES)
q_vol = fatores.quintis(sinais["vol"], elig_rep, False, config.N_QUANTIS, config.MIN_ACOES)

validas = q_mom.notna().any(axis=1) & q_vol.notna().any(axis=1)
print("\n=== Sinais ===")
print(f"Datas de rebalanceamento: {len(datas)}; com quintis válidos: {int(validas.sum())}")
if validas.any():
    print(f"Primeira data com quintis: {validas.idxmax():%d/%m/%Y}")
    print("Ações por quintil na última data (momento):")
    print(q_mom.loc[ultima].value_counts().sort_index().to_string())
    corr = fatores.correlacao_media(sinais["momento"], sinais["vol"], elig_rep)
    print(f"Correlação de postos média entre momento e volatilidade: {corr.mean():.2f}")

print("\nMaiores e menores valores do MOMENTO (confira se algum é absurdo):")
print(fatores.extremos_sinal(sinais["momento"], elig_rep).round(3).to_string())
print("\nMaiores e menores valores da VOLATILIDADE DIÁRIA:")
print(fatores.extremos_sinal(sinais["vol"], elig_rep).round(4).to_string())

todos_extremos = dados.listar_extremos(adj, limite=0.20)
todos_extremos.to_csv(dados.DATA_DIR / "extremos_universo.csv", index=False)
print(f"\nRetornos diários acima de ±20% nas candidatas: {len(todos_extremos)} "
      "(lista completa em data/extremos_universo.csv; confira os suspeitos)")

pd.concat({"momento": q_mom, "vol": q_vol}, axis=1).to_parquet(dados.DATA_DIR / "quintis.parquet")
elig_rep.to_parquet(dados.DATA_DIR / "universo_representantes.parquet")
sinais["momento"].to_parquet(dados.DATA_DIR / "sinal_momento.parquet")
sinais["vol"].to_parquet(dados.DATA_DIR / "sinal_vol.parquet")
print("\nPartes C e D concluídas. Rode também:  python -m pytest -v")
