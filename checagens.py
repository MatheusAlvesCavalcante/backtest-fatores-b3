import pandas as pd

ibov = pd.read_parquet("data/ibov.parquet")["ibov"]
acoes = pd.read_parquet("data/acoes_teste.parquet")
cdi = pd.read_parquet("data/cdi.parquet")["cdi"]

print("Ibovespa sem CDI:", list(ibov.index.difference(cdi.index)))
print("Nas ações e não no Ibovespa:", list(acoes.index.difference(ibov.index)))
print("No Ibovespa e não nas ações:", list(ibov.index.difference(acoes.index)))
print("Ibov primeiro, penúltimo e razão:", ibov.iloc[0], ibov.iloc[-2], ibov.iloc[-2] / ibov.iloc[0])