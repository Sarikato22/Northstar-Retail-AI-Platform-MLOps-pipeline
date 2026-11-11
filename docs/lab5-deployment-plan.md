# Lab 5 Deployment Plan

## Deployment Strategy and Rationale

NorthStar should deploy the churn model as a SageMaker real-time endpoint using a canary rollout. The churn score is useful when NorthStar is making customer-level decisions such as retention prioritization or offer selection, so the production path needs low-latency single-record scoring rather than only a nightly file output. Batch Transform would work for overnight full-base scoring, but it would not exercise the low-latency production path this system needs. The endpoint will be `northstar-churn-prod` with two production variants: `champion` receives 90% of traffic and `canary` receives 10% of traffic during the initial window.

The deployment starts on `ml.t2.medium` because the lab requires starting with the cheapest available endpoint instance. On that instance type, endpoint creation, weighted traffic, rollback, and the CloudWatch alarm work. Application Auto Scaling is then attempted and expected to reject `ml.t2.medium` because burstable instances cannot be scalable targets. Since this account has requested or received `ml.m5.large` endpoint quota, the follow-up production configuration moves the same two variants to `ml.m5.large` and attaches target tracking autoscaling.

## Pre-Deployment Checklist

Before deployment begins, the model package group `northstar-churn-models` must contain the champion and candidate model packages. The ML Engineer reviews the latest package metrics from the Lab 4 gate and approves the candidate only if CI passed, AUC remains above baseline, top-10 precision and recall are present, and no customer slice shows a material regression. The SageMaker execution role is `arn:aws:iam::716528268494:role/northstar-dev-MLEngineer`. The data bucket is `northstar-dev-data-716528268494`. The rollback alarm, endpoint config, and autoscaling target tracking config live in `deployment/configs/`.

During preparation for Lab 5, the older Model Registry entries were still present but their backing S3 `model.tar.gz` artifacts had been removed by prior teardown/reset work. Those packages are metadata-only now and cannot be deployed. To recover honestly, the ML Engineer reruns the existing SageMaker pipeline twice to create two fresh deployable packages with live S3 artifacts: the first fresh approved package is treated as the restored champion, and the second fresh approved package is treated as the canary candidate. The goal of this lab deployment is to validate the production rollout controls, rollback path, autoscaling behavior, evidence capture, and teardown discipline; it does not claim that the canary is a materially better model than the restored champion.

## Rollback Criteria

The rollback trigger is the CloudWatch alarm `northstar-churn-rollback-model-latency-canary`, defined in `deployment/configs/rollback-alarm.json`. It watches `AWS/SageMaker` metric `ModelLatency` for `EndpointName=northstar-churn-prod` and `VariantName=canary`. The numeric threshold is average latency greater than `200000` microseconds for two consecutive one-minute periods. SageMaker emits `ModelLatency` in microseconds, so this represents 200 ms. If the alarm fires, or if smoke tests show invocation errors or clearly invalid predictions, the ML Engineer rolls back by setting canary traffic weight to `0` with `update-endpoint-weights-and-capacities`.

## Monitoring Window

The production plan uses a 48-hour canary window before promotion. For this lab, the window is compressed to 60 minutes to control endpoint cost. During the lab window we verify the endpoint is `InService`, confirm both variants and traffic weights, invoke the endpoint at least 100 times and count `InvokedProductionVariant`, inspect the rollback alarm state, and attempt autoscaling. A real 48-hour window would additionally catch daily traffic cycles, delayed latency spikes, scaling behavior under real load, and slower data capture anomalies that a 60-minute lab run may miss.

## Stakeholder Notifications

At deployment start, the ML Engineer notifies the data science owner and platform owner that `northstar-churn-prod` is entering canary. If the canary remains clean through the monitoring window, the ML Engineer announces promotion readiness and records the observed traffic split. If rollback occurs, the ML Engineer notifies the same stakeholders with the alarm state, rollback command, and post-rollback traffic count showing zero canary invocations.

## Post-Deployment Review

After the lab window closes, the team reviews `docs/lab5-deployment-output.txt`, the endpoint description, the observed traffic split, the autoscaling result, the rollback alarm state, and the rollback evidence. The review artifact is this plan plus the captured CLI output. For this lab, the endpoint is not left running after the review; cost control takes priority over a persistent demo endpoint.

## Resource Cleanup

After rollback or promotion evidence is captured, run `scripts/teardown-lab5.sh`. The script deletes scaling policies and scalable targets, rollback alarms, endpoints, endpoint configs, SageMaker models, and in-flight processing or transform jobs. It writes `docs/lab5-teardown-output.txt`, which must show no active endpoints, no endpoint configs, and no registered scaling targets. Rollback alone is not cleanup because a variant at weight `0` can still keep an instance provisioned and billing.
