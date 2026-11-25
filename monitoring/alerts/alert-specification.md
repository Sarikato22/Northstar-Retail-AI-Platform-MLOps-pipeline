# Task 3: NorthStar alert architecture

This is the written alert specification permitted by Task 3. It covers churn
prediction and offer generation. Task 1's alarms had actions disabled; they
and the endpoint were deleted during teardown. The production routing,
additional instrumentation and suppression below are a design, not claims of
deployed integrations or messages sent.

## Metrics and evaluation conventions

- Endpoint: `northstar-churn-prod`, with `EndpointName` and `VariantName`
  dimensions on endpoint metrics. The lab monitored champion; production
  evaluates champion and canary separately while each is serving traffic.
- Native latency is `AWS/SageMaker/ModelLatency`, in **microseconds**.
  Endpoint CPU is `/aws/sagemaker/Endpoints/CPUUtilization`, a per-core sum.
- Existing custom namespaces are `NorthStar/ChurnModel` and
  `NorthStar/Pipeline`. Drift and business metrics use `EndpointName`.
  The lab pipeline event metrics aggregate the transform and feature jobs;
  production incident details must retain the job name and run ID.
- Proposed offer metrics and freshness checks below require production
  instrumentation. They were not run as part of Task 1.
- Only evaluate traffic-based rates/percentiles when the stated sample is
  present. Missing telemetry is unknown, not a successful request or a zero
  business count. Planned shutdown is a maintenance state, not an outage.

## Alert definitions

Each row inherits the routing and acknowledgement target for its severity tier
in the following section. Names all contain `northstar` so discovery and
teardown can find them.

| Alert name | Tier | Metric and exact trigger | Evaluation and owner |
|---|---|---|---|
| `northstar-endpoint-unavailable` | P1 | `AWS/SageMaker/Invocation5XXErrors` Sum / `Invocations` Sum > 0.05, with at least 20 invocations in each period | Two consecutive 5-minute periods during scheduled service. Exclude client-caused 4XX errors. Platform on-call owns restoration; model serving engineer assists. Proposed production alarm. |
| `northstar-offer-policy-violation` | P1 | Proposed `NorthStar/Offers/ConfirmedPolicyViolationCount` Sum > 0 | One 5-minute period. A confirmed violation means a generated offer fails a deterministic entitlement/policy check, such as a prohibited loyalty-tier benefit; do not count an unverified LLM suspicion as confirmation. Gate the offer before delivery. Offer service on-call and loyalty-policy owner investigate. |
| `northstar-application-latency` | P2 | `AWS/SageMaker/ModelLatency` p95 > **200000 microseconds** (200 ms) | Two consecutive 1-minute periods, each with at least 20 invocations. Platform on-call owns it. Two periods limit sensitivity to a single cold-start interval. |
| `northstar-infrastructure-cpu` | P2 | `/aws/sagemaker/Endpoints/CPUUtilization` Average > **80** | Three of three consecutive 5-minute periods. Platform on-call owns it. This uses the reported per-core sum: 80 is 40% of a two-vCPU machine's total capacity, a conservative threshold. It does not mean 80% of the whole instance. Three periods prevent one anomalous startup datapoint from paging. |
| `northstar-offer-latency` | P2 | Proposed `NorthStar/Offers/EndToEndLatencyMs` p95 > **2000 milliseconds** | Three consecutive 1-minute periods with at least 20 completed offer requests each. Measure the entire retrieval-and-generation request, not churn endpoint latency. Offer service on-call owns the 2-second response requirement. |
| `northstar-pipeline-failure` | P3 | `NorthStar/Pipeline/JobFailed` Sum > 0 from a Glue `FAILED`, `ERROR` or `TIMEOUT` state event | One 5-minute period. Data engineering owns it. Include transform and feature-engineering jobs; group duplicates by job run ID. Task counters alone can miss a driver-level S3 failure. Escalate immediately to P2 if the next Monday 6 AM ET scoring deadline is within one hour and no valid replacement feature set is available. |
| `northstar-model-drift` | P3 | `NorthStar/ChurnModel/DriftDetected` Maximum > 0 | One completed, valid analysis with >=500 distinct captured predictions. The publisher sets this flag if any planned PSI > 0.20 or KS p-value < 0.05. ML engineer owns feature plots, capture quality and business-context review; an input breach alone does not authorize retraining. |
| `northstar-business-volume-drop` | P3 | `NorthStar/ChurnModel/ChurnAlertVolume` daily snapshot < 0.70 times the mean of the preceding seven completed daily snapshots | Evaluate the completed UTC day after publication, with a proposed 02:00 UTC deadline. Retention analytics owns interpretation; ML engineer checks scoring. Require all seven reference days and a positive reference mean. Compare the day's `Maximum` snapshot with `ChurnAlertVolume7DayAverage`; never sum repeated snapshots. Missing history stays insufficient, while an explicitly published zero is valid data. |
| `northstar-monitoring-stale` | P4 | Proposed `NorthStar/ChurnModel/FreshDriftResultAgeHours` Maximum > **26** | One hourly check while a daily production drift result is expected and sufficient scoring traffic exists. A separate freshness checker computes age from the last successful, adequately powered result's timestamp; a failed or underpowered job does not reset it. Create a ticket for the ML monitoring owner. If stale for another 24 hours, escalate to P2. A missing checker heartbeat for two hours also escalates to P2. |

