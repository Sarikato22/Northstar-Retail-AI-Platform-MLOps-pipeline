# NorthStar Retail AI Platform

NorthStar Retail AI Platform is an AWS-based MLOps project for a simulated retail company, built around the full lifecycle of customer churn prediction and retention-offer generation. It combines cloud infrastructure, data engineering, feature management, model training, model governance, and retrieval-augmented generation into one evolving platform.

The project demonstrates:

- Terraform-managed AWS infrastructure for networking, storage, IAM, and SageMaker.
- Glue ETL pipelines that clean raw retail transaction data and produce churn-ready customer features.
- SageMaker Feature Store integration with both online and offline feature access.
- XGBoost churn modeling with evaluation artifacts, model registry evidence, and reproducible training outputs.
- Bedrock-powered RAG for generating grounded customer retention offers from policy documents.
- CI/CD foundations for data tests, feature tests, model quality gates, and SageMaker pipeline automation.

The sections below track the implementation details, verification evidence, and commands used as the platform is built out across phases.

This repository currently covers the platform foundation, data and feature pipeline, churn prediction workflow, and RAG-based retention-offer generation.

## Lab 3 Tracks

- **Track A:** XGBoost churn prediction using the Lab 2 SageMaker Feature Store offline store.
- **Track B:** Retention-offer generation with Bedrock, Titan embeddings, local FAISS, and Claude Haiku 4.5.

## Train The Churn Model

Training is handled by `churn_training_skeleton.py`. The script reads training data from the Feature Store offline store through Athena, writes Athena results under the Lab 1 data bucket's `artifacts/athena-results/` prefix, trains XGBoost locally, evaluates the model, and can register the model package as `PendingManualApproval`.

Example:

```bash
python churn_training_skeleton.py \
  --feature-group-name northstar-dev-customer-features \
  --artifacts-bucket northstar-dev-data-716528268494 \
  --max-depth 6 \
  --eta 0.1 \
  --num-round 200 \
  --min-child-weight 5 \
  --subsample 0.8 \
  --colsample-bytree 0.8 \
  --register-model
```

The final submitted run is captured in `docs/lab3-evidence/train-final.log`. Its model metrics are saved in `docs/lab3-evidence/evaluation_metrics.json`, with plots in `docs/lab3-evidence/confusion-matrix.png` and `docs/lab3-evidence/feature-importance.png`.

## Evaluate Track B

The RAG implementation lives in `rag/offer_gen.py`. It indexes the policy documents in `northstar-policy-docs/` using Titan Embeddings and FAISS, retrieves the top policy chunks, and generates a 2-3 sentence retention offer with Claude Haiku 4.5.

The saved Track B evidence is:

- `docs/lab3-evidence/track-b-examples.md` - five input/output examples, retrieved chunk IDs, and two failure cases with fixes.
- `docs/lab3-evidence/rag_eval.csv` - output from the Track B evaluation harness.
- `notebooks/lab3-demo.ipynb` - runnable demo notebook with saved outputs.

## Reports And Evidence

Primary Lab 3 writeups:

- `docs/lab3-model-design.md`
- `docs/lab3-evaluation-report.md`

Supporting AWS exports and evidence:

- `docs/lab3-evidence/mlflow-app.json`
- `docs/lab3-evidence/mlflow-runs.csv`
- `docs/lab3-evidence/model-registry.json`
- `docs/lab3-evidence/athena-query.json`
- `docs/bedrock-access-verification.txt`

The MLflow App uses the Lab 1 bucket and role:

- Artifact store: `s3://northstar-dev-data-716528268494/artifacts/mlflow/`
- Role: `arn:aws:iam::716528268494:role/northstar-dev-MLEngineer`

## Teardown

Lab 3 teardown evidence is in `docs/lab3-teardown-output.txt`. It verifies there are no SageMaker endpoints, endpoint configs, running training jobs, running processing jobs, expensive MLflow Tracking Servers, or AgentCore resources left running. The MLflow App is intentionally kept because it is serverless and reused by later labs.
