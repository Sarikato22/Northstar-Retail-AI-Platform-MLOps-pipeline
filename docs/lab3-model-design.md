**Tracks completed:** A (Churn Prediction) and B (Offer Generation, RAG)

## Why gradient boosting for churn

The lab fixed XGBoost, so this is justification rather than a choice I made, but it holds up for NorthStar's data. We have about 10,000 customers and 11 modeled features. The Feature Group has 13 columns; `churn_risk_score` stays out because it is the recency heuristic we are trying to beat, and `loyalty_tier` stays out because it is the slice column. That is small, purely tabular data with no text or event sequences, so a neural network has little to exploit and too few rows to learn it.

Logistic regression is the real rival, because the retention team wants explanations. But the features overlap (purchase frequency at 30, 90, and 180 days, spend, lifetime value), and about a third of churners still look recent, so the signal lives in interactions a linear model needs hand-built. Trees find them, and the team still gets gain-based importance and per-customer SHAP values. That is less clean than coefficients, but enough to say why a customer was flagged. I did not train a logistic regression, so this is reasoning, not a measured comparison.

I would switch to logistic regression if a regulator or the retention team needed coefficient-level explanations, or if a simple model landed within about 0.01 AUC on the same split. A neural network would need sequence or text data, or hundreds of thousands of customers.

## What the features bought

Recency alone scored 0.7229 AUC against 0.7779 for the full model, a lift of 0.055 with a 95% CI of [0.0365, 0.0730]. The interval excludes zero, so the engineering did measurable work, but 0.055 is modest. Recency already ranks the customers who lapsed months ago, and several features mostly restate some form of purchase activity. I did not run a separate recently-active-only analysis, so I am not claiming a slice lift there.

Carried real signal: `days_since_last_purchase`, `purchase_frequency_180d`, and `purchase_frequency_30d` were the top three features by gain. The weakest gain features were `online_to_store_ratio`, `customer_tenure_days`, and `category_diversity_score`; they may still help individual splits, but in this run they were much less important than recency and frequency. At the top decile, precision is 0.70 against a 22% base rate, and recall@10% is 0.32 against a ceiling near 0.45.

## Why RAG over fine-tuning

The offers have to follow policy documents for loyalty, shipping, and returns that can change over time. Fine-tuning would bake policy into the weights, so every edit would mean retraining and revalidating, and the model could not point to the clause behind an offer. With RAG, I can edit a markdown file, re-index, and have each answer carry retrieved policy context. Fine-tuning would also need labeled examples of compliant offers, which we do not have.

I indexed only the three governing policy documents, not the FAQ, because the offer should cite enforceable loyalty, shipping, and returns policy rather than customer-service summary text. Setup: 800-character chunks with 120 overlap, 27 chunks, Titan v2 embeddings, local FAISS, top 5 retrieval, and Claude Haiku 4.5 at temperature 0.1 for a 2 to 3 sentence output. I did not re-rank, to keep the pipeline simple, and I did not measure what it would add.

The RAGAS scores were faithfulness 0.4352, answer relevance 0.3377, and context recall 0.5083. Those are below the original rubric targets but close to the revised October reference ranges for the course pipeline. The main gap is that the retriever often includes true policy chunks that are adjacent to, but not exactly the same as, the reference answer's expected support.

The primary production risk is quoting a benefit the customer's tier does not carry. POL-LOY-011 defines tier by trailing 12-month spend, but the feature store's `loyalty_tier` comes from lifetime value, so customers near a threshold can land in the wrong tier. The offer would cite a real policy and still be wrong for that customer. The prompt partially mitigates this by treating the supplied tier as unverified, using conditional wording for tier-specific benefits, and forbidding the model from recalculating tier from incomplete data. A production version should still read tier from the loyalty system of record before generation.

## What I would do differently

With 10x the time, I would build the compliance eval before the prompts. Aligning the RAG answers to the policies took many iterations because it was hard to tell quickly whether a change helped. I would write a few hundred customer and question pairs labeled with allowed and disallowed offers, add a deterministic post-generation check against a structured tier-entitlement table, and read tier from the system of record at generation time.

With 10x the data, I would add a second snapshot. The labels are already temporal, with features before T and outcomes after, but every customer shares the same T, so my test set says little about drift. A snapshot a quarter later would test drift and set a retraining cadence. I would also check calibration per tier, since Silver was weakest with recall@10% 0.2301 and AUC 0.7082.