The availability sample guard avoids dividing by zero or paging on a single
failed request in a tiny sample. For low-traffic production periods, propose a
synthetic inference check every minute: five consecutive failures during
scheduled service trigger the same P1 incident. This is additional production
instrumentation, not a timer left running in the lab account.

The lab business proxy counts sampled customers with score >=0.5; its current
observed value was **274**. A production publisher must count unique customers
meeting the same alert definition over each complete day, then publish a final
snapshot, including zero when scoring completed but nobody qualified. Repeated
publication of the same snapshot is idempotent under `Maximum`. Do not compare
an incomplete day with seven full days or substitute the top-decile campaign
size for this fixed-score proxy. Publish a separate scoring-completion signal
so missing data cannot be mistaken for zero. If the prior mean is zero, raise a
data-review ticket rather than divide by zero.

The TA clarified that collecting seven days is not required for the lab.
The seven-day mean describes this production alert's behavior. NorthStar's
weekly scoring cadence will naturally create quiet days, so production review
must consider campaign timing, successfully scored customer volume and holidays
before interpreting a daily decline as lost retention demand. The alert is an
investigation signal, not evidence that customers stopped churning.

## Escalation and response

These are role-based proposed production destinations, not real contact details.
The incident router attaches the alarm name, model/version or job run ID,
threshold, observed value, dashboard link and relevant runbook to each incident.

| Tier | Required action and destination | Acknowledgement target | Further escalation |
|---|---|---|---|
| P1 | Wake the platform/service on-call and page the engineering incident manager immediately; open an incident record | 5 minutes, 24/7 | If unacknowledged at 5 minutes, page the backup on-call and engineering manager. The incident manager coordinates service and policy owners. |
| P2 | Page the responsible service on-call and open a linked incident ticket | 15 minutes, 24/7 | Page backup on-call at 15 minutes; involve the engineering manager if unresolved after 30 minutes or user impact reaches P1 criteria. |
| P3 | Post to the proposed `#northstar-ml-ops` Slack channel and create a ticket assigned to the row's owner | 4 business hours | Escalate to the owner's team lead after 4 business hours. The imminent scoring-deadline rule above promotes a pipeline incident immediately to P2. |
| P4 | Create a ticket in the monitoring backlog; no Slack notification or page | 2 business days | Assign to the monitoring team lead if overdue; apply the explicit stale-monitor escalation above when that condition is met. |

Send one initial notification per incident and record updates in the same
incident/ticket. A repeated event with the same alarm and endpoint/variant or
job run ID updates that incident instead of creating a new one. Resolve only
after fresh measurements meet the relevant clear condition: three healthy
5-minute periods for availability/CPU, three healthy 1-minute periods for
latency, a verified successful replacement job for a pipeline failure, a new
valid clean drift result for drift, or the next complete daily business
observation returning to >=70% of its reference. Policy incidents also require
the policy owner to verify the correction before automated offer delivery
resumes. Restored freshness requires an actual new valid result.

## Suppression during planned model maintenance

**Condition:** The ML owner has an approved maintenance record identifying the
endpoint, start/end times, replacement model and baseline, and an expiry no
later than 60 minutes after the start. Outreach using the affected model is
paused while the model and reference are intentionally changed.

**Suppressed alert:** Suppress external Slack/ticket notifications from
`northstar-model-drift` (P3) for that endpoint during this window. Continue
computing and recording drift metrics and alarm states. Do not suppress
pipeline failures, the business-volume alert, monitoring freshness, or any P1
or P2 availability, CPU, latency or policy alert.

**Release:** Suppression expires automatically at the approved end or after
60 minutes, whichever comes first; no indefinite manual mute. The ML owner
runs a fresh comparison with >=500 predictions against the approved reference
and re-evaluates before resuming outreach. If it still breaches, send one P3
incident with the suppressed observations attached. If no valid comparison is
available, keep outreach paused and escalate the maintenance failure to P2;
do not report the model as healthy. Preserve the old baseline and approval
record so maintenance cannot erase unexplained drift.

## Relation to lab evidence

[`task1-alarms.json`](task1-alarms.json) records the five Task 1 alarm definitions;
it is not the complete Task 3 severity/routing design. The definitions above
provide nine named alerts across all four tiers, including offer generation.
Task 1 runtime observations and subsequent deletion are recorded in
[`lab6-monitoring-output.txt`](../../docs/lab6-monitoring-output.txt).
The input tests in this specification agree with the
[`Task 2 drift plan`](../../docs/lab6-runbook.md). No new AWS resources are needed
to review or submit this written specification.
