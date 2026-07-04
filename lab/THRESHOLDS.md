# Caliber Threshold Analysis

Generated UTC: `2026-07-04T09:01:01.541268+00:00`
Git SHA: `c31299f`
n: `50`
Replicates: `500`
Clean populations: `honest, overconfident, underconfident, noisy, smart_fabricator`

| constant | current | clean FPR | target rates | recommended |
| --- | ---: | ---: | --- | --- |
| LOW_UNCERTAINTY_THRESHOLD | 0.13 | 3.6% | farmer=99.2%, patient_farmer=99.8% | 0.13 (FPR 3.6%, power 99.5%) |
| LOW_RESOLUTION_RATIO | 0.4945 | 0.4% | naive_fabricator=100.0%, template_spammer=100.0% | 0.4945 (FPR 0.4%, power 100.0%) |
| TOP_BUCKET_SHARE_THRESHOLD | 0.6 | 0.6% | farmer=100.0%, patient_farmer=100.0% | 0.6 (FPR 0.6%, power 100.0%) |
| DOMAIN_HHI_THRESHOLD | 0.6 | 0.0% | domain_camper=100.0% | 0.6 (FPR 0.0%, power 100.0%) |
| DUPLICATE_RATIO_THRESHOLD | 0.2 | 0.0% | duplicate_spammer=100.0% | 0.2 (FPR 0.0%, power 100.0%) |
| INSTANT_SHARE_THRESHOLD | 0.5 | 0.0% | farmer=100.0% | 0.5 (FPR 0.0%, power 100.0%) |
| IMPORT_SHARE_THRESHOLD | 0.8 | 0.0% | bulk_importer=100.0% | 0.8 (FPR 0.0%, power 100.0%) |
| MENDEL_P_LOW_THRESHOLD | 0.01 | 0.0% | naive_fabricator=100.0% | 0.01 (FPR 0.0%, power 100.0%) |
