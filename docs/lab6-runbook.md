## Task 2: Drift Detection Plan

### 1. Likely drift types

I expect data drift to be the most likely short-term change for NorthStar. Holiday promotions could increase purchase frequency and reduce the number of days since a customer's last purchase. Catalog changes could affect the variety of products customers buy, while economic changes could lead to lower spending and longer gaps between purchases. I would consider these changes in the model's inputs, rather than assuming they mean the model is becoming less accurate.

I also think concept drift is possible if the relationship between customer behavior and churn changes over time. For example, a purchase during a holiday promotion might not be as strong of a sign of customer loyalty as it was before. This could mean that recent purchases become a weaker predictor of retention than they were during training.

I would keep these types of drift separate from actual model degradation. A change in the input data does not automatically mean the model is performing worse. Once the full 90-day churn labels are available, I would check Recall@10% to see whether the model is still identifying customers who are likely to churn.

### 2. Statistical tests chosen

I used the frozen Lab 2 feature export in `monitoring/baseline/baseline.csv` as my baseline. I treated it as a fixed reference snapshot instead of a rolling calendar window, while keeping each feature's original lookback period.

For comparison, I chose the captured inference inputs from the champion variant. For ongoing monitoring, I would use the most recent completed scoring window with at least 500 valid records. If there were fewer than 500 records, I would report insufficient data instead of assuming there was no drift.

| Feature | Test I chose | Baseline window I used | Drift threshold I chose |
|---|---|---|---|
| `days_since_last_purchase` | PSI | Frozen Lab 2 reference snapshot | Statistic > 0.20 |
| `purchase_frequency_180d` | PSI | Frozen Lab 2 reference snapshot | Statistic > 0.20 |
| `purchase_frequency_30d` | PSI | Frozen Lab 2 reference snapshot | Statistic > 0.20 |
| `category_diversity_score` | KS | Frozen Lab 2 reference snapshot | p-value < 0.05 |
| `total_spend_90d` | KS | Frozen Lab 2 reference snapshot | p-value < 0.05 |

I used PSI to measure changes in recency and purchase frequency, and KS to check for changes in category diversity and spending. I would flag drift if PSI goes above 0.20 or if the KS p-value falls below 0.05.

I would keep these tests and thresholds consistent with `DRIFT_PLAN` in `monitoring/evidently_drift.py`. If a threshold were reached, I would first look into possible data quality issues or business changes before deciding whether retraining is needed.

### 3. Concept drift detection

While waiting for the full 90-day churn labels, I would monitor the seven-day retention-offer redemption rate among customers contacted in the model's highest-risk 10%. I would calculate it as:

`redemption rate = customers redeeming within 7 days / customers successfully delivered an offer`

I would compare this rate with results from previous similar campaigns. I chose this measure because a drop in redemption could be an early sign that the model's targeting is becoming less effective, even before the actual churn labels are available.

There would be a seven-day waiting period after the offer is delivered, plus additional time for data processing. However, I would not assume that a lower redemption rate automatically means concept drift. Other factors, such as offer quality, inventory, or seasonal changes, could also affect the results. I would look into these possible causes and then use the 90-day churn labels to confirm whether the model's performance has actually gotten worse.

## Task 4: SLO Design

I would measure the request SLOs over a rolling 30-day window. I am considering a ficticious traffic of 1000,000 requests per month as an example. For quality and fairness, I would require every valid weekly evaluation to pass, giving each a zero-failure budget.

| SLO | Target | SLI (Good Events / Total Events) | Error Budget | Deployment Freeze Trigger |
|---|---|---|---|---|
| Availability | 99.5% | Successful predictions / total requests | 0.5% of monthly requests: **500 failed requests/month** at 100,000 requests | Freeze model and configuration promotions when failed requests exceed 0.5% of requests in the rolling 30-day window. |
| Latency (p95) | **< 20 ms** (`ModelLatency` ≤ `20000`) | Requests completing < 20 ms / total requests | 5% of monthly requests: **5,000 slow or failed requests/month** at 100,000 requests | Freeze promotions when more than 5% of requests fail or take at least 20 ms in the rolling 30-day window. |
| Prediction Quality | Recall@10% ≥ 0.25 on weekly sample | Weekly sample passing threshold / total weekly samples | **0 failed weekly evaluations/month** | Freeze promotions after any valid weekly sample has Recall@10% < 0.25. |
| Fairness | Recall gap across loyalty tiers ≤ 10pp | Weeks within fairness threshold / total weeks | **0 failed weekly evaluations/month** | Freeze promotions after any valid weekly evaluation has a maximum tier recall gap > 0.10. |

## Task 5: Failure Runbooks
## Runbook: Data Drift on days_since_last_purchase
 
