# Dados

Nada aqui é versionado. Coloque os downloads brutos em `data/raw/<base>/` e não edite esses arquivos.

| Base | Classe | Acesso | Onde |
|---|---|---|---|
| ABIDE I/II | TEA + controles | Aberto | Fenótipo + derivados pré-processados: Preprocessed Connectomes Project (`preprocessed-connectomes-project.org/abide`); também via `nilearn.datasets.fetch_abide_pcp` |
| ADHD-200 | TDAH + controles | Aberto | Fenótipo e pré-processados (pipeline Athena/NIAK): `preprocessed-connectomes-project.org/adhd200` e `fcon_1000.projects.nitrc.org/indi/adhd200` |
| HBN (Healthy Brain Network) | TEA, TDAH, outros + controles, mesmo protocolo | Imagem/EEG abertos; fenótipo clínico exige DUA (LORIS) | `fcon_1000.projects.nitrc.org/indi/cmi_healthy_brain_network`; EEG BIDS no OpenNeuro `ds005505`. No bucket há `HBN/Pheno/HBN_phenotypic_R11.7z`, protegido por senha (só com DUA). O `participants.tsv` aberto tem só sexo, idade e lateralidade |
| CIFASD | TEAF | Data Access Request | `cifasd.org` — extensão futura, fora do escopo da apresentação de dez/2026 |

## Baixado (24–25/11/2026)
Para refazer: `.venv/Scripts/python.exe src/download_phenotypes.py` (bucket público `s3://fcp-indi`).

| Arquivo | Conteúdo |
|---|---|
| `raw/abide/Phenotypic_V1_0b_preprocessed1.csv` | ABIDE I: 1112 sujeitos (539 TEA, 573 controles), 20 sítios, 106 colunas. `DX_GROUP` 1 = TEA, 2 = controle. Valores ausentes como `-9999` |
| `raw/abide2/participants_bids/<sítio>.tsv` | ABIDE II: 1007 sujeitos (474 TEA, 533 controles) em 16 coortes. Sem ETHZ_1, UCLA_Long e UPSM_Long (sem `participants.tsv` no bucket). TDAH comórbido em `nonasd_psydx_label` |
| `raw/adhd200/participants_bids/<sítio>.tsv` | ADHD-200: 1062 linhas em 10 sítios. Brown (26) sem diagnóstico, pois é test release. Codificação **latin-1**. **O NYU repete ~100 sujeitos** |

## Tabelas derivadas (`src/harmonize.py` e notebook 01)
| Arquivo | Conteúdo |
|---|---|
| `interim/phenotype_harmonized.csv` | 2945 sujeitos únicos: 1013 TEA (141 com TDAH comórbido), 359 TDAH, 1573 controles. Colunas comuns às bases, incluindo `release` e `institution` |
| `processed/cohort_matched.csv` | Coorte pareada por sexo × idade (estratos de 1 ano, 1:1:1:1, semente 42; `src/matching.py`, notebook 02). 1136 sujeitos: 284 TEA, 284 TDAH, 568 controles, majoritariamente meninos. Teste de viés de base: 0,42 ± 0,03 (acaso 0,50) |
| `interim/cohort_7_21.csv` | Coorte de análise: 7–21 anos, sem TEA com TDAH comórbido. 2374 sujeitos: 682 TEA, 359 TDAH, 1333 controles |

Limpezas feitas em `harmonize()`:
- Linhas repetidas no `participants.tsv` do ADHD-200 removidas (fica a mais completa).
- **109 controles aparecem em duas releases** (53 NYU ABIDE I×ADHD-200, 44 KKI ABIDE II×ADHD-200, 8 KKI ABIDE I×ABIDE II, 4 KKI ABIDE I×ADHD-200). Critério em `cross_dataset_duplicates`: mesma instituição, sexo e QI total, mais VIQ/PIQ idênticos ou idade idêntica com 2 casas decimais. Fica a cópia da release mais antiga. Nenhum par tinha diagnóstico divergente.
- `institution` junta coortes da mesma instituição (ex.: NYU de ABIDE I, ABIDE II e ADHD-200; Peking_1/2/3). É o grupo usado na validação.
- Escalas exclusivas de uma base (ADOS, ADI-R, ADHD index...) ficam fora da tabela.

Observações:
- **Instituições nas duas famílias (ABIDE e ADHD-200):** NYU, KKI, OHSU e Pittsburgh.
- **Idade:** ABIDE vai de 6,5 a 64 anos e ADHD-200 de 7 a 26.
- **Sexo:** controles do ADHD-200 são 50% masculinos, contra 75% dos controles do ABIDE I+II. Esse é o principal viés de base.
- **QI:** testes diferentes (WASI, WISCC-R chinês, versões de 2 subtestes). Cerca de 6% sem QI total.
- **Comorbidade:** 141 sujeitos TEA (26 ABIDE I, 115 ABIDE II) têm TDAH registrado.

## Para reduzir viés de base
- Modelar sobre `processed/cohort_matched.csv`, que já é pareada por sexo e idade (notebook 02).
- Preferir derivados gerados pelo **mesmo atlas** nas duas bases (ex.: CC200 ou AAL) para as features de conectividade.
