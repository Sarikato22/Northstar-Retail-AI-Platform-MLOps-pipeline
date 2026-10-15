# Track B — RAG Input/Output Examples

Generated: 2026-10-14T21:33:03

Policy documents: 3
Indexed chunks: 27

Offers below are outputs from the running RAG pipeline. Review each answer against the retrieved policies before describing it as correct.

## Example 1: CUST-10000317

### Customer profile

```json
{
  "churn_probability": 0.81,
  "loyalty_tier": "Gold",
  "days_since_last_purchase": 47,
  "total_lifetime_value": 3120.4,
  "avg_order_value": 186.25,
  "category_diversity_score": 0.5,
  "online_to_store_ratio": 0.72,
  "top_categories": [
    "Outdoor",
    "Footwear"
  ]
}
```

### Input question

Generate a personalized retention offer for this at-risk Gold member who shops mostly online for outdoor gear and footwear.

### Generated offer

Subject: Your Gold Benefits Are Waiting—Free Return Shipping on Your Next Order

Body: We'd love to see you back in Outdoor and Footwear gear. As a Gold member, you enjoy free return shipping on eligible purchases, plus a full 30-day return window—so you can shop with confidence [POL-RET-004]. Come explore what's new, and let us know if you have questions; we're here to help you find exactly what you need.

Rationale: The customer is labeled Gold with 47 days since last purchase and concentrated spending in Outdoor and Footwear (low category diversity). Free return shipping is a verified Gold benefit that removes friction for online shoppers (0.72 online-to-store ratio) and aligns with the customer's purchase pattern. The 30-day return window reinforces confidence without overstating eligibility. No discount or new promotion is invented; the message highlights an existing tier benefit relevant to retention.

### Retrieved chunk IDs

- `loyalty-program-terms.md:start_index=4337`
- `loyalty-program-terms.md:start_index=3630`
- `return-policy.md:start_index=614`
- `loyalty-program-terms.md:start_index=2987`
- `loyalty-program-terms.md:start_index=1461`

### Retrieved policy excerpts

**loyalty-program-terms.md, start index 4337**

Offer codes are void if the account is closed, if the offer's stated conditions are not met, or after the stated expiry date. Expired offers **cannot be reinstated by customer service or by any automated system.**

### 5.1 Retention Offers

Retention offers are generated for members identified as at risk of lapsing. These offers:

- Are valid for **45 days** from issue unless stated otherwise
- Are limited to **one active retention offer per member** at a time
- May not be combined with another retention offer
- Do not extend, alter, or waive any provision of the returns policy

**loyalty-program-terms.md, start index 3630**

Benefits are tied to the member's tier at the time the benefit is used, except the return window, which is fixed at the tier held **at the time of purchase** (see POL-RET-004 §1.1).

### 4.1 Annual Gear Credit

Platinum members receive a **$100 gear credit** each January 1. The credit expires December 31 of the same year, does not carry over, has no cash value, and is forfeited if the member is downgraded below Platinum before using it.

---

## 5. Promotional Offers

Targeted offers issued to a member are **single-use, non-transferable, and tied to the member account**. Offers may not be stacked with other targeted offers, though a targeted offer may generally be combined with points redemption.

**return-policy.md, start index 614**

### 1.1 Extended Window for Platinum Members

**Platinum loyalty members receive a 60-day return window** on all eligible merchandise. This is an automatic benefit; the member does not need to request it and no approval is required.

The extended window applies based on the member's tier **at the time of purchase**, not at the time of return. A customer who was Gold when they purchased and reached Platinum afterwards receives the standard 30-day window for that order.

### 1.2 Holiday Purchases

Merchandise purchased between **November 1 and December 24** may be returned through **January 31** of the following year, regardless of tier. Where the holiday window and a member's standard window conflict, the customer receives whichever is longer.

---

## 2. Refund Method

**loyalty-program-terms.md, start index 2987**

