"""Parâmetros do projeto.

Regra: estes valores são escolhidos ANTES de olhar o resultado da estratégia
(pela literatura ou pelo tamanho do universo), nunca ajustados para melhorar o
retorno. Variações deles entram na Parte G como teste de robustez.
"""
from datetime import date, timedelta

# ---- Período ----
INICIO = "2010-01-01"
FIM = "2026-11-11"  # último dia INCLUÍDO (fixo, para reprodutibilidade)
FIM_YF = (date.fromisoformat(FIM) + timedelta(days=1)).isoformat()  # no yfinance 'end' é exclusivo

# ---- Parte C: universo ----
JANELA_LIQUIDEZ = 126          # ~6 meses de pregões
ESTATISTICA_LIQUIDEZ = "mediana"  # "mediana" ou "media" (ADTV); ADTV 30/60 entram na Parte G
CORTE_LIQUIDEZ = 5_000_000     # R$ por dia. Calibrar pelo TAMANHO do universo, não pelo retorno.
HISTORICO_MIN = 253            # pregões com preço (o momento 12-1 usa o preço de t-252)
JANELA_COBERTURA = 252         # janela para checar buracos nos dados
COBERTURA_MIN = 0.95           # fração mínima de dias com preço na janela

# ---- Parte D: fatores ----
SALTO_MOMENTO = 21             # pula o último mês (~21 pregões)
JANELA_MOMENTO = 252           # 12 meses
JANELA_VOL = 252               # volatilidade de 12 meses
N_QUANTIS = 5
MIN_ACOES = 25                 # mínimo de ações elegíveis para formar quintis (5 por quintil)
