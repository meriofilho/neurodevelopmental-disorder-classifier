"""Pareamento por sexo e idade e teste de viés de base.

Os quatro grupos (TEA-ABIDE, Controle-ABIDE, Controle-ADHD200, TDAH-ADHD200) são pareados por
estrato (sexo × faixa de idade): em cada estrato sorteia-se o mesmo número de sujeitos de cada grupo
(o mínimo entre eles). Estratos sem algum dos grupos são descartados.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedGroupKFold, cross_val_score
from sklearn.pipeline import make_pipeline

RANDOM_STATE = 42
BIAS_FEATS = ["age", "sex_m", "fiq", "hand_right"]


def add_group(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(grupo=df["diagnosis"] + " (" + df["dataset"] + ")")


def match_groups(df: pd.DataFrame, age_bin: float = 1.0, seed: int = RANDOM_STATE) -> pd.DataFrame:
    """Subamostra 1:1:1:1 por estrato sexo × faixa de idade (largura `age_bin` anos)."""
    d = add_group(df).assign(_abin=lambda x: np.floor(x["age"] / age_bin))
    grupos = d["grupo"].unique()
    rng = np.random.default_rng(seed)
    keep = []
    for _, cell in d.groupby(["sex", "_abin"]):
        cnt = cell["grupo"].value_counts().reindex(grupos, fill_value=0)
        n = cnt.min()
        if n == 0:
            continue
        for _, sub in cell.groupby("grupo"):
            keep.extend(rng.choice(sub.index.to_numpy(), n, replace=False))
    return d.loc[sorted(keep)].drop(columns="_abin")


def smd(df: pd.DataFrame, col: str, a: str, b: str) -> float:
    """Diferença média padronizada de `col` entre os grupos a e b (|SMD| < 0,1 = bem pareado)."""
    x, y = df.loc[df.grupo == a, col].astype(float), df.loc[df.grupo == b, col].astype(float)
    sd = np.sqrt((x.var() + y.var()) / 2)
    return (x.mean() - y.mean()) / sd if sd > 0 else 0.0


def dataset_bias_test(df: pd.DataFrame, seed: int = RANDOM_STATE) -> np.ndarray:
    """Acurácia balanceada para prever a base (ABIDE × ADHD-200) entre controles, validando por instituição.

    Perto de 0,5 = as features comuns não denunciam a base.
    """
    ctrl = df[df["diagnosis"] == "Controle"]
    X = ctrl.assign(sex_m=(ctrl["sex"] == "M").astype(float))[BIAS_FEATS].astype(float)
    y = (ctrl["dataset"] == "ABIDE").astype(int)
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        RandomForestClassifier(n_estimators=500, min_samples_leaf=5, class_weight="balanced", random_state=seed),
    )
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    return cross_val_score(model, X, y, cv=cv, groups=ctrl["institution"], scoring="balanced_accuracy")
