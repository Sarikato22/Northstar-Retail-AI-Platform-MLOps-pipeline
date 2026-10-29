# Lab 3 - Churn Model Evaluation Report

## 1. Evaluation Overview

The objective of this evaluation is to determine whether the NorthStar churn model identifies customers at risk of churning and whether the engineered Feature Store columns improve performance over a recency-only baseline.

Training data was retrieved from the SageMaker Feature Store offline store using Athena. The model was evaluated on a held-out test split.

### Training and Evaluation Configuration

| Configuration | Value |
|---|---|
| Training data source | Feature Store offline store via Athena |
| Athena QueryExecutionId | `5802afcb-c9cf-41ff-8b05-7472e335fac2` |
| Random seed | 42 |
| Training set size | 6,999 |
| Test set size | 3,000 |
| XGBoost version | 3.2.0 |
| Baseline feature | `days_since_last_purchase` |
| Positive rate, test split | 0.22 |

## 2. Model Evaluation Metrics

| Metric | Measured Value | Requirement | Result |
|---|---:|---|---|
| AUC-ROC, test set | 0.7779 | Report; no fixed threshold | Reported |
| Precision @ top 10% | 0.7033 | >= 0.50 | Pass |
| Recall @ top 10% | 0.3197 | >= 0.25 | Pass |
| Recency-only baseline AUC | 0.7229 | Report baseline | Reported |
| AUC lift over baseline | 0.0550 | 95% CI must exclude zero | Pass |
| 95% CI lower bound | 0.0365 | Must exclude zero as an interval | Pass |
| 95% CI upper bound | 0.0730 | Must exclude zero as an interval | Pass |

The recorded evaluation metrics are available in `lab3-evidence/evaluation_metrics.json`.

## 3. Recency-Only Baseline and AUC Lift

The recency-only baseline uses `days_since_last_purchase` as its only input feature. The full model uses the engineered feature set described in `lab3-model-design.md`.

The full model achieved a test AUC of **0.7779**, compared with **0.7229** for the recency-only baseline. The measured AUC lift was **0.0550**.

Approximately 2,000 paired bootstrap replicates were used to estimate uncertainty in the AUC difference. For each replicate, test-set rows were sampled with replacement, and both models were evaluated on the same sampled rows.

| Statistic | Value |
|---|---:|
| Full-model AUC | 0.7779 |
| Baseline AUC | 0.7229 |
| AUC lift | 0.0550 |
| 95% confidence interval | [0.0365, 0.0730] |

**Interpretation:** The entire confidence interval is above zero, so the evaluation supports the conclusion that the engineered feature model outperforms the recency-only baseline on this held-out split.

## 4. Confusion Matrix

The confusion matrix at threshold 0.5 is:

| | Predicted not churn | Predicted churn |
|---|---:|---:|
| Actual not churn | 1,709 | 631 |
| Actual churn | 229 | 431 |

The confusion matrix visualization is stored at `lab3-evidence/confusion-matrix.png`. This threshold-based view complements the top-10% ranking metrics, which are more directly tied to a retention outreach budget.

## 5. Feature Importance

The feature-importance plot is stored at `lab3-evidence/feature-importance.png`.

The top three features by gain were:

| Rank | Feature | Gain |
|---:|---|---:|
| 1 | `days_since_last_purchase` | 50.57 |
| 2 | `purchase_frequency_180d` | 36.36 |
| 3 | `purchase_frequency_30d` | 27.45 |

The weakest features by gain were `online_to_store_ratio`, `customer_tenure_days`, and `category_diversity_score`. This supports the interpretation that recency remains the dominant signal, while frequency-window features add measurable lift beyond recency alone.

## 6. Loyalty-Tier Slice Evaluation

Slice evaluation measures performance across loyalty tiers. The detailed results are recorded in `lab3-evidence/slice-evaluation.csv`.

| Loyalty Tier | Test n | Positives | AUC | Recall @ top 10% | Too Small to Conclude? |
|---|---:|---:|---:|---:|---|
| Bronze | 1,071 | 236 | 0.7510 | 0.2881 | No |
| Silver | 1,139 | 278 | 0.7082 | 0.2301 | No |
| Gold | 483 | 104 | 0.7434 | 0.3077 | No |
| Platinum | 307 | 42 | 0.8851 | 0.4762 | No |

