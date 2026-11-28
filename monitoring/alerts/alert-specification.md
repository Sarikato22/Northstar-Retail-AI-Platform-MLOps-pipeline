# Task 3: NorthStar Alert Architecture

P1 is the highest priority and P4 is the lowest. My team uses Slack to communicate. I used the Lecture 21 sample table for the response times and channels below.

## Alert definitions
 
| Alert name | Tier | Trigger | Responsible owner |
|---|---|---|---|
| `northstar-endpoint-unavailable` | P1 | SageMaker invocation 5XX error rate > 5% for two consecutive 5-minute periods, with at least 20 invocations per period | Platform on-call |
| `northstar-offer-policy-violation` | P1 | At least one generated offer fails a confirmed entitlement or policy check | Offer service on-call and loyalty-policy owner |
| `northstar-application-latency` | P2 | `ModelLatency` p95 > 200000 microseconds (200 ms) for two consecutive 1-minute periods, with at least 20 invocations per period | Platform on-call |
| `northstar-pipeline-failure` | P3 | A transform or feature-engineering Glue job enters `FAILED`, `ERROR`, or `TIMEOUT` | Data engineering |
| `northstar-model-drift` | P3 | A valid drift analysis with at least 500 captured records reports PSI > 0.20 or KS p-value < 0.05 for a monitored feature | ML engineer |
| `northstar-churn-volume-drop` | P3 | Daily `ChurnAlertVolume` is more than 30% below its trailing 7-day average on a day when scoring traffic is expected | ML engineer and campaign owner |
| `northstar-endpoint-cpu` | P4 | `CPUUtilization` average > 160 for three consecutive 5-minute periods on a variant | Platform on-call |
| `northstar-monitoring-stale` | P4 | No successful, adequately powered drift result for more than 26 hours when daily monitoring is expected and sufficient scoring traffic exists | ML monitoring owner |

## Escalation paths

| Tier | Example condition | Response ? channel |
|---|---|---|
| P1 Critical | Endpoint unavailable or offer-policy check fails | Immediate  page the responsible on-call and engineering manager |
| P2 High | Inference latency exceeds the alert threshold | Within 1 hour  Slack message in `#northstar-ml-ops` + ticket assigned to the alert owner |
| P3 Medium | Moderate model drift, a failed Glue job, or a drop in churn-alert volume | Within 24 hours ticket assigned to the alert owner |
| P4 Low | Sustained high CPU without user impact or a stale monitoring result | Weekly review dashboard and monitoring backlog |


## Suppression rule

During approved model maintenance, suppress only `northstar-model-drift` P3 ticket notifications for the affected endpoint. Keep recording results and leave all other alerts active. Suppression ends after 60 minutes or when maintenance ends, whichever comes first.

After maintenance, run a fresh comparison with at least 500 valid records. If drift is still present, send one P3 notification with the results.
