"""Junta o fenótipo do ABIDE I, ABIDE II e ADHD-200 em uma tabela com colunas comuns.

Uso:  .venv/Scripts/python.exe src/harmonize.py
Saída: data/interim/phenotype_harmonized.csv (1 linha por sujeito com diagnóstico).

Colunas: subject_id, dataset (família: ABIDE / ADHD200), release (ABIDE_I / ABIDE_II / ADHD200),
site (coorte de coleta), institution (instituição/scanner; usar como grupo na validação), diagnosis (TEA/TDAH/Controle), dx_subtype, age, sex (M/F),
fiq, viq, piq, iq_test, hand_right (1 destro / 0 não destro), adhd_comorbid (TEA com TDAH registrado; só ABIDE).
Escalas exclusivas de uma base (ADOS, ADI-R, Conners/ADHD index...) ficam de fora de propósito,
porque a simples presença delas revela o rótulo.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "interim" / "phenotype_harmonized.csv"

# Nomes de sítio do ABIDE alinhados com os do ADHD-200 quando é a mesma instituição.
ABIDE_SITE_MAP = {"PITT": "Pittsburgh"}
ABIDE_DSM = {1: "Autismo", 2: "Asperger", 3: "PDD-NOS", 4: "Asperger/PDD-NOS"}

# Coorte de coleta -> instituição. Coortes da mesma instituição (provavelmente o mesmo scanner) formam um
# único grupo na validação, e é por instituição que se procuram sujeitos repetidos entre as bases.
INSTITUTION = {
    "LEUVEN_1": "LEUVEN", "LEUVEN_2": "LEUVEN", "KUL_3": "LEUVEN",
    "UCLA_1": "UCLA", "UCLA_2": "UCLA", "UM_1": "UM", "UM_2": "UM",
    "NYU_1": "NYU", "NYU_2": "NYU", "KKI_1": "KKI", "OHSU_1": "OHSU", "SDSU_1": "SDSU",
    "TCD_1": "TRINITY", "USM_1": "USM", "BNI_1": "BNI", "EMC_1": "EMC", "GU_1": "GU", "IP_1": "IP",
    "IU_1": "IU", "ONRC_2": "ONRC", "UCD_1": "UCD",
    "Peking_1": "Peking", "Peking_2": "Peking", "Peking_3": "Peking",
}


def _num(s: pd.Series) -> pd.Series:
    """Converte para número e trata os códigos de ausente das duas bases."""
    s = pd.to_numeric(s, errors="coerce")
    return s.mask(s.isin([-9999, -999]) | (s < 0))


def load_abide() -> pd.DataFrame:
    a = pd.read_csv(RAW / "abide" / "Phenotypic_V1_0b_preprocessed1.csv")
    hand = a["HANDEDNESS_CATEGORY"].astype("string")
    comorb = a["COMORBIDITY"].astype("string").str.contains("ADHD", case=False, na=False)
    dx = a["DX_GROUP"].map({1: "TEA", 2: "Controle"})
    return pd.DataFrame({
        "subject_id": "ABIDE_" + a["SUB_ID"].astype(str),
        "dataset": "ABIDE",
        "release": "ABIDE_I",
        "site": a["SITE_ID"].replace(ABIDE_SITE_MAP),
        "diagnosis": dx,
        "dx_subtype": a["DSM_IV_TR"].map(ABIDE_DSM).where(dx == "TEA"),
        "age": _num(a["AGE_AT_SCAN"]),
        "sex": a["SEX"].map({1: "M", 2: "F"}),
        "fiq": _num(a["FIQ"]),
        "viq": _num(a["VIQ"]),
        "piq": _num(a["PIQ"]),
        "iq_test": a["FIQ_TEST_TYPE"].astype("string").replace("-9999", pd.NA),
        "hand_right": hand.map({"R": 1, "L": 0, "Ambi": 0, "Mixed": 0, "L->R": 0}).astype("Float64"),
        "adhd_comorbid": comorb.astype(int),
    })


def load_abide2() -> pd.DataFrame:
    frames = []
    for f in sorted((RAW / "abide2" / "participants_bids").glob("*.tsv")):
        d = pd.read_csv(f, sep="	", encoding="latin1", dtype=str)
        d.columns = d.columns.str.strip().str.lower()
        d["site"] = f.stem
        frames.append(d)
    a = pd.concat(frames, ignore_index=True)
    dx = _num(a["dx_group"]).map({1: "TEA", 2: "Controle"})
    psy = a["nonasd_psydx_label"].astype("string")
    comorb = psy.str.contains("ADHD|attention", case=False, na=False) & (dx == "TEA")
    return pd.DataFrame({
        "subject_id": "ABIDE2_" + a["participant_id"].astype(str).str.strip(),
        "dataset": "ABIDE",
        "release": "ABIDE_II",
        "site": "ABIDEII-" + a["site"],
        "_cohort": a["site"],
        "diagnosis": dx,
        "dx_subtype": _num(a["pdd_dsm_iv_tr"]).map(ABIDE_DSM).where(dx == "TEA"),
        "age": _num(a["age_at_scan"]),
        "sex": _num(a["sex"]).map({1: "M", 2: "F"}),
        "fiq": _num(a["fiq"]),
        "viq": _num(a["viq"]),
        "piq": _num(a["piq"]),
        "iq_test": a["fiq_test_type"].astype("string"),
        # 1 = destro, 2 = canhoto, 3 = ambidestro/misto
        "hand_right": _num(a["handedness_category"]).map({1: 1.0, 2: 0.0, 3: 0.0}).astype("Float64"),
        "adhd_comorbid": comorb.astype(int),
        # Controles do ABIDE II com TDAH registrado (não deveriam existir; marcados por segurança).
        "_ctrl_adhd": (psy.str.contains("ADHD", case=False, na=False) & (dx == "Controle")).astype(int),
    })


def _adhd_hand(v) -> float:
    """ADHD-200 mistura 'Right'/'Left' com escore de Edinburgh (-1 a 1)."""
    if pd.isna(v):
        return np.nan
    v = str(v).strip()
    if v.lower() == "right":
        return 1.0
    if v.lower() == "left":
        return 0.0
    try:
        x = float(v)
    except ValueError:
        return np.nan
    return 1.0 if x > 0 else 0.0


def load_adhd200() -> pd.DataFrame:
    frames = []
    for f in sorted((RAW / "adhd200" / "participants_bids").glob("*.tsv")):
        d = pd.read_csv(f, sep="\t", encoding="latin1", dtype=str)
        d["site"] = f.stem
        frames.append(d)
    h = pd.concat(frames, ignore_index=True)

    dx_raw = h["dx"].astype("string")
    diagnosis = np.select(
        [dx_raw.str.startswith("ADHD", na=False), dx_raw.str.startswith("Typically", na=False)],
        ["TDAH", "Controle"], default=None,
    )
    fiq = _num(h["full4_iq"]).fillna(_num(h["full2_iq"]))
    out = pd.DataFrame({
        "subject_id": "ADHD200_" + h["site"] + "_" + h["participant_id"].astype(str),
        "dataset": "ADHD200",
        "release": "ADHD200",
        "site": h["site"],
        "diagnosis": diagnosis,
        "dx_subtype": dx_raw.str.replace("ADHD-", "", regex=False).where(diagnosis == "TDAH"),
        "age": _num(h["age"]),
        "sex": h["gender"].map({"Male": "M", "Female": "F"}),
        "fiq": fiq,
        "viq": _num(h["verbal_iq"]),
        "piq": _num(h["performance_iq"]),
        "iq_test": h["iq_measure"].astype("string"),
        "hand_right": h["handedness"].map(_adhd_hand).astype("Float64"),
        "adhd_comorbid": 0,
    })
    # O participants.tsv do NYU (e 1 do Peking_1) repete sujeitos: fica a linha mais completa.
    completude = out.notna().sum(axis=1)
    out = out.loc[completude.sort_values(ascending=False).index].drop_duplicates("subject_id")
    return out.sort_index()


RELEASE_PRIORITY = ["ABIDE_I", "ABIDE_II", "ADHD200"]  # quem fica quando a mesma pessoa aparece em duas bases


def cross_dataset_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Pares de sujeitos de releases diferentes que são a mesma pessoa.

    Mesma instituição, sexo e QI total, e um destes:
    1. QI verbal e de execução presentes e idênticos nas duas cópias, idade a até 0,1 ano; ou
    2. (quando falta VIQ/PIQ) idade idêntica com 2 casas decimais, as duas idades não inteiras, e nenhum
       VIQ/PIQ contraditório.
    Idade + QI total com só 1 casa decimal (ou idade inteira, como no ABIDE II do OHSU) gera falsos pares,
    inclusive com diagnósticos diferentes, por isso não é usado.
    Retorna uma linha por par, com sufixos _a (release de maior prioridade) e _b.
    """
    t = df.dropna(subset=["fiq"])
    pares = []
    for i, ra in enumerate(RELEASE_PRIORITY):
        for rb in RELEASE_PRIORITY[i + 1:]:
            a, b = t[t.release == ra], t[t.release == rb]
            p = a.merge(b, on=["institution", "sex", "fiq"], suffixes=("_a", "_b"))
            ambos = p[["viq_a", "viq_b", "piq_a", "piq_b"]].notna().all(axis=1)
            iq_igual = (p.viq_a == p.viq_b) & (p.piq_a == p.piq_b)
            sem_contradicao = ((p.viq_a == p.viq_b) | p.viq_a.isna() | p.viq_b.isna()) &                               ((p.piq_a == p.piq_b) | p.piq_a.isna() | p.piq_b.isna())
            idade_dec = (p.age_a % 1 != 0) & (p.age_b % 1 != 0) & (p.age_a.round(2) == p.age_b.round(2))
            regra1 = ambos & iq_igual & ((p.age_a - p.age_b).abs() <= 0.1)
            regra2 = ~ambos & sem_contradicao & idade_dec
            pares.append(p[regra1 | regra2].assign(regra=np.where(regra1[regra1 | regra2], 1, 2)))
    return pd.concat(pares, ignore_index=True)


