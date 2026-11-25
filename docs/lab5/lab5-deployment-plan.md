## 1. Deployment strategy and rationale
 
We deploy the churn model as a SageMaker real-time endpoint with a canary rollout. Retention decisions happen per customer, so we need low-latency single-record scoring, not just a nightly batch file. The endpoint `northstar-churn-prod` has two variants: `champion` gets 90% of traffic and `canary` gets 10%.
 
We start on `ml.t2.medium` because the lab requires the cheapest instance. It handles everything except autoscaling, which AWS rejects on burstable instances. Then we move both variants to `ml.m5.large` and add autoscaling.
 
If old registry entries lost their S3 artifacts during teardown, rerun the pipeline twice. The first fresh package becomes champion, the second becomes canary. This lab tests rollout controls, not whether the canary is better.
 
## 2. Pre-deployment checklist
 
Run this setup first (every later command uses these names):
 
```bash
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
export ENDPOINT=northstar-churn-prod
export ROLE_ARN=arn:aws:iam::716528268494:role/northstar-dev-MLEngineer
export BUCKET=northstar-dev-data-716528268494
export CHAMPION_MODEL=northstar-churn-prod-champion
export CANARY_MODEL=northstar-churn-prod-canary
```
 
- [ ] Package group `northstar-churn-models` has two fresh packages with live S3 artifacts. If not, run `aws sagemaker start-pipeline-execution --pipeline-name northstar-churn-pipeline` twice.
- [ ] **The ML Engineer approves the candidate package** in the registry. Approve only if the Lab 4 gate shows CI passed, AUC above baseline, top-10 precision and recall present, and no customer slice with a material regression.
- [ ] `deployment/configs/` contains `endpoint-config-canary-t2.json`, `endpoint-config-canary-m5.json`, `rollback-alarm.json`, and `autoscaling-target-tracking.json`.
- [ ] No leftover endpoint: `aws sagemaker list-endpoints --name-contains northstar` returns nothing.
## 3. Deploy steps
 
1. Select the two latest approved package ARNs. The older one becomes champion and the newer one becomes canary:
```bash
PACKAGE_ARNS=($(aws sagemaker list-model-packages \
  --model-package-group-name northstar-churn-models \
  --model-approval-status Approved \
  --query 'sort_by(ModelPackageSummaryList,&CreationTime)[-2:].ModelPackageArn' \
  --output text))
export CHAMPION_PACKAGE_ARN=${PACKAGE_ARNS[0]}
export CANARY_PACKAGE_ARN=${PACKAGE_ARNS[1]}
printf 'Champion: %s\nCanary: %s\n' "$CHAMPION_PACKAGE_ARN" "$CANARY_PACKAGE_ARN"
```

2. Create both SageMaker models. Names must match the endpoint configs:
```bash
aws sagemaker create-model \
  --model-name $CHAMPION_MODEL \
  --execution-role-arn $ROLE_ARN \
  --primary-container ModelPackageName=$CHAMPION_PACKAGE_ARN
aws sagemaker create-model \
  --model-name $CANARY_MODEL \
  --execution-role-arn $ROLE_ARN \
  --primary-container ModelPackageName=$CANARY_PACKAGE_ARN
```

3. Create the endpoint config and endpoint (two variants, 90/10, `ml.t2.medium`):
```bash
aws sagemaker create-endpoint-config --cli-input-json file://deployment/configs/endpoint-config-canary-t2.json
aws sagemaker create-endpoint --endpoint-name $ENDPOINT --endpoint-config-name northstar-churn-prod-canary-t2
aws sagemaker wait endpoint-in-service --endpoint-name $ENDPOINT
```

4. Create the rollback alarm: `aws cloudwatch put-metric-alarm --cli-input-json file://deployment/configs/rollback-alarm.json`

5. Create a sample row, then smoke test one record. It must return a score between 0 and 1:
```bash
printf '12,410,3,8,19,86.40,742.18,3880.00,3.2,0.64,0.72\n' > /tmp/lab5-sample.csv
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name $ENDPOINT \
  --content-type text/csv \
  --body fileb:///tmp/lab5-sample.csv \
  /tmp/lab5-out.txt
cat /tmp/lab5-out.txt
```

