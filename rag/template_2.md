Generate a personalized retention email for the following at-risk customer.
Follow the system prompt and use only benefits supported by the retrieved
policy context.

## Customer Profile
- Customer ID: {customer_id}
- Loyalty Tier: {loyalty_tier}
- Churn Probability: {churn_probability:.0%}
- Days Since Last Purchase: {days_since_last_purchase}
- Total Lifetime Value: ${total_lifetime_value:,.2f}
- Average Order Value: ${avg_order_value:.2f}
- Category Diversity Score: {category_diversity_score:.2f} (0–1; distinct categories / 8)
- Online-to-Store Ratio: {online_to_store_ratio:.2f} (1.0 = purely online; 0.0 = purely in store)
- Top Product Categories: {top_categories}

## How to Interpret the Customer Signals
Use these interpretations to select relevant messaging. Do not treat them
as additional policy permissions.

- Loyalty Tier:
  Use the supplied label to guide benefit selection and retrieval.
  If it is derived from lifetime value or is otherwise unverified,
  phrase tier-dependent benefits conditionally.
  Do not infer current membership from lifetime value or average order value.

- Churn Probability:
  A higher value indicates greater predicted risk of leaving.
  Use it to motivate relevant retention messaging, not to justify stronger
  discounts, policy exceptions, or claims about the customer's intentions.

- Days Since Last Purchase:
  A larger value indicates a longer purchase gap.
  It may support welcoming the customer back, but does not establish
  dissatisfaction, an expired account, or an imminent points deadline.

- Total Lifetime Value:
  This is historical customer value, not trailing 12-month qualifying spend,
  a points balance, or eligibility for additional benefits.

- Average Order Value:
  Use this as context when considering whether a policy-backed spending
  threshold is a relevant incentive.
  It does not establish the value of the customer's next order or guarantee
  that the customer qualifies for free shipping.

- Category Diversity Score:
  Lower values indicate purchases concentrated in fewer categories.
  Higher values indicate purchases spread across more categories.
  For concentrated shoppers, prioritize a familiar category.
  For broader shoppers, you may reference multiple supplied top categories.
  Do not invent an unlisted category preference or assume the customer wants
  cross-category discovery.

- Online-to-Store Ratio:
  Values closer to 1 indicate more online shopping; values closer to 0
  indicate more in-store shopping.
  Prefer a relevant shipping benefit for predominantly online shoppers
  when eligibility and necessary conditions are supported.
  Prefer a relevant non-shipping benefit for predominantly in-store shoppers.
  Do not assume the customer never uses the less frequent channel.

- Top Product Categories:
  These are the source of category personalization.
  Reference at least one supplied category; do not invent products, prices,
  inventory, or category preferences.

## Task
Write an email subject line and one opening paragraph.

1. Reference at least one category from Top Product Categories.
2. Include one specific policy-supported incentive.
   If current tier is verified, use a benefit applicable to that tier.
   If tier is unverified, express tier-dependent eligibility conditionally.
   Do not assert that the customer currently holds the supplied tier.
3. Choose an incentive relevant to the customer's shopping patterns.
   An existing loyalty benefit is acceptable; do not describe it as a
   newly issued promotion.
4. Include a clear call to action.
5. Use a timely invitation to return, rather than claiming a deadline.
   Mention expiration or limited-time availability only when the supplied
   data and retrieved policies establish that it applies to this customer.
6. Include any material conditions needed to make the incentive accurate.
7. Do not expose the customer ID, churn score, lifetime value, or other
   internal analytics in the customer-facing Subject or Body.
8. If the inputs do not support a category or eligible incentive, state
   the limitation instead of fabricating an offer.

## Output Format
Subject: [customer-facing subject line]
Body: [one customer-facing paragraph of 2–3 sentences]
Rationale: [one internal sentence explaining how the supplied customer
signals support the chosen category and incentive]

Keep the Rationale separate from the customer-facing email.
Follow the system prompt's policy-citation requirements.