Points already redeemed against a subsequent purchase are not clawed back.

---

## 4. Tier Benefits

| Benefit | Bronze | Silver | Gold | Platinum |
|---|---|---|---|---|
| Points earn rate | 1× | 1.25× | 1.5× | 2× |
| Birthday reward | $5 | $10 | $20 | $40 |
| Free standard shipping | $75+ | $50+ | Always | Always |
| Free return shipping | No | No | Yes | Yes |
| Return window | 30 days | 30 days | 30 days | **60 days** |
| Early access to sales | No | 12 hours | 24 hours | 48 hours |
| Free gear repair | No | No | 2 per year | Unlimited |
| Dedicated support line | No | No | No | Yes |
| Annual gear credit | No | No | No | $100 |

**loyalty-program-terms.md, start index 1461**

Members receive email notice **30 days before** a scheduled downgrade.

### 2.3 Tier Protection

A member who has held Gold or Platinum for **24 consecutive months or longer** is protected from a single downgrade evaluation once per rolling 24-month period. Protection applies automatically and cannot be requested, deferred, or transferred.

---

## 3. Points

Members earn **1 point per $1** of qualifying merchandise spend.

| Tier | Earn rate | Effective value |
|---|---|---|
| Bronze | 1× | 1 point per $1 |
| Silver | 1.25× | 1.25 points per $1 |
| Gold | 1.5× | 1.5 points per $1 |
| Platinum | 2× | 2 points per $1 |

### Review

- Policy claims verified against retrieved excerpts: [Complete after review]
- Tier benefits accurate: [Complete after review]
- Category recommendation relevant: [Complete after review]

---

## Example 2: CUST-10000904

### Customer profile

```json
{
  "churn_probability": 0.74,
  "loyalty_tier": "Bronze",
  "days_since_last_purchase": 68,
  "total_lifetime_value": 312.8,
  "avg_order_value": 41.15,
  "category_diversity_score": 0.125,
  "online_to_store_ratio": 0.2,
  "top_categories": [
    "Apparel"
  ]
}
```

### Input question

Generate a retention offer for this Bronze member who shops in store, buys only apparel, and has not purchased in over two months.

### Generated offer

Subject: We miss you—come back to Apparel and earn rewards faster

Body: It's been a while since we've seen you, and we'd love to welcome you back to NorthStar. As a Bronze member, you earn 1 point per $1 on all qualifying apparel purchases, and once you spend $75 or more, you'll qualify for free standard shipping [POL-LOY-011]. Shop apparel today and start earning toward your next reward.

Rationale: The customer is Bronze-tier (unverified but supplied as label), has concentrated purchases in Apparel (diversity score 0.12), and a 68-day purchase gap. Bronze benefits—points earn rate and conditional free shipping at $75—are policy-backed, relevant to apparel shopping, and achievable given the customer's $41.15 average order value. This messaging welcomes the customer back without inventing a promotion or asserting unverified tier status.

### Retrieved chunk IDs

- `loyalty-program-terms.md:start_index=4337`
- `return-policy.md:start_index=614`
- `return-policy.md:start_index=2082`
- `loyalty-program-terms.md:start_index=3630`
- `loyalty-program-terms.md:start_index=2987`

### Retrieved policy excerpts

**loyalty-program-terms.md, start index 4337**

Offer codes are void if the account is closed, if the offer's stated conditions are not met, or after the stated expiry date. Expired offers **cannot be reinstated by customer service or by any automated system.**

### 5.1 Retention Offers

Retention offers are generated for members identified as at risk of lapsing. These offers:

- Are valid for **45 days** from issue unless stated otherwise
- Are limited to **one active retention offer per member** at a time
- May not be combined with another retention offer
- Do not extend, alter, or waive any provision of the returns policy

**return-policy.md, start index 614**

### 1.1 Extended Window for Platinum Members

