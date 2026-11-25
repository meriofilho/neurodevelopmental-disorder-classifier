"""Pesos de balanceamento de covariáveis (sexo × idade): alternativa ao pareamento que mantém todos os sujeitos.

Em vez de descartar sujeitos até os grupos terem a mesma distribuição de sexo e idade (notebook 02), cada sujeito
recebe um peso 1 / P(seu grupo | sexo, idade), estimado por regressão logística multinomial (pesos de propensão
inversa para vários grupos). Com os pesos, todos os grupos passam a ter a distribuição de sexo e idade da amostra
inteira. Os grupos são os mesmos quatro do pareamento (TEA-ABIDE, Controle-ABIDE, Controle-ADHD200, TDAH-ADHD200),
então os pesos também equilibram os controles das duas bases.

Os pesos são normalizados para média 1 dentro de cada classe diagnóstica: o balanceamento entre classes continua
a cargo de `class_weight="balanced"` nos modelos (não é aplicado duas vezes).

Os pesos usam só sexo, idade e o grupo, calculados uma vez na coorte inteira (etapa de desenho, como o pareamento);
não usam QI nem neuroimagem.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

from matching import add_group


def _covariaveis(df: pd.DataFrame) -> np.ndarray:
    sexo = (df["sex"] == "M").astype(float).to_numpy()[:, None]
    idade = df[["age"]].to_numpy(float)
    spl = SplineTransformer(n_knots=5, degree=3).fit_transform(idade)
    # Splines de idade + interação com sexo: a curva de idade pode ser diferente para meninos e meninas.
    return np.hstack([sexo, spl, spl * sexo])


def propensity(df: pd.DataFrame) -> pd.DataFrame:
    """P(grupo | sexo, idade) para cada sujeito; colunas = grupos."""
    d = add_group(df)
    modelo = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))
    modelo.fit(_covariaveis(d), d["grupo"])
    return pd.DataFrame(modelo.predict_proba(_covariaveis(d)), index=d.index, columns=modelo.classes_)


def covariate_weights(df: pd.DataFrame, trim_q: float = 0.99) -> pd.Series:
    """Peso de cada sujeito: 1 / P(seu grupo | sexo, idade), aparado no quantil `trim_q` e com média 1 por classe.

    O aparo limita sujeitos raros (ex.: meninas com TEA) que teriam peso enorme e dominariam o treino.
    """
    d = add_group(df)
    p = propensity(df)
    p_proprio = p.to_numpy()[np.arange(len(d)), p.columns.get_indexer(d["grupo"])]
    w = pd.Series(1.0 / p_proprio, index=d.index)
    w = w.clip(upper=w.quantile(trim_q))
    return w / w.groupby(d["diagnosis"]).transform("mean")


def effective_n(w) -> float:
    """Tamanho efetivo de Kish: (Σw)² / Σw². Quanto mais desiguais os pesos, menor."""
    w = np.asarray(w, float)
    return w.sum() ** 2 / (w ** 2).sum()


def weighted_smd(df: pd.DataFrame, col: str, a: str, b: str, w=None) -> float:
    """Diferença média padronizada de `col` entre os grupos a e b, com pesos opcionais (|SMD| < 0,1 = equilibrado)."""
    d = add_group(df)
    w = pd.Series(1.0, index=d.index) if w is None else pd.Series(np.asarray(w, float), index=d.index)
    x = d[col].astype(float)

    def mv(g):
        m = d["grupo"] == g
        mu = np.average(x[m], weights=w[m])
        return mu, np.average((x[m] - mu) ** 2, weights=w[m])

    (ma, va), (mb, vb) = mv(a), mv(b)
    sd = np.sqrt((va + vb) / 2)
    return (ma - mb) / sd if sd > 0 else 0.0
