"""Roda as Partes A e B: baixa dados, diagnostica e calcula métricas de
Ibovespa e CDI. Execute da raiz do projeto:  python rodar_parte_ab.py
"""
import pandas as pd

from src import dados, metricas

INICIO = "2010-01-01"
# Lista pequena só para testar o pipeline. O universo de verdade vem na Parte C.
TICKERS_TESTE = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "WEGE3.SA"]

# ---------- Parte A: dados e retornos ----------
print("Baixando Ibovespa e ações de teste...")
ibov = dados.baixar_precos(["^BVSP"], inicio=INICIO)["^BVSP"].dropna()
acoes = dados.baixar_precos(TICKERS_TESTE, inicio=INICIO)

print("Baixando CDI no Banco Central...")
cdi = dados.baixar_cdi(inicio=INICIO)

ibov.to_frame("ibov").to_parquet(dados.DATA_DIR / "ibov.parquet")
acoes.to_parquet(dados.DATA_DIR / "acoes_teste.parquet")
cdi.to_frame().to_parquet(dados.DATA_DIR / "cdi.parquet")

print("\n=== Diagnóstico das ações de teste ===")
print(dados.diagnostico(acoes).to_string())

extremos = dados.listar_extremos(acoes, limite=0.20)
if extremos.empty:
    print("\nNenhum retorno diário acima de 20% encontrado.")
else:
    print(f"\n=== ATENÇÃO: {len(extremos)} retorno(s) diário(s) acima de 20% (nada foi excluído) ===")
    print(extremos.round({"preco_anterior": 2, "preco": 2, "retorno": 4, "retorno_dia_seguinte": 4}).to_string())
    print("Confira cada data em outra fonte antes de decidir o que fazer.")

r_ibov = dados.retornos_simples(ibov).dropna()
r_ibov.name = "ibov"

# ---------- Parte B: métricas ----------
rf = cdi.reindex(r_ibov.index)
faltando = rf.isna().sum()
print(f"\nDatas do Ibovespa sem CDI correspondente: {faltando}")

# Período em que Ibovespa E CDI existem ao mesmo tempo (base de todas as métricas abaixo)
comum = rf.dropna().index
print(f"Período analisado: {comum.min():%d/%m/%Y} a {comum.max():%d/%m/%Y} ({len(comum)} pregões)")

tabela = pd.DataFrame(
    {
        "Ibovespa (preço)": metricas.resumo(r_ibov, rf),
        "CDI": metricas.resumo(rf.dropna(), pd.Series(0.0, index=rf.dropna().index)),
    }
)
tabela.loc["sharpe", "CDI"] = float("nan")  # Sharpe do CDI contra ele mesmo não faz sentido
print("\n=== Métricas, período completo (Sharpe do CDI não se aplica) ===")
print(tabela.round(4).to_string())

# Os dois acumulados sobre as MESMAS datas, para a comparação ser justa
print("\nCDI acumulado no período:", round(metricas.retorno_acumulado(rf.loc[comum]), 4))
print("Ibovespa acumulado (preço):", round(metricas.retorno_acumulado(r_ibov.loc[comum]), 4))