The weakest observed tier was **Silver**, with an AUC of **0.7082** and recall of **0.2301**, based on **1,139** test examples and **278** positive examples. Platinum was the strongest slice by both AUC and recall, but it also had the smallest test-set count and only 42 positives, so its high score should not be overinterpreted. No tier was too small for the lab's reliability flag.

## 7. MLflow Experiment Tracking

The supporting evidence files are:

- `lab3-evidence/mlflow-runs.csv`
- `lab3-evidence/mlflow-app.json`

The MLflow App evidence shows at least three finished runs with logged parameters and metrics. The app reuses the Lab 1 S3 bucket under `artifacts/mlflow/` and the `northstar-dev-MLEngineer` role.

## 8. Model Registry

Model Registry evidence is available in `lab3-evidence/model-registry.json`. The latest recorded versions are registered with `PendingManualApproval`, and the metadata for version 3 matches the final evaluation metrics: AUC 0.7779, baseline AUC 0.7229, precision@10% 0.7033, and recall@10% 0.3197.

## 9. Track B RAG Evaluation

The offer-generation pipeline was evaluated with the Track B harness. The October 2026 lab note records lower measured RAGAS values for the reference pipeline than the original rubric targets, so these results are interpreted against the observed reference ranges rather than as deterministic pass/fail gates.

| Dimension | Measured average | Original target | Reference pipeline, measured 2026-10-12 | Result |
|---|---:|---:|---:|---|
| Faithfulness | 0.4352 | >= 0.80 | 0.47-0.68 | Slightly below reference |
| Answer relevance | 0.3377 | >= 0.75 | 0.38-0.45 | Slightly below reference |
| Context recall | 0.5083 | >= 0.70 | 0.53-0.58, ceiling 0.61-0.67 | Slightly below reference |

The scores are close to but mostly below the measured reference ranges. Manual review of the generated examples showed policy-grounded offers with the main remaining risks concentrated around tier verification and incomplete retrieval of the exact supporting policy chunk.

## 10. Limitations

- **Split variability:** Evaluation metrics may vary across train/test splits.
- **Model version:** XGBoost version affects exact metrics; this run used 3.2.0.
- **Baseline comparison:** The paired bootstrap confidence interval quantifies uncertainty in the AUC difference.
- **Slice sample sizes:** Gold and Platinum have fewer examples than Bronze and Silver, so slice conclusions should be monitored with future data.
- **Feature importance:** Importance rankings describe predictive contribution, not causation.
- **RAGAS variability:** The Track B metrics are LLM-judged estimates and can move between runs.

## 11. Conclusion

The full churn prediction model achieved a test AUC of **0.7779**, precision at the top 10% of **0.7033**, and recall at the top 10% of **0.3197**.

The recency-only baseline achieved a test AUC of **0.7229**, resulting in an AUC lift of **0.0550** with a 95% paired-bootstrap confidence interval of **[0.0365, 0.0730]**. The precision and recall requirements were satisfied, and the lift confidence interval excluded zero.

The loyalty-tier analysis identified **Silver** as the weakest observed slice. The Track B offer-generation system produced grounded examples, but the RAGAS scores remain slightly below the measured reference pipeline ranges and should be treated as the main remaining evaluation risk.

## Supporting Evidence

- Training log: `lab3-evidence/train-final.log`
- Evaluation metrics: `lab3-evidence/evaluation_metrics.json`
- Athena query export: `lab3-evidence/athena-query.json`
- Confusion matrix: `lab3-evidence/confusion-matrix.png`
- Feature importance: `lab3-evidence/feature-importance.png`
- Loyalty-tier slice evaluation: `lab3-evidence/slice-evaluation.csv`
- MLflow runs: `lab3-evidence/mlflow-runs.csv`
- MLflow App export: `lab3-evidence/mlflow-app.json`
- Model Registry export: `lab3-evidence/model-registry.json`
- Track B RAGAS results: `lab3-evidence/rag_eval.csv`
