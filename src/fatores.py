"""Parte D: sinais dos fatores e ranking em quintis.

Os sinais da data t usam só preços até t:
- momento 12-1: P[t-21] / P[t-252] - 1 (pula o último mês)
- volatilidade: desvio padrão dos retornos diários dos últimos 252 pregões

Sobre o Adj Close: o Yahoo reescreve o passado com dividendos futuros, mas por
um fator multiplicativo que é o mesmo para todas as datas anteriores ao
provento. Razões entre preços passados (retornos) não mudam, então não há
vazamento por causa do ajuste.

Os sinais são calculados no calendário de pregões do Ibovespa (adj_close já
alinhado), para que "252 linhas" sejam ~12 meses.
"""
import numpy as np
import pandas as pd


def momento_12_1(adj_close, saltar=21, janela=252):
    """Retorno de `janela` pregões atrás até `saltar` pregões atrás."""
    return adj_close.shift(saltar) / adj_close.shift(janela) - 1


def volatilidade(adj_close, janela=252, cobertura=0.9):
    """Desvio padrão diário dos retornos nos últimos `janela` pregões (não anualizado)."""
    ret = adj_close.pct_change(fill_method=None)
    return ret.rolling(janela, min_periods=int(cobertura * janela)).std()


def calcular_sinais(
    adj_close, datas, saltar=21, janela_momento=252, janela_vol=252
):
    """Calcula os dois sinais em todas as datas e devolve só as datas de rebalanceamento."""
    return {
        "momento": momento_12_1(adj_close, saltar, janela_momento).loc[datas],
        "vol": volatilidade(adj_close, janela_vol).loc[datas],
    }


def quintis(sinal, elegivel, maior_melhor=True, n_grupos=5, min_acoes=25):
    """Divide as ações elegíveis em `n_grupos` por data. Grupo 1 = o melhor.

    maior_melhor=True  -> maior valor do sinal é melhor (momento)
    maior_melhor=False -> menor valor é melhor (volatilidade)
    Datas com menos de `min_acoes` ações com sinal válido ficam sem grupo (NaN).
    """
    base = sinal.where(elegivel)
    pct = base.rank(axis=1, ascending=not maior_melhor, pct=True, method="first")
    grupos = np.ceil(pct * n_grupos)
    validas = base.notna().sum(axis=1)
    grupos.loc[validas < min_acoes] = np.nan
    return grupos


def correlacao_media(sinal_a, sinal_b, elegivel):
    """Correlação de postos (Spearman) entre dois sinais, data a data."""
    ra = sinal_a.where(elegivel).rank(axis=1)
    rb = sinal_b.where(elegivel).rank(axis=1)
    return ra.corrwith(rb, axis=1)


def extremos_sinal(sinal, elegivel, n=5):
    """Os n menores e n maiores valores do sinal entre ações elegíveis (para inspeção)."""
    serie = sinal.where(elegivel).unstack().dropna().sort_values()
    return pd.concat([serie.head(n), serie.tail(n)])