6. Send 100 invocations and count where they landed:
```bash
for i in $(seq 100); do
  aws sagemaker-runtime invoke-endpoint \
    --endpoint-name $ENDPOINT \
    --content-type text/csv \
    --body fileb:///tmp/lab5-sample.csv \
    --query InvokedProductionVariant \
    --output text \
    /tmp/lab5-out.txt
done | sort | uniq -c
```

7. Move to `ml.m5.large` and attach autoscaling. If quota is pending, capture the quota status and `ml.t2.medium` rejection instead.
```bash
aws sagemaker create-endpoint-config --cli-input-json file://deployment/configs/endpoint-config-canary-m5.json
aws sagemaker update-endpoint --endpoint-name $ENDPOINT --endpoint-config-name northstar-churn-prod-canary-m5
aws sagemaker wait endpoint-in-service --endpoint-name $ENDPOINT

for VARIANT in champion canary; do
  aws application-autoscaling register-scalable-target \
    --service-namespace sagemaker \
    --resource-id endpoint/$ENDPOINT/variant/$VARIANT \
    --scalable-dimension sagemaker:variant:DesiredInstanceCount \
    --min-capacity 1 \
    --max-capacity 2
  aws application-autoscaling put-scaling-policy \
    --policy-name northstar-churn-$VARIANT-target-tracking \
    --service-namespace sagemaker \
    --resource-id endpoint/$ENDPOINT/variant/$VARIANT \
    --scalable-dimension sagemaker:variant:DesiredInstanceCount \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration file://deployment/configs/autoscaling-target-tracking.json
done
```
## 4. Rollback criteria
 
| Item | Value |
|---|---|
| Alarm | `northstar-churn-rollback-model-latency-canary` |
| Metric | `AWS/SageMaker` `ModelLatency`, variant `canary` |
| Threshold | Average above `200000` microseconds (200 ms) for 2 consecutive 1-minute periods |
| Also roll back if | Smoke tests show invocation errors or clearly invalid predictions |
| Who decides | The ML Engineer. If the alarm fires, they roll back without waiting for approval |
 
```bash
aws sagemaker update-endpoint-weights-and-capacities --endpoint-name $ENDPOINT --desired-weights-and-capacities VariantName=canary,DesiredWeight=0 VariantName=champion,DesiredWeight=1
```
 
Then rerun the 100-call loop. Zero canary invocations means the rollback worked.
 
## 5. Monitoring window
 
Production uses 48 hours. The lab compresses this to 60 minutes to control cost. A real window catches daily traffic cycles, delayed latency spikes, scaling under real load, and slow data anomalies.
 
Watch the alarm state (`aws cloudwatch describe-alarms --alarm-names northstar-churn-rollback-model-latency-canary`), the endpoint status, and the traffic split.
 
**Clean means:** endpoint stays `InService`, alarm stays `OK` the whole window, the 100-call count shows both variants near 90/10, and there are no invocation errors.
 
## 6. Stakeholder notifications
 
| Stage | Data science owner | Platform owner |
|---|---|---|
| Deployment start | Endpoint name, 90/10 split, window length | Same, plus instance type |
| Promotion | Readiness note with observed traffic split | Same |
| Rollback | Alarm state and rollback command | Same, plus post-rollback count showing zero canary calls |
 
The ML Engineer sends all three.
 
## 7. Post-deployment review
 
Held after the window closes. The ML Engineer, data science owner, and platform owner attend. The artifact is this plan plus `docs/lab5-deployment-output.txt`, with endpoint, traffic split, autoscaling, alarm, and rollback evidence.
 
## 8. Resource cleanup
 
Rollback is not cleanup. A variant at weight 0 still bills for its instance. After the review, run:
 
```bash
bash scripts/teardown-lab5.sh
```
 
It deletes scaling policies and targets, rollback alarms, the endpoint, endpoint configs, SageMaker models, and running processing or transform jobs. It writes `docs/lab5-teardown-output.txt`. Cleanup is verified when that file shows no active endpoints, endpoint configs, or scaling targets.
 
