"""Baixa séries temporais por ROI (fMRI de repouso) do ABIDE I processadas pelo C-PAC (ABIDE Preprocessed).

Uso:  .venv/Scripts/python.exe src/download_connectivity.py [--atlas cc200] [--strategy filt_noglobal]
Saída: data/raw/abide/rois_<atlas>_<strategy>/<FILE_ID>_rois_<atlas>.1D  (1 linha por volume, 1 coluna por ROI)

Por que esta fonte:
- C-PAC `filt_noglobal`: filtro 0,01–0,1 Hz, CompCor, 24 parâmetros de movimento, tendências; sem regressão
  do sinal global. É a configuração mais próxima do pipeline Athena usado no ADHD-200.
- O C-PAC do ADHD-200 no S3 só tem 162 sujeitos, e o ABIDE II não tem ROIs do C-PAC (só DCAN).
- ADHD-200: as séries CC200 do pipeline Athena ficam no NITRC e exigem login (ver data/README.md).

Arquivos já existentes não são baixados de novo.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlretrieve

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
BASE = "https://s3.amazonaws.com/fcp-indi/data/Projects/ABIDE_Initiative/Outputs/cpac"


def baixar(url: str, dest: Path) -> str:
    if dest.exists() and dest.stat().st_size > 0:
        return "ok"
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        urlretrieve(url, tmp)
    except HTTPError as e:
        return f"erro {e.code}"
    tmp.replace(dest)
    return "novo"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", default="cc200")
    ap.add_argument("--strategy", default="filt_noglobal",
                    choices=["filt_noglobal", "filt_global", "nofilt_noglobal", "nofilt_global"])
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    pheno = pd.read_csv(RAW / "abide" / "Phenotypic_V1_0b_preprocessed1.csv")
    ids = pheno.loc[pheno["FILE_ID"] != "no_filename", "FILE_ID"].astype(str)
    dest_dir = RAW / "abide" / f"rois_{args.atlas}_{args.strategy}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    tarefas = {
        f"{fid}_rois_{args.atlas}.1D": f"{BASE}/{args.strategy}/rois_{args.atlas}/{fid}_rois_{args.atlas}.1D"
        for fid in ids
    }
    contagem = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futuros = {ex.submit(baixar, url, dest_dir / nome): nome for nome, url in tarefas.items()}
        for i, f in enumerate(as_completed(futuros), 1):
            r = f.result()
            contagem[r] = contagem.get(r, 0) + 1
            if r.startswith("erro"):
                print(f"{r}: {futuros[f]}")
            if i % 200 == 0:
                print(f"{i}/{len(tarefas)}")
    print(f"{len(tarefas)} sujeitos com FILE_ID -> {dest_dir.relative_to(ROOT)}: {contagem}")


if __name__ == "__main__":
    main()
