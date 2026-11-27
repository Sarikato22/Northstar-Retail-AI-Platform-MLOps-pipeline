# Task 3: NorthStar Alert Architecture
 
I designed the following alert specification for NorthStar's churn prediction
and offer-generation services. This is a written design, not a claim that
production notification integrations were deployed.
 
## Alert definitions
 
I chose eight alerts across P1–P4, covering all five monitoring layers.
 
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
 
I would evaluate endpoint alerts separately for champion and canary while
each serves traffic. I would treat missing telemetry as unknown rather than
healthy.
 
For CPU, SageMaker reports the sum across vCPUs, so the range is 0 to 200% on
the 2-vCPU instances this platform uses. I chose the reading of "80% of the
whole machine," which is a threshold of 160. Requiring three 5-minute periods
keeps the unreliable first datapoint after an endpoint reaches `InService`
from tripping the alert on its own. I made it P4 because high CPU is an early
warning, and the P2 latency alert pages if users are actually affected.
 
For pipeline failures, I chose Glue job-state events rather than task-failure
counters because a job can fail before its tasks run. For model drift, I used
the same tests and thresholds as my Task 2 plan. For the business layer, a
sharp drop in churn alert volume can mean scoring has stopped or the model's
outputs have shifted, so I made it P3 and would check the pipeline and
endpoint alerts first.
 
The offer-policy check and monitoring-freshness check are proposed production
instrumentation.
 
## Escalation paths
 
I assigned the following notification actions and response targets to each tier.
 
| Tier | Notification and escalation | Acknowledgement target |
|---|---|---|
| P1 | Wake the responsible on-call and page the engineering manager immediately. If unacknowledged after 5 minutes, page the backup on-call. | 5 minutes |
| P2 | Page the responsible on-call. If unacknowledged after 15 minutes, page the backup on-call. | 15 minutes |
| P3 | Post to `#northstar-ml-ops` and create a ticket for the responsible owner. Escalate to the team lead if overdue. | 4 business hours |
| P4 | Create a monitoring-backlog ticket without paging or posting to Slack. Escalate to the monitoring team lead if overdue. | 2 business days |
 
These destinations are proposed role-based routing, not deployed integrations
or real contact details.
 
I would use the read-only `ModelMonitor` role for observation and the
`ModelMonitorExecution` role for running the Evidently processing job.
 
## Suppression rule
 
During an approved model-maintenance window, I would suppress Slack and ticket
notifications from `northstar-model-drift` for the affected endpoint. This
prevents expected changes during a model or baseline update from creating
repeated notifications.
 
I would continue recording drift results and would not suppress other alerts.
The suppression would expire automatically after 60 minutes or when maintenance
ends, whichever comes first.
 
After maintenance, I would run a fresh drift analysis with at least 500 valid
records. If a threshold is still breached, I would send one P3 notification
with the recorded results.