**Platinum loyalty members receive a 60-day return window** on all eligible merchandise. This is an automatic benefit; the member does not need to request it and no approval is required.

The extended window applies based on the member's tier **at the time of purchase**, not at the time of return. A customer who was Gold when they purchased and reached Platinum afterwards receives the standard 30-day window for that order.

### 1.2 Holiday Purchases

Merchandise purchased between **November 1 and December 24** may be returned through **January 31** of the following year, regardless of tier. Where the holiday window and a member's standard window conflict, the customer receives whichever is longer.

---

## 2. Refund Method

**return-policy.md, start index 2082**

---

## 3. Condition Requirements

To be eligible for return, merchandise must be:

- Unworn, unwashed, and free of damage beyond normal inspection
- Accompanied by all original tags, packaging, and included accessories
- Presented with proof of purchase (receipt, order number, or loyalty account lookup)

Footwear must be returned in its original box. A footwear return without the box may be refused or assessed a $15 repackaging fee at the store manager's discretion.

---

## 4. Non-Returnable Merchandise

The following are **final sale** and cannot be returned or exchanged under any circumstance, including for Platinum members and including during the holiday window:

**loyalty-program-terms.md, start index 3630**

Benefits are tied to the member's tier at the time the benefit is used, except the return window, which is fixed at the tier held **at the time of purchase** (see POL-RET-004 §1.1).

### 4.1 Annual Gear Credit

Platinum members receive a **$100 gear credit** each January 1. The credit expires December 31 of the same year, does not carry over, has no cash value, and is forfeited if the member is downgraded below Platinum before using it.

---

## 5. Promotional Offers

Targeted offers issued to a member are **single-use, non-transferable, and tied to the member account**. Offers may not be stacked with other targeted offers, though a targeted offer may generally be combined with points redemption.

**loyalty-program-terms.md, start index 2987**

Points already redeemed against a subsequent purchase are not clawed back.

---

## 4. Tier Benefits

| Benefit | Bronze | Silver | Gold | Platinum |
|---|---|---|---|---|
| Points earn rate | 1× | 1.25× | 1.5× | 2× |
| Birthday reward | $5 | $10 | $20 | $40 |
| Free standard shipping | $75+ | $50+ | Always | Always |
| Free return shipping | No | No | Yes | Yes |
| Return window | 30 days | 30 days | 30 days | **60 days** |
| Early access to sales | No | 12 hours | 24 hours | 48 hours |
| Free gear repair | No | No | 2 per year | Unlimited |
| Dedicated support line | No | No | No | Yes |
| Annual gear credit | No | No | No | $100 |

### Review

- Policy claims verified against retrieved excerpts: [Complete after review]
- Tier benefits accurate: [Complete after review]
- Category recommendation relevant: [Complete after review]

---

## Example 3: CUST-10000122

### Customer profile

```json
{
  "churn_probability": 0.66,
  "loyalty_tier": "Platinum",
  "days_since_last_purchase": 39,
  "total_lifetime_value": 8940.0,
  "avg_order_value": 447.0,
  "category_diversity_score": 0.75,
  "online_to_store_ratio": 0.55,
  "top_categories": [
    "Outdoor",
    "Electronics",
    "Home"
  ]
}
```

### Input question

Generate a retention offer for this high-value Platinum member with broad category interest and a large average order.

### Generated offer

Subject: Your Platinum Gear Credit Awaits—Plus Free Returns on Outdoor Gear

Body:
We'd love to see you back soon. As a Platinum member, you have access to unlimited free gear repair and a $100 annual gear credit (valid through December 31) [POL-LOY-011]—both perfect for keeping your Outdoor and Electronics gear in top shape. Plus, eligible purchases you make as a Platinum member enjoy a 60-day return window [POL-RET-004], giving you extra time to decide. Shop now and make the most of your membership benefits.

