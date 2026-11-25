# Recipient Scope of Work (rascunho para anexar ao DUA)

> Rascunho em inglês para o anexo do DUA. Revisar com o PI antes de assinar. Campos entre colchetes a completar.

**Project title:** Machine learning for differential classification of neurodevelopmental disorders (ASD, ADHD and
FASD) using clinical, cognitive and neuroimaging data

**Principal Investigator:** [Name, title], Graduate Program in Bioinformatics, Instituto Metrópole Digital,
Universidade Federal do Rio Grande do Norte (UFRN), Natal, Brazil

**Research team:** [Student name(s)], graduate student(s), Graduate Program in Bioinformatics, UFRN

**Background and aims.** Autism spectrum disorder (ASD), attention-deficit/hyperactivity disorder (ADHD) and fetal
alcohol spectrum disorder (FASD) share overlapping symptoms, which makes differential diagnosis difficult. We are
developing machine learning models to support (not replace) clinical triage by classifying participants as ASD,
ADHD or typically developing, and to identify the clinical, cognitive and brain features that best separate the
groups, with special attention to cases with overlapping ASD and ADHD presentations.

Our current work uses public data from ABIDE I/II and ADHD-200. Because ASD and ADHD participants in those resources
come from different studies, models can learn dataset differences instead of diagnostic differences. The HBN, with
ASD, ADHD and other diagnoses assessed under a single protocol, allows us to evaluate the models without this
confound.

**Data requested:** HBN phenotypic data, including Diagnosis_ClinicianConsensus, KSADS, cognitive and language tests
(e.g., WISC-V, WASI-II, KBIT-2, NIH Toolbox, CELF), behavioral and symptom questionnaires (e.g., CBCL, SRS-2, SCQ,
Conners, ESWAN, SDQ), handedness, demographics and medical/developmental history, linked to the openly available
HBN MRI and EEG data.

**Planned analyses.**
1. Supervised classification (decision trees, random forests, gradient boosting) of ASD vs. ADHD vs. typically
   developing participants using (a) clinical and cognitive phenotype only, (b) MRI/EEG-derived features, and
   (c) their combination.
2. Evaluation with cross-validation grouped by collection site, balanced accuracy and per-class sensitivity.
3. Analysis of participants with comorbid ASD and ADHD and of the features that drive misclassification.
4. Exploratory dimensionality reduction (PCA/UMAP) and feature-importance analysis.

This includes analyses based solely on phenotypic data, which we understand may fall outside the Standard Scope of
Work; we request that it be included.

**Data security.** Data will be stored only on password-protected, encrypted institutional computers and/or the
UFRN high-performance computing cluster (NPAD), accessible only to the research team listed in this DUA. Data will
not be shared, uploaded to public repositories or exposed to the internet. Only aggregate results will be reported.
No attempt will be made to re-identify participants. Data will be destroyed at the end of the project, and CMI will
be notified.

**Outputs.** Academic presentations, a graduate thesis and peer-reviewed publications, which will acknowledge the
Child Mind Institute Biobank as required by the DUA. CMI will be notified of publications.
