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
    files = list(Path("/northstar-policy-docs").glob("*.md"))
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

    prompt = f"""
You are NorthStar's retention-offer assistant.

Generate a personalized offer in 2-3 sentences using only the customer
profile and policy excerpts below.

Rules:
- Recommend a category only from the customer's top_categories.
- Do not invent discounts, promo codes, products, or bonus points.
- Do not promise benefits unless eligibility is supported by the evidence.
- Loyalty tiers are determined by trailing 12-month qualifying spend.
  If the supplied tier has not been verified against that rule, qualify
  tier-specific benefits instead of promising them.
- Respect shipping restrictions, return windows, final-sale exclusions,
  and retention-offer combination rules.
- Retention offers are generally valid for 45 days unless the policy says
  otherwise.
- Include the source filename or policy ID in your answer.

Customer profile:
{customer_context}

Request:
{question}

Retrieved policy excerpts:
{policy_context}

Write the offer now.
"""

    llm = ChatBedrock(model_id=gen_model, model_kwargs={"temperature": 0.1, "max_tokens": 300,},)

    response = llm.invoke(prompt)

    return {"answer": str(response.content).strip(),"contexts": contexts,}


if __name__ == "__main__":
    documents = load_policy_documents()
    chunks = split_policy_documents(documents)

    print(f"Loaded {len(documents)} policy documents.")
    print(f"Created {len(chunks)} chunks.")
    print("No Bedrock calls were made.")