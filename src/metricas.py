"""Parte B: métricas de desempenho.

Todas as funções recebem uma Series de retornos SIMPLES periódicos
(diários por padrão, periodos=252). Para retornos mensais use periodos=12.
"""
import numpy as np
import pandas as pd


def retorno_acumulado(r):
    return (1 + r).prod() - 1


def retorno_anualizado(r, periodos=252):
    """Média geométrica anualizada: (1 + acumulado) ** (periodos / n) - 1."""
    r = r.dropna()
    return (1 + r).prod() ** (periodos / len(r)) - 1


def vol_anualizada(r, periodos=252):
    """Desvio padrão escalado pela raiz do tempo."""
    return r.dropna().std() * np.sqrt(periodos)


def sharpe(r, rf, periodos=252):
    """Sharpe = média do retorno em excesso / desvio do excesso * sqrt(periodos).

    rf: retorno da taxa livre de risco na MESMA periodicidade e alinhado em datas.
    """
    excesso = (r - rf).dropna()
    desvio = excesso.std()
    if desvio == 0 or np.isnan(desvio):
        return np.nan
    return excesso.mean() / desvio * np.sqrt(periodos)


def serie_drawdown(r):
    """Queda em relação ao pico anterior da curva de capital (valores <= 0)."""
    capital = (1 + r.dropna()).cumprod()
    pico = capital.cummax()
    return capital / pico - 1


def max_drawdown(r):
    return serie_drawdown(r).min()


def resumo(r, rf, periodos=252):
    """Tabela-resumo de uma série de retornos (alinha r e rf pelas datas)."""
    df = pd.concat([r.rename("r"), rf.rename("rf")], axis=1, join="inner").dropna()
    r, rf = df["r"], df["rf"]
    return pd.Series(
        {
            "retorno_anualizado": retorno_anualizado(r, periodos),
            "volatilidade_anual": vol_anualizada(r, periodos),
            "sharpe": sharpe(r, rf, periodos),
            "max_drawdown": max_drawdown(r),
            "n_periodos": len(r),
        }
    )
