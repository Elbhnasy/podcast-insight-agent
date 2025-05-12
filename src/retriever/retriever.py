from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
import os

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("podcast-summaries")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

def retrieve_and_respond(query: str, llm, top_k: int = 5, min_score: float = 0.30):
    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        namespace="summaries"
    )

    # Direct similarity search with scores
    results_with_scores = vector_store.similarity_search_with_score(query=query, k=top_k)

    # Filter by score
    high_score_docs = []
    metadata_list = []

    for doc, score in results_with_scores:
        if score >= min_score:
            high_score_docs.append(doc)
            metadata_list.append(doc.metadata)

    context = "\n\n".join([
        f"Title: {doc.metadata.get('podcast_title', '')}\nSummary:\n{doc.page_content}"
        for doc in high_score_docs
    ])

    # Create a more comprehensive prompt template with better context handling
    prompt_template = PromptTemplate(
        input_variables=["context", "question", "source_count"],
        template=(
            "You are an expert AI analyst specializing in podcast content analysis.\n\n"
            "Below are {source_count} relevant podcast summaries related to the user's question:\n\n"
            "{context}\n\n"
            "TASK: Answer the question below using ONLY information from these podcast summaries.\n"
            "- Cite specific podcasts using [Title] format when referencing information\n"
            "- If the information provided is insufficient, clearly state what's missing\n"
            "- Maintain a neutral, analytical tone throughout\n"
            "- Structure complex answers with bullet points when appropriate\n"
            "- Do NOT fabricate information not present in the summaries\n\n"
            "Question: {question}\n\n"
            "Answer: "
        )
    )

    # Handle empty results case
    if not high_score_docs:
        return ("I don't have enough information from the podcast database to answer "
                "this question confidently. Could you try asking something related to "
                "recent AI developments, tools, or insights from tech podcasts?"), []

    # Format the response with improved prompt
    final_prompt = prompt_template.format(
        context=context, 
        question=query,
        source_count=len(high_score_docs)
    )
    
    response_content = llm.invoke(final_prompt).content
    
    # Add a footnote with sources if we have results
    if high_score_docs:
        source_list = "\n\n**Sources:**\n" + "\n".join([
            f"- {doc.metadata.get('podcast_title', 'Untitled')} ({doc.metadata.get('podcast_url', 'No URL')})"
            for doc in high_score_docs
        ])
        response_content += source_list
        
    return response_content, metadata_list