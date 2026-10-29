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

## DataOps Maturity

Current level: 3

Evidence: From a DataOps standpoint, I think this project has a lot of what I would expect a normal data pipeline to have. We have a data contract in `docs/lab2-evidence/lab2-data-contract.md`, and the actual transformation work is in `glue-scripts/transform.py` and `glue-scripts/feature_engineer.py`. What makes it feel more mature now is that the pipeline does not just trust the data because it exists. `tests/test_data.py` checks schema, freshness, leakage risk, transaction grain, bounded feature distributions, and frequency-window logic. The green CI log in `docs/lab4-build-green.log` shows those checks actually ran, including `test_transaction_grain_preserved PASSED` and `test_bounded_features_in_range PASSED`. So the data side is not perfect, but it is being tested in the same pipeline as the model.

Gap to Level 4: In a real busines setting, there would be automated data refresh and drift monitoring. Right now, some upstream work still has to be manually coordinated, especially re-running the Glue/feature jobs before pushing. The pipeline checks freshness, but it is not continuously watching production data drift after deployment.

Top priority investment: Add an EventBridge schedule or S3 event trigger that runs the Glue transform and feature jobs automatically, then publish freshness and drift metrics to CloudWatch.

This would make the data layer feel much less manual.

## MLOps Maturity

Current level: 3

Evidence: From an MLOps perspective, I would also put this around level 3 because the model lifecycle is partly automated now. `buildspec.yml` runs the tests, starts the SageMaker pipeline, trains the model, pulls the evaluation metrics, and runs the model and fairness gates. `docs/lab4-build-green.log` shows the model gate passed, including the champion comparison warning `champion v5 auc=0.7855; candidate auc=0.7855`. `docs/lab4-mlflow-runs.txt` shows four MLflow App runs with different hyperparameters and metrics, so we are not just relying on the auto-created SageMaker Experiments. `docs/lab4-model-package.json` also shows model package v8 has lineage metadata like the training data S3 URI, training timestamp, commit SHA, and metrics. The champion-challenger rule helps keep us from replacing the model just because there is a newer version.

Gap to Level 4: I think what we are missing is: We register and evaluate models, but we do not automatically deploy an approved champion, roll back to the previous champion if a production model fails, or feed live prediction outcomes back into monitoring.

Top priority investment: Add a SageMaker endpoint deployment stage with automatic rollback to the last approved model package, plus a daily batch evaluation job that publishes production AUC to CloudWatch.
