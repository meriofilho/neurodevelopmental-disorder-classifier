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

## Conectividade funcional (fMRI de repouso, séries temporais por ROI)
**Atlas escolhido: AAL (116 regiões).** Arquivo de atlas idêntico nos dois pipelines (`aal_mask_pad`, rótulos
2001–9170). Comparado em 25/11/2026: mesmos 116 rótulos, Dice médio por região 0,92 (mín. 0,81); a diferença vem da
resolução (ABIDE 3 mm, Athena 4 mm). Atlas em `raw/atlases/`.

O **CC200 foi descartado**: o "CC200" do ABIDE (`cc200_roi_atlas`, 200 regiões, 3 mm) e o do Athena
(`ADHD200_parcellate_200`, 190 regiões, 4 mm) são parcelações diferentes (Dice típico 0,39, centros a ~9 mm).
Os arquivos baixados continuam em `raw/abide/rois_cc200_filt_noglobal/` e `raw/adhd200/athena/extracted/`, sem uso.

| Base | Fonte | Situação |
|---|---|---|
| ABIDE I | C-PAC `filt_noglobal` (ABIDE Preprocessed, S3 aberto): filtro 0,01–0,1 Hz, CompCor, movimento, sem sinal global | **Baixado** em `raw/abide/rois_aal_filt_noglobal/` (`src/download_connectivity.py --atlas aal`): 1035 sujeitos, `.1D` com cabeçalho `#2001 ... #9170` × 78–316 volumes. 77 sujeitos sem imagem processada; 86 reprovados no QC de algum avaliador (`qc_*` no fenótipo) |
| ADHD-200 | Pipeline **Athena** (Neuro Bureau, NITRC, login gratuito): "AAL Time Courses Corrected Filtering" + "Test Release AAL Time Courses" | **Baixado** em `raw/adhd200/athena/ADHD200_AAL_TCs_*.tar*`, extraído em `raw/adhd200/athena/extracted_aal/<sítio>/<id>/`. 965 sujeitos, 1395 sessões. Usar `sfnwmrda*_aal_TCs.1D` (filtrado); `snwmrda*` é sem filtro. Colunas `Mean_2001 ... Mean_9170` após `File` e `Sub-brick`. QC em `raw/adhd200/adhd200_preprocessed_phenotypics.tsv` (`QC_Athena`: 897 passaram, 68 reprovaram) |
| ABIDE II | Só há saídas DCAN (atlas Gordon/Power/HCP, CIFTI) e fMRIPrep/denoise (volumes completos) | Sem séries AAL prontas. Fica fora da conectividade |

Cobertura na coorte pareada (`processed/cohort_matched.csv`):
- ABIDE I: 159/167 TEA e 135/140 controles com AAL.
- ADHD-200: 279/284 TDAH e 282/284 controles com AAL; passando no `QC_Athena`: 253 TDAH e 269 controles.
- ABIDE II (117 TEA, 144 controles) sem conectividade. Para os modelos com imagem será preciso refazer o pareamento
  só com quem tem AAL.

Pipelines verificados e descartados (25/11/2026):
- C-PAC do ADHD-200 no S3 (`ADHD200/Outputs/cpac`): só 162 sujeitos.
- `denoise` (as três bases): volumes completos (~100 MB/sessão) em espaço nativo; exigiria registro ao MNI.
- fMRIPrep (as três bases): BOLD em MNI com ~550 MB/sessão; a versão em superfície fsaverage5 é leve (~15 MB),
  mas o bucket não tem os arquivos de confounds para remover movimento.

**Atenção:** C-PAC (ABIDE) e Athena (ADHD-200) são pipelines diferentes, ainda que com o mesmo atlas. Diferenças
entre eles viram mais um confundimento de base: repetir o teste de viés entre controles com as features de
conectividade e harmonizar por instituição (ComBat) antes de modelar. Não se sabe ao certo se o Athena removeu o
sinal global; verificar na documentação do pipeline antes de escolher `filt_noglobal` × `filt_global` no ABIDE.

### Downloads manuais do NITRC (Athena)
Pacote **ADHD200 Preproc Athena** em `https://www.nitrc.org/frs/?group_id=383` (login gratuito; aceitar o acordo de
coleta de e-mail). Baixados em 25/11/2026 e guardados em `raw/adhd200/athena/`:
`ADHD200_AAL_TCs_filtfix.tar.gz`, `ADHD200_AAL_TCs_TestRelease.tar`, `ADHD200_CC200_TCs_filtfix.tar.gz`,
`ADHD200_CC200_TCs_TestRelease.tar`. Também `raw/adhd200/adhd200_preprocessed_phenotypics.tsv` (973 sujeitos).
A pasta `data/NITRC-multi-file-downloads/` (e o `.zip`) tem um download errado (`15min_dsi_project`) e pode ser apagada.

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