### Detection
- Alert: `northstar-model-drift` (P3) fires when `DriftDetected` = 1, meaning PSI > 0.2 on `days_since_last_purchase`.
- Confirm in `drift_violations.json`: `captured_records` >= 500, `underpowered_window` is false, and PSI for the feature is above 0.2.
- Secondary signals: `purchase_frequency_30d` or `purchase_frequency_180d` also flagged, and a holiday promotion or catalog change in the last few days.
### Triage (< 5 minutes)
- Step 1: Download the latest `drift_violations.json` from `s3://<bucket>/monitoring/reports/<job>/` and record the job name, record count, and PSI in the ticket.
- Step 2: Check the job output for the duplicate-payload line from `load_capture`. If a large number of rows were dropped, test traffic may be distorting the window.
- Step 3: Check the last three runs of `northstar-dev-transform` and `northstar-dev-feature-engineer` for failures or changed row counts.
- Step 4: Ask the campaign owner whether a promotion or catalog change started around when drift first appeared.
### Containment Options
- Option A: Roll back the cause. Choose this when drift starts right after a pipeline or model change. Pause the pipeline or promotion, restore the last approved version, and regenerate the features before scoring resumes.
- Option B: Graceful degradation. Choose this when the shift is real customer behavior or no safe fix is available yet. Pause new automated personalized retention offers and have the campaign owner send an existing generic offer or hold the campaign for manual review. Keep capturing data and running drift jobs. Do not replace the baseline to clear the alert.
### Escalation
- Trigger for escalating beyond on-call: PSI is still above 0.2 on the next run after containment, or a campaign is due within 60 minutes and targeting cannot be confirmed safe, or customers have already received offers based on drifted features.
- Who is paged: ML team lead, plus the data engineering lead if the pipeline is the cause.
- SLA for response: 30 minutes.
### Resolution Verification
- Run a new drift job on at least 500 distinct records captured after the fix.
- `days_since_last_purchase` PSI must be <= 0.2 and all other monitored features must pass their tests.
- After the publisher runs, `DriftDetected` must be 0 and `northstar-model-drift` must be in `OK`. A failed job or missing data is not recovery.
### Post-Incident Actions
- Within 24 hours: attach the before and after reports to the ticket, write down the root cause, and decide with the ML owner whether to retrain or review the baseline.
- Postmortem required: yes if incorrect offers reached customers, a campaign was missed, or the same cause recurs within 30 days. Otherwise close the ticket with the notes above.
## Runbook: Inference Latency Spike
 
### Detection
- Alert: `northstar-application-latency` fires when `ModelLatency` p95 > 500000 microseconds (500 ms) for more than 5 minutes (6 consecutive 1-minute periods), with at least 20 invocations per minute.
- Secondary signals: `Invocation5XXErrors` rising, `CPUUtilization` or `MemoryUtilization` climbing on the same variant, and caller timeouts or retries.
- Ignore the first few minutes after a deploy. Cold start runs about 6x slower (~24,000 microseconds) and is not an incident.
### Triage (< 5 minutes)
- Step 1: Pull `ModelLatency` p95 for champion and canary separately and note which variant is slow, or whether both are.
- Step 2: Run `describe-endpoint` and check the status and when the config last changed. Note any traffic weight change in the last 30 minutes.
- Step 3: Check `Invocations`, `Invocation5XXErrors`, `CPUUtilization` (0 to 200% on a 2-vCPU instance), and `MemoryUtilization` for the slow variant.
- Step 4: Check the endpoint log group in CloudWatch for errors or restarts.
### Containment Options
- Option A: Roll back. Choose this when the spike started with a deploy. If only canary is slow, set canary weight to 0 so champion takes all traffic. If both are slow after a config change, switch back to the previous endpoint config. Weight 0 does not stop billing, so delete the canary variant once the incident is closed.
- Option B: Graceful degradation. Choose this when neither variant can serve current load. Pause nonessential scoring and retry loops, defer the retention campaign, and keep pending requests so they can be replayed after recovery. Send a generic offer or use manual review for time-sensitive customers. Do not return default or made-up churn scores.
### Escalation
- Trigger for escalating beyond on-call: p95 is still above 500000 microseconds 15 minutes after containment, or `Invocation5XXErrors` exceed 5% for two consecutive 5-minute periods (treat that as P1).
- Who is paged: platform lead for the latency case, engineering manager for the P1 case.
- SLA for response: 15 minutes for the platform lead, 5 minutes for the P1 page.
### Resolution Verification
- p95 `ModelLatency` must be under 20000 microseconds (20 ms) for five consecutive 1-minute periods on every variant still serving traffic, with at least 20 invocations per minute and zero `Invocation5XXErrors`.
- `northstar-application-latency` must return to `OK`.
- After a rollback or redeploy, discard the first datapoint. It will read near 24,000 microseconds from cold start and does not mean recovery failed.
### Post-Incident Actions
- Within 24 hours: write up the timeline, which variant was affected, the latency and error graphs, and any delayed campaigns. Clean up the canary variant if it was rolled back, and add a load or warm-up check for the confirmed cause.
- Postmortem required: yes if the incident reaches P1, a campaign was delayed, or p95 stayed above 500 ms for 30 minutes or more. Otherwise record cause and fix in the ticket.
 