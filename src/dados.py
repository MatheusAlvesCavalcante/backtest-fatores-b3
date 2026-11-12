"""Parte A: dados e retornos.

- baixar_precos: preços AJUSTADOS (dividendos, JCP, splits) via yfinance
- baixar_cdi: CDI diário (série 12 do SGS do Banco Central, em % ao dia)
- diagnostico: checagens de qualidade (buracos, retornos absurdos)
- retornos_*: simples, logarítmicos e mensais
"""
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yfinance as yf

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def baixar_precos(tickers, inicio="2010-01-01", fim=None):
    """Retorna DataFrame (datas x tickers) com o preço de fechamento AJUSTADO.

    auto_adjust=False para termos 'Close' e 'Adj Close' e escolher
    explicitamente o ajustado (o 'Close' puro ignora dividendos).
    """
    bruto = yf.download(
        tickers, start=inicio, end=fim, auto_adjust=False, progress=False
    )
    precos = bruto["Adj Close"]
    if isinstance(precos, pd.Series): 
        precos = precos.to_frame(tickers[0] if isinstance(tickers, list) else tickers)
    precos.index = pd.to_datetime(precos.index).tz_localize(None)
    return precos.sort_index()


def baixar_cdi(inicio="2010-01-01", fim=None):
    """CDI diário como fração (0.0004 = 0,04% ao dia).

    A API do BCB limita o tamanho da janela em séries diárias,
    então baixamos em blocos de 5 anos.
    """
    fim = pd.Timestamp(fim) if fim else pd.Timestamp.today().normalize()
    ini = pd.Timestamp(inicio)
    pedacos = []
    while ini <= fim:
        f = min(ini + pd.DateOffset(years=5) - pd.Timedelta(days=1), fim)
        url = (
            "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
            f"?formato=json&dataInicial={ini:%d/%m/%Y}&dataFinal={f:%d/%m/%Y}"
        )
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        pedacos.append(pd.DataFrame(r.json()))
        ini = f + pd.Timedelta(days=1)

    df = pd.concat(pedacos, ignore_index=True)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = df["valor"].astype(float) / 100  
    return (
        df.drop_duplicates("data").set_index("data")["valor"].sort_index().rename("cdi")
    )


def retornos_simples(precos):
    """r_t = P_t / P_{t-1} - 1. Os retornos simples COMPÕEM: (1+r1)(1+r2)... - 1."""
    return precos.pct_change(fill_method=None)


def retornos_log(precos):
    """ln(P_t / P_{t-1}). Os logs SOMAM no tempo."""
    return np.log(precos / precos.shift(1))


def retornos_mensais(precos):
    """Retorno mensal a partir do último preço ajustado de cada mês."""
    return precos.resample("ME").last().pct_change(fill_method=None)


def diagnostico(precos, limite=0.20):
    """Resumo de qualidade por ativo. Olhe com atenção a coluna n_extremos:
    retornos diários > 20% em ações líquidas costumam ser erro de ajuste."""
    ret = retornos_simples(precos)
    return pd.DataFrame(
        {
            "primeiro_dado": precos.apply(lambda s: s.first_valid_index()),
            "ultimo_dado": precos.apply(lambda s: s.last_valid_index()),
            "n_obs": precos.count(),
            "pct_faltante": precos.isna().mean().round(4),
            "retorno_max": ret.max().round(4),
            "retorno_min": ret.min().round(4),
            "n_extremos": (ret.abs() > limite).sum(),
        }
    )


def listar_extremos(precos, limite=0.20):
    """Lista cada dia em que o retorno diário passou de ±limite. NÃO exclui nada.
 
    Colunas:
    - preco_anterior / preco: o salto de preço que gerou o retorno
    - retorno: a variação do dia
    - retorno_dia_seguinte: se for aproximadamente o oposto do retorno, o preço
      subiu e voltou (típico de glitch nos dados); se continuar na mesma
      direção, pode ser um evento real ou um erro de ajuste de split.
    """
    ret = retornos_simples(precos)
    seguinte = ret.shift(-1)
    registros = []
    for ticker in precos.columns:
        for data in ret.index[ret[ticker].abs() > limite]:
            pos = precos.index.get_loc(data)
            registros.append(
                {
                    "ticker": ticker,
                    "data": data,
                    "preco_anterior": precos[ticker].iloc[pos - 1],
                    "preco": precos[ticker].iloc[pos],
                    "retorno": ret.loc[data, ticker],
                    "retorno_dia_seguinte": seguinte.loc[data, ticker],
                }
            )
    colunas = ["ticker", "data", "preco_anterior", "preco", "retorno", "retorno_dia_seguinte"]
    return pd.DataFrame(registros, columns=colunas).sort_values(["ticker", "data"]).reset_index(drop=True)


def alinhar_calendario(precos, calendario):
    """Mantém só as datas que existem no calendário de referência.
 
    Usamos as datas do Ibovespa como calendário oficial de pregão: o Yahoo traz
    nas ações algumas linhas em feriados em que a B3 esteve fechada. Nada é
    alterado nos preços; apenas as datas fora do calendário são removidas, e a
    lista removida é impressa para ficar registrada.
    """
    removidas = precos.index.difference(calendario)
    if len(removidas) > 0:
        datas = [d.strftime("%d/%m/%Y") for d in removidas]
        print(f"Removidas {len(removidas)} data(s) fora do calendário de pregão: {datas}")
    return precos.loc[precos.index.isin(calendario)]