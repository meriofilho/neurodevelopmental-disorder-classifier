"""Modelos e avaliação multiclasse (Controle, TDAH, TEA) com validação agrupada por sítio."""
import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, recall_score, roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

RANDOM_STATE = 42
CLASSES = ["Controle", "TDAH", "TEA"]  # códigos 0, 1, 2


class BalancedXGB(XGBClassifier):
    """XGBoost com pesos de amostra balanceados por classe (equivalente a class_weight='balanced')."""

    def fit(self, X, y, **kw):
        kw.setdefault("sample_weight", compute_sample_weight("balanced", y))
        return super().fit(X, y, **kw)


def features(df: pd.DataFrame, conjunto: str = "qi") -> pd.DataFrame:
    """Conjuntos de features fenotípicas comuns às duas bases.

    'minimo': idade, sexo, QI total.  'qi': + QI verbal, de execução e a discrepância VIQ − PIQ.
    Lateralidade fica de fora: falta em ~23% do ABIDE e ~0% do ADHD-200 (a ausência denunciaria a base).
    """
    X = pd.DataFrame({"idade": df["age"], "sexo_m": (df["sex"] == "M").astype(float), "qi_total": df["fiq"]})
    if conjunto == "qi":
        X["qi_verbal"] = df["viq"]
        X["qi_execucao"] = df["piq"]
        X["discrep_viq_piq"] = df["viq"] - df["piq"]
    return X.astype(float)


def target(df: pd.DataFrame) -> np.ndarray:
    return df["diagnosis"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()


def _imputer(seed):
    # Imputação iterativa (estima VIQ/PIQ a partir das outras colunas) em vez de mediana,
    # para não criar um pico de valores iguais que revele quem não tinha o dado.
    return IterativeImputer(max_iter=10, random_state=seed)


def make_models(seed: int = RANDOM_STATE, tree_depth: int = 3) -> dict:
    """Modelos comparados. Lineares (regressão logística, LDA) padronizam as features; árvores não precisam."""
    return {
        "Regressão logística": make_pipeline(
            _imputer(seed), StandardScaler(),
            LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000, random_state=seed),
        ),
        "LDA": make_pipeline(
            _imputer(seed), StandardScaler(),
            # priors iguais = equivalente a balancear as classes
            LinearDiscriminantAnalysis(priors=[1 / 3, 1 / 3, 1 / 3]),
        ),
        "Árvore de decisão": make_pipeline(
            _imputer(seed),
            DecisionTreeClassifier(max_depth=tree_depth, min_samples_leaf=10, class_weight="balanced", random_state=seed),
        ),
        "Random Forest": make_pipeline(
            _imputer(seed),
            RandomForestClassifier(n_estimators=500, min_samples_leaf=5, max_features="sqrt",
                                   class_weight="balanced", random_state=seed, n_jobs=1),
        ),
        "XGBoost": make_pipeline(
            _imputer(seed),
            BalancedXGB(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                        eval_metric="mlogloss", random_state=seed, n_jobs=1),
        ),
    }


def make_models_conn(seed: int = RANDOM_STATE, tree_depth: int = 3) -> dict:
    """Modelos para conectividade (milhares de features, sem valores ausentes).

    Regressão logística L2 com C escolhido por validação interna (3 dobras, só no treino de cada dobra externa).
    LDA fica de fora: com 6441 features, o shrinkage leva ~2 min por ajuste.
    RF e XGBoost usam threads (n_jobs=-1); o que quebra no Windows é o multiprocessamento do joblib.
    """
    return {
        "Regressão logística": make_pipeline(
            StandardScaler(),
            LogisticRegressionCV(Cs=[1e-4, 1e-3, 1e-2, 1e-1], cv=3, class_weight="balanced",
                                 scoring="balanced_accuracy", max_iter=2000, random_state=seed),
        ),
        "Árvore de decisão": DecisionTreeClassifier(max_depth=tree_depth, min_samples_leaf=10,
                                                    class_weight="balanced", random_state=seed),
        "Random Forest": RandomForestClassifier(n_estimators=500, min_samples_leaf=5, max_features="sqrt",
                                                class_weight="balanced", random_state=seed, n_jobs=-1),
        "XGBoost": BalancedXGB(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8,
                               colsample_bytree=0.1, max_bin=64, tree_method="hist",
                               random_state=seed, n_jobs=-1),
    }


def metrics_binary(y: np.ndarray, proba: np.ndarray, nomes=("negativo", "positivo")) -> dict:
    """Métricas para tarefas binárias (classe 1 = positivo)."""
    pred = proba.argmax(axis=1)
    rec = recall_score(y, pred, labels=[0, 1], average=None)
    return {
        "acc_balanceada": balanced_accuracy_score(y, pred),
        f"sens_{nomes[1]}": rec[1], f"espec_{nomes[0]}": rec[0],
        "auc": roc_auc_score(y, proba[:, 1]),
    }


def metrics(y: np.ndarray, proba: np.ndarray) -> dict:
    if proba.shape[1] == 2:
        return metrics_binary(y, proba)
    pred = proba.argmax(axis=1)
    rec = recall_score(y, pred, labels=[0, 1, 2], average=None)
    tea_tdah = np.isin(y, [1, 2])
    confusao = ((y == 2) & (pred == 1)) | ((y == 1) & (pred == 2))
    return {
        "acc_balanceada": balanced_accuracy_score(y, pred),
        "sens_Controle": rec[0], "sens_TDAH": rec[1], "sens_TEA": rec[2],
        "auc_macro_ovr": roc_auc_score(y, proba, multi_class="ovr", average="macro"),
        # Entre os casos TEA/TDAH reais: fração classificada como o OUTRO transtorno.
        "confusao_TEA_TDAH": confusao[tea_tdah].mean(),
    }


def repeated_group_cv(model, X, y, groups, seeds=range(10), n_splits=5, metric_fn=None):
    """Repete GroupKFold embaralhado (grupos = sítio) com várias sementes.

    Não usa StratifiedGroupKFold: com ~23 sítios ele gera a MESMA divisão para qualquer semente.

    Retorna (tabela de métricas por semente, probabilidades fora-da-dobra da primeira semente).
    """
    linhas, primeira = [], None
    for s in seeds:
        cv = GroupKFold(n_splits=n_splits, shuffle=True, random_state=s)
        proba = cross_val_predict(model, X, y, groups=groups, cv=cv, method="predict_proba")
        linhas.append({"semente": s, **(metric_fn or metrics)(y, proba)})
        if primeira is None:
            primeira = proba
    return pd.DataFrame(linhas), primeira


def confusion_table(y, proba) -> pd.DataFrame:
    cm = confusion_matrix(y, proba.argmax(axis=1), labels=[0, 1, 2])
    return pd.DataFrame(cm, index=[f"real {c}" for c in CLASSES], columns=[f"pred {c}" for c in CLASSES])
