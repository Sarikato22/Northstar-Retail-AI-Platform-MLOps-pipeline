**Tracks completed:** A (Churn Prediction) and B (Offer Generation, RAG)
 
## Why gradient boosting for churn
 
The lab fixed XGBoost, so this is justification rather than a choice I made, but it holds up for NorthStar's data. We have about 10,000 customers and 11 modeled features. The Feature Group has 13 columns; `churn_risk_score` stays out because it is the recency heuristic we are trying to beat, and `loyalty_tier` stays out because it is the slice column. That is small, purely tabular data with no text or event sequences, so a neural network has little to exploit and too few rows to learn it.
 
Logistic regression is the real rival, because the retention team wants explanations. But the features overlap (purchase frequency at 30, 90, and 180 days, spend, lifetime value), and about a third of churners still look recent, so the signal lives in interactions a linear model needs hand-built. Trees find them, and the team still gets gain-based importance and per-customer SHAP values. That is less clean than coefficients, but enough to say why a customer was flagged. I did not train a logistic regression, so this is reasoning, not a measured comparison.
 
I would switch to logistic regression if a regulator or the retention team needed coefficient-level explanations, or if a simple model landed within about 0.01 AUC on the same split. A neural network would need sequence or text data, or hundreds of thousands of customers.
 
## What the features bought
 
Recency alone scored 0.7229 AUC against 0.7779 for the full model, a lift of 0.055 with a 95% CI of [0.0365, 0.073]. The interval excludes zero, so the engineering did measurable work, but 0.055 is modest. Recency already ranks the customers who lapsed months ago, and several features (the frequency and spend windows) mostly restate it. AUC may also understate the behavioral features, since they target the minority of churners who still look active. [FILL IN: AUC or recall on recently active customers only, baseline vs full, if you ran it.]
 
Carried real signal: [FILL IN from feature-importance.png: top 3 by gain]. Decorative: [FILL IN: bottom features near zero gain, and whether they duplicate recency]. At the top decile, precision is 0.70 against a 22% base rate (about 3x), and recall@10% is 0.32 against a ceiling near 0.45.
 
## Why RAG over fine-tuning (Track B)
 
The offers have to follow three policy documents (loyalty terms, shipping, returns) that change over time. Fine-tuning would bake policy into the weights, so every edit means retraining and revalidating, and the model could not point to the clause behind an offer. With RAG I edit a markdown file and re-index, and each answer carries its sources. Fine-tuning would also need labeled examples of compliant offers, which we do not have.
 
I indexed only the three policy documents, not the FAQ, because [FILL IN why]. Setup: 800-character chunks with 120 overlap ([N] chunks), Titan v2 embeddings, local FAISS, top 5, and Claude Haiku 4.5 at temperature 0.1 for a 2 to 3 sentence output. I did not re-rank, to keep the pipeline simple, and I did not measure what it would add.
 
The primary production risk is quoting a benefit the customer's tier does not carry. POL-LOY-011 defines tier by trailing 12-month spend, but the feature store's `loyalty_tier` comes from lifetime value, so customers near a threshold can land in the wrong tier. The offer would cite a real policy and still be wrong for that customer. A retrieval miss on an exclusion is the second risk. [FILL IN: how your prompt handles the tier gap, or say plainly that it does not.]
 
## What I would do differently
 
With 10x the time, I would build the compliance eval before the prompts. Aligning them to the policies took me an enormous number of hours because I could not tell quickly whether a change helped. I would write a few hundred customer and question pairs labeled with allowed and disallowed offers, add a deterministic post-generation check against a structured tier-entitlement table, and read tier from the system of record at generation time.
 
With 10x the data, I would add a second snapshot. The labels are already temporal (features before T, outcome after), but every customer shares the same T, so my test set says nothing about drift. A snapshot a quarter later would test drift and set a retraining cadence. I would also check calibration per tier, since Silver was weakest (recall@10% 0.23, AUC 0.708).
 