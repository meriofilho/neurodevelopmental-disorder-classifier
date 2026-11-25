# CLAUDE.md

Contexto para trabalhar neste projeto. Visão geral em [README.md](README.md); canvas completo em `docs/canvas/`.

## Projeto
Classificação multiclasse (TEA, TDAH, Controle; TEAF futuro) com dados públicos ABIDE I, ABIDE II e ADHD-200 (HBN em pedido de acesso).
Baseline = árvore de decisão; modelo principal = RF/XGBoost; referências lineares = regressão logística e LDA. Trabalho acadêmico (BIF0051, UFRN), apresentação 01–04/12/2026.
Idioma do projeto: português (código e nomes de variáveis podem ser em inglês).

## Ambiente
Python 3.12 em `.venv/` (rodar com `.venv/Scripts/python.exe`). Bibliotecas principais: scikit-learn, xgboost,
imbalanced-learn, nilearn, shap, umap-learn. Novas dependências: adicionar em `requirements.txt` e regenerar `requirements-lock.txt`.

## Convenções
- Fenótipos em `data/raw/` (ver `data/README.md`); ADHD-200 `.tsv` deve ser lido com `encoding="latin1"`; ABIDE usa `-9999` como ausente.
- Conectividade: atlas **AAL** (116 ROIs; o CC200 do ABIDE e o do Athena são parcelações diferentes). ABIDE I = C-PAC `filt_noglobal` em `data/raw/abide/rois_aal_filt_noglobal/`; ADHD-200 = Athena `sfnwmrda*_aal_TCs.1D` em `data/raw/adhd200/athena/extracted_aal/`. ABIDE II não tem conectividade. Pipelines diferentes: testar viés entre controles e harmonizar (ComBat) antes de modelar.
- Tabela de trabalho: `harmonize()` em `src/harmonize.py` (remove sujeitos repetidos) e coorte `data/interim/cohort_7_21.csv`.
- `data/raw/` é somente leitura; todo processamento grava em `data/interim/` ou `data/processed/`.
- Dados nunca vão para o git (ver `.gitignore`).
- Notebooks numerados (`01_exploracao_fenotipo.ipynb`, ...); lógica reaproveitada vai para `src/`.
- Semente fixa (`RANDOM_STATE = 42`) em toda divisão e modelo.
- Divisão treino/teste sempre agrupada por **instituição** (`GroupKFold(shuffle=True)` / `LeaveOneGroupOut` com `groups=institution`); nunca split aleatório simples.
  Não usar `StratifiedGroupKFold` para repetições: com poucas instituições ele gera a mesma divisão para qualquer semente.
- Avaliação: `src/evaluation.py` (`repeated_group_cv`, 10 sementes). Rodar com `n_jobs=1`: paralelismo do joblib quebra no Windows.
- Todo pré-processamento (imputação, escala, seleção de features, reamostragem) dentro de `Pipeline`, ajustado só no treino.

## Riscos metodológicos
1. **Base de dados = classe.** TEA vem só do ABIDE e TDAH só do ADHD-200. Qualquer feature que denuncie a origem
   (sítio, protocolo de aquisição, pipeline de pré-processamento, escalas exclusivas) permite ao modelo "acertar" sem
   aprender nada clínico. Mitigações: usar controles das duas bases; testar se um classificador distingue
   *controles ABIDE × controles ADHD-200* (se sim, há viés de base); harmonizar (ex.: ComBat) e usar o mesmo pipeline de imagem.
   **Notebook 01 (com ABIDE II):** acurácia balanceada 0,55 entre controles 7–21 anos só com fenótipo (acaso 0,50), puxada por sexo e idade.
   **Notebook 02:** pareamento sexo × idade (`src/matching.py`) leva a 0,42 ± 0,03. Modelar sobre `data/processed/cohort_matched.csv` (1136 sujeitos).
   **Notebook 03:** baseline só com fenótipo: árvore 0,40; regressão logística, LDA e RF 0,38; XGBoost 0,37 (acaso 0,33). Falta sinal; próximos passos: fenótipo clínico do HBN e neuroimagem.
2. **Vazamento por escalas.** ADOS/ADI-R só existem para ABIDE e Conners/ADHD-RS só para ADHD-200 — a mera presença
   da escala revela o rótulo. Usar apenas features comuns às duas bases (idade, sexo, QI, lateralidade, imagem).
3. **Sítio como feature.** Útil para harmonização, mas não deve entrar como preditor no modelo final.
4. **Comorbidade TEA+TDAH.** 141 sujeitos TEA (ABIDE I+II) têm TDAH registrado; ficam fora da coorte, mas na tabela harmonizada.
5. **Desbalanceamento.** `class_weight="balanced"` ou reamostragem dentro do pipeline; reportar acurácia balanceada.
6. **Escopo de classes.** `docs/ideia.txt` fala em 4 classes (com TEAF); o canvas final fixa 3 classes + TEAF como roadmap.
   O canvas é a versão vigente.