Rationale:
The customer is labeled Platinum with high lifetime value ($8,940) and a 39-day purchase gap, indicating recent lapsing risk. The supplied top categories (Outdoor, Electronics, Home) align well with gear repair and maintenance messaging. The annual gear credit and extended return window are verified Platinum benefits that reward loyalty without requiring a new promotional code or discount. The 60-day return window is particularly relevant for an online-leaning shopper (0.55 ratio) considering higher-value Outdoor or Electronics purchases. These existing benefits are timely, policy-backed, and directly tied to the customer's tier and shopping patterns.

### Retrieved chunk IDs

- `loyalty-program-terms.md:start_index=4337`
- `loyalty-program-terms.md:start_index=3630`
- `return-policy.md:start_index=614`
- `return-policy.md:start_index=2082`
- `loyalty-program-terms.md:start_index=2987`

### Retrieved policy excerpts

**loyalty-program-terms.md, start index 4337**

Offer codes are void if the account is closed, if the offer's stated conditions are not met, or after the stated expiry date. Expired offers **cannot be reinstated by customer service or by any automated system.**

### 5.1 Retention Offers

Retention offers are generated for members identified as at risk of lapsing. These offers:

- Are valid for **45 days** from issue unless stated otherwise
- Are limited to **one active retention offer per member** at a time
- May not be combined with another retention offer
- Do not extend, alter, or waive any provision of the returns policy

**loyalty-program-terms.md, start index 3630**

Benefits are tied to the member's tier at the time the benefit is used, except the return window, which is fixed at the tier held **at the time of purchase** (see POL-RET-004 §1.1).

### 4.1 Annual Gear Credit

Platinum members receive a **$100 gear credit** each January 1. The credit expires December 31 of the same year, does not carry over, has no cash value, and is forfeited if the member is downgraded below Platinum before using it.

---

## 5. Promotional Offers

Targeted offers issued to a member are **single-use, non-transferable, and tied to the member account**. Offers may not be stacked with other targeted offers, though a targeted offer may generally be combined with points redemption.

**return-policy.md, start index 614**

### 1.1 Extended Window for Platinum Members

**Platinum loyalty members receive a 60-day return window** on all eligible merchandise. This is an automatic benefit; the member does not need to request it and no approval is required.

The extended window applies based on the member's tier **at the time of purchase**, not at the time of return. A customer who was Gold when they purchased and reached Platinum afterwards receives the standard 30-day window for that order.

### 1.2 Holiday Purchases

Merchandise purchased between **November 1 and December 24** may be returned through **January 31** of the following year, regardless of tier. Where the holiday window and a member's standard window conflict, the customer receives whichever is longer.

---

## 2. Refund Method

**return-policy.md, start index 2082**

---

## 3. Condition Requirements

To be eligible for return, merchandise must be:

- Unworn, unwashed, and free of damage beyond normal inspection
- Accompanied by all original tags, packaging, and included accessories
- Presented with proof of purchase (receipt, order number, or loyalty account lookup)

Footwear must be returned in its original box. A footwear return without the box may be refused or assessed a $15 repackaging fee at the store manager's discretion.

---

## 4. Non-Returnable Merchandise

The following are **final sale** and cannot be returned or exchanged under any circumstance, including for Platinum members and including during the holiday window:

**loyalty-program-terms.md, start index 2987**

Points already redeemed against a subsequent purchase are not clawed back.

---

## 4. Tier Benefits

| Benefit | Bronze | Silver | Gold | Platinum |
|---|---|---|---|---|
| Points earn rate | 1× | 1.25× | 1.5× | 2× |
| Birthday reward | $5 | $10 | $20 | $40 |
| Free standard shipping | $75+ | $50+ | Always | Always |
| Free return shipping | No | No | Yes | Yes |
| Return window | 30 days | 30 days | 30 days | **60 days** |
| Early access to sales | No | 12 hours | 24 hours | 48 hours |
| Free gear repair | No | No | 2 per year | Unlimited |
| Dedicated support line | No | No | No | Yes |
| Annual gear credit | No | No | No | $100 |

