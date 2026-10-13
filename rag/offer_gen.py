from pathlib import Path
from typing import Any

from langchain_aws import BedrockEmbeddings, ChatBedrock
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

embedding_model = "amazon.titan-embed-text-v2:0"
gen_model = "anthropic.claude-3-haiku-20240307-v1:0"

chunks = 800
overlap = 120
top_n = 5

rag_dir = Path(__file__).parent

def load_prompt_template(template_number):
    template_path = rag_dir / f"template_{template_number}.md"

    if not template_path.is_file():
        raise FileNotFoundError(
            f"Prompt template not found: {template_path}"
        )

    return template_path.read_text(encoding="utf-8")

def load_policy_documents():
    files = list((rag_dir.parent / "northstar-policy-docs").glob("*.md"))
    documents = []

    for file in files:
        text = file.read_text(encoding="utf-8").strip()

        if text:
            documents.append({
                "text": text,
                "source": file.name,
            })

    return documents


def split_policy_documents(documents):
    from langchain_core.documents import Document

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = chunks,
        chunk_overlap = overlap,
        add_start_index=True,
    )
    source_documents = []

    for document in documents:
        source_documents.append(Document(page_content=document["text"],metadata={"source": document["source"]},))
    return splitter.split_documents(source_documents)

#Embedding model creates the FAISS index
def build_vector_store(chunks):
    embeddings = BedrockEmbeddings(
        model_id=embedding_model,
    )
    return FAISS.from_documents(chunks, embeddings)

#Brings back only the top n 
def retrieve_policy_context(vector_store,question,):
    return vector_store.similarity_search(question, k=top_n)

#Calls claude to interpret the answer
def generate_offer(customer_context, question,vector_store):
    retrieved_documents = retrieve_policy_context(
        vector_store,
        f"Customer profile: {customer_context}\nRequest: {question}",
    )

    contexts = [document.page_content for document in retrieved_documents]

    if not contexts:
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

    system_prompt = load_prompt_template(1).format(
        retrieved_context=policy_context
    )

    customer_prompt = load_prompt_template(2).format(
        customer_id=customer_context.get("customer_id", "Unknown"),
        loyalty_tier=customer_context.get("loyalty_tier", "Unknown"),
        churn_probability=customer_context.get("churn_probability", 0),
        days_since_last_purchase=customer_context.get(
            "days_since_last_purchase", "Unknown"
        ),
        total_lifetime_value=customer_context.get(
            "total_lifetime_value", 0
        ),
        avg_order_value=customer_context.get("avg_order_value", 0),
        category_diversity_score=customer_context.get(
            "category_diversity_score", 0
        ),
        online_to_store_ratio=customer_context.get(
            "online_to_store_ratio", 0
        ),
        top_categories=", ".join(
            customer_context.get("top_categories", [])
        ) or "Unknown",
    )

    safety_prompt = load_prompt_template(5)

    prompt = (
        f"{system_prompt}\n\n"
        f"{safety_prompt}\n\n"
        f"{customer_prompt}\n\n"
        "Follow the system prompt's policy-citation requirements."
    )

    llm = ChatBedrock(model_id=gen_model, model_kwargs={"temperature": 0.1, "max_tokens": 300,},)

    response = llm.invoke(prompt)

    return {"answer": str(response.content).strip(),"contexts": contexts,}


if __name__ == "__main__":
    documents = load_policy_documents()
    chunks = split_policy_documents(documents)

    print(f"Loaded {len(documents)} policy documents.")
    print(f"Created {len(chunks)} chunks.")
    print("No Bedrock calls were made.")