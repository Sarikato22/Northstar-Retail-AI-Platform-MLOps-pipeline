# Lab 4 Task 2 Pipeline Rationale

This project uses GitHub as the source repo and AWS CodePipeline for the CI/CD
pipeline. I chose CodePipeline because the rest of the workflow is already in
AWS: CodeBuild runs the tests, SageMaker runs training, SageMaker Model
Registry stores model packages, and CloudWatch/SNS handle failure alerts.

The pipeline maps the required phases this way:

- Source: GitHub push to `main` starts `northstar-pipeline`.
- Test: CodeBuild runs `pytest` for data and feature tests before training.
- Build: CodeBuild upserts and starts the SageMaker Pipeline, which runs the
  SageMaker Training Job using `models/churn/train_sagemaker.py`.
- Evaluate: CodeBuild downloads `evaluation_metrics.json` and runs
  `tests/test_model.py` plus `tests/test_fairness.py`.
- Register: the SageMaker Pipeline registers the trained model in
  `northstar-churn-models` with `PendingManualApproval`.

If training or a gate fails, the build fails. If a model package was registered
before a later test failed, `buildspec.yml` marks that package `Rejected`.
The `northstar-ci-build-failure` CloudWatch alarm watches CodeBuild failures
and notifies the `northstar-model-approvals` SNS topic.
