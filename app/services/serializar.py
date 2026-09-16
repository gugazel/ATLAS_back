"""Converte tabelas do pandas em listas de dicionários prontas para JSON (NaN vira null)."""
import math

import numpy as np
import pandas as pd


def valor(v):
    if isinstance(v, (list, tuple, np.ndarray)):
        return [valor(x) for x in v]
    if v is None or v is pd.NA:
        return None
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return None if math.isnan(v) else float(v)
    return v


def linhas(df: pd.DataFrame, colunas: list[str]) -> list[dict]:
    presentes = [c for c in colunas if c in df.columns]
    return [{c: valor(v) for c, v in zip(presentes, linha)} for linha in df[presentes].itertuples(index=False)]
