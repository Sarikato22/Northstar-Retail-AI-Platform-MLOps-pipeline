# Lab 4 MLOps Assessment

## Champion-Challenger

A challenger model replaces the current champion only if all of these are true:

- `challenger_auc_roc >= champion_auc_roc + 0.02`
- `precision_top10 >= 0.50`
- `recall_top10 >= 0.25`
- the 95% confidence interval for `(challenger_auc_roc - baseline_auc)` has `lift_ci_low > 0`

This makes the promotion decision binary. If the challenger does not beat the champion by at least 0.02 AUC, it stays `PendingManualApproval` and the current champion remains active.

## Retraining Triggers

Scheduled trigger:

- AWS service: Amazon EventBridge Scheduler
- Schedule expression: `cron(0 9 ? * MON *)`
- Action: start `northstar-pipeline` once per week on Monday at 09:00 UTC.

Performance trigger:

- AWS services: SageMaker Model Monitor or a daily batch evaluation job publishes `ProductionAUC` to CloudWatch; a CloudWatch alarm watches the metric; EventBridge starts `northstar-pipeline` when the alarm enters `ALARM`.
- Threshold: retrain when `ProductionAUC < 0.76` for 2 consecutive daily evaluation periods.

## Experiment Tracking

Experiment tracking evidence is saved in `docs/lab4-mlflow-runs.txt`. It uses the SageMaker MLflow App from Lab 3, not the SageMaker Pipeline auto-created Experiments.

## Model Lineage

Model package lineage evidence is saved in `docs/lab4-model-package.json`. Version 8 has customer metadata for the training data S3 URI, training timestamp, commit SHA, and evaluation metrics.
