"""Pandas feature helpers used by the Lab 4 feature tests."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

N_CATEGORIES = 8.0


def _cutoff(snapshot_date: datetime) -> pd.Timestamp:
    return pd.Timestamp(snapshot_date).normalize()


def _prepared(transactions: pd.DataFrame) -> pd.DataFrame:
    df = transactions.copy()
    df["purchase_date"] = pd.to_datetime(df["purchase_date"], errors="coerce")
    return df


def _history(transactions: pd.DataFrame, snapshot_date: datetime) -> pd.DataFrame:
    cutoff = _cutoff(snapshot_date)
    df = _prepared(transactions)
    return df[df["purchase_date"] <= cutoff].copy()


def compute_recency_features(transactions: pd.DataFrame, snapshot_date: datetime) -> pd.DataFrame:
    cutoff = _cutoff(snapshot_date)
    hist = _history(transactions, snapshot_date)
    if hist.empty:
        return pd.DataFrame({
            "customer_id": pd.Series(dtype=object),
            "days_since_last_purchase": pd.Series(dtype=float),
            "customer_tenure_days": pd.Series(dtype=float),
        })
    grouped = hist.groupby("customer_id")["purchase_date"].agg(["min", "max"]).reset_index()
    grouped["days_since_last_purchase"] = (cutoff - grouped["max"]).dt.days.astype(float)
    grouped["customer_tenure_days"] = (cutoff - grouped["min"]).dt.days.astype(float)
    return grouped[["customer_id", "days_since_last_purchase", "customer_tenure_days"]]


def compute_frequency_features(transactions: pd.DataFrame, snapshot_date: datetime) -> pd.DataFrame:
    cutoff = _cutoff(snapshot_date)
    hist = _history(transactions, snapshot_date)
    out = pd.DataFrame({
        "customer_id": pd.Series(sorted(hist["customer_id"].dropna().unique()), dtype=object)
    })

    for days in (30, 90, 180):
        window = hist[hist["purchase_date"] > cutoff - pd.Timedelta(days=days)]
        counts = window.groupby("customer_id").size().rename(f"purchase_frequency_{days}d")
        out = out.merge(counts, on="customer_id", how="left")

    cols = ["purchase_frequency_30d", "purchase_frequency_90d", "purchase_frequency_180d"]
    out[cols] = out[cols].fillna(0.0).astype(float)
    return out


def compute_monetary_features(transactions: pd.DataFrame, snapshot_date: datetime) -> pd.DataFrame:
    cutoff = _cutoff(snapshot_date)
    hist = _history(transactions, snapshot_date)
    out = pd.DataFrame({
        "customer_id": pd.Series(sorted(hist["customer_id"].dropna().unique()), dtype=object)
    })

    lifetime = hist.groupby("customer_id").agg(
        avg_order_value=("order_value", "mean"),
        total_lifetime_value=("order_value", "sum"),
    ).reset_index()
    out = out.merge(lifetime, on="customer_id", how="left")

    last_90 = hist[hist["purchase_date"] > cutoff - pd.Timedelta(days=90)]
    spend_90 = last_90.groupby("customer_id")["order_value"].sum().rename("total_spend_90d")
    out = out.merge(spend_90, on="customer_id", how="left")

    last_180 = hist[hist["purchase_date"] > cutoff - pd.Timedelta(days=180)]
    basket = last_180.groupby("customer_id")["num_items"].mean().rename("avg_basket_size_6m")
    out = out.merge(basket, on="customer_id", how="left")

    cols = ["avg_order_value", "total_lifetime_value", "total_spend_90d", "avg_basket_size_6m"]
    out[cols] = out[cols].fillna(0.0).astype(float)
    return out


def compute_behavioral_features(transactions: pd.DataFrame) -> pd.DataFrame:
    df = _prepared(transactions)
    out = pd.DataFrame({
        "customer_id": pd.Series(sorted(df["customer_id"].dropna().unique()), dtype=object)
    })

    known_categories = df[df["product_category"].fillna("unknown") != "unknown"]
    diversity = (
        known_categories.groupby("customer_id")["product_category"].nunique() / N_CATEGORIES
    ).rename("category_diversity_score")
    out = out.merge(diversity, on="customer_id", how="left")

    online_ratio = (
        df.assign(is_online=(df["channel"] == "online").astype(float))
        .groupby("customer_id")["is_online"]
        .mean()
        .rename("online_to_store_ratio")
    )
    out = out.merge(online_ratio, on="customer_id", how="left")

    cols = ["category_diversity_score", "online_to_store_ratio"]
    out[cols] = out[cols].fillna(0.0).clip(lower=0.0, upper=1.0)
    return out


def build_churn_feature_set(
    customers: pd.DataFrame,
    transactions: pd.DataFrame,
    snapshot_date: datetime,
) -> pd.DataFrame:
    out = customers[["customer_id"]].drop_duplicates().copy()
    for part in (
        compute_recency_features(transactions, snapshot_date),
        compute_frequency_features(transactions, snapshot_date),
        compute_monetary_features(transactions, snapshot_date),
        compute_behavioral_features(_history(transactions, snapshot_date)),
    ):
        out = out.merge(part, on="customer_id", how="left")

    numeric_cols = [col for col in out.columns if col != "customer_id"]
    out[numeric_cols] = out[numeric_cols].fillna(0.0)
    if "customer_tenure_days" in out.columns:
        out["customer_tenure_days"] = out["customer_tenure_days"].replace(0.0, np.nan)
        out["customer_tenure_days"] = out["customer_tenure_days"].fillna(999.0)
    if "days_since_last_purchase" in out.columns:
        out["days_since_last_purchase"] = out["days_since_last_purchase"].replace(0.0, np.nan)
        out["days_since_last_purchase"] = out["days_since_last_purchase"].fillna(999.0)

    return out
