"""Baixa as tabelas de fenótipo do ABIDE I, ABIDE II e ADHD-200 (bucket público fcp-indi, AWS S3).

Uso:  .venv/Scripts/python.exe src/download_phenotypes.py
Arquivos já existentes não são baixados de novo.
"""
from pathlib import Path
from urllib.request import urlretrieve

BASE = "https://s3.amazonaws.com/fcp-indi/data/Projects"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

ABIDE = {
    # Fenótipo do ABIDE Preprocessed (PCP): inclui FILE_ID e métricas de QC.
    "abide/Phenotypic_V1_0b_preprocessed1.csv": f"{BASE}/ABIDE_Initiative/Phenotypic_V1_0b_preprocessed1.csv",
}
ABIDE2_SITES = ["BNI_1", "EMC_1", "GU_1", "IP_1", "IU_1", "KKI_1", "KUL_3", "NYU_1", "NYU_2",
                "OHSU_1", "ONRC_2", "SDSU_1", "TCD_1", "UCD_1", "UCLA_1", "USM_1"]
ABIDE2 = {
    # participants.tsv da versão BIDS. ETHZ_1, UCLA_Long e UPSM_Long não têm esse arquivo no bucket.
    f"abide2/participants_bids/{s}.tsv": f"{BASE}/ABIDE2/RawData/ABIDEII-{s}/participants.tsv"
    for s in ABIDE2_SITES
}
ADHD_SITES = ["Brown", "KKI", "NYU", "NeuroIMAGE", "OHSU",
              "Peking_1", "Peking_2", "Peking_3", "Pittsburgh", "WashU"]
ADHD = {
    # participants.tsv da versão BIDS: cobre os 10 sítios (os CSVs avulsos não incluem Peking_2/3 e WashU).
    # Atenção: arquivos em latin-1, não UTF-8.
    f"adhd200/participants_bids/{s}.tsv": f"{BASE}/ADHD200/RawDataBIDS/{s}/participants.tsv"
    for s in ADHD_SITES
}


def main() -> None:
    for rel, url in {**ABIDE, **ABIDE2, **ADHD}.items():
        dest = RAW / rel
        if dest.exists():
            print(f"ok   {rel}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(url, dest)
        print(f"novo {rel}")


if __name__ == "__main__":
    main()