def _duplicate_groups(dup: pd.DataFrame) -> list[set]:
    """Junta pares encadeados (A=B e B=C -> {A, B, C}) com union-find."""
    pai = {}

    def raiz(x):
        pai.setdefault(x, x)
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    for a, b in zip(dup.subject_id_a, dup.subject_id_b):
        pai[raiz(a)] = raiz(b)
    grupos = {}
    for x in pai:
        grupos.setdefault(raiz(x), set()).add(x)
    return list(grupos.values())


def harmonize() -> pd.DataFrame:
    df = pd.concat([load_abide(), load_abide2(), load_adhd200()], ignore_index=True)
    df = df[df["diagnosis"].notna()].copy()  # tira Brown (test release, sem dx)
    df["institution"] = df.pop("_cohort").fillna(df["site"]).replace(INSTITUTION)
    df["institution"] = df["institution"].replace(INSTITUTION)
    df = df[df.pop("_ctrl_adhd").fillna(0) == 0]

    # Mesma pessoa em mais de uma base: fica a cópia da release de maior prioridade;
    # se os diagnósticos divergirem, saem todas as cópias.
    info = df.set_index("subject_id")[["release", "diagnosis"]]
    prioridade = {r: i for i, r in enumerate(RELEASE_PRIORITY)}
    fora = set()
    for g in _duplicate_groups(cross_dataset_duplicates(df)):
        sub = info.loc[sorted(g)]
        if sub["diagnosis"].nunique() > 1:
            fora |= g
        else:
            fica = sub["release"].map(prioridade).idxmin()
            fora |= g - {fica}

    cols = ["subject_id", "dataset", "release", "site", "institution", "diagnosis", "dx_subtype", "age", "sex",
            "fiq", "viq", "piq", "iq_test", "hand_right", "adhd_comorbid"]
    return df.loc[~df.subject_id.isin(fora), cols].reset_index(drop=True)


if __name__ == "__main__":
    df = harmonize()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"{len(df)} sujeitos -> {OUT.relative_to(ROOT)}")
    print(pd.crosstab(df["release"], df["diagnosis"], margins=True))
