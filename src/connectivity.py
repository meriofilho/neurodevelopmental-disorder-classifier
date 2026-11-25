"""Séries temporais AAL -> matrizes de conectividade funcional (correlação de Pearson, z de Fisher).

Uso:  .venv/Scripts/python.exe src/connectivity.py
Saídas:
  data/processed/connectivity_aal.npz   X (sujeitos × pares de ROIs, float32), subject_id, rois, pares
  data/processed/connectivity_aal_meta.csv  subject_id, release, n_vols, arquivo, motivo de exclusão (se houver)

Fontes (ver data/README.md):
  ABIDE I  : C-PAC filt_noglobal, data/raw/abide/rois_aal_filt_noglobal/<FILE_ID>_rois_aal.1D
  ADHD-200 : Athena, data/raw/adhd200/athena/extracted_aal/<sítio>/<id>/sfnwmrda<id>_session_<s>_rest_<r>_aal_TCs.1D

Regras de qualidade:
  - ABIDE I: sai quem tem "fail" em algum avaliador de QC (qc_rater_1, qc_anat_rater_2, qc_func_rater_2).
  - ADHD-200: sai quem tem QC_Athena != 1 (adhd200_preprocessed_phenotypics.tsv).
  - Mínimo de MIN_VOLS volumes.
  - ROIs sem sinal (variância zero) em mais de 2% dos sujeitos saem para todos; depois sai quem ainda tem
    alguma ROI sem sinal.
  - ADHD-200 com várias sessões: usa a primeira (menor sessão, menor run), como o ABIDE, que tem uma só.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
MIN_VOLS = 70
ZERO_ROI_MAX_FRAC = 0.02


def _abide_series() -> list[dict]:
    p = pd.read_csv(RAW / "abide" / "Phenotypic_V1_0b_preprocessed1.csv")
    qc = p[["qc_rater_1", "qc_anat_rater_2", "qc_func_rater_2"]].fillna("").astype(str).agg(" ".join, axis=1)
    p["qc_fail"] = qc.str.lower().str.contains("fail")
    pasta = RAW / "abide" / "rois_aal_filt_noglobal"
    out = []
    for _, r in p[p["FILE_ID"] != "no_filename"].iterrows():
        f = pasta / f"{r.FILE_ID}_rois_aal.1D"
        if not f.exists():
            continue
        with open(f) as fh:
            rois = [c.lstrip("#") for c in fh.readline().split()]
        ts = np.loadtxt(f, skiprows=1)
        out.append({"subject_id": f"ABIDE_{r.SUB_ID}", "release": "ABIDE_I", "arquivo": f.name,
                    "rois": rois, "ts": ts, "qc_fail": bool(r.qc_fail)})
    return out


def _adhd_series() -> list[dict]:
    q = pd.read_csv(RAW / "adhd200" / "adhd200_preprocessed_phenotypics.tsv", sep="\t", na_values=["N/A"])
    qc_ok = set(q.loc[q["QC_Athena"] == 1, "ScanDir ID"].astype(str).str.lstrip("0"))
    escolhido = {}
    for f in (RAW / "adhd200" / "athena" / "extracted_aal").glob("*/*/sfnwmrda*_aal_TCs.1D"):
        m = re.search(r"session_(\d+)_rest_(\d+)", f.name)
        chave = (f.parent.parent.name, f.parent.name.lstrip("0"))
        ordem = (int(m.group(1)), int(m.group(2)))
        if chave not in escolhido or ordem < escolhido[chave][0]:
            escolhido[chave] = (ordem, f)
    out = []
    for (site, sid), (_, f) in sorted(escolhido.items()):
        d = pd.read_csv(f, sep="\t")
        cols = [c for c in d.columns if c.strip().startswith("Mean_")]
        out.append({"subject_id": f"ADHD200_{site}_{sid}", "release": "ADHD200", "arquivo": f.name,
                    "rois": [c.strip().replace("Mean_", "") for c in cols],
                    "ts": d[cols].astype(float).to_numpy(), "qc_fail": sid not in qc_ok})
    return out


def standardize_by_group(X: np.ndarray, groups) -> np.ndarray:
    """Padroniza cada feature dentro de cada grupo (instituição): média 0 e DP 1 no grupo.

    Não usa rótulos. Como a validação deixa instituições inteiras fora do treino, cada instituição é padronizada só
    com os próprios dados, sem vazar informação entre treino e teste. Remove deslocamentos de sítio (scanner,
    protocolo), mas também a parte da diferença entre grupos que coincide com a proporção de casos em cada sítio.
    """
    X = np.asarray(X, dtype=float).copy()
    groups = np.asarray(groups)
    for g in np.unique(groups):
        m = groups == g
        mu, sd = X[m].mean(axis=0), X[m].std(axis=0)
        X[m] = (X[m] - mu) / np.where(sd > 0, sd, 1.0)
    return X


def _fisher_z(ts: np.ndarray) -> np.ndarray:
    r = np.corrcoef(ts, rowvar=False)
    np.fill_diagonal(r, 0.0)
    return np.arctanh(np.clip(r, -0.999999, 0.999999))


def build() -> tuple[np.ndarray, pd.DataFrame, list[str], list[tuple[str, str]]]:
    series = _abide_series() + _adhd_series()
    rois = series[0]["rois"]
    for s in series:
        if s["rois"] != rois:
            raise ValueError(f"Ordem de ROIs diferente em {s['arquivo']}")

    zero = np.array([s["ts"].std(axis=0) == 0 for s in series])
    roi_ok = zero.mean(axis=0) <= ZERO_ROI_MAX_FRAC
    rois_usadas = [r for r, ok in zip(rois, roi_ok) if ok]

    meta, mats = [], []
    for s, z in zip(series, zero):
        motivo = ""
        if s["qc_fail"]:
            motivo = "QC"
        elif s["ts"].shape[0] < MIN_VOLS:
            motivo = f"<{MIN_VOLS} volumes"
        elif z[roi_ok].any():
            motivo = "ROI sem sinal"
        meta.append({"subject_id": s["subject_id"], "release": s["release"], "n_vols": s["ts"].shape[0],
                     "arquivo": s["arquivo"], "excluido": motivo})
        if not motivo:
            mats.append(_fisher_z(s["ts"][:, roi_ok]))

    meta = pd.DataFrame(meta)
    iu = np.triu_indices(len(rois_usadas), k=1)
    X = np.array([m[iu] for m in mats], dtype=np.float32)
    pares = [(rois_usadas[i], rois_usadas[j]) for i, j in zip(*iu)]
    return X, meta, rois_usadas, pares


if __name__ == "__main__":
    X, meta, rois, pares = build()
    OUT.mkdir(parents=True, exist_ok=True)
    ok = meta[meta["excluido"] == ""]
    np.savez_compressed(OUT / "connectivity_aal.npz", X=X, subject_id=ok["subject_id"].to_numpy(),
                        rois=np.array(rois), pares=np.array(pares))
    meta.to_csv(OUT / "connectivity_aal_meta.csv", index=False)
    print(f"{X.shape[0]} sujeitos × {X.shape[1]} pares ({len(rois)} ROIs) -> data/processed/connectivity_aal.npz")
    print(pd.crosstab(meta["release"], meta["excluido"].replace("", "incluído")))
