"""Your Lab 3 churn model, packaged for the Lab 4 pipeline.

YOU WRITE THIS FILE. The pipeline's training job runs train_sagemaker.py
(beside this file; do not edit it), which imports this module and calls
train(). Everything the job needs from you goes through the three names below.

Contract (train_sagemaker.py checks it in the first seconds of the job):

    FEATURE_COLUMNS   list[str]   model input columns, in order
    LABEL             str         "churn_label"
    train(df, seed=42) -> (xgboost.Booster, dict)

`df` is the full labeled feature table: every column of your Lab 2 output,
including `loyalty_tier` for slice evaluation. It is already loaded. Do not
query Athena or the Feature Store from here; the training container stages
the data for you and has no business making service calls for its input.

The metrics dict must include the four numbers the CI gate in
tests/test_model.py reads. Your Lab 3 evaluate_model() already returns them:

    precision_top10, recall_top10      gated at 0.50 / 0.25
    lift_ci_low, lift_ci_high          bootstrap 95% CI on AUC lift over the
                                       recency-only baseline; lift_ci_low > 0

Include anything else you reported in Lab 3 (auc_roc, baseline_auc,
positive_rate_val, slice results). It is all written to evaluation_metrics.json
and attached to the registered model.

What runs in the container: the SageMaker XGBoost 1.7-1 image ships pandas,
numpy, scikit-learn, xgboost and boto3. It does NOT ship mlflow or sagemaker,
so do not import them at the top of this file. MLflow tracking stays in your
Lab 3 script.

Only this directory (models/churn/) is uploaded to the training job, so the
code must live here. `import churn_training_skeleton` will fail inside the
container even though it works on your laptop. Copy the functions you need.

Test it locally before pushing:

    python models/churn/train_sagemaker.py \
        --train-channel <dir containing your features CSV or Parquet> \
        --model-dir /tmp/model --output-data-dir /tmp/out
"""

# Keeps Lab 3 annotations like `-> tuple[np.ndarray, np.ndarray]` from being
# evaluated, whatever Python the training container runs.
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

# Must match the columns your Lab 3 model was trained on, in the same order.
FEATURE_COLUMNS = [
    "days_since_last_purchase",
    "customer_tenure_days",
    "purchase_frequency_30d",
    "purchase_frequency_90d",
    "purchase_frequency_180d",
    "avg_order_value",
    "total_spend_90d",
    "total_lifetime_value",
    "avg_basket_size_6m",
    "category_diversity_score",
    "online_to_store_ratio",
]

LABEL = "churn_label"
BASELINE_FEATURE = "days_since_last_purchase"
SLICE_COLUMN = "loyalty_tier"

EVAL_THRESHOLDS = {
    "precision_top10": 0.50,
    "recall_top10": 0.25,
}

BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 42
MIN_SLICE_SIZE = 30


def _preprocess_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    df = df.dropna(subset=[LABEL]).copy().reset_index(drop=True)
    if df.empty:
        raise ValueError("No rows with a non-missing churn_label were found.")
    if SLICE_COLUMN not in df.columns:
        raise ValueError(f"'{SLICE_COLUMN}' is required for slice evaluation.")
    if df[SLICE_COLUMN].isna().any():
        raise ValueError("loyalty_tier contains missing values.")

    missing = [col for col in FEATURE_COLUMNS + [LABEL] if col not in df.columns]
    if missing:
        raise ValueError(f"Training data missing required columns: {missing}")

    X_df = df[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    X = X_df.fillna(-1).to_numpy(dtype=np.float32)

    labels = pd.to_numeric(df[LABEL], errors="raise")
    if labels.isna().any() or not labels.isin([0, 1]).all():
        raise ValueError("churn_label must contain only 0 and 1.")
    y = labels.to_numpy(dtype=np.int32)
    if len(np.unique(y)) != 2:
        raise ValueError("Training data must contain both churn_label classes.")

    return X, y, df


def _train_model(X_train, y_train, X_val, y_val, args) -> xgb.Booster:
    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=FEATURE_COLUMNS)
    dval = xgb.DMatrix(X_val, label=y_val, feature_names=FEATURE_COLUMNS)

    spw = (
        args.scale_pos_weight
        if args.scale_pos_weight is not None
        else float((y_train == 0).sum() / max((y_train == 1).sum(), 1))
    )
    if spw <= 0:
        raise ValueError("scale_pos_weight must be greater than zero.")

    params = {
        "objective": "binary:logistic",
        "eval_metric": ["logloss", "auc"],
        "max_depth": args.max_depth,
        "eta": args.eta,
        "min_child_weight": args.min_child_weight,
        "subsample": args.subsample,
        "colsample_bytree": args.colsample_bytree,
        "scale_pos_weight": spw,
        "monotone_constraints": "(1,0,0,0,0,0,0,0,0,0,0)",
        "seed": args.seed,
        "verbosity": 1,
    }

    return xgb.train(
        params=params,
        dtrain=dtrain,
        num_boost_round=args.num_round,
        evals=[(dtrain, "train"), (dval, "validation")],
        early_stopping_rounds=20,
        verbose_eval=25,
    )


