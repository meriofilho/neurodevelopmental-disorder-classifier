"""Modelos que combinam fenótipo e conectividade.

A matriz de entrada tem as colunas de fenótipo primeiro (n_feno colunas, podem ter NaN) e depois as de
conectividade (sem NaN). Três formas de usar os dados, para cada tipo de modelo:

- "Fenótipo": só as colunas de fenótipo (imputação iterativa).
- "Conectividade": só as colunas de conectividade.
- "Fusão precoce": todas as colunas juntas num único modelo. Com 6441 pares de conectividade e ~5 de fenótipo,
  o fenótipo tende a ficar diluído (no RF, cada divisão sorteia ~80 de 6446 colunas).
- "Fusão tardia": um modelo para o fenótipo e outro para a conectividade, com a média das probabilidades
  (VotingClassifier soft). Dá o mesmo peso às duas fontes.
"""
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from evaluation import RANDOM_STATE, BalancedXGB, _imputer


def _base_models(seed: int) -> dict:
    """Modelos por tipo, cada um em duas versões: para fenótipo (poucas features) e para conectividade."""
    return {
        "Regressão logística": {
            "feno": LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000, random_state=seed),
            "conn": LogisticRegressionCV(Cs=[1e-4, 1e-3, 1e-2, 1e-1], cv=3, class_weight="balanced",
                                         scoring="balanced_accuracy", max_iter=2000, random_state=seed),
            "escala": True,
        },
        "Árvore de decisão": {
            "feno": DecisionTreeClassifier(max_depth=3, min_samples_leaf=10, class_weight="balanced", random_state=seed),
            "conn": DecisionTreeClassifier(max_depth=3, min_samples_leaf=10, class_weight="balanced", random_state=seed),
            "escala": False,
        },
        "Random Forest": {
            "feno": RandomForestClassifier(n_estimators=500, min_samples_leaf=5, class_weight="balanced",
                                           random_state=seed, n_jobs=-1),
            "conn": RandomForestClassifier(n_estimators=500, min_samples_leaf=5, max_features="sqrt",
                                           class_weight="balanced", random_state=seed, n_jobs=-1),
            "escala": False,
        },
        "XGBoost": {
            "feno": BalancedXGB(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8,
                                eval_metric="logloss", random_state=seed, n_jobs=-1),
            "conn": BalancedXGB(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8,
                                colsample_bytree=0.1, max_bin=64, tree_method="hist", random_state=seed, n_jobs=-1),
            "escala": False,
        },
    }


def _prep(cols_feno, cols_conn, usar_feno, usar_conn, escala, seed):
    partes = []
    if usar_feno:
        passos = [_imputer(seed)] + ([StandardScaler()] if escala else [])
        partes.append(("feno", make_pipeline(*passos), cols_feno))
    if usar_conn:
        partes.append(("conn", StandardScaler() if escala else "passthrough", cols_conn))
    return ColumnTransformer(partes)


def make_fusion_models(n_feno: int, n_conn: int, seed: int = RANDOM_STATE) -> dict:
    """Retorna {(modelo, conjunto): estimador} para os 4 conjuntos de features."""
    cols_feno = list(range(n_feno))
    cols_conn = list(range(n_feno, n_feno + n_conn))
    out = {}
    for nome, b in _base_models(seed).items():
        esc = b["escala"]
        so_feno = make_pipeline(_prep(cols_feno, cols_conn, True, False, esc, seed), clone(b["feno"]))
        so_conn = make_pipeline(_prep(cols_feno, cols_conn, False, True, esc, seed), clone(b["conn"]))
        out[(nome, "Fenótipo")] = so_feno
        out[(nome, "Conectividade")] = so_conn
        out[(nome, "Fusão precoce")] = make_pipeline(_prep(cols_feno, cols_conn, True, True, esc, seed), clone(b["conn"]))
        out[(nome, "Fusão tardia")] = VotingClassifier([("feno", clone(so_feno)), ("conn", clone(so_conn))], voting="soft")
    return out
