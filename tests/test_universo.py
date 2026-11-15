"""Testes da Parte C. Rode da raiz do projeto:  python -m pytest -v"""
import numpy as np
import pandas as pd

from src import universo

CORTE = 5_000_000
MAPA = pd.Series(
    {"AAAA3": "AAAA", "AAAA4": "AAAA", "BBBB3": "BBBB", "CCCC3": "CCCC"}
)


def _dados(n=500, vol_a3=100_000, vol_a4=300_000, seed=0):
    rng = np.random.default_rng(seed)
    datas = pd.bdate_range("2018-01-01", periods=n)
    adj = pd.DataFrame(
        100 * np.cumprod(1 + rng.normal(0, 0.01, size=(n, 4)), axis=0),
        index=datas,
        columns=list(MAPA.index),
    )
    close = adj.copy()
    volume = pd.DataFrame(
        {"AAAA3": vol_a3, "AAAA4": vol_a4, "BBBB3": 10_000, "CCCC3": 200_000},
        index=datas,
        dtype=float,
    )
    return adj, close, volume


def _elegibilidade(adj, close, volume):
    liq = universo.liquidez(universo.volume_financeiro(close, volume), 126)
    return liq, universo.regras_elegibilidade(adj, liq, CORTE)


def test_corte_de_liquidez_e_historico():
    adj, close, volume = _dados()
    liq, regras = _elegibilidade(adj, close, volume)
    ele = regras["elegivel"]
    assert not ele["BBBB3"].any()  # volume abaixo do corte, nunca elegível
    assert ele.iloc[-1][["AAAA3", "AAAA4", "CCCC3"]].all()
    assert not ele.iloc[:250].any().any()  # sem histórico suficiente


def test_um_representante_por_empresa_e_o_mais_liquido():
    adj, close, volume = _dados()
    liq, regras = _elegibilidade(adj, close, volume)
    rep = universo.escolher_representantes(regras["elegivel"], liq, MAPA)
    ultima = rep.iloc[-1]
    assert ultima["AAAA4"] and not ultima["AAAA3"]
    por_empresa = rep.T.groupby(MAPA).sum().T
    assert (por_empresa <= 1).all().all()


def test_representante_muda_quando_a_liquidez_muda():
    adj, close, volume = _dados(vol_a3=500_000, vol_a4=300_000)
    liq, regras = _elegibilidade(adj, close, volume)
    rep = universo.escolher_representantes(regras["elegivel"], liq, MAPA)
    assert rep.iloc[-1]["AAAA3"] and not rep.iloc[-1]["AAAA4"]


def test_elegibilidade_nao_usa_o_futuro():
    adj, close, volume = _dados()
    i = 400
    base_liq, base = _elegibilidade(adj, close, volume)
    adj2, close2, volume2 = adj.copy(), close.copy(), volume.copy()
    adj2.iloc[i + 1 :] = np.nan  # futuro some
    close2.iloc[i + 1 :] = np.nan
    volume2.iloc[i + 1 :] = 0.0
    liq2, regras2 = _elegibilidade(adj2, close2, volume2)
    pd.testing.assert_series_equal(
        base["elegivel"].iloc[i], regras2["elegivel"].iloc[i], check_names=False
    )
    pd.testing.assert_series_equal(base_liq.iloc[i], liq2.iloc[i], check_names=False)


def test_datas_de_rebalanceamento_sao_o_ultimo_pregao_do_mes():
    cal = pd.bdate_range("2020-01-01", "2020-06-30")
    datas = universo.datas_rebalanceamento(cal)
    assert len(datas) == 6
    for d in datas:
        mesmo_mes = cal[(cal.year == d.year) & (cal.month == d.month)]
        assert d == mesmo_mes.max()


def test_ler_candidatos_ignora_cabecalho_e_rodape(tmp_path):
    arq = tmp_path / "c.csv"
    arq.write_text(
        "IBOV - Composição\nCódigo;Ação;Tipo\nPETR4;PETROBRAS;PN\nSANB11;SANTANDER;UNT\n"
        "PETR4;PETROBRAS;PN\nQuantidade Teórica Total;100;\nTotal;2;\n",
        encoding="latin-1",
    )
    assert universo.ler_candidatos(arq) == ["PETR4", "SANB11"]
