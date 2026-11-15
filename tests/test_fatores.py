"""Testes da Parte D. Rode da raiz do projeto:  python -m pytest -v"""
import numpy as np
import pandas as pd

from src import fatores


def _precos(n=700, k=8, seed=0):
    rng = np.random.default_rng(seed)
    datas = pd.bdate_range("2018-01-01", periods=n)
    ret = rng.normal(0.0004, 0.02, size=(n, k))
    return pd.DataFrame(
        100 * np.cumprod(1 + ret, axis=0),
        index=datas,
        columns=[f"A{i}" for i in range(k)],
    )


def _depende_do_futuro(func, precos, i):
    """True se o sinal na linha i muda quando os preços DEPOIS de i são alterados."""
    datas = pd.DatetimeIndex([precos.index[i]])
    base = func(precos).loc[datas]
    futuro = precos.copy()
    futuro.iloc[i + 1 :] = futuro.iloc[i + 1 :] * 3.0
    alterado = func(futuro).loc[datas]
    return not np.allclose(base.to_numpy(), alterado.to_numpy(), equal_nan=True)


def test_momento_bate_com_a_formula():
    p = _precos()
    esperado = p.iloc[400 - 21] / p.iloc[400 - 252] - 1
    obtido = fatores.momento_12_1(p).iloc[400]
    pd.testing.assert_series_equal(obtido, esperado, check_names=False)


def test_momento_pula_o_ultimo_mes():
    """Mudar o preço dos últimos 21 pregões não pode alterar o momento 12-1."""
    p = _precos()
    i = 450
    alterado = p.copy()
    alterado.iloc[i - 20 : i + 1] = alterado.iloc[i - 20 : i + 1] * 2.0
    a = fatores.momento_12_1(p).iloc[i]
    b = fatores.momento_12_1(alterado).iloc[i]
    pd.testing.assert_series_equal(a, b)


def test_sinais_nao_dependem_do_futuro():
    p = _precos()
    assert not _depende_do_futuro(fatores.momento_12_1, p, 450)
    assert not _depende_do_futuro(fatores.volatilidade, p, 450)


def test_sinais_iguais_com_dados_cortados_na_data():
    p = _precos()
    i = 450
    datas = pd.DatetimeIndex([p.index[i]])
    completo = fatores.calcular_sinais(p, datas)
    cortado = fatores.calcular_sinais(p.iloc[: i + 1], datas)
    for nome in ("momento", "vol"):
        pd.testing.assert_frame_equal(completo[nome], cortado[nome])


def test_detector_pega_vazamento():
    """Garante que o teste de vazamento funciona: um sinal que olha o futuro é detectado."""
    p = _precos()
    vazado = lambda x: x.shift(-5) / x - 1  # usa o preço de t+5
    assert _depende_do_futuro(vazado, p, 450)


def _sinal_cem():
    return pd.DataFrame(
        [np.arange(1, 101, dtype=float)] * 3,
        index=pd.bdate_range("2020-01-31", periods=3),
        columns=[f"T{i}" for i in range(100)],
    )


def test_quintis_balanceados():
    s = _sinal_cem()
    q = fatores.quintis(s, pd.DataFrame(True, index=s.index, columns=s.columns))
    assert (q.apply(lambda linha: linha.value_counts().sort_index().tolist(), axis=1)
            .apply(lambda x: x == [20] * 5).all())


def test_quintil_1_e_o_melhor():
    s = _sinal_cem()
    ele = pd.DataFrame(True, index=s.index, columns=s.columns)
    q_alto = fatores.quintis(s, ele, maior_melhor=True)
    q_baixo = fatores.quintis(s, ele, maior_melhor=False)
    assert q_alto.iloc[0]["T99"] == 1 and q_alto.iloc[0]["T0"] == 5
    assert q_baixo.iloc[0]["T0"] == 1 and q_baixo.iloc[0]["T99"] == 5


def test_quintis_ignoram_nao_elegiveis_e_exigem_minimo():
    s = _sinal_cem()
    ele = pd.DataFrame(True, index=s.index, columns=s.columns)
    ele.iloc[:, :20] = False
    q = fatores.quintis(s, ele)
    assert q.iloc[:, :20].isna().all().all()
    assert q.iloc[:, 20:].notna().all().all()
    poucos = pd.DataFrame(False, index=s.index, columns=s.columns)
    poucos.iloc[:, :10] = True
    assert fatores.quintis(s, poucos).isna().all().all()
