# Pedido de acesso ao fenótipo clínico do HBN (Child Mind Institute)

Objetivo: obter o fenótipo completo do Healthy Brain Network (diagnóstico por consenso clínico, KSADS, escalas
comportamentais e cognitivas). É a única base pública com **TEA, TDAH e controles no mesmo protocolo**, o que
resolve o confundimento "base de dados = classe" do projeto.

Levantamento feito em 25/11/2026 a partir da página de fenótipo do HBN, do formulário REDCap e do modelo de DUA.

## O que já é aberto (sem pedido)
- Ressonância (sMRI, fMRI, DWI) e eye-tracking: bucket S3 `fcp-indi/data/Projects/HBN/` (há também saídas do C-PAC).
- EEG em BIDS: OpenNeuro `ds005505` e o portal HBN-EEG.
- `participants.tsv` com sexo, idade e lateralidade (Edinburgh). **Sem diagnóstico.**
- O arquivo `HBN/Pheno/HBN_phenotypic_R11.7z` está no bucket, mas é protegido por senha (só com o DUA).

## O que o DUA libera
Entre outros instrumentos: `Diagnosis_ClinicianConsensus` (diagnóstico DSM-5 por consenso), KSADS, CBCL, SRS-2,
SCQ, ADOS-2 (subgrupo), Conners, ESWAN, SDQ, Vineland (subgrupo), WISC-V/WASI-II/WAIS-IV, KBIT-2, NIH Toolbox,
CELF, CTOPP-2, Edinburgh e histórico médico/gestacional. Lista completa em `Pheno_Protocol.html` no site do HBN.

## Passo a passo
1. **Definir o PI.** O DUA é assinado pelo *Recipient Principal Investigator*, "geralmente o chefe do grupo ou
   laboratório". Para a UFRN: o orientador ou o Prof. Patrick Terrematte (BIF0051). Alunos entram como usuários
   do DUA do PI.
2. **Baixar o modelo mais recente do DUA.** O formulário REDCap aponta para `DataUseAgreementTemplate2025.pdf`; a
   página de fenótipo ainda aponta para a versão 2024. Usar a que o formulário indicar. **O texto não pode ser editado.**
3. **Preencher a página "Recipient Information and Certifications"** (ver campos abaixo) e marcar **HBN**.
4. **Anexar o escopo do projeto** ([escopo_do_projeto.md](escopo_do_projeto.md)), se o uso for além do escopo padrão (ver nota abaixo).
5. **Assinaturas:** PI + representante institucional autorizado a assinar acordos jurídicos (na UFRN, provavelmente
   a Pró-Reitoria de Pesquisa / PROPESQ ou o setor de convênios; confirmar internamente).
6. **Mandar e-mail para `CMIDataUsage@childmind.org` antes de enviar o formulário**, para confirmar que o DUA está
   completo ([email_cmi.md](email_cmi.md)). O formulário avisa que DUAs incompletos ou com alterações não são processados.
7. **Enviar pelo formulário REDCap** `https://redcap.link/HBN_DUA`, com o DUA assinado (PDF escaneado) e o **CV do PI**.
8. **Aguardar:** até 3 semanas (página) ou 14 dias úteis (formulário). O acesso vem por e-mail de
   `lorisadmin@data.healthybrainnetwork.org`.

**Prazo:** não fica pronto para a apresentação de 01–04/12/2026. Na apresentação, o HBN entra como próximo passo.

**Aviso no site:** desde 21/10/2026 o LORIS está fora do ar por uma vulnerabilidade de segurança; aprovações podem
atrasar e o acesso virá por instruções alternativas no e-mail de aprovação.

## Campos da página de assinatura
| Campo | Valor |
|---|---|
| First / Last Name, Degree, Academic Position | do PI |
| Institution | Universidade Federal do Rio Grande do Norte (UFRN) |
| Department | Instituto Metrópole Digital / Programa de Pós-Graduação em Bioinformática |
| Endereço, telefone, país | do PI / instituição (Brasil) |
| E-mail | **institucional** do PI (o login do LORIS usa e-mail institucional) |
| Research Project (title) | *Machine learning for differential classification of neurodevelopmental disorders (ASD, ADHD and FASD) using clinical, cognitive and neuroimaging data* |
| Data Requested | HBN |

Formulário REDCap (página 1): data, nome e e-mail institucional de quem preenche, papel (Recipient / PI /
Institutional Official), cargo, primeira solicitação. A página 2 não foi lida.

## Escopo padrão × escopo próprio
O escopo padrão cobre a "exploração da estrutura e função cerebral, incluindo relações com o fenótipo", usando MRI/EEG
e o fenótipo. Como o projeto também treina classificadores **só com dados clínicos e cognitivos**, vale anexar o
escopo próprio para não haver dúvida. Ver [escopo_do_projeto.md](escopo_do_projeto.md).

## Obrigações que afetam como trabalhamos
- **Não redistribuir** os dados nem dar acesso a quem não está no DUA. Dados do HBN **nunca** entram no git
  (`data/` já está no `.gitignore`) nem em páginas publicadas.
- **Não tentar reidentificar** participantes.
- **Segurança:** computador com senha, atualizado e com antivírus. Evitar guardar em notebook/mídia portátil; se
  precisar, **criptografar** (ex.: BitLocker no Windows) ou usar o cluster NPAD/UFRN. Não expor na internet.
- **Assistentes de IA:** o DUA proíbe transferir os dados a terceiros fora do acordo. Ao trabalhar com o Claude ou
  outra ferramenta em nuvem, enviar só **resultados agregados** (contagens, métricas, figuras), nunca linhas de
  sujeitos. Confirmar com o PI se isso atende à interpretação da instituição.
- **Publicações:** avisar o CMI por e-mail quando e onde sair e incluir o agradecimento padrão:
  > This manuscript was prepared using a limited access dataset obtained from the Child Mind Institute Biobank,
  > Healthy Brain Network. This manuscript reflects the views of the authors and does not necessarily reflect the
  > opinions or views of the Child Mind Institute.
- **Validade:** 7 anos. Ao terminar o projeto ou se o PI sair da instituição, os dados devem ser destruídos e o CMI avisado.