### Review

- Policy claims verified against retrieved excerpts: [Complete after review]
- Tier benefits accurate: [Complete after review]
- Category recommendation relevant: [Complete after review]

---

## Example 4: CUST-10000588

### Customer profile

```json
{
  "churn_probability": 0.7,
  "loyalty_tier": "Silver",
  "total_lifetime_value": 1985.0,
  "days_since_last_purchase": 52,
  "avg_order_value": 132.3,
  "category_diversity_score": 0.375,
  "online_to_store_ratio": 0.61,
  "top_categories": [
    "Home",
    "Beauty"
  ]
}
```

### Input question

Generate a retention offer for this Silver member whose lifetime value is just under the Gold threshold.

### Generated offer

Subject: We miss you—earn extra points on Home and Beauty purchases

Body: It's been a while since we've seen you, and we'd love to welcome you back. As a Silver member, your Home and Beauty purchases earn 1.25 points per $1 of qualifying merchandise spend [POL-LOY-011], and orders of $50 or more qualify for free standard shipping [POL-SHP-007]—so your next visit can be rewarding. Shop now and reconnect with the gear you love.

Rationale: The customer's concentrated category purchases (Home, Beauty; diversity score 0.38) and predominantly online shopping pattern (ratio 0.61) make the Silver-tier points earn rate and conditional free-shipping threshold relevant retention incentives. The 52-day purchase gap and 70% churn probability support a timely, benefit-focused welcome-back message without inventing new promotions or asserting unverified tier status.

### Retrieved chunk IDs

- `loyalty-program-terms.md:start_index=4337`
- `loyalty-program-terms.md:start_index=3630`
- `loyalty-program-terms.md:start_index=2987`
- `return-policy.md:start_index=614`
- `loyalty-program-terms.md:start_index=1461`

### Retrieved policy excerpts

**loyalty-program-terms.md, start index 4337**

Offer codes are void if the account is closed, if the offer's stated conditions are not met, or after the stated expiry date. Expired offers **cannot be reinstated by customer service or by any automated system.**

### 5.1 Retention Offers

Retention offers are generated for members identified as at risk of lapsing. These offers:

- Are valid for **45 days** from issue unless stated otherwise
- Are limited to **one active retention offer per member** at a time
- May not be combined with another retention offer
- Do not extend, alter, or waive any provision of the returns policy

**loyalty-program-terms.md, start index 3630**

Benefits are tied to the member's tier at the time the benefit is used, except the return window, which is fixed at the tier held **at the time of purchase** (see POL-RET-004 §1.1).

### 4.1 Annual Gear Credit

Platinum members receive a **$100 gear credit** each January 1. The credit expires December 31 of the same year, does not carry over, has no cash value, and is forfeited if the member is downgraded below Platinum before using it.

---

## 5. Promotional Offers

Targeted offers issued to a member are **single-use, non-transferable, and tied to the member account**. Offers may not be stacked with other targeted offers, though a targeted offer may generally be combined with points redemption.

**loyalty-program-terms.md, start index 2987**

Points already redeemed against a subsequent purchase are not clawed back.

---

## 4. Tier Benefits

| Benefit | Bronze | Silver | Gold | Platinum |
|---|---|---|---|---|
| Points earn rate | 1× | 1.25× | 1.5× | 2× |
| Birthday reward | $5 | $10 | $20 | $40 |
| Free standard shipping | $75+ | $50+ | Always | Always |
| Free return shipping | No | No | Yes | Yes |
| Return window | 30 days | 30 days | 30 days | **60 days** |
| Early access to sales | No | 12 hours | 24 hours | 48 hours |
| Free gear repair | No | No | 2 per year | Unlimited |
| Dedicated support line | No | No | No | Yes |
| Annual gear credit | No | No | No | $100 |

**return-policy.md, start index 614**

### 1.1 Extended Window for Platinum Members

