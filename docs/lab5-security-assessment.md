# Lab 5 Security Assessment
 
## Task 3a:
 
| Threat | STRIDE | Likelihood | Impact | Mitigation | AWS Control |
|---|---|:-:|:-:|---|---|
| Someone uses a data engineering login to call the churn endpoint. | Spoofing | L | H | The Lab 2 role split contains this. DataEngineer has no sagemaker:InvokeEndpoint, so that login can't score customers. Only MLEngineer and deployment automation can invoke. | IAM policies scoped to the endpoint, CloudTrail data events for SageMaker endpoints |
| The approved model file in S3 gets swapped before deployment. | Tampering | L | H | Deploy only from approved Model Registry packages, and only MLEngineer can write to artifacts/. | SageMaker Model Registry approval status, S3 versioning |
| A teammate says they never changed the canary traffic weights. | Repudiation | L | M | Do deploys and rollbacks under named IAM roles and keep the CLI output always. | CloudTrail management events, CloudWatch alarm history |
| Someone authorized sends a huge number of queries to guess who was in the training data. | Information Disclosure | M | H | This is a gap Lab 2 roles don't address. IAM controls who can call the endpoint, but not what an allowed user does with unlimited queries. I'd add per-caller limits. | API Gateway usage plan, CloudWatch anomaly detection |
| Threat	STRIDE	Likelihood	Impact	Mitigation	AWS Control
Too much traffic at once (a spike or someone’s load test) crashes the endpoint, so we can’t score customers during a campaign. | Denial of Service | M | M | Run it on ml.m5.large and turn on autoscaling so AWS adds instances when traffic jumps. I also want an alarm for when responses get slow. ml.t2.medium can’t use autoscaling, so it’s not an option for production | Application Auto Scaling, CloudWatch alarm on ModelLatency |
| The deployment role gets broad S3 access and can read raw customer PII. | Elevation of Privilege | M | H | Keep policies scoped to prefixes. MLEngineer gets artifacts/ and features/, and raw data stays with DataEngineer. | IAM least-privilege policies, IAM Access Analyzer |
 
## Task 3b: Data Classification
 
| Data Asset | Tier | Encryption | IAM Access | Share with Vendor? |
|---|---|---|---|---|
| Customer PII | Restricted | SSE-KMS (key control and audit trail) | DataEngineer writes. MLEngineer and ModelMonitor don't read it. | No, unless there's a data processing agreement |
| Transaction history | Restricted | SSE-KMS (personal data used for profiling) | DataEngineer manages. MLEngineer reads approved training prefixes. | Only with an approved processor |
| Behavioral clickstream | Restricted | SSE-KMS (linked to customer ID, so personal data) | DataEngineer ingests. MLEngineer uses derived features. | No raw sharing |
| Product catalog | Public | SSE-S3 (no personal data) | Broad read, write by data platform owners | Yes |
| Model weights | Confidential | SSE-KMS (business logic, want audit trail) | MLEngineer writes and deploys. Others read only. | No |
| Inference logs | Restricted | SSE-KMS (can contain customer feature values) | MLEngineer and monitoring workflows | No raw sharing |
| Feature Store records | Restricted | SSE-KMS (derived customer profiles) | DataEngineer writes. MLEngineer reads. | Only with an approved processor |
 
## Task 4: Privacy Impact Assessment
 
### Personal data inventory
 
- **Raw S3 data:** customer_id, loyalty tier, purchase and transaction history, and behavioral fields like online-to-store ratio.
- **Glue:** turns the raw data into model features.
- **Feature Store:** customer-level feature vectors for training and inference.
- **Training:** reads the curated features and writes model artifacts.
- **Endpoint and logs:** the endpoint receives feature rows, and data capture and logs may keep payloads and predictions.
### Lawful basis
 
I'd go with legitimate interests. Churn prediction is about keeping customers, which is a normal business reason, and customers would expect a store to use their purchase history for that. It doesn't use sensitive categories of data either. It needs a documented balancing test first.
 
Contract doesn't fit because a sale doesn't depend on a churn score. Consent is awkward because people can withdraw it, and the model needs consistent historical data.
 
### Data minimization
 
The model only needs behavior summaries like recency, frequency, monetary value, and loyalty tier. I left out names, emails, phone numbers, addresses, payment card data, free-text notes, and demographics like age, gender, or health. We keep customer_id as a pseudonymous key and store the mapping separately.
 
### Right to erasure workflow
 
For customer_id = C00123456:
 
1. **Raw S3 data:** find the objects that contain the ID, rewrite them without that customer's rows, and delete the old versions.
2. **Feature Store:** for the online store, delete the record so inference can't use it. The offline store is append-only history in S3, so the old rows have to be removed or rewritten separately, and future training queries should exclude the ID.
3. **Training data:** remove the customer from the curated datasets and exclude them from the next retraining run.
4. **Inference logs:** search data capture and CloudWatch logs for the ID and delete the matching records.
The hardest step is the trained model. It isn't a database row, so there's nothing to delete. The customer's data is baked into the learned parameters, and the real fix is retraining without them. The offline Feature Store is close behind because its history can't be deleted with one call.
 