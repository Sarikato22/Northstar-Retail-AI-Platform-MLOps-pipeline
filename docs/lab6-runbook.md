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