**Platinum loyalty members receive a 60-day return window** on all eligible merchandise. This is an automatic benefit; the member does not need to request it and no approval is required.

The extended window applies based on the member's tier **at the time of purchase**, not at the time of return. A customer who was Gold when they purchased and reached Platinum afterwards receives the standard 30-day window for that order.

### 1.2 Holiday Purchases

Merchandise purchased between **November 1 and December 24** may be returned through **January 31** of the following year, regardless of tier. Where the holiday window and a member's standard window conflict, the customer receives whichever is longer.

---

## 2. Refund Method

**loyalty-program-terms.md, start index 1461**

Members receive email notice **30 days before** a scheduled downgrade.

### 2.3 Tier Protection

A member who has held Gold or Platinum for **24 consecutive months or longer** is protected from a single downgrade evaluation once per rolling 24-month period. Protection applies automatically and cannot be requested, deferred, or transferred.

---

## 3. Points

Members earn **1 point per $1** of qualifying merchandise spend.

| Tier | Earn rate | Effective value |
|---|---|---|
| Bronze | 1× | 1 point per $1 |
| Silver | 1.25× | 1.25 points per $1 |
| Gold | 1.5× | 1.5 points per $1 |
| Platinum | 2× | 2 points per $1 |

### Review

- Policy claims verified against retrieved excerpts: [Complete after review]
- Tier benefits accurate: [Complete after review]
- Category recommendation relevant: [Complete after review]

---

## Example 5: CUST-DEMO-005

### Customer profile

```json
{
  "customer_id": "CUST-DEMO-005",
  "loyalty_tier": "Silver",
  "churn_probability": 0.62,
  "days_since_last_purchase": 45,
  "total_lifetime_value": 1250.0,
  "avg_order_value": 95.0,
  "category_diversity_score": 0.375,
  "online_to_store_ratio": 0.6,
  "top_categories": [
    "Home",
    "Beauty"
  ]
}
```

### Input question

Generate a personalized retention offer for this Silver member interested in Home and Beauty products.

### Generated offer

Subject: We miss you—earn extra points on Home and Beauty purchases

Body: It's been a while since we've seen you, and we'd love to have you back. As a Silver member, your Home and Beauty purchases earn 1.25 points per $1 of qualifying merchandise spend [POL-LOY-011], and orders of $50 or more qualify for free standard shipping [POL-SHP-007]—so your next visit rewards you for shopping in the categories you love most. Come back and pick up where you left off.

Rationale: The customer has concentrated purchases in Home and Beauty (low category diversity), a 45-day purchase gap, and a 62% churn probability. Silver tier is supplied and unverified by current membership status, but the customer's lifetime value ($1,250) and average order value ($95) align with Silver-tier spending patterns. The 1.25× points earn rate and $50 free-shipping threshold are existing Silver benefits directly applicable to the customer's top categories and typical order size, making them relevant retention incentives without requiring a new promotion or discount.

### Retrieved chunk IDs

- `loyalty-program-terms.md:start_index=4337`
- `loyalty-program-terms.md:start_index=3630`
- `return-policy.md:start_index=614`
- `loyalty-program-terms.md:start_index=2987`
- `loyalty-program-terms.md:start_index=1461`

### Retrieved policy excerpts

**loyalty-program-terms.md, start index 4337**

Offer codes are void if the account is closed, if the offer's stated conditions are not met, or after the stated expiry date. Expired offers **cannot be reinstated by customer service or by any automated system.**

### 5.1 Retention Offers

Retention offers are generated for members identified as at risk of lapsing. These offers:

- Are valid for **45 days** from issue unless stated otherwise
- Are limited to **one active retention offer per member** at a time
- May not be combined with another retention offer
- Do not extend, alter, or waive any provision of the returns policy

**loyalty-program-terms.md, start index 3630**

