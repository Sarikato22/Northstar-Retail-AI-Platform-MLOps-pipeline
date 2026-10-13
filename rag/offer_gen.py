from pathlib import Path
from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

embedding_model = "amazon.titan-embed-text-v2:0"
gen_model = "anthropic.claude-3-haiku-20240307-v1:0"

chunk_size = 800
chunk_overlap = 120
top_n = 5

rag_dir = Path(__file__).parent
policy_dir = rag_dir.parent / "northstar-policy-docs"

#Ignore FAQ in folder
policy_sources = [
    "loyalty-program-terms.md",
    "shipping-policy.md",
    "return-policy.md",
]

_vector_store = None #will use it to cache and same time

## Load a prompt template from the rag folder
def load_prompt_template(template_number):
    template_path = rag_dir / f"template_{template_number}.md"

    if not template_path.is_file():
        raise FileNotFoundError(
            f"Prompt template not found: {template_path}"
        )

    return template_path.read_text(encoding="utf-8")


## Read policy files and store their text and source names
def load_policy_documents():
    documents = []

    for file in sorted(policy_dir.glob("*.md")):
        text = file.read_text(encoding="utf-8").strip()

        if text:
            documents.append(
                Document(
                    page_content=text,
                    metadata={"source": file.name},
                )
            )

    if not documents:
        raise FileNotFoundError(
            f"No policy documents found in {policy_dir}"
        )

    return documents


## Split long policy documents into smaller overlapping chunks
def split_policy_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )

    return splitter.split_documents(documents)


## Embed the policy chunks and create a searchable FAISS index
def build_vector_store(document_chunks):
    embeddings = BedrockEmbeddings(model_id=embedding_model,)
    return FAISS.from_documents(document_chunks, embeddings)


##Searching policy chunks
def retrieve_policy_context(vector_store, question, customer_context):
    loyalty_tier = customer_context.get("loyalty_tier", "unknown")

    query = (
        f"Customer request: {question}\n"
        f"Customer loyalty tier: {loyalty_tier}\n"
        "Relevant policy topics: loyalty entitlements, points earning, "
        "birthday rewards, shipping thresholds, return windows, "
        "final-sale exclusions, and retention-offer restrictions"
    )

    #Ignoring FAQ
    policy_filter = {"source": {"$in": policy_sources}}

    return vector_store.similarity_search(query,k=top_n,filter=policy_filter,)

def generate_offer(customer_context, question, vector_store):
    retrieved_documents = retrieve_policy_context(vector_store,question,customer_context,)

    contexts = [document.page_content for document in retrieved_documents]
    #Fallback
    if not retrieved_documents:
        return {
            "answer": (
                "Please contact NorthStar support to confirm which "
                "retention offers and benefits are currently available."
            ),
            "contexts": [],
        }
    policy_context = "\n\n".join(
        f"Source: {document.metadata.get('source', 'unknown')}\n"
        f"{document.page_content}"
        for document in retrieved_documents
    )

    ## Insert retrieved policies into Template 1
    system_prompt = load_prompt_template(1).replace(
        "{retrieved_context}",
        policy_context,
    )
    top_categories = customer_context.get("top_categories", [])

    if isinstance(top_categories, str):
        top_categories = [top_categories] if top_categories else []

    ## Filling Template 2, with customers info
    customer_prompt = load_prompt_template(2).format(
        customer_id=customer_context.get("customer_id", "Unknown"),
        loyalty_tier=customer_context.get("loyalty_tier", "Unknown"),
        churn_probability=float(
            customer_context.get("churn_probability") or 0
        ),
        days_since_last_purchase=customer_context.get(
            "days_since_last_purchase", "Unknown"
        ),
        total_lifetime_value=float(
            customer_context.get("total_lifetime_value") or 0
        ),
        avg_order_value=float(
            customer_context.get("avg_order_value") or 0
        ),
        category_diversity_score=float(
            customer_context.get("category_diversity_score") or 0
        ),
        online_to_store_ratio=float(
            customer_context.get("online_to_store_ratio") or 0
        ),
        top_categories=", ".join(
            str(category) for category in top_categories
        ) or "Unknown",
    )

    ## Load tier-specific benefit rules and safety restrictions
    tier_prompt = load_prompt_template(3)
    safety_prompt = load_prompt_template(5)

    #Combining
    prompt = (
        f"{system_prompt}\n\n"
        f"Tier-specific benefit guidelines:\n{tier_prompt}\n\n"
        f"{safety_prompt}\n\n"
        f"{customer_prompt}\n\n"
        "Follow the policy-citation requirements. "
        "Use only the retrieved policy context to support policy claims."
    )

    ## Send the propmt to Claude through Bedrock
    llm = ChatBedrock(
        model_id=gen_model,
        model_kwargs={
            "temperature": 0.1,
            "max_tokens": 300,
        },
    )

    response = llm.invoke(prompt)

    return {"answer": str(response.content).strip(),"contexts": contexts,}


## Function signature expected by the evaluation harness
def rag_invoke_fn(customer_context, question):
    global _vector_store

    ## Build the index on the first call, then reuse it
    if _vector_store is None:
        documents = load_policy_documents()
        document_chunks = split_policy_documents(documents)
        _vector_store = build_vector_store(document_chunks)

    return generate_offer(
        customer_context,
        question,
        _vector_store,
    )

if __name__ == "__main__":
    documents = load_policy_documents()
    document_chunks = split_policy_documents(documents)

    # print(f"Loaded {len(documents)} policy documents.")
    # print(f"Created {len(document_chunks)} chunks.")
    # print("Local document check complete. No Bedrock calls were made.")