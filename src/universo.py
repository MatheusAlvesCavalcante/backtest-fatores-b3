"""Parte C: universo de ações elegíveis em cada data.

Tudo aqui usa APENAS informação disponível até a data avaliada (janelas
retrospectivas), para não vazar o futuro para o universo.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

PADRAO_TICKER = re.compile(r"^[A-Z]{4}\d{1,2}$")  # ex.: PETR4, SANB11


# ---------------------------------------------------------------- candidatas
def ler_candidatos(caminho):
    """Lê o CSV da composição do índice (baixado do site da B3) e devolve os tickers.

    Pega o primeiro campo de cada linha e mantém só o que tem formato de ticker
    (ABCD3, ABCD11). Isso descarta cabeçalhos e rodapés do arquivo da B3 e
    funciona com separador ';', ',' ou tabulação, em utf-8 ou latin-1.
    """
    texto = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            texto = Path(caminho).read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    tickers = []
    for linha in texto.splitlines():
        campo = re.split(r"[;,\t]", linha.strip(), maxsplit=1)[0].strip().strip('"').upper()
        if PADRAO_TICKER.match(campo) and campo not in tickers:
            tickers.append(campo)
    if not tickers:
        raise ValueError(f"Nenhum ticker encontrado em {caminho}")
    return tickers


def rascunho_mapa(tickers):
    """Rascunho do mapa ticker -> empresa, agrupando pelas 4 primeiras letras.

    É só um ponto de partida: revise a mão (units como SANB11 agrupam com
    SANB3/SANB4; empresas diferentes com prefixo parecido devem ser separadas).
    """
    return (
        pd.DataFrame({"empresa": [t[:4] for t in tickers], "ticker": tickers})
        .sort_values(["empresa", "ticker"])
        .reset_index(drop=True)
    )


def carregar_mapa(caminho):
    """Série indexada por ticker com o nome da empresa."""
    df = pd.read_csv(caminho, dtype=str)
    if df["ticker"].duplicated().any():
        raise ValueError("Ticker repetido em empresas.csv")
    return df.set_index("ticker")["empresa"]


# ----------------------------------------------------------------- liquidez
def volume_financeiro(close, volume):
    """Volume em reais = fechamento (sem ajuste de dividendos) x quantidade."""
    return close * volume


def liquidez(vol_fin, janela=126, estatistica="mediana"):
    """Liquidez retrospectiva: mediana (padrão) ou média do volume financeiro.

    A mediana resiste a dias de volume anormal. A média com janela curta é o
    ADTV; ADTV 30/60 serão comparados na Parte G. A data t entra na janela.
    """
    minimo = int(0.8 * janela)
    janela_rolante = vol_fin.rolling(janela, min_periods=minimo)
    if estatistica == "mediana":
        return janela_rolante.median()
    if estatistica == "media":
        return janela_rolante.mean()
    raise ValueError("estatistica deve ser 'mediana' ou 'media'")


# ------------------------------------------------------------- elegibilidade
def regras_elegibilidade(
    adj_close, liq, corte, historico_min=253, janela_cobertura=252, cobertura_min=0.95
):
    """Aplica as três regras em todas as datas. Devolve um dict de DataFrames booleanos.

    historico: tem pelo menos `historico_min` pregões com preço até a data
    cobertura: fração de dias com preço na janela >= `cobertura_min`
    liquidez:  liquidez retrospectiva >= `corte` (R$ por dia)
    """
    tem_preco = adj_close.notna()
    historico = tem_preco.cumsum() >= historico_min
    cobertura = (
        tem_preco.rolling(janela_cobertura, min_periods=janela_cobertura).mean()
        >= cobertura_min
    )
    liquido = liq >= corte
    return {
        "historico": historico,
        "cobertura": cobertura,
        "liquidez": liquido,
        "elegivel": historico & cobertura & liquido,
    }


def datas_rebalanceamento(calendario):
    """Último pregão de cada mês presente no calendário."""
    serie = pd.Series(calendario, index=calendario)
    ultimas = serie.groupby([serie.index.year, serie.index.month]).max()
    return pd.DatetimeIndex(ultimas.values)


# --------------------------------------------------------- uma classe/empresa
def escolher_representantes(elegivel, liq, mapa):
    """Em cada data, entre as classes elegíveis de uma empresa, marca só a mais líquida.

    A escolha usa a liquidez retrospectiva da própria data (sem olhar o
    futuro), então a classe representante pode mudar ao longo do tempo.
    Devolve DataFrame booleano com no máximo UMA ação por empresa por data.
    """
    empresas = mapa.reindex(elegivel.columns)
    if empresas.isna().any():
        faltando = list(empresas.index[empresas.isna()])
        raise ValueError(f"Tickers sem empresa no mapa: {faltando}")
    rep = pd.DataFrame(False, index=elegivel.index, columns=elegivel.columns)
    for _, colunas in empresas.groupby(empresas).groups.items():
        colunas = list(colunas)
        liq_elegiveis = liq[colunas].where(elegivel[colunas], -np.inf)
        melhor = liq_elegiveis.idxmax(axis=1)
        algum = elegivel[colunas].any(axis=1)
        for c in colunas:
            rep[c] = algum & (melhor == c)
    return rep


def resumo_empresas(mapa, elegivel_acao, elegivel_rep):
    """Tabela por empresa: quantas classes, quantos meses elegível e representante atual."""
    linhas = []
    for empresa, tickers in mapa.groupby(mapa).groups.items():
        tickers = [t for t in tickers if t in elegivel_acao.columns]
        if not tickers:
            continue
        ultima = elegivel_rep.index[-1]
        rep_atual = [t for t in tickers if elegivel_rep.loc[ultima, t]]
        linhas.append(
            {
                "empresa": empresa,
                "n_classes": len(tickers),
                "tickers": " ".join(sorted(tickers)),
                "meses_elegivel": int(elegivel_rep[tickers].any(axis=1).sum()),
                "meses_com_2_ou_mais_classes_elegiveis": int(
                    (elegivel_acao[tickers].sum(axis=1) >= 2).sum()
                ),
                "representante_ultima_data": rep_atual[0] if rep_atual else "",
            }
        )
    return pd.DataFrame(linhas).sort_values(
        ["n_classes", "meses_elegivel"], ascending=False
    ).reset_index(drop=True)