Benefits are tied to the member's tier at the time the benefit is used, except the return window, which is fixed at the tier held **at the time of purchase** (see POL-RET-004 §1.1).

### 4.1 Annual Gear Credit

Platinum members receive a **$100 gear credit** each January 1. The credit expires December 31 of the same year, does not carry over, has no cash value, and is forfeited if the member is downgraded below Platinum before using it.

---

## 5. Promotional Offers

Targeted offers issued to a member are **single-use, non-transferable, and tied to the member account**. Offers may not be stacked with other targeted offers, though a targeted offer may generally be combined with points redemption.

**return-policy.md, start index 614**

### 1.1 Extended Window for Platinum Members

**Platinum loyalty members receive a 60-day return window** on all eligible merchandise. This is an automatic benefit; the member does not need to request it and no approval is required.

The extended window applies based on the member's tier **at the time of purchase**, not at the time of return. A customer who was Gold when they purchased and reached Platinum afterwards receives the standard 30-day window for that order.

### 1.2 Holiday Purchases

Merchandise purchased between **November 1 and December 24** may be returned through **January 31** of the following year, regardless of tier. Where the holiday window and a member's standard window conflict, the customer receives whichever is longer.

---

## 2. Refund Method

**loyalty-program-terms.md, start index 2987**

Points already redeemed against a subsequent purchase are not clawed back.

---

## 4. Tier Benefits

| Benefit | Bronze | Silver | Gold | Platinum |
|---|---|---|---|---|
| Points earn rate | 1× | 1.25× | 1.5× | 2× |
| Birthday reward | $5 | $10 | $20 | $40 |
| Free standard shipping | $75+ | $50+ | Always | Always |
| Free return shipping | No | No | Yes | Yes |
| Return window | 30 days | 30 days | 30 days | **60 days** |
| Early access to sales | No | 12 hours | 24 hours | 48 hours |
| Free gear repair | No | No | 2 per year | Unlimited |
| Dedicated support line | No | No | No | Yes |
| Annual gear credit | No | No | No | $100 |

**loyalty-program-terms.md, start index 1461**

Members receive email notice **30 days before** a scheduled downgrade.

### 2.3 Tier Protection

A member who has held Gold or Platinum for **24 consecutive months or longer** is protected from a single downgrade evaluation once per rolling 24-month period. Protection applies automatically and cannot be requested, deferred, or transferred.

---

## 3. Points

Members earn **1 point per $1** of qualifying merchandise spend.

| Tier | Earn rate | Effective value |
|---|---|---|
| Bronze | 1× | 1 point per $1 |
| Silver | 1.25× | 1.25 points per $1 |
| Gold | 1.5× | 1.5 points per $1 |
| Platinum | 2× | 2 points per $1 |

### Review

- Policy claims verified against retrieved excerpts: [Complete after review]
- Tier benefits accurate: [Complete after review]
- Category recommendation relevant: [Complete after review]

---

## Failure case 1 — Incorrect loyalty-tier benefit

**Failure condition:** The generated offer promises a benefit belonging to a higher loyalty tier, or treats the feature-store tier as definitive when trailing-12-month spend could disagree.

**Fix proposed:** Require explicit support for every tier-specific benefit in the retrieved policy. Qualify uncertain tier eligibility and consult the authoritative loyalty record when available.

**Evidence:** Add the actual affected example number and quote the generated claim and conflicting policy excerpt if observed. Otherwise, label this as a potential failure mode, not an observed model failure.

## Failure case 2 — Unsupported claim or irrelevant offer

**Failure condition:** The offer adds an unsupported promotion, return window, deadline, or benefit, or recommends products unrelated to the customer's stated interests.

**Fix proposed:** Restrict policy claims to retrieved evidence, include the customer profile in evaluation contexts, remove invented deadlines, and verify category relevance before presenting the offer.

**Evidence:** Add the actual affected example number and the generated claim if observed. Otherwise, retain this as a potential failure mode until a real output demonstrates it.