def _train_recency_baseline(X_train, y_train, X_val, seed: int) -> np.ndarray:
    i = FEATURE_COLUMNS.index(BASELINE_FEATURE)
    dtr = xgb.DMatrix(X_train[:, [i]], label=y_train, feature_names=[BASELINE_FEATURE])
    dva = xgb.DMatrix(X_val[:, [i]], feature_names=[BASELINE_FEATURE])
    spw = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))

    params = {
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "max_depth": 4,
        "eta": 0.1,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "scale_pos_weight": spw,
        "seed": seed,
    }
    return xgb.train(params, dtr, num_boost_round=200).predict(dva)


def _bootstrap_lift_ci(y_true, proba, baseline_proba, n=BOOTSTRAP_N, seed=BOOTSTRAP_SEED):
    y_true = np.asarray(y_true)
    proba = np.asarray(proba)
    baseline_proba = np.asarray(baseline_proba)
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y_true))
    diffs = []

    for _ in range(n):
        sample = rng.choice(idx, size=len(idx), replace=True)
        labels = y_true[sample]
        if len(np.unique(labels)) < 2:
            continue
        diffs.append(
            roc_auc_score(labels, proba[sample])
            - roc_auc_score(labels, baseline_proba[sample])
        )

    if len(diffs) < n // 2:
        raise ValueError("Too few usable bootstrap replicates for lift CI.")

    return (
        float(np.quantile(diffs, 0.025)),
        float(np.quantile(diffs, 0.975)),
    )


def _evaluate_model(model, X_val, y_val, baseline_proba) -> dict:
    dval = xgb.DMatrix(X_val, feature_names=FEATURE_COLUMNS)
    y_pred_proba = model.predict(dval)

    auc_roc = roc_auc_score(y_val, y_pred_proba)
    top10_threshold = np.percentile(y_pred_proba, 90)
    top10_mask = y_pred_proba >= top10_threshold
    precision_top10 = y_val[top10_mask].mean() if top10_mask.sum() > 0 else 0.0
    recall_top10 = y_val[top10_mask].sum() / y_val.sum() if y_val.sum() > 0 else 0.0

    baseline_auc = roc_auc_score(y_val, baseline_proba)
    auc_vs_baseline = auc_roc - baseline_auc
    lift_ci_low, lift_ci_high = _bootstrap_lift_ci(y_val, y_pred_proba, baseline_proba)

    metrics = {
        "auc_roc": round(float(auc_roc), 4),
        "precision_top10": round(float(precision_top10), 4),
        "recall_top10": round(float(recall_top10), 4),
        "auc_vs_baseline": round(float(auc_vs_baseline), 4),
        "baseline_auc": round(float(baseline_auc), 4),
        "lift_ci_low": round(float(lift_ci_low), 4),
        "lift_ci_high": round(float(lift_ci_high), 4),
        "positive_rate_val": round(float(y_val.mean()), 4),
        "n_val_samples": int(len(y_val)),
        "eval_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    failures = [
        f"{metric}={metrics[metric]:.4f} < {threshold}"
        for metric, threshold in EVAL_THRESHOLDS.items()
        if metrics[metric] < threshold
    ]
    if lift_ci_low <= 0:
        failures.append(
            f"auc_lift 95% CI [{lift_ci_low:.4f}, {lift_ci_high:.4f}] includes zero"
        )

    metrics["evaluation_passed"] = not failures
    metrics["evaluation_failures"] = failures
    return metrics


