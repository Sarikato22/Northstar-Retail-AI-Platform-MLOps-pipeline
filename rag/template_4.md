Context recall measures whether retrieved context covers the information needed by the evaluation reference. Query construction is one factor; also inspect filters, retrieved chunks, and retrieval settings. Remember: **you are retrieving policy, not products.**

**Option A — Tier-benefit query.** Retrieve the entitlements that constrain the offer.

```python
query = (
    f"loyalty tier {customer['loyalty_tier']} benefits points earn rate "
    f"free shipping threshold return window birthday reward"
)
```

**Option B — Constraint query.** Retrieve the limits the offer must not violate.

```python
query = (
    "final sale non-returnable exclusions expired offers cannot be reinstated "
    "retention offer validity single use combinability"
)
```

**Option C — Hybrid with metadata filter.** Retrieve both, weighted toward the customer's situation.

```python
filters = {"doc_id": {"$in": ["POL-LOY-011", "POL-SHP-007", "POL-RET-004"]}}
query = (
    f"tier {customer['loyalty_tier']} entitlements and shipping thresholds "
    f"for a customer who shops "
    f"{'online' if customer['online_to_store_ratio'] > 0.5 else 'in store'}"
)