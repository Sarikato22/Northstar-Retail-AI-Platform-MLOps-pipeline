"""Publish observed drift and the scored-customer churn-volume proxy locally."""

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3


def build_metrics(drift, traffic):
    if drift["underpowered_window"] or drift["captured_records"] < 500:
        raise ValueError("Refusing to publish drift from an underpowered window")
    if len(drift["per_feature"]) != 5 or drift["features_evaluated"] != 5:
        raise ValueError("Expected results for all five planned features")
    dimensions = [{"Name": "EndpointName", "Value": traffic["endpoint"]}]
    now = datetime.now(timezone.utc)
    metrics = [
        {"MetricName": "DriftDetected", "Value": int(drift["drift_detected"]), "Unit": "Count"},
        {"MetricName": "DriftViolationCount", "Value": drift["violation_count"], "Unit": "Count"},
    ]
    for feature, result in drift["per_feature"].items():
        metrics.append({"MetricName": f"{result['method'].upper()}_{feature}",
                        "Value": result["value"], "Unit": "None"})
    for metric in metrics:
        metric.update(Dimensions=dimensions, Timestamp=now)
    metrics.append({"MetricName": "ChurnAlertVolume", "Value": traffic["churn_alert_volume"],
                    "Unit": "Count", "Dimensions": dimensions,
                    "Timestamp": datetime.fromisoformat(traffic["finished_at"])})
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", default="monitoring/reports/drift_violations.json")
    parser.add_argument("--traffic", default="monitoring/reports/traffic-summary.json")
    parser.add_argument("--namespace", default="NorthStar/ChurnModel")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()
    drift = json.loads(Path(args.summary).read_text())
    traffic = json.loads(Path(args.traffic).read_text())
    metrics = build_metrics(drift, traffic)
    cw = boto3.client("cloudwatch", region_name=args.region)
    day = datetime.fromisoformat(traffic["finished_at"]).astimezone(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    history = cw.get_metric_statistics(
        Namespace=args.namespace, MetricName="ChurnAlertVolume",
        Dimensions=metrics[-1]["Dimensions"], StartTime=day-timedelta(days=7),
        EndTime=day, Period=86400, Statistics=["Maximum"])["Datapoints"]
    # No backfilled observations: seven real daily snapshots are required.
    by_day = {point["Timestamp"].date(): point["Maximum"] for point in history}
    expected = {(day-timedelta(days=n)).date() for n in range(1, 8)}
    if expected.issubset(by_day):
        average = sum(by_day[d] for d in expected) / 7
        metrics.append({"MetricName": "ChurnAlertVolume7DayAverage", "Value": average,
                        "Unit": "Count", "Dimensions": metrics[-1]["Dimensions"],
                        "Timestamp": datetime.fromisoformat(traffic["finished_at"])})
    else:
        print(f"Seven-day business baseline unavailable ({len(expected & by_day.keys())}/7 days); no average published")
    cw.put_metric_data(Namespace=args.namespace, MetricData=metrics)
    print(f"Published {len(metrics)} observed metrics to {args.namespace}")


if __name__ == "__main__":
    main()