def _evaluate_slices(model, X_val, y_val, slice_column: pd.Series) -> dict:
    dval = xgb.DMatrix(X_val, feature_names=FEATURE_COLUMNS)
    y_pred_proba = model.predict(dval)
    y_true = np.asarray(y_val)
    slice_column = pd.Series(slice_column).reset_index(drop=True)

    aggregate_threshold = np.percentile(y_pred_proba, 90)
    aggregate_mask = y_pred_proba >= aggregate_threshold
    aggregate_recall = (
        float(y_true[aggregate_mask].sum() / y_true.sum())
        if y_true.sum() > 0
        else 0.0
    )

    results = {}
    for slice_value in sorted(slice_column.unique(), key=str):
        mask = (slice_column == slice_value).to_numpy()
        y_slice = y_true[mask]
        proba_slice = y_pred_proba[mask]
        n_slice = int(mask.sum())
        slice_threshold = np.percentile(proba_slice, 90)
        top10_mask = proba_slice >= slice_threshold
        positives = int(y_slice.sum())
        recall_top10 = (
            float(y_slice[top10_mask].sum() / positives)
            if positives > 0
            else 0.0
        )
        auc_slice = (
            float(roc_auc_score(y_slice, proba_slice))
            if len(np.unique(y_slice)) == 2
            else None
        )
        results[str(slice_value)] = {
            "n": n_slice,
            "auc_roc": round(auc_slice, 4) if auc_slice is not None else None,
            "recall_top10": round(recall_top10, 4),
            "aggregate_recall_top10": round(aggregate_recall, 4),
            "below_aggregate_by_10pp": bool(recall_top10 < aggregate_recall - 0.10),
            "too_small_for_reliable_claim": bool(n_slice < MIN_SLICE_SIZE),
            "auc_undefined_single_class": auc_slice is None,
        }
    return results


def train(df: pd.DataFrame, seed: int = 42):
    """Train the churn model on `df` and return (booster, metrics).

    TODO (Lab 4): implement this from your Lab 3 code. The usual shape:

      1. X, y from FEATURE_COLUMNS and LABEL (handle missing values the way
         your Lab 3 preprocess_features() did)
      2. train_test_split(..., test_size=0.30, random_state=seed, stratify=y)
         -- carry the tier through the same call if you report slices. Pass
         df["loyalty_tier"] (a Series) or .to_numpy(dtype=object); NOT
         .values, which under pandas 3 is an Arrow array that
         train_test_split cannot index
      3. train the XGBoost model (your Lab 3 train_model())
      4. train the recency-only baseline (train_recency_baseline())
      5. metrics = evaluate_model(...)   # keep Lab 3's raise on a failed gate:
                                         # it fails the training step, so a
                                         # model that misses a gate is never
                                         # registered
      6. return model, metrics

    Return an xgboost.Booster (what xgb.train() gives you). If you used
    XGBClassifier, return clf.get_booster().
    """
    clean_input = df.dropna(subset=[LABEL]).reset_index(drop=True)
    X, y, clean_df = _preprocess_features(clean_input)

    X_train, X_val, y_train, y_val, _, tier_val = train_test_split(
        X,
        y,
        clean_df[SLICE_COLUMN].reset_index(drop=True),
        test_size=0.30,
        random_state=seed,
        stratify=y,
    )

    args = SimpleNamespace(
        max_depth=6,
        eta=0.1,
        num_round=200,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=None,
        seed=seed,
    )

    model = _train_model(X_train, y_train, X_val, y_val, args)
    baseline_proba = _train_recency_baseline(X_train, y_train, X_val, seed)
    metrics = _evaluate_model(model, X_val, y_val, baseline_proba)
    metrics["slice_evaluation"] = _evaluate_slices(model, X_val, y_val, tier_val)

    if not metrics["evaluation_passed"]:
        raise ValueError(
            "Evaluation gates not met: " + "; ".join(metrics["evaluation_failures"])
        )

    return model, metrics
