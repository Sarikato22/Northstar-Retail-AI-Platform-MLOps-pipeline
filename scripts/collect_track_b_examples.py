import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evaluation_harness import OFFER_TEST_CASES, RAGTestCase
from rag.offer_gen import (
    load_policy_documents,
    split_policy_documents,
    build_vector_store,
    retrieve_policy_context,
    generate_offer,
)

ROOT = Path.cwd()
OUTPUT = ROOT / "docs/lab3-evidence/track-b-examples.md"

# Five examples: the four official harness cases plus one additional case.
examples = list(OFFER_TEST_CASES)

examples.append(
    RAGTestCase(
        customer_id="CUST-DEMO-005",
        customer_context={
            "customer_id": "CUST-DEMO-005",
            "loyalty_tier": "Silver",
            "churn_probability": 0.62,
            "days_since_last_purchase": 45,
            "total_lifetime_value": 1250.00,
            "avg_order_value": 95.00,
            "category_diversity_score": 0.375,
            "online_to_store_ratio": 0.60,
            "top_categories": ["Home", "Beauty"],
        },
        question=(
            "Generate a personalized retention offer for this Silver "
            "member interested in Home and Beauty products."
        ),
        ground_truth=(
            "Recommend Home or Beauty products and only claim Silver "
            "benefits supported by the policy."
        ),
    )
)

print("Loading policies and building FAISS index...")
documents = load_policy_documents()
chunks = split_policy_documents(documents)
vector_store = build_vector_store(chunks)

lines = [
    "# Track B — RAG Input/Output Examples",
    "",
    f"Generated: {datetime.now().isoformat(timespec='seconds')}",
    "",
    f"Policy documents: {len(documents)}",
    f"Indexed chunks: {len(chunks)}",
    "",
    "Offers below are outputs from the running RAG pipeline. "
    "Review each answer against the retrieved policies before "
    "describing it as correct.",
    "",
]

for i, tc in enumerate(examples, start=1):
    print(f"[{i}/5] Generating offer for {tc.customer_id}...")

    retrieved = retrieve_policy_context(
        vector_store,
        tc.question,
        tc.customer_context,
    )

    result = generate_offer(
        tc.customer_context,
        tc.question,
        vector_store,
    )

    lines.extend([
        f"## Example {i}: {tc.customer_id}",
        "",
        "### Customer profile",
        "",
        "```json",
        __import__("json").dumps(
            tc.customer_context, indent=2, default=str
        ),
        "```",
        "",
        "### Input question",
        "",
        tc.question,
        "",
        "### Generated offer",
        "",
        result["answer"],
        "",
        "### Retrieved chunk IDs",
        "",
    ])

    if retrieved:
        for doc in retrieved:
            source = doc.metadata.get("source", "unknown")
            start = doc.metadata.get("start_index", "unknown")
            lines.append(f"- `{source}:start_index={start}`")
    else:
        lines.append("- No chunks retrieved.")

    lines.extend(["", "### Retrieved policy excerpts", ""])

    for doc in retrieved:
        source = doc.metadata.get("source", "unknown")
        start = doc.metadata.get("start_index", "unknown")
        lines.extend([
            f"**{source}, start index {start}**",
            "",
            doc.page_content,
            "",
        ])

    lines.extend([
        "### Review",
        "",
        "- Policy claims verified against retrieved excerpts: "
        "[Complete after review]",
        "- Tier benefits accurate: [Complete after review]",
        "- Category recommendation relevant: [Complete after review]",
        "",
        "---",
        "",
    ])

lines.extend([
    "## Failure case 1 — Incorrect loyalty-tier benefit",
    "",
    "**Failure condition:** The generated offer promises a benefit "
    "belonging to a higher loyalty tier, or treats the feature-store "
    "tier as definitive when trailing-12-month spend could disagree.",
    "",
    "**Fix proposed:** Require explicit support for every tier-specific "
    "benefit in the retrieved policy. Qualify uncertain tier eligibility "
    "and consult the authoritative loyalty record when available.",
    "",
    "**Evidence:** Add the actual affected example number and quote "
    "the generated claim and conflicting policy excerpt if observed. "
    "Otherwise, label this as a potential failure mode, not an observed "
    "model failure.",
    "",
    "## Failure case 2 — Unsupported claim or irrelevant offer",
    "",
    "**Failure condition:** The offer adds an unsupported promotion, "
    "return window, deadline, or benefit, or recommends products "
    "unrelated to the customer's stated interests.",
    "",
    "**Fix proposed:** Restrict policy claims to retrieved evidence, "
    "include the customer profile in evaluation contexts, remove "
    "invented deadlines, and verify category relevance before "
    "presenting the offer.",
    "",
    "**Evidence:** Add the actual affected example number and the "
    "generated claim if observed. Otherwise, retain this as a potential "
    "failure mode until a real output demonstrates it.",
    "",
])

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text("\n".join(lines), encoding="utf-8")

print(f"\nSaved: {OUTPUT}")
print("Review the offers and complete the review fields before submitting.")