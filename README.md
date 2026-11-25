# Classificador diferencial de transtornos do neurodesenvolvimento (TEA × TDAH × Controle → TEAF)

Projeto da disciplina **BIF0051 – Aprendizado de Máquina para Bioinformática** (PPgBioinfo / IMD / UFRN, Prof. Patrick Terrematte).
Apresentação: **01–04/12/2026**.

## Pergunta
Um comitê de classificadores (Random Forest / XGBoost) supera uma árvore de decisão interpretável em diferenciar
**TEA, TDAH e controles**, especialmente nos casos confundíveis TEA–TDAH? TEAF (via CIFASD) fica como extensão futura.

## Desenho
| Item | Decisão atual |
|---|---|
| Dados | ABIDE I e II (TEA + controles), ADHD-200 (TDAH + controles); HBN (TEA, TDAH e controles no mesmo protocolo) em pedido de acesso; CIFASD (TEAF) só após Data Access Request |
| Classes | TEA, TDAH, Controle (TEAF = roadmap) |
| Features | Idade, sexo, QI, lateralidade + derivados de neuroimagem (volumes / conectividade) + sítio |
| Baseline | Árvore de decisão rasa com poucas features |
| Modelo principal | Random Forest e/ou XGBoost |
| Validação | Validação cruzada agrupada por instituição de coleta (a instituição de teste nunca aparece no treino) |
| Métricas | Acurácia balanceada, sensibilidade/especificidade por classe, matriz de confusão, AUC-ROC multiclasse |

## Estrutura
```
docs/          canvas do projeto, ideia original, pedido de acesso ao HBN (hbn_dua/); slides das aulas ficam fora do git
data/raw/      dados baixados, nunca editados (abide/, adhd200/, cifasd/)  -- fora do controle de versão
data/interim/  dados limpos / harmonizados intermediários
data/processed/ tabela final de modelagem (1 linha por sujeito)
notebooks/     exploração e análises numeradas (01_, 02_, ...)
src/           código reutilizável (carga, harmonização, features, avaliação)
results/       figuras e modelos gerados
reports/       slides e texto da apresentação
```

## Andamento
| Notebook | O que faz | Resultado principal |
|---|---|---|
| [01](notebooks/01_exploracao_fenotipo_vies.ipynb) | Junta ABIDE I, ABIDE II e ADHD-200; testa viés de base | 2945 sujeitos únicos; controles das duas famílias de bases são distinguíveis (0,55; acaso 0,50), por sexo e idade |
| [02](notebooks/02_pareamento_sexo_idade.ipynb) | Pareia os grupos por sexo e idade | 1136 sujeitos; viés de base some (0,42) |
| [03](notebooks/03_baseline_fenotipo.ipynb) | Regressão logística, LDA, árvore, Random Forest e XGBoost só com fenótipo | Árvore 0,40; logística, LDA e RF 0,38; XGBoost 0,37 (acaso 0,33): pouco sinal, nenhum modelo supera a árvore |
| [04](notebooks/04_conectividade_aal.ipynb) | Conectividade funcional AAL (6441 pares): viés de pipeline e modelos | Controles ABIDE × ADHD-200 separáveis com 0,999 (pipelines diferentes), então TEA × TDAH não é comparável. TEA × Controle no ABIDE I: logística 0,64, XGBoost 0,63, RF 0,61, árvore 0,53. TDAH × Controle no ADHD-200: abaixo do acaso (efeito de sítio) |
| [05](notebooks/05_conectividade_efeito_sitio.ipynb) | Efeito de sítio: recupera controles do ADHD-200 e padroniza features por instituição | TDAH × Controle sai de abaixo do acaso para 0,50–0,53 (sem sinal real). TEA × Controle melhora levemente: logística 0,65, XGBoost 0,64, RF 0,61, árvore 0,55 |

Para reproduzir: `src/download_phenotypes.py` → `src/harmonize.py` → notebooks em ordem.

## Pontos metodológicos em aberto
Ver [CLAUDE.md](CLAUDE.md#riscos-metodológicos) — em especial o **confundimento base de dados ↔ classe**.

## Ambiente
Python 3.12 com ambiente virtual em `.venv/`. Dependências em [requirements.txt](requirements.txt);
versões exatas testadas em [requirements-lock.txt](requirements-lock.txt).

```powershell
.\.venv\Scripts\Activate.ps1
jupyter lab
```

Recriar do zero: `py -3.12 -m venv .venv` e `.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt`.
Como obter os dados: [data/README.md](data/README.md).
